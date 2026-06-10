import io
from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.financial_years.constants import FinancialYearStatus
from apps.financial_years.models import FinancialYear
from apps.financial_years.tests.factories import make_financial_year
from apps.users.tests.factories import make_user

LIST_URL = "/api/v1/fy/"
OPTIONS_URL = "/api/v1/fy/options/"
STATS_URL = "/api/v1/fy/stats/"
ACTIVE_URL = "/api/v1/fy/active/"
DETAIL_URL = "/api/v1/fy/{}/"
ACTIVATE_URL = "/api/v1/fy/{}/activate/"
DEACTIVATE_URL = "/api/v1/fy/{}/deactivate/"
SET_ACTIVE_URL = "/api/v1/fy/{}/set-active/"
IMPORT_URL = "/api/v1/fy/import/"
IMPORT_SPECS_URL = "/api/v1/fy/import/specs/"
IMPORT_SAMPLE_URL = "/api/v1/fy/import/sample/"
EXPORT_URL = "/api/v1/fy/export/"
EXPORT_SPECS_URL = "/api/v1/fy/export/specs/"


# ── GET /fy/ ──────────────────────────────────────────────────────────────────


class FinancialYearListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31), is_active=True
        )
        make_financial_year(
            start_date=date(2025, 4, 1), end_date=date(2026, 3, 31), is_active=False
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 401)

    def test_defaults_to_active_only(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 200)
        codes = [r["long_fy"] for r in response.data["data"]["results"]]
        self.assertIn("FY2024-2025", codes)
        self.assertNotIn("FY2025-2026", codes)

    def test_is_active_false_returns_inactive(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"is_active": "false"})
        self.assertEqual(response.status_code, 200)
        codes = [r["long_fy"] for r in response.data["data"]["results"]]
        self.assertIn("FY2025-2026", codes)
        self.assertNotIn("FY2024-2025", codes)

    def test_response_has_pagination(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertIn("pagination", response.data["data"])

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertTrue(response.data["success"])

    def test_search_param_filters_by_long_fy(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"search": "FY2024"})
        self.assertEqual(response.status_code, 200)
        results = response.data["data"]["results"]
        self.assertTrue(all("2024" in r["long_fy"] for r in results))

    def test_page_size_param_limits_results(self):
        make_financial_year(
            start_date=date(2023, 4, 1), end_date=date(2024, 3, 31), is_active=True
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"page_size": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["results"]), 1)


# ── GET /fy/stats/ ────────────────────────────────────────────────────────────


class FinancialYearStatsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_financial_year(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            status=FinancialYearStatus.IN_PROGRESS,
            is_active=True,
        )
        make_financial_year(
            start_date=date(2025, 4, 1),
            end_date=date(2026, 3, 31),
            status=FinancialYearStatus.FUTURE,
            is_active=True,
        )
        make_financial_year(
            start_date=date(2023, 4, 1),
            end_date=date(2024, 3, 31),
            status=FinancialYearStatus.FUTURE,
            is_active=False,
        )

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
        self.assertEqual(data["in_progress"], 1)

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(STATS_URL)
        self.assertTrue(response.data["success"])


# ── GET /fy/options/ ──────────────────────────────────────────────────────────


class FinancialYearOptionsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.status_code, 401)

    def test_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.status_code, 200)

    def test_returns_only_active_financial_years(self):
        make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31), is_active=True
        )
        make_financial_year(
            start_date=date(2025, 4, 1), end_date=date(2026, 3, 31), is_active=False
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        labels = [e["long_fy"] for e in response.data["data"]]
        self.assertIn("FY2024-2025", labels)
        self.assertNotIn("FY2025-2026", labels)

    def test_each_entry_has_code_and_long_fy(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31), is_active=True
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        entry = response.data["data"][0]
        self.assertIn("code", entry)
        self.assertIn("long_fy", entry)
        self.assertEqual(entry["code"], fy.code)
        self.assertEqual(entry["long_fy"], "FY2024-2025")

    def test_returns_empty_list_when_no_active(self):
        make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31), is_active=False
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.data["data"], [])


# ── GET /fy/active/ ───────────────────────────────────────────────────────────


class FinancialYearActiveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(ACTIVE_URL)
        self.assertEqual(response.status_code, 401)

    def test_returns_in_progress_financial_year(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            status=FinancialYearStatus.IN_PROGRESS,
            is_active=True,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTIVE_URL)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["code"], fy.code)
        self.assertEqual(response.data["data"]["long_fy"], "FY2024-2025")

    def test_returns_404_when_no_in_progress_fy(self):
        make_financial_year(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            status=FinancialYearStatus.FUTURE,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTIVE_URL)
        self.assertEqual(response.status_code, 404)

    def test_returns_404_when_in_progress_is_inactive(self):
        make_financial_year(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            status=FinancialYearStatus.IN_PROGRESS,
            is_active=False,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTIVE_URL)
        self.assertEqual(response.status_code, 404)

    def test_response_has_success_flag(self):
        make_financial_year(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            status=FinancialYearStatus.IN_PROGRESS,
            is_active=True,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(ACTIVE_URL)
        self.assertTrue(response.data["success"])


# ── GET /fy/<code>/ ───────────────────────────────────────────────────────────


class FinancialYearRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )

    def test_returns_financial_year_detail(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.fy.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["long_fy"], "FY2024-2025")

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format("FY-9999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(DETAIL_URL.format(self.fy.code))
        self.assertEqual(response.status_code, 401)

    def test_response_includes_required_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.fy.code))
        data = response.data["data"]
        for field in [
            "code",
            "long_fy",
            "short_fy",
            "start_date",
            "end_date",
            "span_days",
            "status",
            "is_active",
            "created_at",
            "updated_at",
        ]:
            self.assertIn(field, data)


# ── POST /fy/ ─────────────────────────────────────────────────────────────────


class FinancialYearCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_creates_financial_year(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL,
            {"start_date": "2024-04-01", "end_date": "2025-03-31"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["long_fy"], "FY2024-2025")

    def test_creates_with_note(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL,
            {
                "start_date": "2024-04-01",
                "end_date": "2025-03-31",
                "note": "Annual plan",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["note"], "Annual plan")

    def test_derived_fields_populated_on_create(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL,
            {"start_date": "2024-04-01", "end_date": "2025-03-31"},
            format="json",
        )
        data = response.data["data"]
        self.assertEqual(data["short_fy"], "FY24-25")
        self.assertGreater(data["span_days"], 0)

    def test_end_before_start_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL,
            {"start_date": "2025-03-31", "end_date": "2024-04-01"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_overlapping_dates_returns_422(self):
        make_financial_year(start_date=date(2024, 4, 1), end_date=date(2025, 3, 31))
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL,
            {"start_date": "2024-06-01", "end_date": "2024-12-31"},
            format="json",
        )
        self.assertEqual(response.status_code, 422)

    def test_missing_start_date_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"end_date": "2025-03-31"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_missing_end_date_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL, {"start_date": "2024-04-01"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_returns_401(self):
        response = self.client.post(
            LIST_URL,
            {"start_date": "2024-04-01", "end_date": "2025-03-31"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)


# ── PATCH /fy/<code>/ ─────────────────────────────────────────────────────────


class FinancialYearUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )

    def test_updates_note(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.fy.code), {"note": "Updated"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["note"], "Updated")

    def test_updates_status(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.fy.code),
            {"status": FinancialYearStatus.IN_PROGRESS},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["data"]["status"], FinancialYearStatus.IN_PROGRESS
        )

    def test_updates_dates_and_recalculates_derived(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.fy.code),
            {"start_date": "2025-04-01", "end_date": "2026-03-31"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.data["data"]
        self.assertEqual(data["long_fy"], "FY2025-2026")
        self.assertEqual(data["short_fy"], "FY25-26")

    def test_overlapping_update_returns_422(self):
        make_financial_year(start_date=date(2025, 4, 1), end_date=date(2026, 3, 31))
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.fy.code),
            {"start_date": "2025-01-01", "end_date": "2025-12-31"},
            format="json",
        )
        self.assertEqual(response.status_code, 422)

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format("FY-9999"), {"note": "x"}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        response = self.client.patch(
            DETAIL_URL.format(self.fy.code), {"note": "x"}, format="json"
        )
        self.assertEqual(response.status_code, 401)


# ── DELETE /fy/<code>/ ────────────────────────────────────────────────────────


class FinancialYearDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )

    def test_deletes_financial_year(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format(self.fy.code))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(FinancialYear.objects.filter(pk=self.fy.pk).exists())

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format("FY-9999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        response = self.client.delete(DETAIL_URL.format(self.fy.code))
        self.assertEqual(response.status_code, 401)


# ── POST /fy/<code>/activate/ and /deactivate/ ────────────────────────────────


class FinancialYearActivateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_activates_inactive_financial_year(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31), is_active=False
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format(fy.code))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["is_active"])

    def test_activate_idempotent(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31), is_active=True
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format(fy.code))
        self.assertEqual(response.status_code, 200)

    def test_deactivates_active_financial_year(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31), is_active=True
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(DEACTIVATE_URL.format(fy.code))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["data"]["is_active"])

    def test_activate_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format("FY-9999"))
        self.assertEqual(response.status_code, 404)

    def test_deactivate_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(DEACTIVATE_URL.format("FY-9999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_activate_returns_401(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31), is_active=False
        )
        response = self.client.post(ACTIVATE_URL.format(fy.code))
        self.assertEqual(response.status_code, 401)

    def test_unauthenticated_deactivate_returns_401(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31), is_active=True
        )
        response = self.client.post(DEACTIVATE_URL.format(fy.code))
        self.assertEqual(response.status_code, 401)


# ── POST /fy/<code>/set-active/ ───────────────────────────────────────────────


class FinancialYearSetActiveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_changes_status_to_in_progress(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            status=FinancialYearStatus.FUTURE,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(SET_ACTIVE_URL.format(fy.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["data"]["status"], FinancialYearStatus.IN_PROGRESS
        )

    def test_set_active_idempotent(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            status=FinancialYearStatus.IN_PROGRESS,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(SET_ACTIVE_URL.format(fy.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data["data"]["status"], FinancialYearStatus.IN_PROGRESS
        )

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(SET_ACTIVE_URL.format("FY-9999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        response = self.client.post(SET_ACTIVE_URL.format(fy.code))
        self.assertEqual(response.status_code, 401)

    def test_response_has_success_flag(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            status=FinancialYearStatus.FUTURE,
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.post(SET_ACTIVE_URL.format(fy.code))
        self.assertTrue(response.data["success"])

    def test_retires_previous_in_progress_to_completed(self):
        old = make_financial_year(
            start_date=date(2023, 4, 1),
            end_date=date(2024, 3, 31),
            status=FinancialYearStatus.IN_PROGRESS,
        )
        new = make_financial_year(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            status=FinancialYearStatus.FUTURE,
        )
        self.client.force_authenticate(user=self.user)
        self.client.post(SET_ACTIVE_URL.format(new.code))
        old.refresh_from_db()
        new.refresh_from_db()
        self.assertEqual(old.status, FinancialYearStatus.COMPLETED)
        self.assertEqual(new.status, FinancialYearStatus.IN_PROGRESS)


# ── GET /fy/export/ ───────────────────────────────────────────────────────────


class FinancialYearExportAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_financial_year(start_date=date(2024, 4, 1), end_date=date(2025, 3, 31))

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


# ── POST /fy/import/ ──────────────────────────────────────────────────────────


class FinancialYearImportAPITest(TestCase):
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

    def test_csv_import_creates_financial_years(self):
        self.client.force_authenticate(user=self.user)
        csv_content = b"start_date,end_date\n2024-04-01,2025-03-31\n"
        f = io.BytesIO(csv_content)
        f.name = "financial_years.csv"
        response = self.client.post(IMPORT_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, 207)
        self.assertTrue(
            FinancialYear.objects.filter(
                start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
            ).exists()
        )

    def test_import_without_file_returns_422(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(IMPORT_URL, {}, format="multipart")
        self.assertEqual(response.status_code, 422)
