from django.test import TestCase

from apps.permissions import selectors
from apps.permissions.constants import PermissionScope
from apps.permissions.models import (
    GroupPermissionCategory,
    Permission,
    UserPermissionCategory,
)
from apps.permissions.tests.factories import make_permission_category
from apps.users.tests.factories import (
    make_group,
    make_group_with_profile,
    make_user,
    make_user_with_profile,
)

# ── get_all_categories ────────────────────────────────────────────────────────


class GetAllCategoriesTest(TestCase):
    def test_returns_all_categories(self):
        make_permission_category(module="projects", codename="view")
        make_permission_category(module="sprints", codename="view")
        qs = selectors.get_all_categories()
        codes = list(
            qs.values_list("codename", flat=True).filter(
                module__in=["projects", "sprints"]
            )
        )
        self.assertIn("view", codes)
        self.assertEqual(len(codes), 2)

    def test_filters_by_module(self):
        make_permission_category(module="projects", codename="view")
        make_permission_category(module="sprints", codename="view")
        qs = selectors.get_all_categories(module="projects")
        self.assertTrue(all(c.module == "projects" for c in qs))

    def test_returns_empty_queryset_for_unknown_module(self):
        qs = selectors.get_all_categories(module="nonexistent")
        self.assertEqual(qs.count(), 0)

    def test_no_module_filter_returns_queryset(self):
        qs = selectors.get_all_categories()
        self.assertIsNotNone(qs)


# ── get_category_by_code ──────────────────────────────────────────────────────


class GetCategoryByCodeTest(TestCase):
    def test_returns_category_for_valid_code(self):
        cat = make_permission_category()
        result = selectors.get_category_by_code(cat.code)
        self.assertEqual(result.pk, cat.pk)

    def test_returns_none_for_unknown_code(self):
        result = selectors.get_category_by_code("PERM-9999")
        self.assertIsNone(result)

    def test_result_has_permissions_prefetched(self):
        cat = make_permission_category()
        result = selectors.get_category_by_code(cat.code)
        self.assertIsNotNone(result)
        self.assertEqual(result.permissions.count(), 0)


# ── get_group_by_profile_code ─────────────────────────────────────────────────


class GetGroupByProfileCodeTest(TestCase):
    def test_returns_group_for_valid_profile_code(self):
        group, profile = make_group_with_profile()
        result = selectors.get_group_by_profile_code(profile.code)
        self.assertEqual(result.pk, group.pk)

    def test_returns_none_for_unknown_code(self):
        result = selectors.get_group_by_profile_code("USRGRP-9999")
        self.assertIsNone(result)


# ── get_group_assignment_by_code ──────────────────────────────────────────────


class GetGroupAssignmentByCodeTest(TestCase):
    def test_returns_assignment_for_valid_code(self):
        group = make_group()
        cat = make_permission_category()
        assignment = GroupPermissionCategory.objects.create(group=group, category=cat)
        result = selectors.get_group_assignment_by_code(assignment.code)
        self.assertEqual(result.pk, assignment.pk)

    def test_returns_none_for_unknown_code(self):
        result = selectors.get_group_assignment_by_code("GRPPERM-9999")
        self.assertIsNone(result)


# ── get_group_categories ──────────────────────────────────────────────────────


class GetGroupCategoriesTest(TestCase):
    def test_returns_assignments_for_group(self):
        group = make_group()
        cat = make_permission_category()
        GroupPermissionCategory.objects.create(group=group, category=cat)
        qs = selectors.get_group_categories(group)
        self.assertEqual(qs.count(), 1)

    def test_does_not_return_other_group_assignments(self):
        group_a = make_group("A")
        group_b = make_group("B")
        cat = make_permission_category()
        GroupPermissionCategory.objects.create(group=group_b, category=cat)
        qs = selectors.get_group_categories(group_a)
        self.assertEqual(qs.count(), 0)

    def test_ordered_by_module_then_category_order(self):
        group = make_group()
        cat_b = make_permission_category(module="sprints", codename="view", order=1)
        cat_a = make_permission_category(module="projects", codename="view", order=1)
        GroupPermissionCategory.objects.create(group=group, category=cat_b)
        GroupPermissionCategory.objects.create(group=group, category=cat_a)
        qs = selectors.get_group_categories(group)
        self.assertEqual(qs[0].category.module, "projects")
        self.assertEqual(qs[1].category.module, "sprints")


# ── get_user_by_profile_code ──────────────────────────────────────────────────


class GetUserByProfileCodeTest(TestCase):
    def test_returns_user_for_valid_profile_code(self):
        user, profile = make_user_with_profile()
        result = selectors.get_user_by_profile_code(profile.code)
        self.assertEqual(result.pk, user.pk)

    def test_returns_none_for_unknown_code(self):
        result = selectors.get_user_by_profile_code("USER-9999")
        self.assertIsNone(result)


# ── get_user_assignment_by_code ───────────────────────────────────────────────


class GetUserAssignmentByCodeTest(TestCase):
    def test_returns_assignment_for_valid_code(self):
        user = make_user()
        cat = make_permission_category()
        assignment = UserPermissionCategory.objects.create(user=user, category=cat)
        result = selectors.get_user_assignment_by_code(assignment.code)
        self.assertEqual(result.pk, assignment.pk)

    def test_returns_none_for_unknown_code(self):
        result = selectors.get_user_assignment_by_code("USRPERM-9999")
        self.assertIsNone(result)


# ── get_user_categories ───────────────────────────────────────────────────────


class GetUserCategoriesTest(TestCase):
    def test_returns_assignments_for_user(self):
        user = make_user()
        cat = make_permission_category()
        UserPermissionCategory.objects.create(user=user, category=cat)
        qs = selectors.get_user_categories(user)
        self.assertEqual(qs.count(), 1)

    def test_does_not_return_other_user_assignments(self):
        user_a = make_user("a@example.com")
        user_b = make_user("b@example.com")
        cat = make_permission_category()
        UserPermissionCategory.objects.create(user=user_b, category=cat)
        qs = selectors.get_user_categories(user_a)
        self.assertEqual(qs.count(), 0)

    def test_ordered_by_module_then_category_order(self):
        user = make_user()
        cat_b = make_permission_category(module="sprints", codename="view", order=1)
        cat_a = make_permission_category(module="projects", codename="view", order=1)
        UserPermissionCategory.objects.create(user=user, category=cat_b)
        UserPermissionCategory.objects.create(user=user, category=cat_a)
        qs = selectors.get_user_categories(user)
        self.assertEqual(qs[0].category.module, "projects")
        self.assertEqual(qs[1].category.module, "sprints")


# ── get_user_permissions ──────────────────────────────────────────────────────


class GetUserPermissionsTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.perm = Permission.objects.filter(
            content_type__app_label="permissions",
            codename="view_grouppermissioncategory",
        ).first()

    def test_returns_empty_set_for_user_with_no_assignments(self):
        result = selectors.get_user_permissions(self.user)
        self.assertIsInstance(result, set)
        self.assertEqual(len(result), 0)

    def test_returns_permissions_from_direct_assignment(self):
        cat = make_permission_category(module="permissions", codename="view_grp")
        cat.permissions.set([self.perm])
        UserPermissionCategory.objects.create(user=self.user, category=cat)
        result = selectors.get_user_permissions(self.user)
        self.assertIn("permissions.view_grouppermissioncategory", result)

    def test_returns_permissions_from_group_assignment(self):
        group = make_group()
        group.user_set.add(self.user)
        cat = make_permission_category(module="permissions", codename="view_grp")
        cat.permissions.set([self.perm])
        GroupPermissionCategory.objects.create(group=group, category=cat)
        result = selectors.get_user_permissions(self.user)
        self.assertIn("permissions.view_grouppermissioncategory", result)

    def test_deduplicates_permissions_from_group_and_direct(self):
        group = make_group()
        group.user_set.add(self.user)
        cat = make_permission_category(module="permissions", codename="view_grp")
        cat.permissions.set([self.perm])
        GroupPermissionCategory.objects.create(group=group, category=cat)
        UserPermissionCategory.objects.create(user=self.user, category=cat)
        result = selectors.get_user_permissions(self.user)
        perm_str = "permissions.view_grouppermissioncategory"
        self.assertEqual(list(result).count(perm_str), 1)


# ── get_effective_scope ───────────────────────────────────────────────────────


class GetEffectiveScopeTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.cat = make_permission_category(module="projects", codename="edit")

    def test_returns_none_when_no_assignments(self):
        result = selectors.get_effective_scope(self.user, "projects", "edit")
        self.assertEqual(result, PermissionScope.NONE)

    def test_returns_scope_from_direct_assignment(self):
        UserPermissionCategory.objects.create(
            user=self.user, category=self.cat, scope=PermissionScope.TEAM
        )
        result = selectors.get_effective_scope(self.user, "projects", "edit")
        self.assertEqual(result, PermissionScope.TEAM)

    def test_returns_scope_from_group_assignment(self):
        group = make_group()
        group.user_set.add(self.user)
        GroupPermissionCategory.objects.create(
            group=group, category=self.cat, scope=PermissionScope.ALL
        )
        result = selectors.get_effective_scope(self.user, "projects", "edit")
        self.assertEqual(result, PermissionScope.ALL)

    def test_broadest_scope_wins_when_group_and_direct_differ(self):
        group = make_group()
        group.user_set.add(self.user)
        GroupPermissionCategory.objects.create(
            group=group, category=self.cat, scope=PermissionScope.SELF
        )
        UserPermissionCategory.objects.create(
            user=self.user, category=self.cat, scope=PermissionScope.ALL
        )
        result = selectors.get_effective_scope(self.user, "projects", "edit")
        self.assertEqual(result, PermissionScope.ALL)

    def test_returns_none_for_different_module(self):
        UserPermissionCategory.objects.create(
            user=self.user, category=self.cat, scope=PermissionScope.ALL
        )
        result = selectors.get_effective_scope(self.user, "sprints", "edit")
        self.assertEqual(result, PermissionScope.NONE)


# ── get_effective_user_assignments ────────────────────────────────────────────


class GetEffectiveUserAssignmentsTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.cat = make_permission_category(module="projects", codename="view", order=1)

    def test_returns_empty_list_for_user_with_no_assignments(self):
        result = selectors.get_effective_user_assignments(self.user)
        self.assertEqual(result, [])

    def test_group_assignment_has_via_group(self):
        group = make_group()
        group.user_set.add(self.user)
        GroupPermissionCategory.objects.create(
            group=group, category=self.cat, scope=PermissionScope.TEAM
        )
        result = selectors.get_effective_user_assignments(self.user)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["via"], "group")
        self.assertEqual(result[0]["scope"], PermissionScope.TEAM)

    def test_direct_assignment_has_via_direct(self):
        UserPermissionCategory.objects.create(
            user=self.user, category=self.cat, scope=PermissionScope.SELF
        )
        result = selectors.get_effective_user_assignments(self.user)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["via"], "direct")
        self.assertEqual(result[0]["scope"], PermissionScope.SELF)

    def test_both_assignments_have_via_both_and_broadest_scope(self):
        group = make_group()
        group.user_set.add(self.user)
        GroupPermissionCategory.objects.create(
            group=group, category=self.cat, scope=PermissionScope.SELF
        )
        UserPermissionCategory.objects.create(
            user=self.user, category=self.cat, scope=PermissionScope.ALL
        )
        result = selectors.get_effective_user_assignments(self.user)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["via"], "both")
        self.assertEqual(result[0]["scope"], PermissionScope.ALL)

    def test_results_sorted_by_module_then_order(self):
        cat_b = make_permission_category(module="sprints", codename="view", order=1)
        cat_c = make_permission_category(module="projects", codename="edit", order=2)
        UserPermissionCategory.objects.create(user=self.user, category=cat_b)
        UserPermissionCategory.objects.create(user=self.user, category=cat_c)
        UserPermissionCategory.objects.create(user=self.user, category=self.cat)
        result = selectors.get_effective_user_assignments(self.user)
        modules = [r["category"].module for r in result]
        self.assertEqual(modules[0], "projects")
        self.assertEqual(modules[1], "projects")
        self.assertEqual(modules[2], "sprints")

    def test_multiple_groups_highest_scope_used(self):
        group_a = make_group("A")
        group_b = make_group("B")
        group_a.user_set.add(self.user)
        group_b.user_set.add(self.user)
        GroupPermissionCategory.objects.create(
            group=group_a, category=self.cat, scope=PermissionScope.SELF
        )
        GroupPermissionCategory.objects.create(
            group=group_b, category=self.cat, scope=PermissionScope.ALL
        )
        result = selectors.get_effective_user_assignments(self.user)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["scope"], PermissionScope.ALL)
