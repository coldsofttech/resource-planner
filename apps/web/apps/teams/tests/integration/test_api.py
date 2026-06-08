import io

from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.teams.models import Team
from apps.teams.tests.factories import make_team
from apps.users.tests.factories import make_user

LIST_URL = "/api/v1/teams/"
STATS_URL = "/api/v1/teams/stats/"
DETAIL_URL = "/api/v1/teams/{}/"
ACTIVATE_URL = "/api/v1/teams/{}/activate/"
DEACTIVATE_URL = "/api/v1/teams/{}/deactivate/"
IMPORT_URL = "/api/v1/teams/import/"
IMPORT_SPECS_URL = "/api/v1/teams/import/specs/"
IMPORT_SAMPLE_URL = "/api/v1/teams/import/sample/"
EXPORT_URL = "/api/v1/teams/export/"
EXPORT_SPECS_URL = "/api/v1/teams/export/specs/"


# ── GET /teams/ ───────────────────────────────────────────────────────────────


class TeamListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_team("Alpha", is_active=True)
        make_team("Beta", is_active=False)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 401)

    def test_defaults_to_active_only(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("Alpha", names)
        self.assertNotIn("Beta", names)

    def test_is_active_false_returns_inactive(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"is_active": "false"})
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("Beta", names)
        self.assertNotIn("Alpha", names)

    def test_response_has_pagination(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertIn("pagination", response.data["data"])

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertTrue(response.data["success"])

    def test_search_param_filters_by_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"search": "Alpha"})
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("Alpha", names)
        self.assertEqual(len(names), 1)

    def test_page_size_param_limits_results(self):
        make_team("Gamma", is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"page_size": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["results"]), 1)


# ── GET /teams/stats/ ─────────────────────────────────────────────────────────


class TeamStatsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_team("Alpha", is_active=True)
        make_team("Beta", is_active=True)
        make_team("Gamma", is_active=False)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(STATS_URL)
        self.assertEqual(response.status_code, 401)

    def test_returns_correct_stats(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(STATS_URL)
        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertEqual(data["total"], 3)
        self.assertEqual(data["active"], 2)
        self.assertEqual(data["inactive"], 1)


# ── GET /teams/<code>/ ────────────────────────────────────────────────────────


class TeamRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.team = make_team("Alpha")

    def test_returns_team_detail(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.team.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["name"], "Alpha")

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format("TEAM-9999"))
        self.assertEqual(response.status_code, 404)

    def test_response_includes_required_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.team.code))
        data = response.data["data"]
        for field in [
            "code",
            "name",
            "description",
            "is_active",
            "created_at",
            "updated_at",
        ]:
            self.assertIn(field, data)


# ── POST /teams/ ──────────────────────────────────────────────────────────────


class TeamCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_creates_team(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"name": "Alpha"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["name"], "Alpha")

    def test_creates_team_with_description(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL, {"name": "Alpha", "description": "Squad"}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["description"], "Squad")

    def test_creates_team_with_is_active_false(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL, {"name": "Alpha", "is_active": False}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.data["data"]["is_active"])

    def test_duplicate_name_returns_409(self):
        make_team("Alpha")
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"name": "Alpha"}, format="json")
        self.assertEqual(response.status_code, 409)

    def test_missing_name_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_returns_401(self):
        response = self.client.post(LIST_URL, {"name": "Alpha"}, format="json")
        self.assertEqual(response.status_code, 401)


# ── PATCH /teams/<code>/ ──────────────────────────────────────────────────────


class TeamUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.team = make_team("Alpha")

    def test_updates_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.team.code), {"name": "Renamed"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["name"], "Renamed")

    def test_duplicate_name_returns_409(self):
        make_team("Beta")
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.team.code), {"name": "Beta"}, format="json"
        )
        self.assertEqual(response.status_code, 409)

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format("TEAM-9999"), {"name": "X"}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        response = self.client.patch(
            DETAIL_URL.format(self.team.code), {"name": "X"}, format="json"
        )
        self.assertEqual(response.status_code, 401)


# ── DELETE /teams/<code>/ ─────────────────────────────────────────────────────


class TeamDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.team = make_team("Alpha")

    def test_deletes_team(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format(self.team.code))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Team.objects.filter(pk=self.team.pk).exists())

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format("TEAM-9999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        response = self.client.delete(DETAIL_URL.format(self.team.code))
        self.assertEqual(response.status_code, 401)


# ── POST /teams/<code>/activate/ and /deactivate/ ────────────────────────────


class TeamActivateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_activates_inactive_team(self):
        team = make_team("Alpha", is_active=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format(team.code))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["is_active"])

    def test_activate_idempotent(self):
        team = make_team("Alpha", is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format(team.code))
        self.assertEqual(response.status_code, 200)

    def test_deactivates_active_team(self):
        team = make_team("Beta", is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(DEACTIVATE_URL.format(team.code))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["data"]["is_active"])

    def test_activate_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format("TEAM-9999"))
        self.assertEqual(response.status_code, 404)

    def test_deactivate_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(DEACTIVATE_URL.format("TEAM-9999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_activate_returns_401(self):
        team = make_team("Alpha", is_active=False)
        response = self.client.post(ACTIVATE_URL.format(team.code))
        self.assertEqual(response.status_code, 401)

    def test_unauthenticated_deactivate_returns_401(self):
        team = make_team("Alpha", is_active=True)
        response = self.client.post(DEACTIVATE_URL.format(team.code))
        self.assertEqual(response.status_code, 401)


# ── GET /teams/export/ ────────────────────────────────────────────────────────


class TeamExportAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_team("Alpha")

    def test_unauthenticated_returns_401(self):
        response = self.client.get(EXPORT_URL)
        self.assertEqual(response.status_code, 401)

    def test_export_csv_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(EXPORT_URL)
        self.assertEqual(response.status_code, 200)

    def test_export_specs_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)

    def test_export_specs_unauthenticated_returns_401(self):
        response = self.client.get(EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 401)


# ── POST /teams/import/ ───────────────────────────────────────────────────────


class TeamImportAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_import_specs_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(IMPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)

    def test_import_sample_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(IMPORT_SAMPLE_URL)
        self.assertEqual(response.status_code, 200)

    def test_import_unauthenticated_returns_401(self):
        response = self.client.post(IMPORT_URL)
        self.assertEqual(response.status_code, 401)

    def test_import_specs_unauthenticated_returns_401(self):
        response = self.client.get(IMPORT_SPECS_URL)
        self.assertEqual(response.status_code, 401)

    def test_csv_import_creates_teams(self):
        self.client.force_authenticate(user=self.user)
        csv_content = b"name\nAlpha\nBeta"
        f = io.BytesIO(csv_content)
        f.name = "teams.csv"
        response = self.client.post(IMPORT_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, 207)
        self.assertTrue(Team.objects.filter(name="Alpha").exists())
        self.assertTrue(Team.objects.filter(name="Beta").exists())

    def test_import_without_file_returns_422(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(IMPORT_URL, {}, format="multipart")
        self.assertEqual(response.status_code, 422)
