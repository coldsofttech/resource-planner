import io

from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.projects.tests.factories import make_project_type
from apps.recharges.models import ProjectTypeMapping, RechargeType
from apps.recharges.tests.factories import (
    make_project_type_mapping,
    make_recharge_type,
)
from apps.users.tests.factories import make_user

LIST_URL = "/api/v1/recharges/types/"
STATS_URL = "/api/v1/recharges/types/stats/"
OPTIONS_URL = "/api/v1/recharges/types/options/"
DETAIL_URL = "/api/v1/recharges/types/{}/"
ACTIVATE_URL = "/api/v1/recharges/types/{}/activate/"
DEACTIVATE_URL = "/api/v1/recharges/types/{}/deactivate/"
IMPORT_URL = "/api/v1/recharges/types/import/"
IMPORT_SPECS_URL = "/api/v1/recharges/types/import/specs/"
IMPORT_SAMPLE_URL = "/api/v1/recharges/types/import/sample/"
EXPORT_URL = "/api/v1/recharges/types/export/"
EXPORT_SPECS_URL = "/api/v1/recharges/types/export/specs/"
MAPPINGS_URL = "/api/v1/recharges/types/{}/mappings/"
MAPPING_DETAIL_URL = "/api/v1/recharges/types/{}/mappings/{}/"


# ── GET /recharges/types/ ─────────────────────────────────────────────────────


class RechargeTypeListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_recharge_type("BAU", is_active=True)
        make_recharge_type("HOLIDAY", is_active=False)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 401)

    def test_defaults_to_active_only(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("BAU", names)
        self.assertNotIn("HOLIDAY", names)

    def test_is_active_false_returns_inactive(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"is_active": "false"})
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("HOLIDAY", names)
        self.assertNotIn("BAU", names)

    def test_response_includes_pagination(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertIn("pagination", response.data["data"])

    def test_search_filters_results(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"search": "BAU"})
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("BAU", names)
        self.assertEqual(len(names), 1)


# ── GET /recharges/types/stats/ ───────────────────────────────────────────────


class RechargeTypeStatsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_recharge_type("BAU", is_active=True)
        make_recharge_type("PROJECT", is_active=True)
        make_recharge_type("HOLIDAY", is_active=False)

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


# ── GET /recharges/types/options/ ─────────────────────────────────────────────


class RechargeTypeOptionsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_recharge_type("BAU", is_active=True)
        make_recharge_type("HOLIDAY", is_active=False)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.status_code, 401)

    def test_returns_only_active_options(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.status_code, 200)
        names = [o["name"] for o in response.data["data"]]
        self.assertIn("BAU", names)
        self.assertNotIn("HOLIDAY", names)

    def test_options_include_code_and_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        self.assertIn("code", response.data["data"][0])
        self.assertIn("name", response.data["data"][0])


# ── GET /recharges/types/<code>/ ──────────────────────────────────────────────


class RechargeTypeRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.rt = make_recharge_type("BAU")

    def test_unauthenticated_returns_401(self):
        response = self.client.get(DETAIL_URL.format(self.rt.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_recharge_type(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.rt.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["name"], "BAU")

    def test_unknown_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format("RECHTY-999999"))
        self.assertEqual(response.status_code, 404)

    def test_response_includes_code_and_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.rt.code))
        self.assertIn("code", response.data["data"])
        self.assertIn("name", response.data["data"])


# ── POST /recharges/types/ ────────────────────────────────────────────────────


class RechargeTypeCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.post(LIST_URL, {"name": "BAU"}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_creates_recharge_type(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"name": "BAU"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["name"], "BAU")

    def test_duplicate_name_returns_409(self):
        make_recharge_type("BAU")
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"name": "BAU"}, format="json")
        self.assertEqual(response.status_code, 409)

    def test_invalid_name_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"name": "lowercase"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_missing_name_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_response_contains_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"name": "BAU"}, format="json")
        self.assertTrue(response.data["data"]["code"].startswith("RECHTY-"))


# ── PATCH /recharges/types/<code>/ ───────────────────────────────────────────


class RechargeTypeUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.rt = make_recharge_type("BAU")

    def test_unauthenticated_returns_401(self):
        response = self.client.patch(
            DETAIL_URL.format(self.rt.code), {"name": "PROJECT"}, format="json"
        )
        self.assertEqual(response.status_code, 401)

    def test_updates_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.rt.code), {"name": "PROJECT"}, format="json"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["name"], "PROJECT")

    def test_unknown_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format("RECHTY-999999"), {"name": "PROJECT"}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_duplicate_name_returns_409(self):
        make_recharge_type("PROJECT")
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.rt.code), {"name": "PROJECT"}, format="json"
        )
        self.assertEqual(response.status_code, 409)

    def test_invalid_name_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.rt.code), {"name": "lowercase"}, format="json"
        )
        self.assertEqual(response.status_code, 400)


# ── DELETE /recharges/types/<code>/ ──────────────────────────────────────────


class RechargeTypeDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.rt = make_recharge_type("BAU")

    def test_unauthenticated_returns_401(self):
        response = self.client.delete(DETAIL_URL.format(self.rt.code))
        self.assertEqual(response.status_code, 401)

    def test_deletes_recharge_type(self):
        self.client.force_authenticate(user=self.user)
        code = self.rt.code
        response = self.client.delete(DETAIL_URL.format(code))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(RechargeType.objects.filter(code=code).exists())

    def test_unknown_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format("RECHTY-999999"))
        self.assertEqual(response.status_code, 404)


# ── POST /recharges/types/<code>/activate/ ────────────────────────────────────


class RechargeTypeActivateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.rt = make_recharge_type("BAU", is_active=False)

    def test_unauthenticated_returns_401(self):
        response = self.client.post(ACTIVATE_URL.format(self.rt.code))
        self.assertEqual(response.status_code, 401)

    def test_activates_recharge_type(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format(self.rt.code))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["data"]["is_active"])

    def test_unknown_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format("RECHTY-999999"))
        self.assertEqual(response.status_code, 404)


# ── POST /recharges/types/<code>/deactivate/ ──────────────────────────────────


class RechargeTypeDeactivateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.rt = make_recharge_type("BAU", is_active=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.post(DEACTIVATE_URL.format(self.rt.code))
        self.assertEqual(response.status_code, 401)

    def test_deactivates_recharge_type(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(DEACTIVATE_URL.format(self.rt.code))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["data"]["is_active"])

    def test_unknown_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(DEACTIVATE_URL.format("RECHTY-999999"))
        self.assertEqual(response.status_code, 404)


# ── GET /recharges/types/import/specs/ ───────────────────────────────────────


class RechargeTypeImportSpecsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(IMPORT_SPECS_URL)
        self.assertEqual(response.status_code, 401)

    def test_returns_import_specs(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(IMPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertIn("fields", response.data["data"])


# ── GET /recharges/types/import/sample/ ──────────────────────────────────────


class RechargeTypeImportSampleAPITest(TestCase):
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


# ── POST /recharges/types/import/ ─────────────────────────────────────────────


class RechargeTypeImportAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def _make_upload(self, rows: list[str]):
        content = "name\n" + "\n".join(rows)
        return io.BytesIO(content.encode("utf-8"))

    def test_unauthenticated_returns_401(self):
        f = self._make_upload(["BAU"])
        response = self.client.post(IMPORT_URL, {"file": f}, format="multipart")
        self.assertEqual(response.status_code, 401)

    def test_imports_valid_csv(self):
        self.client.force_authenticate(user=self.user)
        f = self._make_upload(["BAU"])
        f.name = "types.csv"
        response = self.client.post(IMPORT_URL, {"file": f}, format="multipart")
        self.assertIn(response.status_code, [200, 207])
        self.assertTrue(RechargeType.objects.filter(name="BAU").exists())

    def test_invalid_name_returns_error_in_results(self):
        self.client.force_authenticate(user=self.user)
        f = self._make_upload(["lowercase"])
        f.name = "types.csv"
        response = self.client.post(IMPORT_URL, {"file": f}, format="multipart")
        self.assertIn(response.status_code, [200, 207])
        self.assertGreater(len(response.data["data"]["errors"]), 0)


# ── GET /recharges/types/export/specs/ ───────────────────────────────────────


class RechargeTypeExportSpecsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 401)

    def test_returns_export_specs(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)
        self.assertIn("columns", response.data["data"])


# ── GET /recharges/types/export/ ─────────────────────────────────────────────


class RechargeTypeExportAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_recharge_type("BAU")

    def test_unauthenticated_returns_401(self):
        response = self.client.get(EXPORT_URL)
        self.assertEqual(response.status_code, 401)

    def test_returns_csv_export(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(EXPORT_URL)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.get("Content-Type", ""))


# ── GET /recharges/types/<code>/mappings/ ────────────────────────────────────


class ProjectTypeMappingListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.rt = make_recharge_type("BAU")
        self.pt1 = make_project_type("Internal")
        self.pt2 = make_project_type("External")
        make_project_type_mapping(self.rt, self.pt1)
        make_project_type_mapping(self.rt, self.pt2)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(MAPPINGS_URL.format(self.rt.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_mappings_for_recharge_type(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(MAPPINGS_URL.format(self.rt.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["pagination"]["total_count"], 2)

    def test_excludes_mappings_for_other_recharge_type(self):
        rt2 = make_recharge_type("PROJECT")
        self.client.force_authenticate(user=self.user)
        response = self.client.get(MAPPINGS_URL.format(rt2.code))
        self.assertEqual(response.data["data"]["pagination"]["total_count"], 0)

    def test_response_includes_pagination(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(MAPPINGS_URL.format(self.rt.code))
        self.assertIn("pagination", response.data["data"])


# ── GET /recharges/types/<code>/mappings/<pk>/ ───────────────────────────────


class ProjectTypeMappingRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.rt = make_recharge_type("BAU")
        self.pt = make_project_type("Internal")
        self.mapping = make_project_type_mapping(self.rt, self.pt)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(
            MAPPING_DETAIL_URL.format(self.rt.code, self.mapping.pk)
        )
        self.assertEqual(response.status_code, 401)

    def test_returns_mapping(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            MAPPING_DETAIL_URL.format(self.rt.code, self.mapping.pk)
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("project_type", response.data["data"])

    def test_unknown_pk_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(MAPPING_DETAIL_URL.format(self.rt.code, 999999))
        self.assertEqual(response.status_code, 404)

    def test_wrong_recharge_type_returns_404(self):
        rt2 = make_recharge_type("PROJECT")
        self.client.force_authenticate(user=self.user)
        response = self.client.get(MAPPING_DETAIL_URL.format(rt2.code, self.mapping.pk))
        self.assertEqual(response.status_code, 404)


# ── POST /recharges/types/<code>/mappings/ ───────────────────────────────────


class ProjectTypeMappingCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.rt = make_recharge_type("BAU")
        self.pt = make_project_type("Internal")

    def test_unauthenticated_returns_401(self):
        response = self.client.post(
            MAPPINGS_URL.format(self.rt.code),
            {"project_type_code": self.pt.code},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_creates_mapping(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            MAPPINGS_URL.format(self.rt.code),
            {"project_type_code": self.pt.code},
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_duplicate_mapping_returns_409(self):
        make_project_type_mapping(self.rt, self.pt)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            MAPPINGS_URL.format(self.rt.code),
            {"project_type_code": self.pt.code},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_unknown_project_type_code_returns_422(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            MAPPINGS_URL.format(self.rt.code),
            {"project_type_code": "PROJTYPE-999999"},
            format="json",
        )
        self.assertEqual(response.status_code, 422)

    def test_missing_project_type_code_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            MAPPINGS_URL.format(self.rt.code), {}, format="json"
        )
        self.assertEqual(response.status_code, 400)

    def test_unknown_recharge_type_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            MAPPINGS_URL.format("RECHTY-999999"),
            {"project_type_code": self.pt.code},
            format="json",
        )
        self.assertEqual(response.status_code, 404)


# ── PATCH /recharges/types/<code>/mappings/<pk>/ ─────────────────────────────


class ProjectTypeMappingUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.rt = make_recharge_type("BAU")
        self.pt_a = make_project_type("Type A")
        self.pt_b = make_project_type("Type B")
        self.mapping = make_project_type_mapping(self.rt, self.pt_a)

    def test_unauthenticated_returns_401(self):
        response = self.client.patch(
            MAPPING_DETAIL_URL.format(self.rt.code, self.mapping.pk),
            {"project_type_code": self.pt_b.code},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_updates_project_type(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            MAPPING_DETAIL_URL.format(self.rt.code, self.mapping.pk),
            {"project_type_code": self.pt_b.code},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_unknown_pk_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            MAPPING_DETAIL_URL.format(self.rt.code, 999999),
            {"project_type_code": self.pt_b.code},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_duplicate_mapping_returns_409(self):
        make_project_type_mapping(self.rt, self.pt_b)
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            MAPPING_DETAIL_URL.format(self.rt.code, self.mapping.pk),
            {"project_type_code": self.pt_b.code},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_invalid_project_type_code_returns_422(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            MAPPING_DETAIL_URL.format(self.rt.code, self.mapping.pk),
            {"project_type_code": "PROJTYPE-999999"},
            format="json",
        )
        self.assertEqual(response.status_code, 422)


# ── DELETE /recharges/types/<code>/mappings/<pk>/ ────────────────────────────


class ProjectTypeMappingDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.rt = make_recharge_type("BAU")
        self.pt = make_project_type("Internal")
        self.mapping = make_project_type_mapping(self.rt, self.pt)

    def test_unauthenticated_returns_401(self):
        response = self.client.delete(
            MAPPING_DETAIL_URL.format(self.rt.code, self.mapping.pk)
        )
        self.assertEqual(response.status_code, 401)

    def test_deletes_mapping(self):
        self.client.force_authenticate(user=self.user)
        pk = self.mapping.pk
        response = self.client.delete(MAPPING_DETAIL_URL.format(self.rt.code, pk))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ProjectTypeMapping.objects.filter(pk=pk).exists())

    def test_unknown_pk_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(MAPPING_DETAIL_URL.format(self.rt.code, 999999))
        self.assertEqual(response.status_code, 404)
