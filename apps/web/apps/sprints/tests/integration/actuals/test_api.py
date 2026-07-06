"""Integration tests for sprint actuals API endpoints."""

from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.sprints.constants import SprintDataImportStatus, SprintDataImportType
from apps.sprints.models import SprintDataImport
from apps.sprints.tests.factories import FakeCsvFile, make_sprint
from apps.teams.tests.factories import make_team
from apps.users.tests.factories import make_user

# ── URL helpers ───────────────────────────────────────────────────────────────

ACTUALS_UPLOAD_URL = "/api/v1/sprints/{sprint}/actuals/{team}/upload/"
ACTUALS_IMPORTS_URL = "/api/v1/sprints/{sprint}/actuals/{team}/imports/"
ACTUALS_TEMPLATE_URL = "/api/v1/sprints/{sprint}/actuals/template/"
ACTUALS_IMPORT_DETAIL_URL = "/api/v1/sprints/{sprint}/actuals/{import_code}/"
ACTUALS_IMPORT_ROWS_URL = "/api/v1/sprints/{sprint}/actuals/{import_code}/rows/"
ACTUALS_IMPORT_ROW_DETAIL_URL = (
    "/api/v1/sprints/{sprint}/actuals/{import_code}/rows/{row_code}/"
)
ACTUALS_REVIEW_URL = "/api/v1/sprints/{sprint}/actuals/{import_code}/review/"
ACTUALS_CONFIRM_URL = "/api/v1/sprints/{sprint}/actuals/{import_code}/confirm/"
ACTUALS_REVIEW_COMPLETE_URL = "/api/v1/sprints/{sprint}/actuals/review-complete/"
ACTUALS_PROJECTS_URL = "/api/v1/sprints/{sprint}/actuals/projects/"
ACTUALS_SYNC_URL = "/api/v1/sprints/{sprint}/actuals/sync-project-actuals/"

CSV_HEADER = "Story Type,Jira ID,Title,Assignee,Efforts,Sprint,Label,Mapping\n"
CSV_ROW = (
    "Story,JIRA-1,Test Title,user@example.com,3600,Sprint 1,sample-label,PROJECT\n"
)


def _make_valid_csv(rows: int = 1) -> FakeCsvFile:
    content = CSV_HEADER + (CSV_ROW * rows)
    return FakeCsvFile(content, name="actuals.csv")


def _upload(client, sprint, team, csv_file=None):
    """Helper that uploads a CSV for a team and returns the response."""
    if csv_file is None:
        csv_file = _make_valid_csv()
    url = ACTUALS_UPLOAD_URL.format(sprint=sprint.code, team=team.code)
    return client.post(url, {"file": csv_file}, format="multipart")


# ── POST …/actuals/<team>/upload/ ─────────────────────────────────────────────


class ActualsUploadTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.sprint = make_sprint()
        self.team = make_team()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        url = ACTUALS_UPLOAD_URL.format(sprint=self.sprint.code, team=self.team.code)
        response = self.client.post(
            url, {"file": _make_valid_csv()}, format="multipart"
        )
        self.assertEqual(response.status_code, 401)

    def test_valid_upload_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = _upload(self.client, self.sprint, self.team)
        self.assertEqual(response.status_code, 200)

    def test_upload_creates_sprint_data_import_record(self):
        self.client.force_authenticate(user=self.user)
        _upload(self.client, self.sprint, self.team)
        self.assertTrue(
            SprintDataImport.objects.filter(
                sprint=self.sprint,
                team=self.team,
                import_type=SprintDataImportType.ACTUAL,
            ).exists()
        )

    def test_upload_response_contains_expected_fields(self):
        self.client.force_authenticate(user=self.user)
        response = _upload(self.client, self.sprint, self.team)
        data = response.data["data"]
        for field in ("code", "import_type", "version_number", "file_name", "status"):
            self.assertIn(field, data)

    def test_upload_response_import_type_is_actual(self):
        self.client.force_authenticate(user=self.user)
        response = _upload(self.client, self.sprint, self.team)
        self.assertEqual(
            response.data["data"]["import_type"], SprintDataImportType.ACTUAL
        )

    def test_upload_response_status_is_active(self):
        self.client.force_authenticate(user=self.user)
        response = _upload(self.client, self.sprint, self.team)
        self.assertEqual(response.data["data"]["status"], SprintDataImportStatus.ACTIVE)

    def test_upload_version_starts_at_one(self):
        self.client.force_authenticate(user=self.user)
        response = _upload(self.client, self.sprint, self.team)
        self.assertEqual(response.data["data"]["version_number"], 1)

    def test_second_upload_increments_version(self):
        self.client.force_authenticate(user=self.user)
        _upload(self.client, self.sprint, self.team)
        response = _upload(self.client, self.sprint, self.team)
        self.assertEqual(response.data["data"]["version_number"], 2)

    def test_second_upload_supersedes_first(self):
        self.client.force_authenticate(user=self.user)
        _upload(self.client, self.sprint, self.team)
        _upload(self.client, self.sprint, self.team)
        superseded = SprintDataImport.objects.filter(
            sprint=self.sprint,
            team=self.team,
            import_type=SprintDataImportType.ACTUAL,
            status=SprintDataImportStatus.SUPERSEDED,
        )
        self.assertEqual(superseded.count(), 1)

    def test_upload_without_file_returns_422(self):
        self.client.force_authenticate(user=self.user)
        url = ACTUALS_UPLOAD_URL.format(sprint=self.sprint.code, team=self.team.code)
        response = self.client.post(url, {}, format="multipart")
        self.assertEqual(response.status_code, 422)

    def test_upload_non_csv_file_returns_422(self):
        self.client.force_authenticate(user=self.user)
        bad_file = FakeCsvFile("data", name="data.xlsx")
        url = ACTUALS_UPLOAD_URL.format(sprint=self.sprint.code, team=self.team.code)
        response = self.client.post(url, {"file": bad_file}, format="multipart")
        self.assertEqual(response.status_code, 422)

    def test_upload_with_missing_csv_columns_returns_422(self):
        self.client.force_authenticate(user=self.user)
        bad_file = FakeCsvFile("Title,Assignee\nTest,user@x.com\n", name="bad.csv")
        url = ACTUALS_UPLOAD_URL.format(sprint=self.sprint.code, team=self.team.code)
        response = self.client.post(url, {"file": bad_file}, format="multipart")
        self.assertEqual(response.status_code, 422)

    def test_upload_unknown_sprint_returns_404(self):
        self.client.force_authenticate(user=self.user)
        url = ACTUALS_UPLOAD_URL.format(sprint="SPRINT-9999", team=self.team.code)
        response = self.client.post(
            url, {"file": _make_valid_csv()}, format="multipart"
        )
        self.assertEqual(response.status_code, 404)

    def test_upload_unknown_team_returns_404(self):
        self.client.force_authenticate(user=self.user)
        url = ACTUALS_UPLOAD_URL.format(sprint=self.sprint.code, team="TEAM-9999")
        response = self.client.post(
            url, {"file": _make_valid_csv()}, format="multipart"
        )
        self.assertEqual(response.status_code, 404)

    def test_upload_inactive_team_returns_404(self):
        inactive_team = make_team(name="Inactive Team", is_active=False)
        self.client.force_authenticate(user=self.user)
        url = ACTUALS_UPLOAD_URL.format(
            sprint=self.sprint.code, team=inactive_team.code
        )
        response = self.client.post(
            url, {"file": _make_valid_csv()}, format="multipart"
        )
        self.assertEqual(response.status_code, 404)


# ── GET …/actuals/<team>/imports/ ─────────────────────────────────────────────


class ActualsListImportsTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.sprint = make_sprint()
        self.team = make_team()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        url = ACTUALS_IMPORTS_URL.format(sprint=self.sprint.code, team=self.team.code)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_returns_empty_list_when_no_imports(self):
        self.client.force_authenticate(user=self.user)
        url = ACTUALS_IMPORTS_URL.format(sprint=self.sprint.code, team=self.team.code)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["results"], [])

    def test_returns_one_import_after_upload(self):
        self.client.force_authenticate(user=self.user)
        _upload(self.client, self.sprint, self.team)
        url = ACTUALS_IMPORTS_URL.format(sprint=self.sprint.code, team=self.team.code)
        response = self.client.get(url)
        self.assertEqual(len(response.data["data"]["results"]), 1)

    def test_returns_multiple_imports(self):
        self.client.force_authenticate(user=self.user)
        _upload(self.client, self.sprint, self.team)
        _upload(self.client, self.sprint, self.team)
        url = ACTUALS_IMPORTS_URL.format(sprint=self.sprint.code, team=self.team.code)
        response = self.client.get(url)
        self.assertEqual(len(response.data["data"]["results"]), 2)

    def test_each_import_has_expected_fields(self):
        self.client.force_authenticate(user=self.user)
        _upload(self.client, self.sprint, self.team)
        url = ACTUALS_IMPORTS_URL.format(sprint=self.sprint.code, team=self.team.code)
        response = self.client.get(url)
        entry = response.data["data"]["results"][0]
        for field in ("code", "version_number", "file_name", "status"):
            self.assertIn(field, entry)

    def test_unknown_sprint_returns_404(self):
        self.client.force_authenticate(user=self.user)
        url = ACTUALS_IMPORTS_URL.format(sprint="SPRINT-9999", team=self.team.code)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_unknown_team_returns_404(self):
        self.client.force_authenticate(user=self.user)
        url = ACTUALS_IMPORTS_URL.format(sprint=self.sprint.code, team="TEAM-9999")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_does_not_return_forecast_imports(self):
        """Actuals list must not include forecast import records."""
        self.client.force_authenticate(user=self.user)
        SprintDataImport.objects.create(
            sprint=self.sprint,
            team=self.team,
            import_type=SprintDataImportType.FORECAST,
            version_number=1,
            file_name="forecast.csv",
            status=SprintDataImportStatus.ACTIVE,
            created_by=self.user,
            updated_by=self.user,
        )
        url = ACTUALS_IMPORTS_URL.format(sprint=self.sprint.code, team=self.team.code)
        response = self.client.get(url)
        self.assertEqual(response.data["data"]["results"], [])


# ── GET …/actuals/template/ ───────────────────────────────────────────────────


class ActualsDownloadTemplateTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.sprint = make_sprint()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        url = ACTUALS_TEMPLATE_URL.format(sprint=self.sprint.code)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_returns_csv_response(self):
        self.client.force_authenticate(user=self.user)
        url = ACTUALS_TEMPLATE_URL.format(sprint=self.sprint.code)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.get("Content-Type", ""))

    def test_template_contains_required_headers(self):
        self.client.force_authenticate(user=self.user)
        url = ACTUALS_TEMPLATE_URL.format(sprint=self.sprint.code)
        response = self.client.get(url)
        content = (
            b"".join(response.streaming_content).decode()
            if hasattr(response, "streaming_content")
            else response.content.decode()
        )
        for col in (
            "Story Type",
            "Jira ID",
            "Title",
            "Assignee",
            "Efforts",
            "Sprint",
            "Label",
            "Mapping",
        ):
            self.assertIn(col, content)


# ── GET …/actuals/<import_code>/ ──────────────────────────────────────────────


class ActualsImportDetailTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.sprint = make_sprint()
        self.team = make_team()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        upload_resp = _upload(self.client, self.sprint, self.team)
        self.import_code = upload_resp.data["data"]["code"]

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        url = ACTUALS_IMPORT_DETAIL_URL.format(
            sprint=self.sprint.code, import_code=self.import_code
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

    def test_returns_import_detail(self):
        url = ACTUALS_IMPORT_DETAIL_URL.format(
            sprint=self.sprint.code, import_code=self.import_code
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["code"], self.import_code)

    def test_response_contains_expected_fields(self):
        url = ACTUALS_IMPORT_DETAIL_URL.format(
            sprint=self.sprint.code, import_code=self.import_code
        )
        response = self.client.get(url)
        data = response.data["data"]
        for field in (
            "code",
            "version_number",
            "file_name",
            "status",
            "sprint_code",
            "team_code",
            "has_review",
            "is_confirmed",
        ):
            self.assertIn(field, data)

    def test_has_review_is_false_before_review(self):
        url = ACTUALS_IMPORT_DETAIL_URL.format(
            sprint=self.sprint.code, import_code=self.import_code
        )
        response = self.client.get(url)
        self.assertFalse(response.data["data"]["has_review"])

    def test_is_confirmed_is_false_before_confirm(self):
        url = ACTUALS_IMPORT_DETAIL_URL.format(
            sprint=self.sprint.code, import_code=self.import_code
        )
        response = self.client.get(url)
        self.assertFalse(response.data["data"]["is_confirmed"])

    def test_unknown_import_code_returns_404(self):
        url = ACTUALS_IMPORT_DETAIL_URL.format(
            sprint=self.sprint.code, import_code="IMPORT-9999"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


# ── GET / POST …/actuals/<import_code>/rows/ ──────────────────────────────────


class ActualsImportRowsTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.sprint = make_sprint()
        self.team = make_team()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        upload_resp = _upload(self.client, self.sprint, self.team)
        self.import_code = upload_resp.data["data"]["code"]
        self.rows_url = ACTUALS_IMPORT_ROWS_URL.format(
            sprint=self.sprint.code, import_code=self.import_code
        )

    def test_unauthenticated_list_rows_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.rows_url)
        self.assertEqual(response.status_code, 401)

    def test_unauthenticated_create_row_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.rows_url, {"title": "X"}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_list_rows_returns_200(self):
        response = self.client.get(self.rows_url)
        self.assertEqual(response.status_code, 200)

    def test_list_rows_response_has_pagination(self):
        response = self.client.get(self.rows_url)
        self.assertIn("pagination", response.data["data"])

    def test_list_rows_contains_csv_rows(self):
        # CSV has 1 row
        response = self.client.get(self.rows_url)
        self.assertEqual(response.data["data"]["pagination"]["total_count"], 1)

    def test_list_rows_response_has_results_key(self):
        response = self.client.get(self.rows_url)
        self.assertIn("results", response.data["data"])

    def test_each_row_has_expected_fields(self):
        response = self.client.get(self.rows_url)
        row = response.data["data"]["results"][0]
        for field in ("code", "title", "assignee", "efforts", "days", "story_type"):
            self.assertIn(field, row)

    def test_create_row_returns_201(self):
        response = self.client.post(
            self.rows_url,
            {"title": "Manually added row", "story_type": "Story"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_create_row_appears_in_list(self):
        self.client.post(
            self.rows_url,
            {"title": "New Row"},
            format="json",
        )
        response = self.client.get(self.rows_url)
        self.assertEqual(response.data["data"]["pagination"]["total_count"], 2)

    def test_create_row_is_marked_manually_added(self):
        response = self.client.post(
            self.rows_url,
            {"title": "Manual Row"},
            format="json",
        )
        self.assertTrue(response.data["data"]["is_manually_added"])

    def test_unknown_import_rows_returns_404(self):
        url = ACTUALS_IMPORT_ROWS_URL.format(
            sprint=self.sprint.code, import_code="IMPORT-9999"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


# ── PATCH / DELETE …/actuals/<import_code>/rows/<row_code>/ ───────────────────


class ActualsImportRowDetailTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.sprint = make_sprint()
        self.team = make_team()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        upload_resp = _upload(self.client, self.sprint, self.team)
        self.import_code = upload_resp.data["data"]["code"]
        # Create a manual row so we can edit/delete it
        rows_url = ACTUALS_IMPORT_ROWS_URL.format(
            sprint=self.sprint.code, import_code=self.import_code
        )
        create_resp = self.client.post(
            rows_url, {"title": "Original Title"}, format="json"
        )
        self.row_code = create_resp.data["data"]["code"]
        self.row_detail_url = ACTUALS_IMPORT_ROW_DETAIL_URL.format(
            sprint=self.sprint.code,
            import_code=self.import_code,
            row_code=self.row_code,
        )

    def test_unauthenticated_update_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.patch(self.row_detail_url, {"title": "X"}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_unauthenticated_delete_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.delete(self.row_detail_url)
        self.assertEqual(response.status_code, 401)

    def test_update_row_returns_200(self):
        response = self.client.patch(
            self.row_detail_url, {"title": "Updated Title"}, format="json"
        )
        self.assertEqual(response.status_code, 200)

    def test_update_row_reflects_new_title(self):
        self.client.patch(
            self.row_detail_url, {"title": "Changed Title"}, format="json"
        )
        rows_url = ACTUALS_IMPORT_ROWS_URL.format(
            sprint=self.sprint.code, import_code=self.import_code
        )
        response = self.client.get(rows_url)
        titles = [r["title"] for r in response.data["data"]["results"]]
        self.assertIn("Changed Title", titles)

    def test_delete_row_returns_200(self):
        response = self.client.delete(self.row_detail_url)
        self.assertEqual(response.status_code, 200)

    def test_deleted_row_does_not_appear_in_list(self):
        self.client.delete(self.row_detail_url)
        rows_url = ACTUALS_IMPORT_ROWS_URL.format(
            sprint=self.sprint.code, import_code=self.import_code
        )
        response = self.client.get(rows_url)
        # Only the CSV row remains (manually added row deleted)
        row_codes = [r["code"] for r in response.data["data"]["results"]]
        self.assertNotIn(self.row_code, row_codes)

    def test_update_unknown_row_returns_404(self):
        url = ACTUALS_IMPORT_ROW_DETAIL_URL.format(
            sprint=self.sprint.code,
            import_code=self.import_code,
            row_code="ROW-9999",
        )
        response = self.client.patch(url, {"title": "X"}, format="json")
        self.assertEqual(response.status_code, 404)

    def test_delete_unknown_row_returns_404(self):
        url = ACTUALS_IMPORT_ROW_DETAIL_URL.format(
            sprint=self.sprint.code,
            import_code=self.import_code,
            row_code="ROW-9999",
        )
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)


# ── POST …/actuals/<import_code>/review/ ──────────────────────────────────────


class ActualsReviewTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.sprint = make_sprint()
        self.team = make_team()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        upload_resp = _upload(self.client, self.sprint, self.team)
        self.import_code = upload_resp.data["data"]["code"]
        self.review_url = ACTUALS_REVIEW_URL.format(
            sprint=self.sprint.code, import_code=self.import_code
        )

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.review_url)
        self.assertEqual(response.status_code, 401)

    def test_review_returns_200(self):
        response = self.client.post(self.review_url)
        self.assertEqual(response.status_code, 200)

    def test_review_response_has_review_code(self):
        response = self.client.post(self.review_url)
        self.assertIn("review_code", response.data["data"])

    def test_review_response_has_has_errors(self):
        response = self.client.post(self.review_url)
        self.assertIn("has_errors", response.data["data"])

    def test_review_response_has_results(self):
        response = self.client.post(self.review_url)
        self.assertIn("results", response.data["data"])

    def test_has_review_is_true_after_review(self):
        self.client.post(self.review_url)
        detail_url = ACTUALS_IMPORT_DETAIL_URL.format(
            sprint=self.sprint.code, import_code=self.import_code
        )
        response = self.client.get(detail_url)
        self.assertTrue(response.data["data"]["has_review"])

    def test_unknown_import_returns_404(self):
        url = ACTUALS_REVIEW_URL.format(
            sprint=self.sprint.code, import_code="IMPORT-9999"
        )
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


# ── POST …/actuals/<import_code>/confirm/ ─────────────────────────────────────


class ActualsConfirmTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.sprint = make_sprint()
        self.team = make_team()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        upload_resp = _upload(self.client, self.sprint, self.team)
        self.import_code = upload_resp.data["data"]["code"]
        self.review_url = ACTUALS_REVIEW_URL.format(
            sprint=self.sprint.code, import_code=self.import_code
        )
        self.confirm_url = ACTUALS_CONFIRM_URL.format(
            sprint=self.sprint.code, import_code=self.import_code
        )

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.confirm_url)
        self.assertEqual(response.status_code, 401)

    def test_confirm_without_review_returns_422(self):
        response = self.client.post(self.confirm_url, {}, format="json")
        self.assertEqual(response.status_code, 422)

    def test_confirm_after_review_returns_200(self):
        self.client.post(self.review_url)
        response = self.client.post(
            self.confirm_url, {"notes": "override"}, format="json"
        )
        self.assertEqual(response.status_code, 200)

    def test_confirm_response_has_expected_fields(self):
        self.client.post(self.review_url)
        response = self.client.post(
            self.confirm_url, {"notes": "override"}, format="json"
        )
        data = response.data["data"]
        for field in ("import_type", "completed_at", "override_applied"):
            self.assertIn(field, data)

    def test_confirmed_import_type_is_actual(self):
        self.client.post(self.review_url)
        response = self.client.post(
            self.confirm_url, {"notes": "override"}, format="json"
        )
        self.assertEqual(
            response.data["data"]["import_type"], SprintDataImportType.ACTUAL
        )

    def test_import_status_becomes_confirmed(self):
        self.client.post(self.review_url)
        self.client.post(self.confirm_url, {"notes": "override"}, format="json")
        record = SprintDataImport.objects.get(code=self.import_code)
        self.assertEqual(record.status, SprintDataImportStatus.CONFIRMED)

    def test_is_confirmed_true_after_confirm(self):
        self.client.post(self.review_url)
        self.client.post(self.confirm_url, {"notes": "override"}, format="json")
        detail_url = ACTUALS_IMPORT_DETAIL_URL.format(
            sprint=self.sprint.code, import_code=self.import_code
        )
        response = self.client.get(detail_url)
        self.assertTrue(response.data["data"]["is_confirmed"])

    def test_unknown_import_returns_404(self):
        url = ACTUALS_CONFIRM_URL.format(
            sprint=self.sprint.code, import_code="IMPORT-9999"
        )
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, 404)


# ── POST …/actuals/review-complete/ ───────────────────────────────────────────


class ActualsReviewCompleteTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.sprint = make_sprint()
        self.user = make_user(is_superuser=True)
        self.url = ACTUALS_REVIEW_COMPLETE_URL.format(sprint=self.sprint.code)

    def test_unauthenticated_returns_401(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

    def test_review_complete_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)

    def test_review_complete_response_has_created_count(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url)
        self.assertIn("created", response.data["data"])

    def test_unknown_sprint_returns_404(self):
        self.client.force_authenticate(user=self.user)
        url = ACTUALS_REVIEW_COMPLETE_URL.format(sprint="SPRINT-9999")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


# ── GET …/actuals/projects/ ───────────────────────────────────────────────────


class ActualsProjectsTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.sprint = make_sprint()
        self.user = make_user(is_superuser=True)
        self.url = ACTUALS_PROJECTS_URL.format(sprint=self.sprint.code)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_returns_empty_results_when_no_actuals(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.data["data"]["results"], [])

    def test_unknown_sprint_returns_404(self):
        self.client.force_authenticate(user=self.user)
        url = ACTUALS_PROJECTS_URL.format(sprint="SPRINT-9999")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


# ── POST …/actuals/sync-project-actuals/ ─────────────────────────────────────


class ActualsSyncProjectActualsTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.sprint = make_sprint()
        self.user = make_user(is_superuser=True)
        self.url = ACTUALS_SYNC_URL.format(sprint=self.sprint.code)

    def test_unauthenticated_returns_401(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 401)

    def test_sync_all_projects_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"all_projects": True}, format="json")
        self.assertEqual(response.status_code, 200)

    def test_sync_response_has_created_count(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {"all_projects": True}, format="json")
        self.assertIn("created", response.data["data"])

    def test_sync_specific_projects_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.url,
            {"all_projects": False, "project_codes": []},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_unknown_sprint_returns_404(self):
        self.client.force_authenticate(user=self.user)
        url = ACTUALS_SYNC_URL.format(sprint="SPRINT-9999")
        response = self.client.post(url, {"all_projects": True}, format="json")
        self.assertEqual(response.status_code, 404)
