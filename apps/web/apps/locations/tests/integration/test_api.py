import io

from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.locations.models import Location
from apps.locations.tests.factories import make_location
from apps.users.tests.factories import make_user

LIST_URL = "/api/v1/locations/"
OPTIONS_URL = "/api/v1/locations/options/"
STATS_URL = "/api/v1/locations/stats/"
DETAIL_URL = "/api/v1/locations/{}/"
ACTIVATE_URL = "/api/v1/locations/{}/activate/"
DEACTIVATE_URL = "/api/v1/locations/{}/deactivate/"
IMPORT_URL = "/api/v1/locations/import/"
IMPORT_SPECS_URL = "/api/v1/locations/import/specs/"
IMPORT_SAMPLE_URL = "/api/v1/locations/import/sample/"
EXPORT_URL = "/api/v1/locations/export/"
EXPORT_SPECS_URL = "/api/v1/locations/export/specs/"


# ── GET /locations/ ───────────────────────────────────────────────────────────


class LocationListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_location("London", "United Kingdom", is_active=True)
        make_location("Paris", "France", is_active=False)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 401)

    def test_defaults_to_active_only(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 200)
        cities = [r["city"] for r in response.data["data"]["results"]]
        self.assertIn("London", cities)
        self.assertNotIn("Paris", cities)

    def test_is_active_false_returns_inactive(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"is_active": "false"})
        self.assertEqual(response.status_code, 200)
        cities = [r["city"] for r in response.data["data"]["results"]]
        self.assertIn("Paris", cities)
        self.assertNotIn("London", cities)

    def test_response_has_pagination(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertIn("pagination", response.data["data"])

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertTrue(response.data["success"])

    def test_search_by_city(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"search": "London"})
        cities = [r["city"] for r in response.data["data"]["results"]]
        self.assertIn("London", cities)
        self.assertEqual(len(cities), 1)

    def test_page_size_param_limits_results(self):
        make_location("Berlin", "Germany", is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"page_size": 1})
        self.assertEqual(len(response.data["data"]["results"]), 1)


# ── GET /locations/stats/ ─────────────────────────────────────────────────────


class LocationStatsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_location("London", "United Kingdom", is_active=True)
        make_location("Paris", "France", is_active=True)
        make_location("Berlin", "Germany", is_active=False)

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


# ── GET /locations/options/ ───────────────────────────────────────────────────


class LocationOptionsAPITest(TestCase):
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

    def test_returns_only_active_locations(self):
        make_location("London", "United Kingdom", is_active=True)
        make_location("Paris", "France", is_active=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        cities = [e["city"] for e in response.data["data"]]
        self.assertIn("London", cities)
        self.assertNotIn("Paris", cities)

    def test_returns_empty_list_when_no_active_locations(self):
        make_location(is_active=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.data["data"], [])

    def test_each_entry_has_code_city_country(self):
        loc = make_location("London", "United Kingdom", is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        entry = response.data["data"][0]
        self.assertIn("code", entry)
        self.assertIn("city", entry)
        self.assertIn("country", entry)
        self.assertEqual(entry["code"], loc.code)


# ── GET /locations/<code>/ ────────────────────────────────────────────────────


class LocationRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.loc = make_location("London", "United Kingdom")

    def test_returns_location_detail(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.loc.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["city"], "London")
        self.assertEqual(response.data["data"]["country"], "United Kingdom")

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format("LOC-9999"))
        self.assertEqual(response.status_code, 404)

    def test_response_includes_required_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.loc.code))
        data = response.data["data"]
        for field in [
            "code",
            "city",
            "country",
            "is_active",
            "is_default",
            "created_at",
        ]:
            self.assertIn(field, data)


# ── POST /locations/ ──────────────────────────────────────────────────────────


class LocationCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_creates_location(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL,
            {"city": "London", "country": "United Kingdom"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["city"], "London")

    def test_creates_location_with_is_default(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL,
            {"city": "London", "country": "UK", "is_default": True},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["data"]["is_default"])

    def test_duplicate_city_country_returns_409(self):
        make_location("London", "United Kingdom")
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL,
            {"city": "London", "country": "United Kingdom"},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_missing_city_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL, {"country": "United Kingdom"}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_missing_country_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"city": "London"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_returns_401(self):
        response = self.client.post(
            LIST_URL, {"city": "London", "country": "UK"}, format="json"
        )
        self.assertEqual(response.status_code, 401)


# ── PATCH /locations/<code>/ ──────────────────────────────────────────────────


class LocationUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.loc = make_location("London", "United Kingdom")

    def test_updates_city(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.loc.code), {"city": "Manchester"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["city"], "Manchester")

    def test_duplicate_returns_409(self):
        make_location("Paris", "France")
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.loc.code),
            {"city": "Paris", "country": "France"},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format("LOC-9999"), {"city": "X"}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        response = self.client.patch(
            DETAIL_URL.format(self.loc.code), {"city": "X"}, format="json"
        )
        self.assertEqual(response.status_code, 401)


# ── DELETE /locations/<code>/ ─────────────────────────────────────────────────


class LocationDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.loc = make_location()

    def test_deletes_location(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format(self.loc.code))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Location.objects.filter(pk=self.loc.pk).exists())

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format("LOC-9999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        response = self.client.delete(DETAIL_URL.format(self.loc.code))
        self.assertEqual(response.status_code, 401)


# ── Activate / Deactivate ─────────────────────────────────────────────────────


class LocationActivateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_activates_inactive_location(self):
        loc = make_location(is_active=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format(loc.code))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["is_active"])

    def test_activate_idempotent(self):
        loc = make_location(is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format(loc.code))
        self.assertEqual(response.status_code, 200)

    def test_deactivates_active_location(self):
        loc = make_location(is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(DEACTIVATE_URL.format(loc.code))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["data"]["is_active"])

    def test_activate_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format("LOC-9999"))
        self.assertEqual(response.status_code, 404)

    def test_deactivate_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(DEACTIVATE_URL.format("LOC-9999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_activate_returns_401(self):
        loc = make_location(is_active=False)
        response = self.client.post(ACTIVATE_URL.format(loc.code))
        self.assertEqual(response.status_code, 401)

    def test_unauthenticated_deactivate_returns_401(self):
        loc = make_location(is_active=True)
        response = self.client.post(DEACTIVATE_URL.format(loc.code))
        self.assertEqual(response.status_code, 401)


# ── Export ────────────────────────────────────────────────────────────────────


class LocationExportAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_location("London", "United Kingdom")

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


# ── Import ────────────────────────────────────────────────────────────────────


class LocationImportAPITest(TestCase):
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

    def test_csv_import_creates_locations(self):
        self.client.force_authenticate(user=self.user)
        csv_content = b"city,country\nLondon,United Kingdom\nParis,France"
        f = io.BytesIO(csv_content)
        f.name = "locations.csv"
        response = self.client.post(IMPORT_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, 207)
        self.assertTrue(
            Location.objects.filter(city="London", country="United Kingdom").exists()
        )
        self.assertTrue(
            Location.objects.filter(city="Paris", country="France").exists()
        )

    def test_import_without_file_returns_422(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(IMPORT_URL, {}, format="multipart")
        self.assertEqual(response.status_code, 422)
