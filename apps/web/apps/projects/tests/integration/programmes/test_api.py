from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.projects.models import Programme
from apps.projects.tests.factories import make_programme
from apps.users.tests.factories import make_user

LIST_URL = "/api/v1/programmes/"
OPTIONS_URL = "/api/v1/programmes/options/"
STATS_URL = "/api/v1/programmes/stats/"
DETAIL_URL = "/api/v1/programmes/{}/"
ACTIVATE_URL = "/api/v1/programmes/{}/activate/"
DEACTIVATE_URL = "/api/v1/programmes/{}/deactivate/"
IMPORT_URL = "/api/v1/programmes/import/"
IMPORT_SPECS_URL = "/api/v1/programmes/import/specs/"
IMPORT_SAMPLE_URL = "/api/v1/programmes/import/sample/"
EXPORT_URL = "/api/v1/programmes/export/"
EXPORT_SPECS_URL = "/api/v1/programmes/export/specs/"


# ── GET /programmes/ ──────────────────────────────────────────────────────────


class ProgrammeListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_programme("Alpha", is_active=True)
        make_programme("Inactive", is_active=False)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 401)

    def test_defaults_to_active_only(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("Alpha", names)
        self.assertNotIn("Inactive", names)

    def test_is_active_false_returns_inactive(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"is_active": "false"})
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("Inactive", names)
        self.assertNotIn("Alpha", names)

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
        response = self.client.get(LIST_URL, {"search": "Alpha"})
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("Alpha", names)
        self.assertEqual(len(names), 1)


# ── POST /programmes/ ─────────────────────────────────────────────────────────


class ProgrammeCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_creates_programme(self):
        response = self.client.post(LIST_URL, {"name": "New Programme"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Programme.objects.filter(name="New Programme").exists())

    def test_duplicate_name_returns_409(self):
        make_programme("Existing")
        response = self.client.post(LIST_URL, {"name": "Existing"}, format="json")
        self.assertEqual(response.status_code, 409)

    def test_missing_name_returns_400(self):
        response = self.client.post(LIST_URL, {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        response = self.client.post(LIST_URL, {"name": "X"}, format="json")
        self.assertEqual(response.status_code, 401)


# ── GET /programmes/<code>/ ───────────────────────────────────────────────────


class ProgrammeRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.programme = make_programme("Alpha")

    def test_retrieves_programme(self):
        response = self.client.get(DETAIL_URL.format(self.programme.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["name"], "Alpha")

    def test_unknown_code_returns_404(self):
        response = self.client.get(DETAIL_URL.format("PROG-99999"))
        self.assertEqual(response.status_code, 404)


# ── PATCH /programmes/<code>/ ─────────────────────────────────────────────────


class ProgrammeUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_updates_name(self):
        p = make_programme("Old Name")
        response = self.client.patch(
            DETAIL_URL.format(p.code), {"name": "New Name"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        p.refresh_from_db()
        self.assertEqual(p.name, "New Name")

    def test_protected_programme_returns_422(self):
        p = Programme.objects.get(name="Others")
        response = self.client.patch(
            DETAIL_URL.format(p.code), {"name": "Renamed"}, format="json"
        )
        self.assertEqual(response.status_code, 422)


# ── DELETE /programmes/<code>/ ────────────────────────────────────────────────


class ProgrammeDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_deletes_programme(self):
        p = make_programme("Temp")
        response = self.client.delete(DETAIL_URL.format(p.code))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Programme.objects.filter(code=p.code).exists())

    def test_protected_returns_422(self):
        p = Programme.objects.get(name="Others")
        response = self.client.delete(DETAIL_URL.format(p.code))
        self.assertEqual(response.status_code, 422)

    def test_unknown_code_returns_404(self):
        response = self.client.delete(DETAIL_URL.format("PROG-99999"))
        self.assertEqual(response.status_code, 404)


# ── POST /programmes/<code>/activate|deactivate/ ─────────────────────────────


class ProgrammeToggleAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_activates_programme(self):
        p = make_programme("Alpha", is_active=False)
        response = self.client.post(ACTIVATE_URL.format(p.code))
        self.assertEqual(response.status_code, 200)
        p.refresh_from_db()
        self.assertTrue(p.is_active)

    def test_deactivates_programme(self):
        p = make_programme("Alpha", is_active=True)
        response = self.client.post(DEACTIVATE_URL.format(p.code))
        self.assertEqual(response.status_code, 200)
        p.refresh_from_db()
        self.assertFalse(p.is_active)

    def test_protected_activate_returns_422(self):
        p = Programme.objects.get(name="Others")
        p.is_active = False
        p.save()
        response = self.client.post(ACTIVATE_URL.format(p.code))
        self.assertEqual(response.status_code, 422)


# ── Import / Export specs ─────────────────────────────────────────────────────


class ProgrammeImportExportSpecsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_import_specs_returns_200(self):
        response = self.client.get(IMPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)

    def test_import_sample_returns_csv(self):
        response = self.client.get(IMPORT_SAMPLE_URL)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])

    def test_export_specs_returns_200(self):
        response = self.client.get(EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)

    def test_stats_returns_200(self):
        response = self.client.get(STATS_URL)
        self.assertEqual(response.status_code, 200)

    def test_options_returns_200(self):
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.status_code, 200)
