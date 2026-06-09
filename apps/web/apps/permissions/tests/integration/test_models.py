from django.db import IntegrityError
from django.test import TestCase

from apps.permissions.constants import PermissionScope
from apps.permissions.models import (
    GroupPermissionCategory,
    PermissionCategory,
    UserPermissionCategory,
)
from apps.permissions.tests.factories import make_permission_category
from apps.users.tests.factories import make_group, make_user

# ── PermissionCategory ────────────────────────────────────────────────────────


class PermissionCategoryCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        cat = make_permission_category()
        self.assertTrue(cat.code.startswith("PERM-"))

    def test_code_contains_pk(self):
        cat = make_permission_category()
        self.assertEqual(cat.code, f"PERM-{cat.pk}")

    def test_code_is_unique_across_categories(self):
        cat1 = make_permission_category(module="projects", codename="view")
        cat2 = make_permission_category(module="sprints", codename="view")
        self.assertNotEqual(cat1.code, cat2.code)


class PermissionCategoryFieldsTest(TestCase):
    def test_order_defaults_to_zero(self):
        cat = PermissionCategory.objects.create(
            module="projects", codename="view", name="View", label="View Projects"
        )
        self.assertEqual(cat.order, 0)

    def test_permissions_m2m_empty_by_default(self):
        cat = make_permission_category()
        self.assertEqual(cat.permissions.count(), 0)

    def test_str_returns_label(self):
        cat = make_permission_category(name="View", module="projects")
        self.assertEqual(str(cat), cat.label)


class PermissionCategoryConstraintTest(TestCase):
    def test_duplicate_module_and_codename_raises_integrity_error(self):
        make_permission_category(module="projects", codename="view")
        with self.assertRaises(IntegrityError):
            make_permission_category(module="projects", codename="view")

    def test_same_codename_different_module_is_allowed(self):
        make_permission_category(module="projects", codename="view")
        cat = make_permission_category(module="sprints", codename="view")
        self.assertIsNotNone(cat.pk)

    def test_different_codename_same_module_is_allowed(self):
        make_permission_category(module="projects", codename="view")
        cat = make_permission_category(module="projects", codename="edit")
        self.assertIsNotNone(cat.pk)


class PermissionCategoryOrderingTest(TestCase):
    def test_ordered_by_module_then_order(self):
        make_permission_category(module="sprints", codename="view", order=1)
        make_permission_category(module="projects", codename="view", order=1)
        make_permission_category(module="projects", codename="edit", order=2)
        codes = list(
            PermissionCategory.objects.filter(
                module__in=["projects", "sprints"]
            ).values_list("module", "order")
        )
        self.assertEqual(codes[0][0], "projects")
        self.assertEqual(codes[2][0], "sprints")


# ── GroupPermissionCategory ───────────────────────────────────────────────────


class GroupPermissionCategoryCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        group = make_group()
        cat = make_permission_category()
        assignment = GroupPermissionCategory.objects.create(group=group, category=cat)
        self.assertTrue(assignment.code.startswith("GRPPERM-"))

    def test_code_contains_pk(self):
        group = make_group()
        cat = make_permission_category()
        assignment = GroupPermissionCategory.objects.create(group=group, category=cat)
        self.assertEqual(assignment.code, f"GRPPERM-{assignment.pk}")


class GroupPermissionCategoryDefaultsTest(TestCase):
    def test_scope_defaults_to_self(self):
        group = make_group()
        cat = make_permission_category()
        assignment = GroupPermissionCategory.objects.create(group=group, category=cat)
        self.assertEqual(assignment.scope, PermissionScope.SELF)

    def test_granted_at_set_automatically(self):
        group = make_group()
        cat = make_permission_category()
        assignment = GroupPermissionCategory.objects.create(group=group, category=cat)
        self.assertIsNotNone(assignment.granted_at)


class GroupPermissionCategoryConstraintTest(TestCase):
    def test_duplicate_group_and_category_raises_integrity_error(self):
        group = make_group()
        cat = make_permission_category()
        GroupPermissionCategory.objects.create(group=group, category=cat)
        with self.assertRaises(IntegrityError):
            GroupPermissionCategory.objects.create(group=group, category=cat)

    def test_same_category_different_groups_is_allowed(self):
        group_a = make_group("Group A")
        group_b = make_group("Group B")
        cat = make_permission_category()
        GroupPermissionCategory.objects.create(group=group_a, category=cat)
        assignment = GroupPermissionCategory.objects.create(group=group_b, category=cat)
        self.assertIsNotNone(assignment.pk)

    def test_same_group_different_categories_is_allowed(self):
        group = make_group()
        cat_a = make_permission_category(codename="view")
        cat_b = make_permission_category(codename="edit")
        GroupPermissionCategory.objects.create(group=group, category=cat_a)
        assignment = GroupPermissionCategory.objects.create(group=group, category=cat_b)
        self.assertIsNotNone(assignment.pk)


# ── UserPermissionCategory ────────────────────────────────────────────────────


class UserPermissionCategoryCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        user = make_user()
        cat = make_permission_category()
        assignment = UserPermissionCategory.objects.create(user=user, category=cat)
        self.assertTrue(assignment.code.startswith("USRPERM-"))

    def test_code_contains_pk(self):
        user = make_user()
        cat = make_permission_category()
        assignment = UserPermissionCategory.objects.create(user=user, category=cat)
        self.assertEqual(assignment.code, f"USRPERM-{assignment.pk}")


class UserPermissionCategoryDefaultsTest(TestCase):
    def test_scope_defaults_to_self(self):
        user = make_user()
        cat = make_permission_category()
        assignment = UserPermissionCategory.objects.create(user=user, category=cat)
        self.assertEqual(assignment.scope, PermissionScope.SELF)

    def test_granted_at_set_automatically(self):
        user = make_user()
        cat = make_permission_category()
        assignment = UserPermissionCategory.objects.create(user=user, category=cat)
        self.assertIsNotNone(assignment.granted_at)


class UserPermissionCategoryConstraintTest(TestCase):
    def test_duplicate_user_and_category_raises_integrity_error(self):
        user = make_user()
        cat = make_permission_category()
        UserPermissionCategory.objects.create(user=user, category=cat)
        with self.assertRaises(IntegrityError):
            UserPermissionCategory.objects.create(user=user, category=cat)

    def test_same_category_different_users_is_allowed(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        cat = make_permission_category()
        UserPermissionCategory.objects.create(user=user_a, category=cat)
        assignment = UserPermissionCategory.objects.create(user=user_b, category=cat)
        self.assertIsNotNone(assignment.pk)

    def test_same_user_different_categories_is_allowed(self):
        user = make_user()
        cat_a = make_permission_category(codename="view")
        cat_b = make_permission_category(codename="edit")
        UserPermissionCategory.objects.create(user=user, category=cat_a)
        assignment = UserPermissionCategory.objects.create(user=user, category=cat_b)
        self.assertIsNotNone(assignment.pk)
