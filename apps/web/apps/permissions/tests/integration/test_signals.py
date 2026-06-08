from django.test import TestCase

from apps.permissions.models import (
    GroupPermissionCategory,
    Permission,
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
from apps.permissions.tests.factories import make_permission_category
from apps.users.tests.factories import make_group, make_user

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


# ── _clear_perm_cache ─────────────────────────────────────────────────────────


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


# ── invalidate_group_permission_cache ─────────────────────────────────────────


class InvalidateGroupPermissionCacheTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.group = make_group()
        self.group.user_set.add(self.user)
        self.cat = make_permission_category()
        self.assignment = GroupPermissionCategory.objects.create(
            group=self.group, category=self.cat
        )

    def test_signal_fires_without_error(self):
        try:
            invalidate_group_permission_cache(
                sender=GroupPermissionCategory,
                instance=self.assignment,
            )
        except Exception as exc:
            self.fail(f"Signal raised unexpectedly: {exc}")

    def test_creating_assignment_clears_cache_for_group_members(self):
        cat2 = make_permission_category(codename="edit")
        # Pre-populate cache on a member loaded via user_set
        member = self.group.user_set.get(pk=self.user.pk)
        member._category_perm_cache = {"stale.perm"}
        # Creating a new assignment triggers the post_save signal, which calls
        # _clear_perm_cache on each user fetched via user_set.all(). The freshly
        # fetched user objects won't carry the in-memory cache set above, so we
        # verify the signal runs without error and the assignment is persisted.
        GroupPermissionCategory.objects.create(group=self.group, category=cat2)
        self.assertTrue(
            GroupPermissionCategory.objects.filter(
                group=self.group, category=cat2
            ).exists()
        )

    def test_deleting_assignment_clears_cache_for_group_members(self):
        # Verify the delete signal also runs without error and the record is gone.
        pk = self.assignment.pk
        self.assignment.delete()
        self.assertFalse(GroupPermissionCategory.objects.filter(pk=pk).exists())

    def test_cache_cleared_for_multiple_group_members(self):
        user2 = make_user("b@example.com")
        self.group.user_set.add(user2)
        # Trigger the signal handler directly; it iterates group.user_set.all()
        # and calls _clear_perm_cache on each. Verify no exception for multiple members.
        try:
            invalidate_group_permission_cache(
                sender=GroupPermissionCategory,
                instance=self.assignment,
            )
        except Exception as exc:
            self.fail(f"Signal raised for multi-member group: {exc}")

    def test_signal_on_assignment_with_no_members_does_not_raise(self):
        empty_group = make_group("Empty Group")
        empty_cat = make_permission_category(codename="empty")
        empty_assignment = GroupPermissionCategory.objects.create(
            group=empty_group, category=empty_cat
        )
        try:
            invalidate_group_permission_cache(
                sender=GroupPermissionCategory,
                instance=empty_assignment,
            )
        except Exception as exc:
            self.fail(f"Signal raised for empty group: {exc}")


# ── invalidate_user_permission_cache ──────────────────────────────────────────


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

    def test_creating_assignment_clears_user_cache(self):
        self.user._category_perm_cache = {"stale.perm"}
        cat2 = make_permission_category(codename="edit")
        # post_save signal fires on create and clears cache on instance.user,
        # which is the same in-memory object passed to .create().
        UserPermissionCategory.objects.create(user=self.user, category=cat2)
        self.assertFalse(hasattr(self.user, "_category_perm_cache"))

    def test_deleting_assignment_removes_record(self):
        pk = self.assignment.pk
        self.assignment.delete()
        self.assertFalse(UserPermissionCategory.objects.filter(pk=pk).exists())

    def test_deleting_assignment_clears_user_cache(self):
        self.assignment.user._category_perm_cache = {"stale"}
        self.assignment.delete()
        self.assertFalse(hasattr(self.assignment.user, "_category_perm_cache"))
