from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.models import Configuration
from apps.permissions.constants import PermissionScope
from apps.permissions.models import (
    GroupPermissionCategory,
    PermissionCategory,
    UserPermissionCategory,
)
from apps.users.models import Group, GroupProfile, User, UserProfile


def mark_setup_complete():
    Configuration.objects.update_or_create(
        config_code="SETUP_COMPLETE",
        defaults={"value": "true", "label": "Setup Complete"},
    )


CATEGORIES_LIST_URL = "/api/v1/permissions/categories/"
CATEGORIES_DETAIL_URL = "/api/v1/permissions/categories/{}/"
GROUPS_LIST_URL = "/api/v1/permissions/groups/{}/"
GROUPS_DETAIL_URL = "/api/v1/permissions/groups/{}/{}/"
USERS_LIST_URL = "/api/v1/permissions/users/{}/"
USERS_DETAIL_URL = "/api/v1/permissions/users/{}/{}/"
USERS_EFFECTIVE_URL = "/api/v1/permissions/users/{}/effective/"


def make_user(email="user@example.com", is_superuser=False):
    if is_superuser:
        return User.objects.create_superuser(
            username=email, email=email, password="TestPass123!"
        )
    return User.objects.create_user(
        username=email, email=email, password="TestPass123!"
    )


def make_user_with_profile(email="user@example.com"):
    user = make_user(email)
    profile = UserProfile.objects.create(user=user)
    return user, profile


def make_group_with_profile(name="Test Group"):
    group = Group.objects.create(name=name)
    profile = GroupProfile.objects.create(group=group)
    return group, profile


def make_permission_category(module="projects", codename="view", name="View", order=1):
    return PermissionCategory.objects.create(
        module=module,
        codename=codename,
        name=name,
        label=f"{name} {module.title()}",
        order=order,
    )


def get_seeded_category(codename):
    return PermissionCategory.objects.get(module="permissions", codename=codename)


def assign_manage_groups_to(user):
    cat = get_seeded_category("manage_groups")
    return UserPermissionCategory.objects.create(
        user=user, category=cat, scope=PermissionScope.ALL
    )


def assign_manage_users_to(user):
    cat = get_seeded_category("manage_users")
    return UserPermissionCategory.objects.create(
        user=user, category=cat, scope=PermissionScope.ALL
    )


# ── GET /permissions/categories/ ─────────────────────────────────────────────


class PermissionCategoryListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user()

    def test_unauthenticated_request_returns_401(self):
        response = self.client.get(CATEGORIES_LIST_URL)
        self.assertEqual(response.status_code, 401)

    def test_authenticated_request_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(CATEGORIES_LIST_URL)
        self.assertEqual(response.status_code, 200)

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(CATEGORIES_LIST_URL)
        self.assertTrue(response.data["success"])

    def test_response_contains_results_and_pagination(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(CATEGORIES_LIST_URL)
        self.assertIn("results", response.data["data"])
        self.assertIn("pagination", response.data["data"])

    def test_seeded_categories_appear_in_results(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(CATEGORIES_LIST_URL)
        codenames = [r["codename"] for r in response.data["data"]["results"]]
        self.assertIn("view", codenames)

    def test_module_filter_narrows_results(self):
        self.client.force_authenticate(user=self.user)
        make_permission_category(module="projects", codename="view")
        response = self.client.get(CATEGORIES_LIST_URL, {"module": "projects"})
        results = response.data["data"]["results"]
        self.assertTrue(all(r["module"] == "projects" for r in results))


# ── GET /permissions/categories/<code>/ ───────────────────────────────────────


class PermissionCategoryDetailAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user()
        self.cat = make_permission_category()

    def test_unauthenticated_returns_401(self):
        response = self.client.get(CATEGORIES_DETAIL_URL.format(self.cat.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_200_for_valid_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(CATEGORIES_DETAIL_URL.format(self.cat.code))
        self.assertEqual(response.status_code, 200)

    def test_response_includes_permissions_list(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(CATEGORIES_DETAIL_URL.format(self.cat.code))
        self.assertIn("permissions", response.data["data"])

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(CATEGORIES_DETAIL_URL.format("PERM-9999"))
        self.assertEqual(response.status_code, 404)


# ── GET /permissions/groups/<group_code>/ ─────────────────────────────────────


class GroupPermissionsListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user()
        self.group, self.gprofile = make_group_with_profile()

    def test_unauthenticated_returns_401(self):
        response = self.client.get(GROUPS_LIST_URL.format(self.gprofile.code))
        self.assertEqual(response.status_code, 401)

    def test_user_without_permission_returns_403(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GROUPS_LIST_URL.format(self.gprofile.code))
        self.assertEqual(response.status_code, 403)

    def test_user_with_permission_returns_200(self):
        assign_manage_groups_to(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GROUPS_LIST_URL.format(self.gprofile.code))
        self.assertEqual(response.status_code, 200)

    def test_superuser_returns_200_without_explicit_permission(self):
        superuser = make_user("admin@example.com", is_superuser=True)
        self.client.force_authenticate(user=superuser)
        response = self.client.get(GROUPS_LIST_URL.format(self.gprofile.code))
        self.assertEqual(response.status_code, 200)

    def test_returns_404_for_unknown_group(self):
        assign_manage_groups_to(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GROUPS_LIST_URL.format("USRGRP-9999"))
        self.assertEqual(response.status_code, 404)


# ── POST /permissions/groups/<group_code>/ ────────────────────────────────────


class GroupPermissionsAssignAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user()
        self.group, self.gprofile = make_group_with_profile()
        self.cat = make_permission_category()

    def test_unauthenticated_returns_401(self):
        response = self.client.post(
            GROUPS_LIST_URL.format(self.gprofile.code),
            {"category_code": self.cat.code, "scope": PermissionScope.ALL},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_user_without_permission_returns_403(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            GROUPS_LIST_URL.format(self.gprofile.code),
            {"category_code": self.cat.code, "scope": PermissionScope.ALL},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_assign_creates_assignment_and_returns_201(self):
        assign_manage_groups_to(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            GROUPS_LIST_URL.format(self.gprofile.code),
            {"category_code": self.cat.code, "scope": PermissionScope.ALL},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["success"])

    def test_response_includes_assignment_code(self):
        assign_manage_groups_to(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            GROUPS_LIST_URL.format(self.gprofile.code),
            {"category_code": self.cat.code, "scope": PermissionScope.TEAM},
            format="json",
        )
        self.assertIn("code", response.data["data"])
        self.assertTrue(response.data["data"]["code"].startswith("GRPPERM-"))

    def test_duplicate_assignment_returns_409(self):
        assign_manage_groups_to(self.user)
        self.client.force_authenticate(user=self.user)
        payload = {"category_code": self.cat.code, "scope": PermissionScope.ALL}
        self.client.post(
            GROUPS_LIST_URL.format(self.gprofile.code), payload, format="json"
        )
        response = self.client.post(
            GROUPS_LIST_URL.format(self.gprofile.code), payload, format="json"
        )
        self.assertEqual(response.status_code, 409)

    def test_invalid_scope_returns_400(self):
        assign_manage_groups_to(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            GROUPS_LIST_URL.format(self.gprofile.code),
            {"category_code": self.cat.code, "scope": 99},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_unknown_category_returns_404(self):
        assign_manage_groups_to(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            GROUPS_LIST_URL.format(self.gprofile.code),
            {"category_code": "PERM-9999", "scope": PermissionScope.ALL},
            format="json",
        )
        self.assertEqual(response.status_code, 404)


# ── PATCH /permissions/groups/<group_code>/<code>/ ────────────────────────────


class GroupPermissionsUpdateScopeAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user()
        self.group, self.gprofile = make_group_with_profile()
        self.cat = make_permission_category()
        self.assignment = GroupPermissionCategory.objects.create(
            group=self.group, category=self.cat, scope=PermissionScope.SELF
        )

    def test_unauthenticated_returns_401(self):
        url = GROUPS_DETAIL_URL.format(self.gprofile.code, self.assignment.code)
        response = self.client.patch(url, {"scope": PermissionScope.ALL}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_user_without_permission_returns_403(self):
        self.client.force_authenticate(user=self.user)
        url = GROUPS_DETAIL_URL.format(self.gprofile.code, self.assignment.code)
        response = self.client.patch(url, {"scope": PermissionScope.ALL}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_updates_scope_and_returns_200(self):
        assign_manage_groups_to(self.user)
        self.client.force_authenticate(user=self.user)
        url = GROUPS_DETAIL_URL.format(self.gprofile.code, self.assignment.code)
        response = self.client.patch(url, {"scope": PermissionScope.ALL}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["scope"], PermissionScope.ALL)

    def test_wrong_group_returns_404(self):
        assign_manage_groups_to(self.user)
        self.client.force_authenticate(user=self.user)
        _, other_profile = make_group_with_profile("Other Group")
        url = GROUPS_DETAIL_URL.format(other_profile.code, self.assignment.code)
        response = self.client.patch(url, {"scope": PermissionScope.ALL}, format="json")
        self.assertEqual(response.status_code, 404)


# ── DELETE /permissions/groups/<group_code>/<code>/ ───────────────────────────


class GroupPermissionsRemoveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user()
        self.group, self.gprofile = make_group_with_profile()
        self.cat = make_permission_category()
        self.assignment = GroupPermissionCategory.objects.create(
            group=self.group, category=self.cat
        )

    def test_unauthenticated_returns_401(self):
        url = GROUPS_DETAIL_URL.format(self.gprofile.code, self.assignment.code)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 401)

    def test_user_without_permission_returns_403(self):
        self.client.force_authenticate(user=self.user)
        url = GROUPS_DETAIL_URL.format(self.gprofile.code, self.assignment.code)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 403)

    def test_removes_assignment_and_returns_204(self):
        assign_manage_groups_to(self.user)
        self.client.force_authenticate(user=self.user)
        url = GROUPS_DETAIL_URL.format(self.gprofile.code, self.assignment.code)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            GroupPermissionCategory.objects.filter(pk=self.assignment.pk).exists()
        )


# ── GET /permissions/users/<user_code>/ ───────────────────────────────────────


class UserPermissionsListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user()
        self.target_user, self.uprofile = make_user_with_profile("target@example.com")

    def test_unauthenticated_returns_401(self):
        response = self.client.get(USERS_LIST_URL.format(self.uprofile.code))
        self.assertEqual(response.status_code, 401)

    def test_user_without_permission_returns_403(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(USERS_LIST_URL.format(self.uprofile.code))
        self.assertEqual(response.status_code, 403)

    def test_user_with_permission_returns_200(self):
        assign_manage_users_to(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(USERS_LIST_URL.format(self.uprofile.code))
        self.assertEqual(response.status_code, 200)

    def test_returns_404_for_unknown_user(self):
        assign_manage_users_to(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(USERS_LIST_URL.format("USER-9999"))
        self.assertEqual(response.status_code, 404)


# ── POST /permissions/users/<user_code>/ ──────────────────────────────────────


class UserPermissionsAssignAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user()
        self.target_user, self.uprofile = make_user_with_profile("target@example.com")
        self.cat = make_permission_category()

    def test_unauthenticated_returns_401(self):
        response = self.client.post(
            USERS_LIST_URL.format(self.uprofile.code),
            {"category_code": self.cat.code, "scope": PermissionScope.ALL},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_user_without_permission_returns_403(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            USERS_LIST_URL.format(self.uprofile.code),
            {"category_code": self.cat.code, "scope": PermissionScope.ALL},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_assign_creates_assignment_and_returns_201(self):
        assign_manage_users_to(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            USERS_LIST_URL.format(self.uprofile.code),
            {"category_code": self.cat.code, "scope": PermissionScope.SELF},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.data["data"]["code"].startswith("USRPERM-"))

    def test_duplicate_assignment_returns_409(self):
        assign_manage_users_to(self.user)
        self.client.force_authenticate(user=self.user)
        payload = {"category_code": self.cat.code, "scope": PermissionScope.ALL}
        self.client.post(
            USERS_LIST_URL.format(self.uprofile.code), payload, format="json"
        )
        response = self.client.post(
            USERS_LIST_URL.format(self.uprofile.code), payload, format="json"
        )
        self.assertEqual(response.status_code, 409)


# ── PATCH /permissions/users/<user_code>/<code>/ ──────────────────────────────


class UserPermissionsUpdateScopeAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user()
        self.target_user, self.uprofile = make_user_with_profile("target@example.com")
        self.cat = make_permission_category()
        self.assignment = UserPermissionCategory.objects.create(
            user=self.target_user, category=self.cat, scope=PermissionScope.SELF
        )

    def test_unauthenticated_returns_401(self):
        url = USERS_DETAIL_URL.format(self.uprofile.code, self.assignment.code)
        response = self.client.patch(url, {"scope": PermissionScope.ALL}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_user_without_permission_returns_403(self):
        self.client.force_authenticate(user=self.user)
        url = USERS_DETAIL_URL.format(self.uprofile.code, self.assignment.code)
        response = self.client.patch(url, {"scope": PermissionScope.ALL}, format="json")
        self.assertEqual(response.status_code, 403)

    def test_updates_scope_and_returns_200(self):
        assign_manage_users_to(self.user)
        self.client.force_authenticate(user=self.user)
        url = USERS_DETAIL_URL.format(self.uprofile.code, self.assignment.code)
        response = self.client.patch(url, {"scope": PermissionScope.ALL}, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["scope"], PermissionScope.ALL)


# ── DELETE /permissions/users/<user_code>/<code>/ ─────────────────────────────


class UserPermissionsRemoveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user()
        self.target_user, self.uprofile = make_user_with_profile("target@example.com")
        self.cat = make_permission_category()
        self.assignment = UserPermissionCategory.objects.create(
            user=self.target_user, category=self.cat
        )

    def test_unauthenticated_returns_401(self):
        url = USERS_DETAIL_URL.format(self.uprofile.code, self.assignment.code)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 401)

    def test_removes_assignment_and_returns_204(self):
        assign_manage_users_to(self.user)
        self.client.force_authenticate(user=self.user)
        url = USERS_DETAIL_URL.format(self.uprofile.code, self.assignment.code)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            UserPermissionCategory.objects.filter(pk=self.assignment.pk).exists()
        )


# ── GET /permissions/users/<user_code>/effective/ ─────────────────────────────


class UserPermissionsEffectiveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user()
        self.target_user, self.uprofile = make_user_with_profile("target@example.com")

    def test_unauthenticated_returns_401(self):
        response = self.client.get(USERS_EFFECTIVE_URL.format(self.uprofile.code))
        self.assertEqual(response.status_code, 401)

    def test_user_without_permission_returns_403(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(USERS_EFFECTIVE_URL.format(self.uprofile.code))
        self.assertEqual(response.status_code, 403)

    def test_returns_200_with_empty_list_when_no_assignments(self):
        assign_manage_users_to(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(USERS_EFFECTIVE_URL.format(self.uprofile.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"], [])

    def test_returns_merged_assignments_with_via_field(self):
        assign_manage_users_to(self.user)
        self.client.force_authenticate(user=self.user)
        cat = make_permission_category(module="projects", codename="view")
        UserPermissionCategory.objects.create(
            user=self.target_user, category=cat, scope=PermissionScope.SELF
        )
        response = self.client.get(USERS_EFFECTIVE_URL.format(self.uprofile.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 1)
        result = response.data["data"][0]
        self.assertIn("via", result)
        self.assertIn("scope", result)
        self.assertIn("scope_display", result)
        self.assertIn("category", result)

    def test_returns_404_for_unknown_user(self):
        assign_manage_users_to(self.user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(USERS_EFFECTIVE_URL.format("USER-9999"))
        self.assertEqual(response.status_code, 404)
