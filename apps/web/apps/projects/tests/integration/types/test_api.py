from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.projects.models import ProjectType
from apps.projects.tests.factories import make_project_type
from apps.users.tests.factories import make_user

LIST_URL = "/api/v1/projects/types/"
OPTIONS_URL = "/api/v1/projects/types/options/"
STATS_URL = "/api/v1/projects/types/stats/"
DETAIL_URL = "/api/v1/projects/types/{}/"
ACTIVATE_URL = "/api/v1/projects/types/{}/activate/"
DEACTIVATE_URL = "/api/v1/projects/types/{}/deactivate/"
IMPORT_URL = "/api/v1/projects/types/import/"
IMPORT_SPECS_URL = "/api/v1/projects/types/import/specs/"
IMPORT_SAMPLE_URL = "/api/v1/projects/types/import/sample/"
EXPORT_URL = "/api/v1/projects/types/export/"
EXPORT_SPECS_URL = "/api/v1/projects/types/export/specs/"


# ── GET /projects/types/ ──────────────────────────────────────────────────────


class ProjectTypeListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_project_type("Alpha", is_active=True)
        make_project_type("Inactive", is_active=False)

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


# ── POST /projects/types/ ─────────────────────────────────────────────────────


class ProjectTypeCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_creates_project_type(self):
        response = self.client.post(LIST_URL, {"name": "Internal"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(ProjectType.objects.filter(name="Internal").exists())

    def test_duplicate_name_returns_409(self):
        make_project_type("Internal")
        response = self.client.post(LIST_URL, {"name": "Internal"}, format="json")
        self.assertEqual(response.status_code, 409)

    def test_missing_name_returns_400(self):
        response = self.client.post(LIST_URL, {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        response = self.client.post(LIST_URL, {"name": "X"}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_creates_with_description(self):
        response = self.client.post(
            LIST_URL,
            {"name": "Internal", "description": "Internal classification"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        pt = ProjectType.objects.get(name="Internal")
        self.assertEqual(pt.description, "Internal classification")

    def test_response_includes_code(self):
        response = self.client.post(LIST_URL, {"name": "Internal"}, format="json")
        self.assertIn("code", response.data["data"])
        self.assertTrue(response.data["data"]["code"].startswith("PROJTYPE-"))


# ── GET /projects/types/<code>/ ───────────────────────────────────────────────


class ProjectTypeRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.pt = make_project_type("Internal")

    def test_retrieves_project_type(self):
        response = self.client.get(DETAIL_URL.format(self.pt.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["name"], "Internal")

    def test_unknown_code_returns_404(self):
        response = self.client.get(DETAIL_URL.format("PROJTYPE-99999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        response = self.client.get(DETAIL_URL.format(self.pt.code))
        self.assertEqual(response.status_code, 401)


# ── PATCH /projects/types/<code>/ ─────────────────────────────────────────────


class ProjectTypeUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_updates_name(self):
        pt = make_project_type("Old Name")
        response = self.client.patch(
            DETAIL_URL.format(pt.code), {"name": "New Name"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        pt.refresh_from_db()
        self.assertEqual(pt.name, "New Name")

    def test_protected_project_type_returns_422(self):
        pt = make_project_type("Protected", is_protected=True)
        response = self.client.patch(
            DETAIL_URL.format(pt.code), {"name": "Renamed"}, format="json"
        )
        self.assertEqual(response.status_code, 422)

    def test_duplicate_name_returns_409(self):
        make_project_type("Alpha")
        pt2 = make_project_type("Beta")
        response = self.client.patch(
            DETAIL_URL.format(pt2.code), {"name": "Alpha"}, format="json"
        )
        self.assertEqual(response.status_code, 409)

    def test_unknown_code_returns_404(self):
        response = self.client.patch(
            DETAIL_URL.format("PROJTYPE-99999"), {"name": "X"}, format="json"
        )
        self.assertEqual(response.status_code, 404)


# ── DELETE /projects/types/<code>/ ────────────────────────────────────────────


class ProjectTypeDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_deletes_project_type(self):
        pt = make_project_type("Temp")
        response = self.client.delete(DETAIL_URL.format(pt.code))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ProjectType.objects.filter(code=pt.code).exists())

    def test_protected_returns_422(self):
        pt = make_project_type("Protected", is_protected=True)
        response = self.client.delete(DETAIL_URL.format(pt.code))
        self.assertEqual(response.status_code, 422)

    def test_unknown_code_returns_404(self):
        response = self.client.delete(DETAIL_URL.format("PROJTYPE-99999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        pt = make_project_type("Temp")
        response = self.client.delete(DETAIL_URL.format(pt.code))
        self.assertEqual(response.status_code, 401)


# ── POST /projects/types/<code>/activate|deactivate/ ─────────────────────────


class ProjectTypeToggleAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_activates_project_type(self):
        pt = make_project_type("Alpha", is_active=False)
        response = self.client.post(ACTIVATE_URL.format(pt.code))
        self.assertEqual(response.status_code, 200)
        pt.refresh_from_db()
        self.assertTrue(pt.is_active)

    def test_deactivates_project_type(self):
        pt = make_project_type("Alpha", is_active=True)
        response = self.client.post(DEACTIVATE_URL.format(pt.code))
        self.assertEqual(response.status_code, 200)
        pt.refresh_from_db()
        self.assertFalse(pt.is_active)

    def test_protected_activate_returns_422(self):
        pt = make_project_type("Protected", is_protected=True, is_active=False)
        response = self.client.post(ACTIVATE_URL.format(pt.code))
        self.assertEqual(response.status_code, 422)

    def test_protected_deactivate_returns_422(self):
        pt = make_project_type("Protected", is_protected=True, is_active=True)
        response = self.client.post(DEACTIVATE_URL.format(pt.code))
        self.assertEqual(response.status_code, 422)

    def test_unknown_activate_returns_404(self):
        response = self.client.post(ACTIVATE_URL.format("PROJTYPE-99999"))
        self.assertEqual(response.status_code, 404)


# ── GET /projects/types/options/ ──────────────────────────────────────────────


class ProjectTypeOptionsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_returns_200(self):
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.status_code, 200)

    def test_returns_only_active(self):
        make_project_type("Active")
        make_project_type("Inactive", is_active=False)
        response = self.client.get(OPTIONS_URL)
        names = [o["name"] for o in response.data["data"]]
        self.assertIn("Active", names)
        self.assertNotIn("Inactive", names)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.status_code, 401)


# ── GET /projects/types/stats/ ────────────────────────────────────────────────


class ProjectTypeStatsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_returns_200(self):
        response = self.client.get(STATS_URL)
        self.assertEqual(response.status_code, 200)

    def test_counts_are_present(self):
        make_project_type("A", is_active=True)
        make_project_type("B", is_active=False)
        response = self.client.get(STATS_URL)
        stats = response.data["data"]
        self.assertIn("total", stats)
        self.assertIn("active", stats)
        self.assertIn("inactive", stats)


# ── Import / Export specs ─────────────────────────────────────────────────────


class ProjectTypeImportExportSpecsAPITest(TestCase):
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

    def test_unauthenticated_import_specs_returns_401(self):
        self.client.logout()
        response = self.client.get(IMPORT_SPECS_URL)
        self.assertEqual(response.status_code, 401)
