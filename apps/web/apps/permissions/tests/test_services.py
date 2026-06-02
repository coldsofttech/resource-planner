from django.test import TestCase

from apps.core.exceptions import AlreadyExistsException, NotFoundException
from apps.core.types import ListParams
from apps.permissions.constants import PermissionScope
from apps.permissions.models import (
    GroupPermissionCategory,
    PermissionCategory,
    UserPermissionCategory,
)
from apps.permissions.services import (
    GroupPermissionCategoryService,
    PermissionCategoryService,
    UserPermissionCategoryService,
)
from apps.users.models import Group, GroupProfile, User, UserProfile


def make_user(email="user@example.com"):
    return User.objects.create_user(
        username=email, email=email, password="TestPass123!"
    )


def make_user_with_profile(email="user@example.com"):
    user = make_user(email)
    profile = UserProfile.objects.create(user=user)
    return user, profile


def make_group(name="Test Group"):
    return Group.objects.create(name=name)


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


DEFAULT_LIST_PARAMS = ListParams()


# ── PermissionCategoryService ─────────────────────────────────────────────────


class PermissionCategoryServiceListTest(TestCase):
    def setUp(self):
        self.svc = PermissionCategoryService()
        make_permission_category(module="projects", codename="view", order=1)
        make_permission_category(module="projects", codename="edit", order=2)
        make_permission_category(module="sprints", codename="view", order=1)

    def test_returns_paginated_result(self):
        result = self.svc.list(params=DEFAULT_LIST_PARAMS)
        self.assertIsNotNone(result.pagination)

    def test_pagination_counts_all_categories(self):
        result = self.svc.list(params=DEFAULT_LIST_PARAMS)
        self.assertGreaterEqual(result.pagination.total_count, 3)

    def test_filters_by_module(self):
        params = ListParams(filters={"module": "projects"})
        result = self.svc.list(params=params)
        for cat in result.results:
            self.assertEqual(cat.module, "projects")

    def test_search_by_name(self):
        params = ListParams(search="View")
        result = self.svc.list(params=params)
        names = [c.name for c in result.results]
        self.assertTrue(any("View" in n for n in names))

    def test_page_size_is_respected(self):
        params = ListParams(page=1, page_size=2)
        result = self.svc.list(params=params)
        self.assertLessEqual(len(result.results), 2)


class PermissionCategoryServiceGetTest(TestCase):
    def setUp(self):
        self.svc = PermissionCategoryService()
        self.cat = make_permission_category()

    def test_returns_category_for_valid_code(self):
        result = self.svc.get(self.cat.code)
        self.assertEqual(result.pk, self.cat.pk)

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.get("PERM-9999")

    def test_returned_category_has_permissions_prefetched(self):
        result = self.svc.get(self.cat.code)
        self.assertEqual(result.permissions.count(), 0)


# ── GroupPermissionCategoryService ───────────────────────────────────────────


class GroupPermissionCategoryServiceListTest(TestCase):
    def setUp(self):
        self.svc = GroupPermissionCategoryService()
        self.group, self.profile = make_group_with_profile()
        self.cat = make_permission_category()
        GroupPermissionCategory.objects.create(group=self.group, category=self.cat)

    def test_returns_paginated_assignments_for_group(self):
        result = self.svc.list(group_code=self.profile.code, params=DEFAULT_LIST_PARAMS)
        self.assertEqual(result.pagination.total_count, 1)

    def test_raises_not_found_for_unknown_group(self):
        with self.assertRaises(NotFoundException):
            self.svc.list(group_code="USRGRP-9999", params=DEFAULT_LIST_PARAMS)


class GroupPermissionCategoryServiceAssignTest(TestCase):
    def setUp(self):
        self.svc = GroupPermissionCategoryService()
        self.group, self.profile = make_group_with_profile()
        self.cat = make_permission_category()

    def test_creates_assignment_successfully(self):
        assignment = self.svc.assign(
            group_code=self.profile.code,
            category_code=self.cat.code,
            scope=PermissionScope.TEAM,
        )
        self.assertIsNotNone(assignment.pk)
        self.assertEqual(assignment.scope, PermissionScope.TEAM)
        self.assertEqual(assignment.group, self.group)
        self.assertEqual(assignment.category, self.cat)

    def test_raises_not_found_for_unknown_group(self):
        with self.assertRaises(NotFoundException):
            self.svc.assign(
                group_code="USRGRP-9999",
                category_code=self.cat.code,
                scope=PermissionScope.ALL,
            )

    def test_raises_not_found_for_unknown_category(self):
        with self.assertRaises(NotFoundException):
            self.svc.assign(
                group_code=self.profile.code,
                category_code="PERM-9999",
                scope=PermissionScope.ALL,
            )

    def test_raises_already_exists_on_duplicate_assignment(self):
        self.svc.assign(
            group_code=self.profile.code,
            category_code=self.cat.code,
            scope=PermissionScope.ALL,
        )
        with self.assertRaises(AlreadyExistsException):
            self.svc.assign(
                group_code=self.profile.code,
                category_code=self.cat.code,
                scope=PermissionScope.SELF,
            )


class GroupPermissionCategoryServiceUpdateScopeTest(TestCase):
    def setUp(self):
        self.svc = GroupPermissionCategoryService()
        self.group, self.profile = make_group_with_profile()
        self.cat = make_permission_category()
        self.assignment = GroupPermissionCategory.objects.create(
            group=self.group, category=self.cat, scope=PermissionScope.SELF
        )

    def test_updates_scope_successfully(self):
        updated = self.svc.update_scope(
            group_code=self.profile.code,
            code=self.assignment.code,
            scope=PermissionScope.ALL,
        )
        self.assertEqual(updated.scope, PermissionScope.ALL)

    def test_persists_updated_scope_to_db(self):
        self.svc.update_scope(
            group_code=self.profile.code,
            code=self.assignment.code,
            scope=PermissionScope.TEAM,
        )
        refreshed = GroupPermissionCategory.objects.get(pk=self.assignment.pk)
        self.assertEqual(refreshed.scope, PermissionScope.TEAM)

    def test_raises_not_found_for_wrong_group(self):
        other_group, other_profile = make_group_with_profile("Other Group")
        with self.assertRaises(NotFoundException):
            self.svc.update_scope(
                group_code=other_profile.code,
                code=self.assignment.code,
                scope=PermissionScope.ALL,
            )

    def test_raises_not_found_for_unknown_assignment(self):
        with self.assertRaises(NotFoundException):
            self.svc.update_scope(
                group_code=self.profile.code,
                code="GRPPERM-9999",
                scope=PermissionScope.ALL,
            )


class GroupPermissionCategoryServiceRemoveTest(TestCase):
    def setUp(self):
        self.svc = GroupPermissionCategoryService()
        self.group, self.profile = make_group_with_profile()
        self.cat = make_permission_category()
        self.assignment = GroupPermissionCategory.objects.create(
            group=self.group, category=self.cat
        )

    def test_removes_assignment_from_db(self):
        self.svc.remove(group_code=self.profile.code, code=self.assignment.code)
        exists = GroupPermissionCategory.objects.filter(pk=self.assignment.pk).exists()
        self.assertFalse(exists)

    def test_raises_not_found_for_wrong_group(self):
        other_group, other_profile = make_group_with_profile("Other Group")
        with self.assertRaises(NotFoundException):
            self.svc.remove(group_code=other_profile.code, code=self.assignment.code)

    def test_raises_not_found_for_unknown_assignment(self):
        with self.assertRaises(NotFoundException):
            self.svc.remove(group_code=self.profile.code, code="GRPPERM-9999")


# ── UserPermissionCategoryService ─────────────────────────────────────────────


class UserPermissionCategoryServiceListTest(TestCase):
    def setUp(self):
        self.svc = UserPermissionCategoryService()
        self.user, self.profile = make_user_with_profile()
        self.cat = make_permission_category()
        UserPermissionCategory.objects.create(user=self.user, category=self.cat)

    def test_returns_paginated_assignments_for_user(self):
        result = self.svc.list(user_code=self.profile.code, params=DEFAULT_LIST_PARAMS)
        self.assertEqual(result.pagination.total_count, 1)

    def test_raises_not_found_for_unknown_user(self):
        with self.assertRaises(NotFoundException):
            self.svc.list(user_code="USER-9999", params=DEFAULT_LIST_PARAMS)


class UserPermissionCategoryServiceAssignTest(TestCase):
    def setUp(self):
        self.svc = UserPermissionCategoryService()
        self.user, self.profile = make_user_with_profile()
        self.cat = make_permission_category()

    def test_creates_assignment_successfully(self):
        assignment = self.svc.assign(
            user_code=self.profile.code,
            category_code=self.cat.code,
            scope=PermissionScope.ALL,
        )
        self.assertIsNotNone(assignment.pk)
        self.assertEqual(assignment.user, self.user)
        self.assertEqual(assignment.category, self.cat)
        self.assertEqual(assignment.scope, PermissionScope.ALL)

    def test_raises_not_found_for_unknown_user(self):
        with self.assertRaises(NotFoundException):
            self.svc.assign(
                user_code="USER-9999",
                category_code=self.cat.code,
                scope=PermissionScope.ALL,
            )

    def test_raises_not_found_for_unknown_category(self):
        with self.assertRaises(NotFoundException):
            self.svc.assign(
                user_code=self.profile.code,
                category_code="PERM-9999",
                scope=PermissionScope.ALL,
            )

    def test_raises_already_exists_on_duplicate_assignment(self):
        self.svc.assign(
            user_code=self.profile.code,
            category_code=self.cat.code,
            scope=PermissionScope.ALL,
        )
        with self.assertRaises(AlreadyExistsException):
            self.svc.assign(
                user_code=self.profile.code,
                category_code=self.cat.code,
                scope=PermissionScope.SELF,
            )


class UserPermissionCategoryServiceUpdateScopeTest(TestCase):
    def setUp(self):
        self.svc = UserPermissionCategoryService()
        self.user, self.profile = make_user_with_profile()
        self.cat = make_permission_category()
        self.assignment = UserPermissionCategory.objects.create(
            user=self.user, category=self.cat, scope=PermissionScope.SELF
        )

    def test_updates_scope_successfully(self):
        updated = self.svc.update_scope(
            user_code=self.profile.code,
            code=self.assignment.code,
            scope=PermissionScope.ALL,
        )
        self.assertEqual(updated.scope, PermissionScope.ALL)

    def test_persists_updated_scope_to_db(self):
        self.svc.update_scope(
            user_code=self.profile.code,
            code=self.assignment.code,
            scope=PermissionScope.TEAM,
        )
        refreshed = UserPermissionCategory.objects.get(pk=self.assignment.pk)
        self.assertEqual(refreshed.scope, PermissionScope.TEAM)

    def test_raises_not_found_for_wrong_user(self):
        other_user, other_profile = make_user_with_profile("other@example.com")
        with self.assertRaises(NotFoundException):
            self.svc.update_scope(
                user_code=other_profile.code,
                code=self.assignment.code,
                scope=PermissionScope.ALL,
            )


class UserPermissionCategoryServiceRemoveTest(TestCase):
    def setUp(self):
        self.svc = UserPermissionCategoryService()
        self.user, self.profile = make_user_with_profile()
        self.cat = make_permission_category()
        self.assignment = UserPermissionCategory.objects.create(
            user=self.user, category=self.cat
        )

    def test_removes_assignment_from_db(self):
        self.svc.remove(user_code=self.profile.code, code=self.assignment.code)
        exists = UserPermissionCategory.objects.filter(pk=self.assignment.pk).exists()
        self.assertFalse(exists)

    def test_raises_not_found_for_wrong_user(self):
        other_user, other_profile = make_user_with_profile("other@example.com")
        with self.assertRaises(NotFoundException):
            self.svc.remove(user_code=other_profile.code, code=self.assignment.code)


class UserPermissionCategoryServiceEffectiveTest(TestCase):
    def setUp(self):
        self.svc = UserPermissionCategoryService()
        self.user, self.profile = make_user_with_profile()
        self.cat = make_permission_category(module="projects", codename="view")

    def test_returns_empty_list_for_user_with_no_assignments(self):
        result = self.svc.effective(user_code=self.profile.code)
        self.assertEqual(result, [])

    def test_returns_combined_group_and_direct_assignments(self):
        group = make_group()
        group.user_set.add(self.user)
        cat_b = make_permission_category(module="sprints", codename="view")
        GroupPermissionCategory.objects.create(
            group=group, category=self.cat, scope=PermissionScope.TEAM
        )
        UserPermissionCategory.objects.create(
            user=self.user, category=cat_b, scope=PermissionScope.SELF
        )
        result = self.svc.effective(user_code=self.profile.code)
        self.assertEqual(len(result), 2)

    def test_raises_not_found_for_unknown_user(self):
        with self.assertRaises(NotFoundException):
            self.svc.effective(user_code="USER-9999")
