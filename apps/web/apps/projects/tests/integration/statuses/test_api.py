from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.projects.models import ProjectSubStatus
from apps.projects.tests.factories import (
    make_csv_file,
    make_project_status,
    make_project_substatus,
)
from apps.users.tests.factories import make_user

# ── Status URL constants ──────────────────────────────────────────────────────

STATUS_LIST_URL = "/api/v1/projects/statuses/"
STATUS_OPTIONS_URL = "/api/v1/projects/statuses/options/"
STATUS_STATS_URL = "/api/v1/projects/statuses/stats/"
STATUS_DETAIL_URL = "/api/v1/projects/statuses/{}/"
STATUS_EXPORT_URL = "/api/v1/projects/statuses/export/"
STATUS_EXPORT_SPECS_URL = "/api/v1/projects/statuses/export/specs/"

# ── SubStatus URL constants ───────────────────────────────────────────────────

SUB_LIST_URL = "/api/v1/projects/statuses/{}/substatus/"
SUB_STATS_URL = "/api/v1/projects/statuses/{}/substatus/stats/"
SUB_OPTIONS_URL = "/api/v1/projects/statuses/{}/substatus/options/"
SUB_REORDER_URL = "/api/v1/projects/statuses/{}/substatus/reorder/"
SUB_DETAIL_URL = "/api/v1/projects/statuses/{}/substatus/{}/"
SUB_ACTIVATE_URL = "/api/v1/projects/statuses/{}/substatus/{}/activate/"
SUB_DEACTIVATE_URL = "/api/v1/projects/statuses/{}/substatus/{}/deactivate/"
SUB_IMPORT_SPECS_URL = "/api/v1/projects/statuses/{}/substatus/import/specs/"
SUB_IMPORT_SAMPLE_URL = "/api/v1/projects/statuses/{}/substatus/import/sample/"
SUB_IMPORT_URL = "/api/v1/projects/statuses/{}/substatus/import/"
SUB_EXPORT_SPECS_URL = "/api/v1/projects/statuses/{}/substatus/export/specs/"
SUB_EXPORT_URL = "/api/v1/projects/statuses/{}/substatus/export/"

FLAT_OPTIONS_URL = "/api/v1/projects/sub-statuses/options/"
GLOBAL_IMPORT_SPECS_URL = "/api/v1/projects/sub-statuses/import/specs/"
GLOBAL_IMPORT_SAMPLE_URL = "/api/v1/projects/sub-statuses/import/sample/"
GLOBAL_IMPORT_URL = "/api/v1/projects/sub-statuses/import/"
GLOBAL_EXPORT_SPECS_URL = "/api/v1/projects/sub-statuses/export/specs/"
GLOBAL_EXPORT_URL = "/api/v1/projects/sub-statuses/export/"


# ── GET /projects/statuses/ ───────────────────────────────────────────────────


class ProjectStatusListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_project_status("Alpha", is_active=True)
        make_project_status("Inactive", is_active=False)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(STATUS_LIST_URL)
        self.assertEqual(response.status_code, 401)

    def test_defaults_to_active_only(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(STATUS_LIST_URL)
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("Alpha", names)
        self.assertNotIn("Inactive", names)

    def test_is_active_false_returns_inactive(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(STATUS_LIST_URL, {"is_active": "false"})
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("Inactive", names)
        self.assertNotIn("Alpha", names)

    def test_response_has_pagination(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(STATUS_LIST_URL)
        self.assertIn("pagination", response.data["data"])

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(STATUS_LIST_URL)
        self.assertTrue(response.data["success"])

    def test_search_filters_by_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(STATUS_LIST_URL, {"search": "Alpha"})
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("Alpha", names)
        self.assertEqual(len(names), 1)


# ── GET /projects/statuses/<code>/ ───────────────────────────────────────────


class ProjectStatusRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.status = make_project_status("Alpha")

    def test_retrieves_status(self):
        response = self.client.get(STATUS_DETAIL_URL.format(self.status.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["name"], "Alpha")

    def test_response_includes_code(self):
        response = self.client.get(STATUS_DETAIL_URL.format(self.status.code))
        self.assertTrue(response.data["data"]["code"].startswith("PROJSTAT-"))

    def test_unknown_code_returns_404(self):
        response = self.client.get(STATUS_DETAIL_URL.format("PROJSTAT-99999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        response = self.client.get(STATUS_DETAIL_URL.format(self.status.code))
        self.assertEqual(response.status_code, 401)


# ── GET /projects/statuses/options/ ──────────────────────────────────────────


class ProjectStatusOptionsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_returns_200(self):
        response = self.client.get(STATUS_OPTIONS_URL)
        self.assertEqual(response.status_code, 200)

    def test_returns_only_active(self):
        make_project_status("Active")
        make_project_status("Inactive", is_active=False)
        response = self.client.get(STATUS_OPTIONS_URL)
        names = [o["name"] for o in response.data["data"]]
        self.assertIn("Active", names)
        self.assertNotIn("Inactive", names)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        response = self.client.get(STATUS_OPTIONS_URL)
        self.assertEqual(response.status_code, 401)


# ── GET /projects/statuses/stats/ ─────────────────────────────────────────────


class ProjectStatusStatsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_returns_200(self):
        response = self.client.get(STATUS_STATS_URL)
        self.assertEqual(response.status_code, 200)

    def test_counts_are_present(self):
        make_project_status("A", is_active=True)
        make_project_status("B", is_active=False)
        response = self.client.get(STATUS_STATS_URL)
        stats = response.data["data"]
        self.assertIn("total", stats)
        self.assertIn("active", stats)
        self.assertIn("inactive", stats)


# ── Status export ─────────────────────────────────────────────────────────────


class ProjectStatusExportAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_export_specs_returns_200(self):
        response = self.client.get(STATUS_EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)

    def test_export_returns_csv(self):
        make_project_status("Alpha")
        response = self.client.get(STATUS_EXPORT_URL)
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_export_specs_returns_401(self):
        self.client.logout()
        response = self.client.get(STATUS_EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 401)


# ── GET /projects/statuses/<status_code>/substatus/ ───────────────────────────


class ProjectSubStatusListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.status = make_project_status("Active")
        make_project_substatus("Draft", status=self.status, is_active=True)
        make_project_substatus("Archived", status=self.status, is_active=False)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(SUB_LIST_URL.format(self.status.code))
        self.assertEqual(response.status_code, 401)

    def test_defaults_to_active_only(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(SUB_LIST_URL.format(self.status.code))
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("Draft", names)
        self.assertNotIn("Archived", names)

    def test_is_active_false_returns_inactive(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            SUB_LIST_URL.format(self.status.code), {"is_active": "false"}
        )
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("Archived", names)
        self.assertNotIn("Draft", names)

    def test_response_has_pagination(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(SUB_LIST_URL.format(self.status.code))
        self.assertIn("pagination", response.data["data"])


# ── POST /projects/statuses/<status_code>/substatus/ ──────────────────────────


class ProjectSubStatusCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.status = make_project_status("Active")

    def test_creates_substatus(self):
        response = self.client.post(
            SUB_LIST_URL.format(self.status.code),
            {"name": "Draft"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(ProjectSubStatus.objects.filter(name="Draft").exists())

    def test_response_includes_code(self):
        response = self.client.post(
            SUB_LIST_URL.format(self.status.code),
            {"name": "Draft"},
            format="json",
        )
        self.assertIn("code", response.data["data"])
        self.assertTrue(response.data["data"]["code"].startswith("PROJSUBSTAT-"))

    def test_duplicate_name_returns_409(self):
        make_project_substatus("Draft", status=self.status)
        response = self.client.post(
            SUB_LIST_URL.format(self.status.code),
            {"name": "Draft"},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_missing_name_returns_400(self):
        response = self.client.post(
            SUB_LIST_URL.format(self.status.code), {}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_unknown_parent_status_returns_404(self):
        response = self.client.post(
            SUB_LIST_URL.format("PROJSTAT-99999"),
            {"name": "Draft"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        response = self.client.post(
            SUB_LIST_URL.format(self.status.code),
            {"name": "Draft"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)


# ── GET /projects/statuses/<status_code>/substatus/<code>/ ────────────────────


class ProjectSubStatusRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.status = make_project_status("Active")
        self.ss = make_project_substatus("Draft", status=self.status)

    def test_retrieves_substatus(self):
        response = self.client.get(
            SUB_DETAIL_URL.format(self.status.code, self.ss.code)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["name"], "Draft")

    def test_response_includes_main_status_fields(self):
        response = self.client.get(
            SUB_DETAIL_URL.format(self.status.code, self.ss.code)
        )
        data = response.data["data"]
        self.assertIn("main_status_code", data)
        self.assertIn("main_status_name", data)

    def test_unknown_code_returns_404(self):
        response = self.client.get(
            SUB_DETAIL_URL.format(self.status.code, "PROJSUBSTAT-99999")
        )
        self.assertEqual(response.status_code, 404)


# ── PATCH /projects/statuses/<status_code>/substatus/<code>/ ──────────────────


class ProjectSubStatusUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.status = make_project_status("Active")

    def test_updates_name(self):
        ss = make_project_substatus("Old Name", status=self.status)
        response = self.client.patch(
            SUB_DETAIL_URL.format(self.status.code, ss.code),
            {"name": "New Name"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        ss.refresh_from_db()
        self.assertEqual(ss.name, "New Name")

    def test_duplicate_name_returns_409(self):
        make_project_substatus("Alpha", status=self.status)
        ss2 = make_project_substatus("Beta", status=self.status)
        response = self.client.patch(
            SUB_DETAIL_URL.format(self.status.code, ss2.code),
            {"name": "Alpha"},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_unknown_code_returns_404(self):
        response = self.client.patch(
            SUB_DETAIL_URL.format(self.status.code, "PROJSUBSTAT-99999"),
            {"name": "X"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)


# ── DELETE /projects/statuses/<status_code>/substatus/<code>/ ─────────────────


class ProjectSubStatusDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.status = make_project_status("Active")

    def test_deletes_substatus(self):
        ss = make_project_substatus("Temp", status=self.status)
        response = self.client.delete(SUB_DETAIL_URL.format(self.status.code, ss.code))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ProjectSubStatus.objects.filter(code=ss.code).exists())

    def test_unknown_code_returns_404(self):
        response = self.client.delete(
            SUB_DETAIL_URL.format(self.status.code, "PROJSUBSTAT-99999")
        )
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        ss = make_project_substatus("Temp", status=self.status)
        response = self.client.delete(SUB_DETAIL_URL.format(self.status.code, ss.code))
        self.assertEqual(response.status_code, 401)


# ── POST activate / deactivate ────────────────────────────────────────────────


class ProjectSubStatusToggleAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.status = make_project_status("Active")

    def test_activates_substatus(self):
        ss = make_project_substatus("Draft", status=self.status, is_active=False)
        response = self.client.post(SUB_ACTIVATE_URL.format(self.status.code, ss.code))
        self.assertEqual(response.status_code, 200)
        ss.refresh_from_db()
        self.assertTrue(ss.is_active)

    def test_deactivates_substatus(self):
        ss = make_project_substatus("Draft", status=self.status, is_active=True)
        response = self.client.post(
            SUB_DEACTIVATE_URL.format(self.status.code, ss.code)
        )
        self.assertEqual(response.status_code, 200)
        ss.refresh_from_db()
        self.assertFalse(ss.is_active)

    def test_unknown_activate_returns_404(self):
        response = self.client.post(
            SUB_ACTIVATE_URL.format(self.status.code, "PROJSUBSTAT-99999")
        )
        self.assertEqual(response.status_code, 404)


# ── GET options / stats ───────────────────────────────────────────────────────


class ProjectSubStatusOptionsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.status = make_project_status("Active")

    def test_options_returns_200(self):
        response = self.client.get(SUB_OPTIONS_URL.format(self.status.code))
        self.assertEqual(response.status_code, 200)

    def test_options_returns_only_active(self):
        make_project_substatus("Draft", status=self.status, is_active=True)
        make_project_substatus("Archived", status=self.status, is_active=False)
        response = self.client.get(SUB_OPTIONS_URL.format(self.status.code))
        names = [o["name"] for o in response.data["data"]]
        self.assertIn("Draft", names)
        self.assertNotIn("Archived", names)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        response = self.client.get(SUB_OPTIONS_URL.format(self.status.code))
        self.assertEqual(response.status_code, 401)


class ProjectSubStatusStatsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.status = make_project_status("Active")

    def test_stats_returns_200(self):
        response = self.client.get(SUB_STATS_URL.format(self.status.code))
        self.assertEqual(response.status_code, 200)

    def test_counts_are_present(self):
        make_project_substatus("A", status=self.status, is_active=True)
        make_project_substatus("B", status=self.status, is_active=False)
        response = self.client.get(SUB_STATS_URL.format(self.status.code))
        stats = response.data["data"]
        self.assertIn("total", stats)
        self.assertIn("active", stats)
        self.assertIn("inactive", stats)


# ── POST /projects/statuses/<status_code>/substatus/reorder/ ──────────────────


class ProjectSubStatusReorderAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.status = make_project_status("Active")

    def test_reorder_returns_200(self):
        ss1 = make_project_substatus("Alpha", status=self.status, order=1)
        ss2 = make_project_substatus("Beta", status=self.status, order=2)
        response = self.client.post(
            SUB_REORDER_URL.format(self.status.code),
            {"codes": [ss2.code, ss1.code]},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_reorder_updates_order(self):
        ss1 = make_project_substatus("Alpha", status=self.status, order=1)
        ss2 = make_project_substatus("Beta", status=self.status, order=2)
        self.client.post(
            SUB_REORDER_URL.format(self.status.code),
            {"codes": [ss2.code, ss1.code]},
            format="json",
        )
        ss1.refresh_from_db()
        ss2.refresh_from_db()
        self.assertEqual(ss2.order, 1)
        self.assertEqual(ss1.order, 2)

    def test_missing_codes_returns_400(self):
        response = self.client.post(
            SUB_REORDER_URL.format(self.status.code), {}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        response = self.client.post(
            SUB_REORDER_URL.format(self.status.code),
            {"codes": []},
            format="json",
        )
        self.assertEqual(response.status_code, 401)


# ── Sub-status import / export endpoints ─────────────────────────────────────


class ProjectSubStatusImportExportAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.status = make_project_status("Active")

    def test_import_specs_returns_200(self):
        response = self.client.get(SUB_IMPORT_SPECS_URL.format(self.status.code))
        self.assertEqual(response.status_code, 200)

    def test_import_sample_returns_csv(self):
        response = self.client.get(SUB_IMPORT_SAMPLE_URL.format(self.status.code))
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])

    def test_export_specs_returns_200(self):
        response = self.client.get(SUB_EXPORT_SPECS_URL.format(self.status.code))
        self.assertEqual(response.status_code, 200)

    def test_bulk_import_creates_substatus(self):
        csv_content = "name\nImported\n"
        f = make_csv_file(csv_content, name="sub.csv")
        response = self.client.post(
            SUB_IMPORT_URL.format(self.status.code),
            {"file": f},
            format="multipart",
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(ProjectSubStatus.objects.filter(name="Imported").exists())

    def test_unauthenticated_import_specs_returns_401(self):
        self.client.logout()
        response = self.client.get(SUB_IMPORT_SPECS_URL.format(self.status.code))
        self.assertEqual(response.status_code, 401)


# ── Flat options endpoint ─────────────────────────────────────────────────────


class ProjectSubStatusFlatOptionsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_flat_options_returns_200(self):
        response = self.client.get(FLAT_OPTIONS_URL)
        self.assertEqual(response.status_code, 200)

    def test_flat_options_returns_only_active(self):
        s = make_project_status("Active")
        make_project_substatus("Draft", status=s, is_active=True)
        make_project_substatus("Hidden", status=s, is_active=False)
        response = self.client.get(FLAT_OPTIONS_URL)
        names = [o["name"] for o in response.data["data"]]
        self.assertIn("Draft", names)
        self.assertNotIn("Hidden", names)

    def test_unauthenticated_returns_401(self):
        self.client.logout()
        response = self.client.get(FLAT_OPTIONS_URL)
        self.assertEqual(response.status_code, 401)


# ── Global import / export endpoints ─────────────────────────────────────────


class ProjectSubStatusGlobalImportExportAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_global_import_specs_returns_200(self):
        response = self.client.get(GLOBAL_IMPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)

    def test_global_import_sample_returns_csv(self):
        response = self.client.get(GLOBAL_IMPORT_SAMPLE_URL)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response["Content-Type"])

    def test_global_export_specs_returns_200(self):
        response = self.client.get(GLOBAL_EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)

    def test_global_bulk_import_creates_substatus(self):
        status = make_project_status("Active")
        csv_content = f"main_status_code,name\n{status.code},GlobalDraft\n"
        f = make_csv_file(csv_content, name="global.csv")
        response = self.client.post(
            GLOBAL_IMPORT_URL,
            {"file": f},
            format="multipart",
        )
        self.assertEqual(response.status_code, 207)
        self.assertTrue(ProjectSubStatus.objects.filter(name="GlobalDraft").exists())

    def test_unauthenticated_global_import_specs_returns_401(self):
        self.client.logout()
        response = self.client.get(GLOBAL_IMPORT_SPECS_URL)
        self.assertEqual(response.status_code, 401)
