from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.employment_types.models import EmploymentType
from apps.employment_types.tests.factories import make_employment_type
from apps.users.tests.factories import make_user

LIST_URL = "/api/v1/emp-types/"
OPTIONS_URL = "/api/v1/emp-types/options/"
STATS_URL = "/api/v1/emp-types/stats/"
DETAIL_URL = "/api/v1/emp-types/{}/"
ACTIVATE_URL = "/api/v1/emp-types/{}/activate/"
DEACTIVATE_URL = "/api/v1/emp-types/{}/deactivate/"
IMPORT_URL = "/api/v1/emp-types/import/"
IMPORT_SPECS_URL = "/api/v1/emp-types/import/specs/"
IMPORT_SAMPLE_URL = "/api/v1/emp-types/import/sample/"
EXPORT_URL = "/api/v1/emp-types/export/"
EXPORT_SPECS_URL = "/api/v1/emp-types/export/specs/"


# ── GET /emp-types/ ───────────────────────────────────────────────────────────


class EmploymentTypeListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_employment_type("Full-time", is_active=True)
        make_employment_type("Casual", is_active=False)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 401)

    def test_defaults_to_active_only(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("Full-time", names)
        self.assertNotIn("Casual", names)

    def test_is_active_false_returns_inactive(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"is_active": "false"})
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("Casual", names)
        self.assertNotIn("Full-time", names)

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
        response = self.client.get(LIST_URL, {"search": "Full"})
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("Full-time", names)
        self.assertEqual(len(names), 1)

    def test_page_size_param_limits_results(self):
        make_employment_type("Part-time", is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"page_size": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["results"]), 1)


# ── GET /emp-types/stats/ ─────────────────────────────────────────────────────


class EmploymentTypeStatsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_employment_type("Full-time", is_active=True)
        make_employment_type("Part-time", is_active=True)
        make_employment_type("Casual", is_active=False)

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


# ── GET /emp-types/options/ ───────────────────────────────────────────────────


class EmploymentTypeOptionsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_employment_type("Full-time", is_active=True, is_default=True)
        make_employment_type("Casual", is_active=False)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.status_code, 401)

    def test_returns_only_active_types(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data["data"]]
        self.assertIn("Full-time", names)
        self.assertNotIn("Casual", names)

    def test_option_includes_is_default(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        option = response.data["data"][0]
        self.assertIn("is_default", option)
        self.assertTrue(option["is_default"])


# ── POST /emp-types/ ──────────────────────────────────────────────────────────


class EmploymentTypeCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.post(LIST_URL, {"name": "Full-time"}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_creates_employment_type(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"name": "Full-time"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(EmploymentType.objects.filter(name="Full-time").exists())

    def test_missing_name_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_duplicate_name_returns_409(self):
        make_employment_type("Full-time")
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"name": "Full-time"}, format="json")
        self.assertEqual(response.status_code, 409)

    def test_response_includes_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"name": "Full-time"}, format="json")
        self.assertIn("code", response.data["data"])


# ── GET /emp-types/<code>/ ────────────────────────────────────────────────────


class EmploymentTypeRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.et = make_employment_type("Full-time")

    def test_unauthenticated_returns_401(self):
        response = self.client.get(DETAIL_URL.format(self.et.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_employment_type(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.et.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["name"], "Full-time")

    def test_unknown_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format("EMPTYPE-9999"))
        self.assertEqual(response.status_code, 404)


# ── PATCH /emp-types/<code>/ ──────────────────────────────────────────────────


class EmploymentTypeUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.et = make_employment_type("Full-time")

    def test_unauthenticated_returns_401(self):
        response = self.client.patch(
            DETAIL_URL.format(self.et.code), {"name": "New"}, format="json"
        )
        self.assertEqual(response.status_code, 401)

    def test_updates_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.et.code), {"name": "Full Time"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.et.refresh_from_db()
        self.assertEqual(self.et.name, "Full Time")

    def test_unknown_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format("EMPTYPE-9999"), {"name": "New"}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_duplicate_name_returns_409(self):
        make_employment_type("Part-time")
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.et.code), {"name": "Part-time"}, format="json"
        )
        self.assertEqual(response.status_code, 409)


# ── DELETE /emp-types/<code>/ ─────────────────────────────────────────────────


class EmploymentTypeDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.et = make_employment_type("Full-time")

    def test_unauthenticated_returns_401(self):
        response = self.client.delete(DETAIL_URL.format(self.et.code))
        self.assertEqual(response.status_code, 401)

    def test_deletes_employment_type(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format(self.et.code))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(EmploymentType.objects.filter(code=self.et.code).exists())

    def test_unknown_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format("EMPTYPE-9999"))
        self.assertEqual(response.status_code, 404)


# ── POST /emp-types/<code>/activate/ ─────────────────────────────────────────


class EmploymentTypeActivateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.et = make_employment_type(is_active=False)

    def test_unauthenticated_returns_401(self):
        response = self.client.post(ACTIVATE_URL.format(self.et.code))
        self.assertEqual(response.status_code, 401)

    def test_activates_employment_type(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format(self.et.code))
        self.assertEqual(response.status_code, 200)
        self.et.refresh_from_db()
        self.assertTrue(self.et.is_active)

    def test_unknown_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format("EMPTYPE-9999"))
        self.assertEqual(response.status_code, 404)


# ── POST /emp-types/<code>/deactivate/ ───────────────────────────────────────


class EmploymentTypeDeactivateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.et = make_employment_type(is_active=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.post(DEACTIVATE_URL.format(self.et.code))
        self.assertEqual(response.status_code, 401)

    def test_deactivates_employment_type(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(DEACTIVATE_URL.format(self.et.code))
        self.assertEqual(response.status_code, 200)
        self.et.refresh_from_db()
        self.assertFalse(self.et.is_active)

    def test_unknown_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(DEACTIVATE_URL.format("EMPTYPE-9999"))
        self.assertEqual(response.status_code, 404)


# ── GET /emp-types/import/specs/ ─────────────────────────────────────────────


class EmploymentTypeImportSpecsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(IMPORT_SPECS_URL)
        self.assertEqual(response.status_code, 401)

    def test_returns_200_for_authenticated_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(IMPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)


# ── GET /emp-types/import/sample/ ────────────────────────────────────────────


class EmploymentTypeImportSampleAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(IMPORT_SAMPLE_URL)
        self.assertEqual(response.status_code, 401)

    def test_returns_csv_file(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(IMPORT_SAMPLE_URL)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.get("Content-Type", ""))


# ── GET /emp-types/export/specs/ ─────────────────────────────────────────────


class EmploymentTypeExportSpecsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 401)

    def test_returns_200_for_authenticated_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)
