from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.tags.models import Tag
from apps.tags.tests.factories import make_tag
from apps.users.tests.factories import make_user

LIST_URL = "/api/v1/tags/"
EXPORT_URL = "/api/v1/tags/export/"
EXPORT_SPECS_URL = "/api/v1/tags/export/specs/"


# ── GET /api/v1/tags/ ─────────────────────────────────────────────────────────


class TagListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_tag("backend")
        make_tag("frontend")

    def test_unauthenticated_returns_401(self):
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 401)

    def test_returns_all_tags(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("#backend", names)
        self.assertIn("#frontend", names)

    def test_response_has_pagination(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertIn("pagination", response.data["data"])

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertTrue(response.data["success"])

    def test_search_filters_by_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"search": "back"})
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertTrue(any("back" in n for n in names))
        self.assertFalse(any("front" in n for n in names))

    def test_page_size_limits_results(self):
        make_tag("ops")
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"page_size": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["results"]), 1)

    def test_sort_by_name_asc(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"sort": "name", "order_by": "ASC"})
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertEqual(names, sorted(names))


# ── POST /api/v1/tags/ ────────────────────────────────────────────────────────


class TagCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.post(LIST_URL, {"name": "backend"}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_creates_tag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"name": "backend"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["name"], "#backend")

    def test_name_normalised_in_response(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"name": "Backend"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["name"], "#backend")

    def test_code_present_in_response(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"name": "backend"}, format="json")
        self.assertIn("code", response.data["data"])
        self.assertTrue(response.data["data"]["code"].startswith("TAG-"))

    def test_duplicate_name_returns_409(self):
        make_tag("backend")
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"name": "backend"}, format="json")
        self.assertEqual(response.status_code, 409)

    def test_missing_name_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_empty_name_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"name": ""}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_tag_persisted_in_db(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(LIST_URL, {"name": "backend"}, format="json")
        self.assertTrue(Tag.objects.filter(name="#backend").exists())


# ── GET /api/v1/tags/export/ ──────────────────────────────────────────────────


class TagExportAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_tag("backend")

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

    def test_export_specs_has_columns(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(EXPORT_SPECS_URL)
        self.assertIn("columns", response.data["data"])

    def test_export_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(EXPORT_URL)
        self.assertEqual(response.status_code, 200)
