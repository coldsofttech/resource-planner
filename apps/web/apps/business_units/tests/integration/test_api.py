import io

from django.test import TestCase
from rest_framework.test import APIClient

from apps.business_units.models import BusinessUnit
from apps.business_units.tests.factories import make_business_unit
from apps.configurations.tests.factories import mark_setup_complete
from apps.users.tests.factories import make_user

LIST_URL = "/api/v1/bu/"
STATS_URL = "/api/v1/bu/stats/"
OPTIONS_URL = "/api/v1/bu/options/"
DETAIL_URL = "/api/v1/bu/{}/"
ACTIVATE_URL = "/api/v1/bu/{}/activate/"
DEACTIVATE_URL = "/api/v1/bu/{}/deactivate/"
IMPORT_URL = "/api/v1/bu/import/"
IMPORT_SPECS_URL = "/api/v1/bu/import/specs/"
IMPORT_SAMPLE_URL = "/api/v1/bu/import/sample/"
EXPORT_URL = "/api/v1/bu/export/"
EXPORT_SPECS_URL = "/api/v1/bu/export/specs/"


# ── GET /bu/ ──────────────────────────────────────────────────────────────────


class BusinessUnitListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_business_unit("Finance", "FIN", is_active=True)
        make_business_unit("Technology", "TECH", is_active=False)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 401)

    def test_defaults_to_active_only(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("Finance", names)
        self.assertNotIn("Technology", names)

    def test_is_active_false_returns_inactive(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"is_active": "false"})
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("Technology", names)
        self.assertNotIn("Finance", names)

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
        response = self.client.get(LIST_URL, {"search": "Finance"})
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("Finance", names)
        self.assertEqual(len(names), 1)

    def test_page_size_param_limits_results(self):
        make_business_unit("Operations", "OPS", is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"page_size": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["results"]), 1)


# ── GET /bu/stats/ ────────────────────────────────────────────────────────────


class BusinessUnitStatsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_business_unit("Finance", "FIN", is_active=True)
        make_business_unit("Technology", "TECH", is_active=True)
        make_business_unit("Operations", "OPS", is_active=False)

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


# ── GET /bu/options/ ──────────────────────────────────────────────────────────


class BusinessUnitOptionsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_business_unit("Finance", "FIN", is_active=True)
        make_business_unit("Inactive", "INA", is_active=False)

    def test_unauthenticated_returns_200(self):
        # Public: consumed by the unauthenticated project-onboarding portal.
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.status_code, 200)

    def test_returns_only_active_units(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.status_code, 200)
        names = [o["name"] for o in response.data["data"]]
        self.assertIn("Finance", names)
        self.assertNotIn("Inactive", names)

    def test_each_option_has_code_and_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.status_code, 200)
        option = response.data["data"][0]
        self.assertIn("code", option)
        self.assertIn("name", option)


# ── GET /bu/<code>/ ───────────────────────────────────────────────────────────


class BusinessUnitRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.bu = make_business_unit("Finance", "FIN")

    def test_returns_unit_detail(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.bu.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["name"], "Finance")

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format("BU-9999"))
        self.assertEqual(response.status_code, 404)

    def test_response_includes_required_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.bu.code))
        data = response.data["data"]
        for field in [
            "code",
            "name",
            "short_name",
            "is_active",
            "created_at",
            "updated_at",
        ]:
            self.assertIn(field, data)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(DETAIL_URL.format(self.bu.code))
        self.assertEqual(response.status_code, 401)


# ── POST /bu/ ─────────────────────────────────────────────────────────────────


class BusinessUnitCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_creates_unit(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL, {"name": "Finance", "short_name": "FIN"}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["name"], "Finance")
        self.assertEqual(response.data["data"]["short_name"], "FIN")

    def test_creates_with_is_active_false(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL,
            {"name": "Finance", "short_name": "FIN", "is_active": False},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.data["data"]["is_active"])

    def test_duplicate_name_returns_409(self):
        make_business_unit("Finance", "FIN")
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL, {"name": "Finance", "short_name": "FIN2"}, format="json"
        )
        self.assertEqual(response.status_code, 409)

    def test_missing_name_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"short_name": "FIN"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_missing_short_name_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"name": "Finance"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_returns_401(self):
        response = self.client.post(
            LIST_URL, {"name": "Finance", "short_name": "FIN"}, format="json"
        )
        self.assertEqual(response.status_code, 401)


# ── PATCH /bu/<code>/ ─────────────────────────────────────────────────────────


class BusinessUnitUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.bu = make_business_unit("Finance", "FIN")

    def test_updates_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.bu.code), {"name": "Renamed"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["name"], "Renamed")

    def test_updates_short_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.bu.code), {"short_name": "RNM"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["short_name"], "RNM")

    def test_duplicate_name_returns_409(self):
        make_business_unit("Technology", "TECH")
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.bu.code), {"name": "Technology"}, format="json"
        )
        self.assertEqual(response.status_code, 409)

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format("BU-9999"), {"name": "X"}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        response = self.client.patch(
            DETAIL_URL.format(self.bu.code), {"name": "X"}, format="json"
        )
        self.assertEqual(response.status_code, 401)


# ── DELETE /bu/<code>/ ────────────────────────────────────────────────────────


class BusinessUnitDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.bu = make_business_unit("Finance", "FIN")

    def test_deletes_unit(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format(self.bu.code))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(BusinessUnit.objects.filter(pk=self.bu.pk).exists())

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format("BU-9999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        response = self.client.delete(DETAIL_URL.format(self.bu.code))
        self.assertEqual(response.status_code, 401)


# ── POST /bu/<code>/activate/ and /deactivate/ ───────────────────────────────


class BusinessUnitActivateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_activates_inactive_unit(self):
        bu = make_business_unit("Finance", "FIN", is_active=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format(bu.code))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["is_active"])

    def test_activate_idempotent(self):
        bu = make_business_unit("Finance", "FIN", is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format(bu.code))
        self.assertEqual(response.status_code, 200)

    def test_deactivates_active_unit(self):
        bu = make_business_unit("Technology", "TECH", is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(DEACTIVATE_URL.format(bu.code))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["data"]["is_active"])

    def test_activate_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format("BU-9999"))
        self.assertEqual(response.status_code, 404)

    def test_deactivate_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(DEACTIVATE_URL.format("BU-9999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_activate_returns_401(self):
        bu = make_business_unit("Finance", "FIN", is_active=False)
        response = self.client.post(ACTIVATE_URL.format(bu.code))
        self.assertEqual(response.status_code, 401)

    def test_unauthenticated_deactivate_returns_401(self):
        bu = make_business_unit("Finance", "FIN", is_active=True)
        response = self.client.post(DEACTIVATE_URL.format(bu.code))
        self.assertEqual(response.status_code, 401)


# ── GET /bu/export/ ───────────────────────────────────────────────────────────


class BusinessUnitExportAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_business_unit("Finance", "FIN")

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


# ── POST /bu/import/ ──────────────────────────────────────────────────────────


class BusinessUnitImportAPITest(TestCase):
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

    def test_csv_import_creates_units(self):
        self.client.force_authenticate(user=self.user)
        csv_content = b"name,short_name\nFinance,FIN\nTechnology,TECH"
        f = io.BytesIO(csv_content)
        f.name = "business_units.csv"
        response = self.client.post(IMPORT_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, 207)
        self.assertTrue(BusinessUnit.objects.filter(name="Finance").exists())
        self.assertTrue(BusinessUnit.objects.filter(name="Technology").exists())

    def test_import_without_file_returns_422(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(IMPORT_URL, {}, format="multipart")
        self.assertEqual(response.status_code, 422)
