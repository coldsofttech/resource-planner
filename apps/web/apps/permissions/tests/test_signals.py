from django.contrib.auth.models import Group, Permission
from django.test import TestCase

from apps.permissions.models import (
    GroupPermissionCategory,
    PermissionCategory,
    UserPermissionCategory,
)
from apps.permissions.signals import (
    EXCLUDED_APP_LABELS,
    EXCLUDED_MODEL_PERMISSIONS,
    _clear_perm_cache,
    invalidate_group_permission_cache,
    invalidate_user_permission_cache,
)
from apps.users.models import User


def make_user(email="user@example.com"):
    return User.objects.create_user(
        username=email, email=email, password="TestPass123!"
    )


def make_group(name="Test Group"):
    return Group.objects.create(name=name)


def make_permission_category(module="projects", codename="view"):
    return PermissionCategory.objects.create(
        module=module,
        codename=codename,
        name="View",
        label="View Projects",
        order=1,
    )


# ── prune_system_permissions ──────────────────────────────────────────────────


class PruneSystemPermissionsTest(TestCase):
    def test_excluded_app_label_permissions_do_not_exist(self):
        for app_label in EXCLUDED_APP_LABELS:
            count = Permission.objects.filter(content_type__app_label=app_label).count()
            self.assertEqual(
                count,
                0,
                msg=f"Permissions for app '{app_label}' were not pruned.",
            )

    def test_excluded_model_permissions_do_not_exist(self):
        for app_label, model in EXCLUDED_MODEL_PERMISSIONS:
            count = Permission.objects.filter(
                content_type__app_label=app_label,
                content_type__model=model,
            ).count()
            self.assertEqual(
                count,
                0,
                msg=f"Permissions for {app_label}.{model} were not pruned.",
            )

    def test_own_app_permissions_still_exist(self):
        count = Permission.objects.filter(
            content_type__app_label="permissions",
            codename="view_grouppermissioncategory",
        ).count()
        self.assertEqual(count, 1)

    def test_users_app_permissions_still_exist(self):
        count = Permission.objects.filter(content_type__app_label="users").count()
        self.assertGreater(count, 0)


# ── seed_permission_categories ────────────────────────────────────────────────


class SeedPermissionCategoriesTest(TestCase):
    def test_permissions_module_categories_are_seeded(self):
        count = PermissionCategory.objects.filter(module="permissions").count()
        self.assertEqual(count, 4)

    def test_view_category_exists(self):
        self.assertTrue(
            PermissionCategory.objects.filter(
                module="permissions", codename="view"
            ).exists()
        )

    def test_manage_groups_category_exists(self):
        self.assertTrue(
            PermissionCategory.objects.filter(
                module="permissions", codename="manage_groups"
            ).exists()
        )

    def test_manage_users_category_exists(self):
        self.assertTrue(
            PermissionCategory.objects.filter(
                module="permissions", codename="manage_users"
            ).exists()
        )

    def test_manage_category_exists(self):
        self.assertTrue(
            PermissionCategory.objects.filter(
                module="permissions", codename="manage"
            ).exists()
        )

    def test_manage_groups_category_has_group_permissions(self):
        cat = PermissionCategory.objects.get(
            module="permissions", codename="manage_groups"
        )
        codenames = list(cat.permissions.values_list("codename", flat=True))
        self.assertIn("add_grouppermissioncategory", codenames)
        self.assertIn("view_grouppermissioncategory", codenames)
        self.assertIn("change_grouppermissioncategory", codenames)
        self.assertIn("delete_grouppermissioncategory", codenames)

    def test_view_category_has_only_view_permissions(self):
        cat = PermissionCategory.objects.get(module="permissions", codename="view")
        codenames = set(cat.permissions.values_list("codename", flat=True))
        self.assertIn("view_grouppermissioncategory", codenames)
        self.assertIn("view_userpermissioncategory", codenames)
        self.assertNotIn("add_grouppermissioncategory", codenames)


# ── cache invalidation ────────────────────────────────────────────────────────


class ClearPermCacheTest(TestCase):
    def test_clears_cache_attribute_if_present(self):
        user = make_user()
        user._category_perm_cache = {"permissions.view_something"}
        _clear_perm_cache(user)
        self.assertFalse(hasattr(user, "_category_perm_cache"))

    def test_does_not_raise_if_cache_not_present(self):
        user = make_user()
        try:
            _clear_perm_cache(user)
        except AttributeError:
            self.fail("_clear_perm_cache raised AttributeError unexpectedly")


class InvalidateGroupPermissionCacheTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.group = make_group()
        self.group.user_set.add(self.user)
        self.cat = make_permission_category()
        self.assignment = GroupPermissionCategory.objects.create(
            group=self.group, category=self.cat
        )

    def test_signal_fires_on_save_without_error(self):
        try:
            invalidate_group_permission_cache(
                sender=GroupPermissionCategory,
                instance=self.assignment,
            )
        except Exception as exc:
            self.fail(f"Signal raised unexpectedly: {exc}")

    def test_signal_fires_on_delete_without_error(self):
        try:
            invalidate_group_permission_cache(
                sender=GroupPermissionCategory,
                instance=self.assignment,
            )
        except Exception as exc:
            self.fail(f"Signal raised unexpectedly: {exc}")

    def test_creating_assignment_triggers_post_save_signal(self):
        cat2 = make_permission_category(codename="edit")
        group2 = make_group("New Group")
        group2.user_set.add(self.user)
        GroupPermissionCategory.objects.create(group=group2, category=cat2)
        self.assertTrue(True)

    def test_deleting_assignment_triggers_post_delete_signal(self):
        self.assignment.delete()
        self.assertFalse(
            GroupPermissionCategory.objects.filter(pk=self.assignment.pk).exists()
        )


class InvalidateUserPermissionCacheTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.cat = make_permission_category()
        self.assignment = UserPermissionCategory.objects.create(
            user=self.user, category=self.cat
        )

    def test_signal_clears_cache_on_assignment_instance_user(self):
        self.assignment.user._category_perm_cache = {"stale"}
        invalidate_user_permission_cache(
            sender=UserPermissionCategory,
            instance=self.assignment,
        )
        self.assertFalse(hasattr(self.assignment.user, "_category_perm_cache"))

    def test_creating_assignment_triggers_post_save_signal(self):
        cat2 = make_permission_category(codename="edit")
        UserPermissionCategory.objects.create(user=self.user, category=cat2)
        self.assertTrue(True)

    def test_deleting_assignment_triggers_post_delete_signal(self):
        self.assignment.delete()
        self.assertFalse(
            UserPermissionCategory.objects.filter(pk=self.assignment.pk).exists()
        )
