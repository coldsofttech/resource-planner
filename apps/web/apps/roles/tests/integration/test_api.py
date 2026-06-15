from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.roles.models import Role
from apps.roles.tests.factories import make_role
from apps.users.tests.factories import make_user

LIST_URL = "/api/v1/roles/"
OPTIONS_URL = "/api/v1/roles/options/"
STATS_URL = "/api/v1/roles/stats/"
DETAIL_URL = "/api/v1/roles/{}/"
ACTIVATE_URL = "/api/v1/roles/{}/activate/"
DEACTIVATE_URL = "/api/v1/roles/{}/deactivate/"
SET_DEFAULT_URL = "/api/v1/roles/{}/set-default/"
IMPORT_URL = "/api/v1/roles/import/"
IMPORT_SPECS_URL = "/api/v1/roles/import/specs/"
IMPORT_SAMPLE_URL = "/api/v1/roles/import/sample/"
EXPORT_URL = "/api/v1/roles/export/"
EXPORT_SPECS_URL = "/api/v1/roles/export/specs/"


# ── GET /roles/ ───────────────────────────────────────────────────────────────


class RoleListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_role("Developer", is_active=True)
        make_role("COBOL Guru", is_active=False)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 401)

    def test_defaults_to_active_only(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 200)
        roles = [r["role"] for r in response.data["data"]["results"]]
        self.assertIn("Developer", roles)
        self.assertNotIn("COBOL Guru", roles)

    def test_is_active_false_returns_inactive(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"is_active": "false"})
        self.assertEqual(response.status_code, 200)
        roles = [r["role"] for r in response.data["data"]["results"]]
        self.assertIn("COBOL Guru", roles)
        self.assertNotIn("Developer", roles)

    def test_response_has_pagination(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertIn("pagination", response.data["data"])

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertTrue(response.data["success"])

    def test_search_param_filters_by_role(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"search": "Developer"})
        self.assertEqual(response.status_code, 200)
        roles = [r["role"] for r in response.data["data"]["results"]]
        self.assertIn("Developer", roles)
        self.assertEqual(len(roles), 1)

    def test_page_size_param_limits_results(self):
        make_role("Analyst", is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"page_size": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["results"]), 1)


# ── GET /roles/stats/ ─────────────────────────────────────────────────────────


class RoleStatsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_role("Developer", is_active=True)
        make_role("Analyst", is_active=True)
        make_role("COBOL Guru", is_active=False)

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


# ── GET /roles/options/ ───────────────────────────────────────────────────────


class RoleOptionsAPITest(TestCase):
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

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        self.assertTrue(response.data["success"])

    def test_returns_only_active_roles(self):
        make_role("Developer", is_active=True)
        make_role("COBOL Guru", is_active=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        roles = [e["role"] for e in response.data["data"]]
        self.assertIn("Developer", roles)
        self.assertNotIn("COBOL Guru", roles)

    def test_returns_empty_list_when_no_active_roles(self):
        make_role("COBOL Guru", is_active=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.data["data"], [])

    def test_each_entry_has_code_and_role(self):
        role = make_role("Developer", is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        entry = response.data["data"][0]
        self.assertIn("code", entry)
        self.assertIn("role", entry)
        self.assertEqual(entry["code"], role.code)
        self.assertEqual(entry["role"], "Developer")

    def test_results_ordered_alphabetically(self):
        make_role("Tester", is_active=True)
        make_role("Analyst", is_active=True)
        make_role("Developer", is_active=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        names = [e["role"] for e in response.data["data"]]
        self.assertEqual(names, sorted(names))


# ── GET /roles/<code>/ ────────────────────────────────────────────────────────


class RoleRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.role = make_role("Developer")

    def test_unauthenticated_returns_401(self):
        response = self.client.get(DETAIL_URL.format(self.role.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_role_detail(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.role.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["role"], "Developer")

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format("ROLE-9999"))
        self.assertEqual(response.status_code, 404)

    def test_response_includes_required_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.role.code))
        data = response.data["data"]
        for field in (
            "code",
            "role",
            "is_active",
            "is_default",
            "is_assignable",
            "is_leadership",
            "created_at",
            "updated_at",
        ):
            self.assertIn(field, data)


# ── POST /roles/ ──────────────────────────────────────────────────────────────


class RoleCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.post(LIST_URL, {"role": "Developer"}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_creates_role(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"role": "Developer"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Role.objects.filter(role="Developer").exists())

    def test_returns_role_detail_on_create(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"role": "Developer"}, format="json")
        self.assertEqual(response.data["data"]["role"], "Developer")

    def test_missing_role_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_duplicate_role_returns_409(self):
        make_role("Developer")
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, {"role": "Developer"}, format="json")
        self.assertEqual(response.status_code, 409)

    def test_is_assignable_accepted(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL,
            {"role": "Developer", "is_assignable": True},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Role.objects.get(role="Developer").is_assignable)

    def test_is_leadership_accepted(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL,
            {"role": "Tech Lead", "is_leadership": True},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Role.objects.get(role="Tech Lead").is_leadership)


# ── PATCH /roles/<code>/ ──────────────────────────────────────────────────────


class RoleUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.role = make_role("Developer")

    def test_unauthenticated_returns_401(self):
        response = self.client.patch(
            DETAIL_URL.format(self.role.code),
            {"role": "Senior Developer"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_updates_role_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.role.code),
            {"role": "Senior Developer"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.role.refresh_from_db()
        self.assertEqual(self.role.role, "Senior Developer")

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format("ROLE-9999"), {"role": "X"}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_duplicate_role_name_returns_409(self):
        make_role("Analyst")
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.role.code), {"role": "Analyst"}, format="json"
        )
        self.assertEqual(response.status_code, 409)

    def test_partial_update_leaves_other_fields_unchanged(self):
        self.client.force_authenticate(user=self.user)
        self.client.patch(
            DETAIL_URL.format(self.role.code), {"is_assignable": True}, format="json"
        )
        self.role.refresh_from_db()
        self.assertEqual(self.role.role, "Developer")
        self.assertTrue(self.role.is_assignable)


# ── DELETE /roles/<code>/ ─────────────────────────────────────────────────────


class RoleDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.role = make_role("Developer")

    def test_unauthenticated_returns_401(self):
        response = self.client.delete(DETAIL_URL.format(self.role.code))
        self.assertEqual(response.status_code, 401)

    def test_deletes_role(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format(self.role.code))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Role.objects.filter(pk=self.role.pk).exists())

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format("ROLE-9999"))
        self.assertEqual(response.status_code, 404)


# ── POST /roles/<code>/activate/ ──────────────────────────────────────────────


class RoleActivateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.role = make_role("Developer", is_active=False)

    def test_unauthenticated_returns_401(self):
        response = self.client.post(ACTIVATE_URL.format(self.role.code))
        self.assertEqual(response.status_code, 401)

    def test_activates_role(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format(self.role.code))
        self.assertEqual(response.status_code, 200)
        self.role.refresh_from_db()
        self.assertTrue(self.role.is_active)

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(ACTIVATE_URL.format("ROLE-9999"))
        self.assertEqual(response.status_code, 404)


# ── POST /roles/<code>/deactivate/ ────────────────────────────────────────────


class RoleDeactivateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.role = make_role("Developer", is_active=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.post(DEACTIVATE_URL.format(self.role.code))
        self.assertEqual(response.status_code, 401)

    def test_deactivates_role(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(DEACTIVATE_URL.format(self.role.code))
        self.assertEqual(response.status_code, 200)
        self.role.refresh_from_db()
        self.assertFalse(self.role.is_active)

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(DEACTIVATE_URL.format("ROLE-9999"))
        self.assertEqual(response.status_code, 404)


# ── POST /roles/<code>/set-default/ ──────────────────────────────────────────


class RoleSetDefaultAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.role = make_role("Developer")

    def test_unauthenticated_returns_401(self):
        response = self.client.post(SET_DEFAULT_URL.format(self.role.code))
        self.assertEqual(response.status_code, 401)

    def test_sets_role_as_default(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(SET_DEFAULT_URL.format(self.role.code))
        self.assertEqual(response.status_code, 200)
        self.role.refresh_from_db()
        self.assertTrue(self.role.is_default)

    def test_clears_previous_default(self):
        old = make_role("Analyst", is_default=True)
        self.client.force_authenticate(user=self.user)
        self.client.post(SET_DEFAULT_URL.format(self.role.code))
        old.refresh_from_db()
        self.assertFalse(old.is_default)

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(SET_DEFAULT_URL.format("ROLE-9999"))
        self.assertEqual(response.status_code, 404)


# ── GET /roles/import/specs/ ─────────────────────────────────────────────────


class RoleImportSpecsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(IMPORT_SPECS_URL)
        self.assertEqual(response.status_code, 401)

    def test_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(IMPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)

    def test_response_includes_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(IMPORT_SPECS_URL)
        self.assertIn("fields", response.data["data"])


# ── GET /roles/export/specs/ ─────────────────────────────────────────────────


class RoleExportSpecsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 401)

    def test_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)

    def test_response_includes_columns(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(EXPORT_SPECS_URL)
        self.assertIn("columns", response.data["data"])
