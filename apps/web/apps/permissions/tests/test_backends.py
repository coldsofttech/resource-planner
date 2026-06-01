from unittest.mock import MagicMock

from django.contrib.auth.models import Group, Permission
from django.test import TestCase

from apps.permissions.backends import PermissionCategoryBackend
from apps.permissions.constants import PermissionScope
from apps.permissions.models import (
    GroupPermissionCategory,
    PermissionCategory,
    UserPermissionCategory,
)
from apps.users.models import User


def make_user(email="user@example.com", is_active=True, is_superuser=False):
    if is_superuser:
        return User.objects.create_superuser(
            username=email, email=email, password="TestPass123!"
        )
    return User.objects.create_user(
        username=email, email=email, password="TestPass123!", is_active=is_active
    )


def make_group(name="Test Group"):
    return Group.objects.create(name=name)


def make_permission_category(module="permissions", codename="test_cat", order=1):
    return PermissionCategory.objects.create(
        module=module,
        codename=codename,
        name="Test",
        label="Test Category",
        order=order,
    )


def get_real_permission(codename="view_grouppermissioncategory"):
    return Permission.objects.get(
        content_type__app_label="permissions",
        codename=codename,
    )


# ── authenticate ──────────────────────────────────────────────────────────────


class PermissionCategoryBackendAuthenticateTest(TestCase):
    def test_authenticate_always_returns_none(self):
        backend = PermissionCategoryBackend()
        result = backend.authenticate(request=None, username="any", password="any")
        self.assertIsNone(result)


# ── has_perm — model-level ────────────────────────────────────────────────────


class PermissionCategoryBackendHasPermTest(TestCase):
    def setUp(self):
        self.backend = PermissionCategoryBackend()
        self.user = make_user()
        self.perm = get_real_permission()
        self.cat = make_permission_category()
        self.cat.permissions.set([self.perm])

    def test_inactive_user_is_denied(self):
        inactive = make_user("inactive@example.com", is_active=False)
        self.assertFalse(
            self.backend.has_perm(inactive, "permissions.view_grouppermissioncategory")
        )

    def test_superuser_is_granted_without_assignment(self):
        superuser = make_user("admin@example.com", is_superuser=True)
        self.assertTrue(
            self.backend.has_perm(superuser, "permissions.view_grouppermissioncategory")
        )

    def test_user_with_direct_assignment_has_perm(self):
        UserPermissionCategory.objects.create(
            user=self.user, category=self.cat, scope=PermissionScope.ALL
        )
        self.assertTrue(
            self.backend.has_perm(self.user, "permissions.view_grouppermissioncategory")
        )

    def test_user_with_group_assignment_has_perm(self):
        group = make_group()
        group.user_set.add(self.user)
        GroupPermissionCategory.objects.create(
            group=group, category=self.cat, scope=PermissionScope.ALL
        )
        self.assertTrue(
            self.backend.has_perm(self.user, "permissions.view_grouppermissioncategory")
        )

    def test_user_without_assignment_is_denied(self):
        self.assertFalse(
            self.backend.has_perm(self.user, "permissions.view_grouppermissioncategory")
        )

    def test_user_denied_for_unassigned_permission(self):
        UserPermissionCategory.objects.create(
            user=self.user, category=self.cat, scope=PermissionScope.ALL
        )
        self.assertFalse(
            self.backend.has_perm(self.user, "permissions.add_grouppermissioncategory")
        )


# ── has_perm — object-level ───────────────────────────────────────────────────


class PermissionCategoryBackendObjectScopeTest(TestCase):
    def setUp(self):
        self.backend = PermissionCategoryBackend()
        self.user = make_user()
        self.perm = get_real_permission()
        self.cat = make_permission_category()
        self.cat.permissions.set([self.perm])

    def test_all_scope_grants_access_to_any_object(self):
        UserPermissionCategory.objects.create(
            user=self.user, category=self.cat, scope=PermissionScope.ALL
        )
        obj = MagicMock()
        self.assertTrue(
            self.backend.has_perm(
                self.user, "permissions.view_grouppermissioncategory", obj
            )
        )

    def test_self_scope_grants_access_to_owned_object(self):
        UserPermissionCategory.objects.create(
            user=self.user, category=self.cat, scope=PermissionScope.SELF
        )
        obj = MagicMock()
        obj.created_by_id = self.user.pk
        self.assertTrue(
            self.backend.has_perm(
                self.user, "permissions.view_grouppermissioncategory", obj
            )
        )

    def test_self_scope_denies_access_to_unowned_object(self):
        other = make_user("other@example.com")
        UserPermissionCategory.objects.create(
            user=self.user, category=self.cat, scope=PermissionScope.SELF
        )
        obj = MagicMock()
        obj.created_by_id = other.pk
        self.assertFalse(
            self.backend.has_perm(
                self.user, "permissions.view_grouppermissioncategory", obj
            )
        )

    def test_team_scope_grants_access_when_user_in_team(self):
        UserPermissionCategory.objects.create(
            user=self.user, category=self.cat, scope=PermissionScope.TEAM
        )
        team = MagicMock()
        team.members.filter.return_value.exists.return_value = True
        obj = MagicMock()
        obj.team = team
        self.assertTrue(
            self.backend.has_perm(
                self.user, "permissions.view_grouppermissioncategory", obj
            )
        )

    def test_team_scope_denies_access_when_user_not_in_team(self):
        UserPermissionCategory.objects.create(
            user=self.user, category=self.cat, scope=PermissionScope.TEAM
        )
        team = MagicMock()
        team.members.filter.return_value.exists.return_value = False
        obj = MagicMock()
        obj.team = team
        self.assertFalse(
            self.backend.has_perm(
                self.user, "permissions.view_grouppermissioncategory", obj
            )
        )

    def test_denied_when_no_assignment_even_with_object(self):
        obj = MagicMock()
        self.assertFalse(
            self.backend.has_perm(
                self.user, "permissions.view_grouppermissioncategory", obj
            )
        )


# ── get_all_permissions ───────────────────────────────────────────────────────


class PermissionCategoryBackendGetAllPermissionsTest(TestCase):
    def setUp(self):
        self.backend = PermissionCategoryBackend()
        self.user = make_user()
        self.perm = get_real_permission()
        self.cat = make_permission_category()
        self.cat.permissions.set([self.perm])

    def test_returns_empty_set_for_user_with_no_assignments(self):
        result = self.backend.get_all_permissions(self.user)
        self.assertIsInstance(result, set)
        self.assertEqual(len(result), 0)

    def test_returns_permission_string_for_assigned_category(self):
        UserPermissionCategory.objects.create(
            user=self.user, category=self.cat, scope=PermissionScope.ALL
        )
        result = self.backend.get_all_permissions(self.user)
        self.assertIn("permissions.view_grouppermissioncategory", result)

    def test_returns_empty_set_for_inactive_user(self):
        inactive = make_user("inactive@example.com", is_active=False)
        UserPermissionCategory.objects.create(
            user=inactive, category=self.cat, scope=PermissionScope.ALL
        )
        result = self.backend.get_all_permissions(inactive)
        self.assertEqual(result, set())


# ── has_module_perms ──────────────────────────────────────────────────────────


class PermissionCategoryBackendHasModulePermsTest(TestCase):
    def setUp(self):
        self.backend = PermissionCategoryBackend()
        self.user = make_user()
        self.perm = get_real_permission()
        self.cat = make_permission_category()
        self.cat.permissions.set([self.perm])

    def test_returns_true_when_user_has_permission_in_module(self):
        UserPermissionCategory.objects.create(
            user=self.user, category=self.cat, scope=PermissionScope.ALL
        )
        self.assertTrue(self.backend.has_module_perms(self.user, "permissions"))

    def test_returns_false_when_user_has_no_permission_in_module(self):
        self.assertFalse(self.backend.has_module_perms(self.user, "permissions"))

    def test_returns_false_for_inactive_user(self):
        inactive = make_user("inactive@example.com", is_active=False)
        self.assertFalse(self.backend.has_module_perms(inactive, "permissions"))

    def test_returns_true_for_superuser(self):
        superuser = make_user("admin@example.com", is_superuser=True)
        self.assertTrue(self.backend.has_module_perms(superuser, "permissions"))


# ── permission caching ────────────────────────────────────────────────────────


class PermissionCategoryBackendCacheTest(TestCase):
    def setUp(self):
        self.backend = PermissionCategoryBackend()
        self.user = make_user()

    def test_cache_is_set_after_first_permission_check(self):
        self.assertFalse(hasattr(self.user, "_category_perm_cache"))
        self.backend.get_all_permissions(self.user)
        self.assertTrue(hasattr(self.user, "_category_perm_cache"))

    def test_cached_value_is_used_on_subsequent_calls(self):
        self.backend.get_all_permissions(self.user)
        self.user._category_perm_cache = {"injected.perm"}
        result = self.backend.get_all_permissions(self.user)
        self.assertIn("injected.perm", result)

    def test_signal_clears_cache_so_newly_granted_permission_is_visible(self):
        self.backend.get_all_permissions(self.user)
        perm = Permission.objects.get(
            content_type__app_label="permissions",
            codename="view_grouppermissioncategory",
        )
        cat = make_permission_category()
        cat.permissions.set([perm])
        UserPermissionCategory.objects.create(
            user=self.user, category=cat, scope=PermissionScope.ALL
        )
        result = self.backend.get_all_permissions(self.user)
        self.assertIn("permissions.view_grouppermissioncategory", result)
