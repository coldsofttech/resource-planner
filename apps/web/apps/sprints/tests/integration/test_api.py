import io
from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.financial_years.tests.factories import make_financial_year
from apps.sprints.constants import SprintStatus
from apps.sprints.models import Sprint
from apps.sprints.tests.factories import make_sprint
from apps.users.tests.factories import make_user

LIST_URL = "/api/v1/sprints/"
STATS_URL = "/api/v1/sprints/stats/"
OPTIONS_URL = "/api/v1/sprints/options/"
MONTHS_URL = "/api/v1/sprints/months/"
ACTIVE_URL = "/api/v1/sprints/active/"
GENERATE_URL = "/api/v1/sprints/generate/"
IMPORT_URL = "/api/v1/sprints/import/"
IMPORT_SPECS_URL = "/api/v1/sprints/import/specs/"
IMPORT_SAMPLE_URL = "/api/v1/sprints/import/sample/"
EXPORT_URL = "/api/v1/sprints/export/"
EXPORT_SPECS_URL = "/api/v1/sprints/export/specs/"
DETAIL_URL = "/api/v1/sprints/{}/"
ACTIVATE_URL = "/api/v1/sprints/{}/activate/"
DEACTIVATE_URL = "/api/v1/sprints/{}/deactivate/"
SET_ACTIVE_URL = "/api/v1/sprints/{}/set-active/"
CLOSE_URL = "/api/v1/sprints/{}/close/"
CAPACITY_URL = "/api/v1/sprints/{}/capacity/"
CAPACITY_REBUILD_URL = "/api/v1/sprints/{}/capacity/rebuild/"


# ── GET /sprints/ ─────────────────────────────────────────────────────────────


class SprintListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        self.s1 = make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
            is_active=True,
        )
        self.s2 = make_sprint(
            financial_year=self.fy,
            sprint_number=2,
            start_date=date(2024, 4, 15),
            end_date=date(2024, 4, 28),
            is_active=False,
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 401)

    def test_defaults_to_active_only(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 200)
        codes = [r["code"] for r in response.data["data"]["results"]]
        self.assertIn(self.s1.code, codes)
        self.assertNotIn(self.s2.code, codes)

    def test_is_active_false_returns_inactive(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"is_active": "false"})
        self.assertEqual(response.status_code, 200)
        codes = [r["code"] for r in response.data["data"]["results"]]
        self.assertIn(self.s2.code, codes)
        self.assertNotIn(self.s1.code, codes)

    def test_response_has_pagination(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertIn("pagination", response.data["data"])

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertTrue(response.data["success"])

    def test_filter_by_status(self):
        make_sprint(
            financial_year=self.fy,
            sprint_number=3,
            start_date=date(2024, 4, 29),
            end_date=date(2024, 5, 12),
            status=SprintStatus.IN_PROGRESS,
            is_active=True,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"status": SprintStatus.IN_PROGRESS})
        results = response.data["data"]["results"]
        self.assertTrue(all(r["status"] == SprintStatus.IN_PROGRESS for r in results))

    def test_search_filters_by_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"search": "Sprint 1"})
        self.assertEqual(response.status_code, 200)
        results = response.data["data"]["results"]
        self.assertTrue(all("1" in r["name"] for r in results))

    def test_page_size_limits_results(self):
        self.client.force_authenticate(user=self.user)
        make_sprint(
            financial_year=self.fy,
            sprint_number=3,
            start_date=date(2024, 4, 29),
            end_date=date(2024, 5, 12),
        )
        response = self.client.get(LIST_URL, {"page_size": 1, "is_active": "all"})
        self.assertEqual(len(response.data["data"]["results"]), 1)


# ── GET /sprints/stats/ ───────────────────────────────────────────────────────


class SprintStatsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        make_sprint(
            financial_year=fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
            status=SprintStatus.IN_PROGRESS,
        )
        make_sprint(
            financial_year=fy,
            sprint_number=2,
            start_date=date(2024, 4, 15),
            end_date=date(2024, 4, 28),
            status=SprintStatus.FUTURE,
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.get(STATS_URL)
        self.assertEqual(response.status_code, 401)

    def test_returns_correct_counts(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(STATS_URL)
        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertEqual(data["total"], 2)
        self.assertEqual(data["in_progress"], 1)
        self.assertEqual(data["future"], 1)

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(STATS_URL)
        self.assertTrue(response.data["success"])


# ── GET /sprints/options/ ─────────────────────────────────────────────────────


class SprintOptionsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.status_code, 401)

    def test_returns_active_sprints_only(self):
        make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
            is_active=True,
        )
        make_sprint(
            financial_year=self.fy,
            sprint_number=2,
            start_date=date(2024, 4, 15),
            end_date=date(2024, 4, 28),
            is_active=False,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 1)

    def test_filters_by_fy_code(self):
        fy2 = make_financial_year(
            start_date=date(2025, 4, 1), end_date=date(2026, 3, 31)
        )
        make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        make_sprint(
            financial_year=fy2,
            sprint_number=2,
            start_date=date(2025, 4, 1),
            end_date=date(2025, 4, 14),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL, {"fy_code": self.fy.code})
        self.assertEqual(len(response.data["data"]), 1)

    def test_each_entry_has_expected_keys(self):
        make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        entry = response.data["data"][0]
        for key in (
            "code",
            "sprint_number",
            "name",
            "start_date",
            "end_date",
            "month",
            "status",
        ):
            self.assertIn(key, entry)


# ── GET /sprints/months/ ──────────────────────────────────────────────────────


class SprintMonthsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.get(MONTHS_URL, {"fy_code": self.fy.code})
        self.assertEqual(response.status_code, 401)

    def test_missing_fy_code_returns_422(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(MONTHS_URL)
        self.assertEqual(response.status_code, 422)

    def test_returns_months_for_fy(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(MONTHS_URL, {"fy_code": self.fy.code})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["data"], [{"value": "2024-04", "label": "Apr 2024"}]
        )


# ── GET /sprints/active/ ──────────────────────────────────────────────────────


class SprintActiveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(ACTIVE_URL)
        self.assertEqual(response.status_code, 401)

    def test_returns_in_progress_sprint(self):
        sprint = make_sprint(status=SprintStatus.IN_PROGRESS, is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTIVE_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["code"], sprint.code)

    def test_returns_404_when_no_active_sprint(self):
        make_sprint(status=SprintStatus.FUTURE)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTIVE_URL)
        self.assertEqual(response.status_code, 404)

    def test_returns_404_when_in_progress_sprint_is_inactive(self):
        make_sprint(status=SprintStatus.IN_PROGRESS, is_active=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTIVE_URL)
        self.assertEqual(response.status_code, 404)


# ── GET /sprints/<code>/ ──────────────────────────────────────────────────────


class SprintRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.sprint = make_sprint()

    def test_unauthenticated_returns_401(self):
        response = self.client.get(DETAIL_URL.format(self.sprint.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_sprint_detail(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.sprint.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["code"], self.sprint.code)

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format("SPRINT-9999"))
        self.assertEqual(response.status_code, 404)

    def test_response_includes_required_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.sprint.code))
        data = response.data["data"]
        for field in (
            "code",
            "sprint_number",
            "name",
            "start_date",
            "end_date",
            "month",
            "status",
            "is_active",
            "is_closed",
            "is_in_progress",
            "days_remaining",
        ):
            self.assertIn(field, data)


# ── POST /sprints/ ────────────────────────────────────────────────────────────


class SprintCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.post(
            LIST_URL,
            {
                "fy_code": self.fy.code,
                "sprint_number": 1,
                "start_date": "2024-04-01",
                "end_date": "2024-04-14",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_creates_sprint_successfully(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL,
            {
                "fy_code": self.fy.code,
                "sprint_number": 1,
                "start_date": "2024-04-01",
                "end_date": "2024-04-14",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["sprint_number"], 1)

    def test_missing_fy_code_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL,
            {"sprint_number": 1, "start_date": "2024-04-01", "end_date": "2024-04-14"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_missing_sprint_number_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL,
            {
                "fy_code": self.fy.code,
                "start_date": "2024-04-01",
                "end_date": "2024-04-14",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_end_before_start_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL,
            {
                "fy_code": self.fy.code,
                "sprint_number": 1,
                "start_date": "2024-04-14",
                "end_date": "2024-04-01",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_unknown_fy_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL,
            {
                "fy_code": "FY-9999",
                "sprint_number": 1,
                "start_date": "2024-04-01",
                "end_date": "2024-04-14",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_overlapping_sprint_returns_422(self):
        make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL,
            {
                "fy_code": self.fy.code,
                "sprint_number": 2,
                "start_date": "2024-04-07",
                "end_date": "2024-04-21",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 422)


# ── PATCH /sprints/<code>/ ────────────────────────────────────────────────────


class SprintUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        self.sprint = make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.patch(
            DETAIL_URL.format(self.sprint.code), {"name": "X"}, format="json"
        )
        self.assertEqual(response.status_code, 401)

    def test_updates_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.sprint.code), {"name": "Updated"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["name"], "Updated")

    def test_updates_note(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.sprint.code), {"note": "Some note"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["note"], "Some note")

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format("SPRINT-9999"), {"name": "X"}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_end_before_start_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.sprint.code),
            {"start_date": "2024-04-14", "end_date": "2024-04-01"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)


# ── DELETE /sprints/<code>/ ───────────────────────────────────────────────────


class SprintDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.sprint = make_sprint()

    def test_unauthenticated_returns_401(self):
        response = self.client.delete(DETAIL_URL.format(self.sprint.code))
        self.assertEqual(response.status_code, 401)

    def test_deletes_sprint(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format(self.sprint.code))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Sprint.objects.filter(pk=self.sprint.pk).exists())

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format("SPRINT-9999"))
        self.assertEqual(response.status_code, 404)


# ── POST /sprints/<code>/activate/ and /deactivate/ ──────────────────────────


class SprintActivateDeactivateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_activates_inactive_sprint(self):
        sprint = make_sprint(is_active=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format(sprint.code))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["is_active"])

    def test_deactivates_active_sprint(self):
        sprint = make_sprint(is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(DEACTIVATE_URL.format(sprint.code))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["data"]["is_active"])

    def test_activate_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format("SPRINT-9999"))
        self.assertEqual(response.status_code, 404)

    def test_deactivate_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(DEACTIVATE_URL.format("SPRINT-9999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_activate_returns_401(self):
        sprint = make_sprint(is_active=False)
        response = self.client.post(ACTIVATE_URL.format(sprint.code))
        self.assertEqual(response.status_code, 401)

    def test_unauthenticated_deactivate_returns_401(self):
        sprint = make_sprint(is_active=True)
        response = self.client.post(DEACTIVATE_URL.format(sprint.code))
        self.assertEqual(response.status_code, 401)


# ── POST /sprints/<code>/set-active/ ─────────────────────────────────────────


class SprintSetActiveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )

    def test_sets_sprint_to_in_progress(self):
        sprint = make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
            status=SprintStatus.FUTURE,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(SET_ACTIVE_URL.format(sprint.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["status"], SprintStatus.IN_PROGRESS)

    def test_retires_previous_in_progress(self):
        old = make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
            status=SprintStatus.IN_PROGRESS,
        )
        new = make_sprint(
            financial_year=self.fy,
            sprint_number=2,
            start_date=date(2024, 4, 15),
            end_date=date(2024, 4, 28),
            status=SprintStatus.FUTURE,
        )
        self.client.force_authenticate(user=self.user)
        self.client.post(SET_ACTIVE_URL.format(new.code))
        old.refresh_from_db()
        self.assertEqual(old.status, SprintStatus.COMPLETED)

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(SET_ACTIVE_URL.format("SPRINT-9999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        sprint = make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        response = self.client.post(SET_ACTIVE_URL.format(sprint.code))
        self.assertEqual(response.status_code, 401)


# ── POST /sprints/<code>/close/ ───────────────────────────────────────────────


class SprintCloseAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.sprint = make_sprint()

    def test_unauthenticated_returns_401(self):
        response = self.client.post(
            CLOSE_URL.format(self.sprint.code), {"lock": True}, format="json"
        )
        self.assertEqual(response.status_code, 401)

    def test_closes_sprint(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            CLOSE_URL.format(self.sprint.code), {"lock": True}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["is_closed"])

    def test_unlocks_sprint(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(
            CLOSE_URL.format(self.sprint.code), {"lock": True}, format="json"
        )
        response = self.client.post(
            CLOSE_URL.format(self.sprint.code), {"lock": False}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["data"]["is_closed"])

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            CLOSE_URL.format("SPRINT-9999"), {"lock": True}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_defaults_lock_to_true(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            CLOSE_URL.format(self.sprint.code), {}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["is_closed"])


# ── POST /sprints/generate/ ───────────────────────────────────────────────────


class SprintGenerateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.post(GENERATE_URL, {"fy_code": "FY-1"}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_missing_fy_code_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(GENERATE_URL, {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_unknown_fy_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(GENERATE_URL, {"fy_code": "FY-9999"}, format="json")
        self.assertEqual(response.status_code, 404)

    def test_generates_sprints_for_fy(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2024, 4, 28)
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(GENERATE_URL, {"fy_code": fy.code}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertGreater(len(response.data["data"]), 0)

    def test_raises_422_when_sprints_already_exist(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        make_sprint(
            financial_year=fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(GENERATE_URL, {"fy_code": fy.code}, format="json")
        self.assertEqual(response.status_code, 422)


# ── GET /sprints/<code>/capacity/ ─────────────────────────────────────────────


class SprintCapacityAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.sprint = make_sprint()
        # make_sprint triggers the post_save signal which calls rebuild_for_sprint,
        # creating a Capacity row for self.user via update_or_create.

    def test_unauthenticated_returns_401(self):
        response = self.client.get(CAPACITY_URL.format(self.sprint.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_capacity_rows(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(CAPACITY_URL.format(self.sprint.code))
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data["data"]), 0)

    def test_returns_404_for_unknown_sprint(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(CAPACITY_URL.format("SPRINT-9999"))
        self.assertEqual(response.status_code, 404)

    def test_each_capacity_row_has_expected_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(CAPACITY_URL.format(self.sprint.code))
        row = response.data["data"][0]
        for field in (
            "member",
            "working_days",
            "holiday_days",
            "leave_days",
            "net_capacity",
        ):
            self.assertIn(field, row)


# ── POST /sprints/<code>/capacity/rebuild/ ────────────────────────────────────


class SprintCapacityRebuildAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.sprint = make_sprint()

    def test_unauthenticated_returns_401(self):
        response = self.client.post(CAPACITY_REBUILD_URL.format(self.sprint.code))
        self.assertEqual(response.status_code, 401)

    def test_rebuild_returns_count(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(CAPACITY_REBUILD_URL.format(self.sprint.code))
        self.assertEqual(response.status_code, 200)
        self.assertIn("rebuilt", response.data["data"])

    def test_returns_404_for_unknown_sprint(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(CAPACITY_REBUILD_URL.format("SPRINT-9999"))
        self.assertEqual(response.status_code, 404)


# ── Import / Export ───────────────────────────────────────────────────────────


class SprintImportExportAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )

    def test_import_specs_unauthenticated_returns_401(self):
        response = self.client.get(IMPORT_SPECS_URL)
        self.assertEqual(response.status_code, 401)

    def test_import_sample_unauthenticated_returns_401(self):
        response = self.client.get(IMPORT_SAMPLE_URL)
        self.assertEqual(response.status_code, 401)

    def test_import_unauthenticated_returns_401(self):
        response = self.client.post(IMPORT_URL)
        self.assertEqual(response.status_code, 401)

    def test_import_specs_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(IMPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)

    def test_import_sample_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(IMPORT_SAMPLE_URL)
        self.assertEqual(response.status_code, 200)

    def test_import_without_file_returns_422(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(IMPORT_URL, {}, format="multipart")
        self.assertEqual(response.status_code, 422)

    def test_csv_import_creates_sprints(self):
        self.client.force_authenticate(user=self.user)
        csv_content = (
            f"fy_code,sprint_number,start_date,end_date\n"
            f"{self.fy.code},1,2024-04-01,2024-04-14\n"
        ).encode()
        f = io.BytesIO(csv_content)
        f.name = "sprints.csv"
        response = self.client.post(IMPORT_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, 207)
        self.assertTrue(
            Sprint.objects.filter(sprint_number=1, financial_year=self.fy).exists()
        )

    def test_export_unauthenticated_returns_401(self):
        response = self.client.get(EXPORT_URL)
        self.assertEqual(response.status_code, 401)

    def test_export_csv_returns_200(self):
        make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(EXPORT_URL)
        self.assertEqual(response.status_code, 200)

    def test_export_specs_unauthenticated_returns_401(self):
        response = self.client.get(EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 401)

    def test_export_specs_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)
