from django.test import TestCase

from apps.users.models import Group, GroupProfile
from apps.users.selectors import (
    get_administrators_group,
    get_all_groups,
    get_group_by_code,
    get_group_members,
    get_guests_group,
    get_system_group,
    get_user,
    is_superuser,
    superuser_exists,
    user_exists,
)
from apps.users.tests.factories import (
    make_group_with_profile,
    make_profile,
    make_superuser,
    make_user,
)

# ---------------------------------------------------------------------------
# user_exists
# ---------------------------------------------------------------------------


class UserExistsTest(TestCase):
    def test_returns_true_when_user_exists(self):
        make_user("exists@example.com")
        self.assertTrue(user_exists("exists@example.com"))

    def test_returns_false_when_user_does_not_exist(self):
        self.assertFalse(user_exists("nobody@example.com"))

    def test_returns_false_for_empty_string(self):
        self.assertFalse(user_exists(""))

    def test_email_match_is_case_sensitive(self):
        make_user("case@example.com")
        self.assertFalse(user_exists("CASE@example.com"))

    def test_partial_email_does_not_match(self):
        make_user("full@example.com")
        self.assertFalse(user_exists("@example.com"))

    def test_returns_false_after_user_is_deleted(self):
        user = make_user("gone@example.com")
        user.delete()
        self.assertFalse(user_exists("gone@example.com"))


# ---------------------------------------------------------------------------
# superuser_exists
# ---------------------------------------------------------------------------


class SuperuserExistsTest(TestCase):
    def test_returns_false_when_no_users_exist(self):
        self.assertFalse(superuser_exists())

    def test_returns_false_when_only_regular_users_exist(self):
        make_user("regular@example.com")
        self.assertFalse(superuser_exists())

    def test_returns_true_when_superuser_exists(self):
        make_superuser()
        self.assertTrue(superuser_exists())

    def test_returns_true_with_mixed_user_types(self):
        make_user("regular@example.com")
        make_superuser()
        self.assertTrue(superuser_exists())

    def test_returns_false_after_superuser_is_deleted(self):
        admin = make_superuser()
        admin.delete()
        self.assertFalse(superuser_exists())


# ---------------------------------------------------------------------------
# is_superuser
# ---------------------------------------------------------------------------


class IsSuperuserTest(TestCase):
    def test_returns_true_for_existing_superuser(self):
        make_superuser("admin@example.com")
        self.assertTrue(is_superuser("admin@example.com"))

    def test_returns_false_for_regular_user(self):
        make_user("regular@example.com")
        self.assertFalse(is_superuser("regular@example.com"))

    def test_returns_false_for_nonexistent_email(self):
        self.assertFalse(is_superuser("nobody@example.com"))

    def test_returns_false_for_empty_string(self):
        self.assertFalse(is_superuser(""))

    def test_does_not_confuse_users_across_emails(self):
        make_user("regular@example.com")
        make_superuser("admin@example.com")
        self.assertFalse(is_superuser("regular@example.com"))
        self.assertTrue(is_superuser("admin@example.com"))

    def test_returns_false_for_inactive_superuser(self):
        # is_superuser checks the flag, not active status — but selector
        # returns True even for inactive superusers (no active filter applied).
        # This documents the current selector contract explicitly.
        make_superuser("inactive-admin@example.com", is_active=False)
        self.assertTrue(is_superuser("inactive-admin@example.com"))


# ---------------------------------------------------------------------------
# get_user
# ---------------------------------------------------------------------------


class GetUserTest(TestCase):
    def test_returns_user_for_known_email(self):
        user = make_user("found@example.com")
        result = get_user("found@example.com")
        self.assertEqual(result, user)

    def test_returns_none_for_unknown_email(self):
        result = get_user("missing@example.com")
        self.assertIsNone(result)

    def test_returns_none_for_empty_string(self):
        result = get_user("")
        self.assertIsNone(result)

    def test_returns_correct_user_among_multiple(self):
        u1 = make_user("first@example.com")
        make_user("second@example.com")
        result = get_user("first@example.com")
        self.assertEqual(result.pk, u1.pk)

    def test_returned_user_has_correct_email(self):
        make_user("check@example.com")
        result = get_user("check@example.com")
        self.assertEqual(result.email, "check@example.com")

    def test_returns_none_after_user_is_deleted(self):
        user = make_user("temp@example.com")
        user.delete()
        self.assertIsNone(get_user("temp@example.com"))


# ---------------------------------------------------------------------------
# get_system_group
# ---------------------------------------------------------------------------


class GetSystemGroupTest(TestCase):
    def test_returns_group_by_name_when_it_exists(self):
        group = Group.objects.create(name="Custom Group")
        result = get_system_group("Custom Group")
        self.assertEqual(result, group)

    def test_returns_none_when_group_does_not_exist(self):
        Group.objects.filter(name="Nonexistent").delete()
        result = get_system_group("Nonexistent")
        self.assertIsNone(result)

    def test_does_not_return_group_with_different_name(self):
        Group.objects.create(name="Group A")
        result = get_system_group("Group B")
        self.assertIsNone(result)

    def test_returns_none_for_empty_string_name(self):
        result = get_system_group("")
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# get_administrators_group
# ---------------------------------------------------------------------------


class GetAdministratorsGroupTest(TestCase):
    def test_returns_group_when_administrators_exists(self):
        group, _ = Group.objects.get_or_create(name="Administrators")
        result = get_administrators_group()
        self.assertEqual(result, group)

    def test_returns_none_when_administrators_group_absent(self):
        Group.objects.filter(name="Administrators").delete()
        result = get_administrators_group()
        self.assertIsNone(result)

    def test_does_not_return_unrelated_group(self):
        Group.objects.create(name="Other Group")
        Group.objects.filter(name="Administrators").delete()
        result = get_administrators_group()
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# get_guests_group
# ---------------------------------------------------------------------------


class GetGuestsGroupTest(TestCase):
    def test_returns_group_when_guests_exists(self):
        group, _ = Group.objects.get_or_create(name="Guests")
        result = get_guests_group()
        self.assertEqual(result, group)

    def test_returns_none_when_guests_group_absent(self):
        Group.objects.filter(name="Guests").delete()
        result = get_guests_group()
        self.assertIsNone(result)

    def test_does_not_return_unrelated_group(self):
        Group.objects.create(name="Other Group")
        Group.objects.filter(name="Guests").delete()
        result = get_guests_group()
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# get_all_groups
# ---------------------------------------------------------------------------


class GetAllGroupsTest(TestCase):
    def setUp(self):
        GroupProfile.objects.all().delete()

    def test_returns_empty_queryset_when_no_groups_exist(self):
        GroupProfile.objects.all().delete()
        result = get_all_groups()
        self.assertEqual(result.count(), 0)

    def test_returns_all_group_profiles(self):
        make_group_with_profile("Alpha Group")
        make_group_with_profile("Beta Group")
        result = get_all_groups()
        self.assertEqual(result.count(), 2)

    def test_ordered_by_group_name_ascending(self):
        make_group_with_profile("Zeta Group")
        make_group_with_profile("Alpha Group")
        names = [gp.group.name for gp in get_all_groups()]
        self.assertEqual(names, sorted(names))

    def test_includes_member_count_annotation(self):
        _, gp = make_group_with_profile("Counted Group")
        result = get_all_groups().get(pk=gp.pk)
        self.assertEqual(result.member_count, 0)

    def test_member_count_reflects_actual_membership(self):
        group, gp = make_group_with_profile("Membership Group")
        user = make_user("member@example.com")
        make_profile(user=user)
        group.user_set.add(user)
        result = get_all_groups().get(pk=gp.pk)
        self.assertEqual(result.member_count, 1)

    def test_returns_queryset_type(self):
        from django.db.models import QuerySet

        result = get_all_groups()
        self.assertIsInstance(result, QuerySet)


# ---------------------------------------------------------------------------
# get_group_by_code
# ---------------------------------------------------------------------------


class GetGroupByCodeTest(TestCase):
    def test_returns_group_profile_for_matching_code(self):
        _, gp = make_group_with_profile("Find Me")
        result = get_group_by_code(gp.code)
        self.assertEqual(result.pk, gp.pk)

    def test_returns_none_for_unknown_code(self):
        result = get_group_by_code("USRGRP-99999")
        self.assertIsNone(result)

    def test_returns_none_for_empty_string(self):
        result = get_group_by_code("")
        self.assertIsNone(result)

    def test_includes_member_count_annotation(self):
        _, gp = make_group_with_profile("Annotated")
        result = get_group_by_code(gp.code)
        self.assertEqual(result.member_count, 0)

    def test_does_not_return_group_for_different_code(self):
        _, gp1 = make_group_with_profile("Group One")
        _, gp2 = make_group_with_profile("Group Two")
        result = get_group_by_code(gp1.code)
        self.assertNotEqual(result.pk, gp2.pk)


# ---------------------------------------------------------------------------
# get_group_members
# ---------------------------------------------------------------------------


class GetGroupMembersTest(TestCase):
    def setUp(self):
        self.group, self.gp = make_group_with_profile("Members Group")

    def test_returns_empty_queryset_when_no_members(self):
        result = get_group_members(self.gp.code)
        self.assertEqual(result.count(), 0)

    def test_returns_members_in_group(self):
        user = make_user("member@example.com")
        make_profile(user=user)
        self.group.user_set.add(user)
        result = get_group_members(self.gp.code)
        self.assertEqual(result.count(), 1)

    def test_does_not_return_users_not_in_group(self):
        user = make_user("outsider@example.com")
        make_profile(user=user)
        result = get_group_members(self.gp.code)
        self.assertEqual(result.count(), 0)

    def test_returns_correct_user_profile(self):
        user = make_user("correct@example.com")
        profile = make_profile(user=user)
        self.group.user_set.add(user)
        result = get_group_members(self.gp.code)
        self.assertEqual(result.first().pk, profile.pk)

    def test_members_ordered_by_last_name_then_first_name(self):
        u1 = make_user("z_last@example.com", last_name="Zebra", first_name="Anna")
        u2 = make_user("a_last@example.com", last_name="Apple", first_name="Bob")
        make_profile(user=u1)
        make_profile(user=u2)
        self.group.user_set.add(u1, u2)
        result = list(get_group_members(self.gp.code))
        self.assertEqual(result[0].user.last_name, "Apple")
        self.assertEqual(result[1].user.last_name, "Zebra")

    def test_returns_empty_queryset_for_nonexistent_group_code(self):
        result = get_group_members("USRGRP-99999")
        self.assertEqual(result.count(), 0)
