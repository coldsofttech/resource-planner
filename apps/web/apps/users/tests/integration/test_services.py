from unittest.mock import patch

from django.test import TestCase

from apps.auth.constants import AuthMode
from apps.core.exceptions import (
    AlreadyExistsException,
    ConflictException,
    NotFoundException,
)
from apps.oauth.models import OAuth
from apps.users.models import Group, GroupProfile, User, UserProfile
from apps.users.services import (
    AdminUserService,
    BaseUserService,
    GroupsAdminService,
    SSOUserService,
)
from apps.users.tests.factories import (
    make_group_with_profile,
    make_user,
    make_user_with_profile,
)

OAUTH_BASE = {
    "client_id": "cid",
    "client_secret": "csecret",
    "auth_endpoint": "https://idp.example.com/auth",
    "token_endpoint": "https://idp.example.com/token",
    "userinfo_endpoint": "https://idp.example.com/userinfo",
    "scope": "openid email",
}

USER_BASE = {
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane@example.com",
    "password": "StrongPass123!",
}


def make_provider(name="Test Provider"):
    return OAuth.objects.create(name=name, **OAUTH_BASE)


# ---------------------------------------------------------------------------
# BaseUserService._create_user — classic auth
# ---------------------------------------------------------------------------


class BaseUserServiceCreateUserTest(TestCase):
    def setUp(self):
        self.svc = BaseUserService()

    def test_returns_user_instance(self):
        user = self.svc._create_user(**USER_BASE)
        self.assertIsInstance(user, User)

    def test_created_user_has_correct_email(self):
        user = self.svc._create_user(**USER_BASE)
        self.assertEqual(user.email, "jane@example.com")

    def test_created_user_has_correct_first_name(self):
        user = self.svc._create_user(**USER_BASE)
        self.assertEqual(user.first_name, "Jane")

    def test_created_user_has_correct_last_name(self):
        user = self.svc._create_user(**USER_BASE)
        self.assertEqual(user.last_name, "Doe")

    def test_created_user_is_persisted(self):
        user = self.svc._create_user(**USER_BASE)
        self.assertTrue(User.objects.filter(pk=user.pk).exists())

    def test_user_profile_is_created(self):
        user = self.svc._create_user(**USER_BASE)
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_classic_user_has_usable_password(self):
        user = self.svc._create_user(**USER_BASE)
        self.assertTrue(user.has_usable_password())

    def test_classic_user_can_authenticate_with_password(self):
        user = self.svc._create_user(**USER_BASE)
        self.assertTrue(user.check_password("StrongPass123!"))

    def test_user_is_not_superuser_by_default(self):
        user = self.svc._create_user(**USER_BASE)
        self.assertFalse(user.is_superuser)

    def test_user_is_active_by_default(self):
        user = self.svc._create_user(**USER_BASE)
        self.assertTrue(user.is_active)

    def test_raises_already_exists_for_duplicate_email(self):
        self.svc._create_user(**USER_BASE)
        with self.assertRaises(AlreadyExistsException):
            self.svc._create_user(**USER_BASE)

    def test_second_call_does_not_create_a_second_user(self):
        self.svc._create_user(**USER_BASE)
        try:
            self.svc._create_user(**USER_BASE)
        except AlreadyExistsException:
            pass
        self.assertEqual(User.objects.filter(email="jane@example.com").count(), 1)

    def test_created_by_is_stored_on_profile(self):
        creator = make_user("creator@example.com")
        user = self.svc._create_user(**USER_BASE, created_by=creator)
        self.assertEqual(user.profile.created_by, creator)

    def test_created_by_defaults_to_none_on_profile(self):
        user = self.svc._create_user(**USER_BASE)
        self.assertIsNone(user.profile.created_by)

    def test_regular_user_is_added_to_guests_group(self):
        guests, _ = Group.objects.get_or_create(name="Guests")
        user = self.svc._create_user(**USER_BASE)
        self.assertIn(guests, user.groups.all())

    def test_regular_user_is_not_in_administrators_group(self):
        admins, _ = Group.objects.get_or_create(name="Administrators")
        user = self.svc._create_user(**USER_BASE)
        self.assertNotIn(admins, user.groups.all())


# ---------------------------------------------------------------------------
# BaseUserService._create_user — SAML / OAuth auth modes
# ---------------------------------------------------------------------------


class BaseUserServiceSSOAuthModeTest(TestCase):
    def setUp(self):
        self.svc = BaseUserService()

    @patch(
        "apps.configurations.selectors.Auth.get_auth_mode",
        return_value=AuthMode.SAML,
    )
    def test_saml_mode_creates_user_with_unusable_password(self, _mock):
        user = self.svc._create_user(**USER_BASE)
        self.assertFalse(user.has_usable_password())

    @patch(
        "apps.configurations.selectors.Auth.get_auth_mode",
        return_value=AuthMode.OAUTH,
    )
    def test_oauth_mode_creates_user_with_unusable_password(self, _mock):
        user = self.svc._create_user(**USER_BASE)
        self.assertFalse(user.has_usable_password())

    @patch(
        "apps.configurations.selectors.Auth.get_auth_mode",
        return_value=AuthMode.SAML,
    )
    def test_saml_mode_still_creates_profile(self, _mock):
        user = self.svc._create_user(**USER_BASE)
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    @patch(
        "apps.configurations.selectors.Auth.get_auth_mode",
        return_value=AuthMode.OAUTH,
    )
    def test_oauth_mode_still_creates_profile(self, _mock):
        user = self.svc._create_user(**USER_BASE)
        self.assertTrue(UserProfile.objects.filter(user=user).exists())


# ---------------------------------------------------------------------------
# BaseUserService._create_user — superuser path
# ---------------------------------------------------------------------------


class BaseUserServiceCreateSuperuserTest(TestCase):
    def setUp(self):
        self.svc = BaseUserService()

    def test_creates_superuser_when_flag_set(self):
        user = self.svc._create_user(**USER_BASE, is_superuser=True)
        self.assertTrue(user.is_superuser)

    def test_creates_superuser_profile(self):
        user = self.svc._create_user(**USER_BASE, is_superuser=True)
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_raises_conflict_when_superuser_already_exists(self):
        self.svc._create_user(**USER_BASE, is_superuser=True)
        with self.assertRaises(ConflictException):
            self.svc._create_user(
                first_name="Other",
                last_name="Admin",
                email="other@example.com",
                password="StrongPass123!",
                is_superuser=True,
            )

    def test_raises_already_exists_if_email_taken_even_for_superuser(self):
        self.svc._create_user(**USER_BASE, is_superuser=True)
        with self.assertRaises(AlreadyExistsException):
            self.svc._create_user(**USER_BASE, is_superuser=True)

    def test_superuser_is_added_to_administrators_group(self):
        admins, _ = Group.objects.get_or_create(name="Administrators")
        user = self.svc._create_user(**USER_BASE, is_superuser=True)
        self.assertIn(admins, user.groups.all())

    def test_superuser_is_not_in_guests_group(self):
        guests, _ = Group.objects.get_or_create(name="Guests")
        user = self.svc._create_user(**USER_BASE, is_superuser=True)
        self.assertNotIn(guests, user.groups.all())


# ---------------------------------------------------------------------------
# BaseUserService._create_sso_user — direct method tests
# ---------------------------------------------------------------------------


class BaseUserServiceCreateSSOUserTest(TestCase):
    def setUp(self):
        self.svc = BaseUserService()
        self.provider = make_provider()

    def test_raises_already_exists_when_email_is_taken(self):
        make_user("sso@example.com")
        with self.assertRaises(AlreadyExistsException):
            self.svc._create_sso_user(
                first_name="SSO",
                last_name="User",
                email="sso@example.com",
                sso_provider=self.provider,
                sso_uid="uid-001",
            )

    def test_creates_user_with_unusable_password(self):
        user = self.svc._create_sso_user(
            first_name="SSO",
            last_name="User",
            email="sso@example.com",
            sso_provider=self.provider,
            sso_uid="uid-001",
        )
        self.assertFalse(user.has_usable_password())

    def test_creates_profile_with_correct_sso_uid(self):
        user = self.svc._create_sso_user(
            first_name="SSO",
            last_name="User",
            email="sso@example.com",
            sso_provider=self.provider,
            sso_uid="uid-custom",
        )
        self.assertEqual(user.profile.sso_uid, "uid-custom")

    def test_creates_profile_with_correct_provider_object_id(self):
        user = self.svc._create_sso_user(
            first_name="SSO",
            last_name="User",
            email="sso@example.com",
            sso_provider=self.provider,
            sso_uid="uid-001",
        )
        self.assertEqual(user.profile.sso_provider_object_id, self.provider.pk)

    def test_user_is_persisted(self):
        user = self.svc._create_sso_user(
            first_name="SSO",
            last_name="User",
            email="sso@example.com",
            sso_provider=self.provider,
            sso_uid="uid-001",
        )
        self.assertTrue(User.objects.filter(pk=user.pk).exists())


# ---------------------------------------------------------------------------
# AdminUserService.create
# ---------------------------------------------------------------------------


class AdminUserServiceCreateTest(TestCase):
    def setUp(self):
        self.svc = AdminUserService()

    def test_returns_user_instance(self):
        user = self.svc.create(**USER_BASE)
        self.assertIsInstance(user, User)

    def test_created_user_is_superuser(self):
        user = self.svc.create(**USER_BASE)
        self.assertTrue(user.is_superuser)

    def test_created_user_has_correct_email(self):
        user = self.svc.create(**USER_BASE)
        self.assertEqual(user.email, "jane@example.com")

    def test_creates_user_profile(self):
        user = self.svc.create(**USER_BASE)
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_raises_conflict_when_superuser_already_exists(self):
        self.svc.create(**USER_BASE)
        with self.assertRaises(ConflictException):
            self.svc.create(
                first_name="Second",
                last_name="Admin",
                email="second@example.com",
                password="StrongPass123!",
            )

    def test_raises_already_exists_for_duplicate_email(self):
        self.svc.create(**USER_BASE)
        with self.assertRaises(AlreadyExistsException):
            self.svc.create(**USER_BASE)

    def test_superuser_persisted_in_database(self):
        user = self.svc.create(**USER_BASE)
        self.assertTrue(User.objects.filter(pk=user.pk, is_superuser=True).exists())


# ---------------------------------------------------------------------------
# SSOUserService.get_or_create — new user path
# ---------------------------------------------------------------------------


class SSOUserServiceNewUserTest(TestCase):
    def setUp(self):
        self.svc = SSOUserService()
        self.provider = make_provider()

    def test_returns_tuple(self):
        result = self.svc.get_or_create(
            email="sso@example.com",
            first_name="SSO",
            last_name="User",
            sso_provider=self.provider,
            sso_uid="uid-001",
        )
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_created_flag_is_true_for_new_user(self):
        _, created = self.svc.get_or_create(
            email="sso@example.com",
            first_name="SSO",
            last_name="User",
            sso_provider=self.provider,
            sso_uid="uid-001",
        )
        self.assertTrue(created)

    def test_new_user_has_correct_email(self):
        user, _ = self.svc.get_or_create(
            email="sso@example.com",
            first_name="SSO",
            last_name="User",
            sso_provider=self.provider,
            sso_uid="uid-001",
        )
        self.assertEqual(user.email, "sso@example.com")

    def test_new_user_has_unusable_password(self):
        user, _ = self.svc.get_or_create(
            email="sso@example.com",
            first_name="SSO",
            last_name="User",
            sso_provider=self.provider,
            sso_uid="uid-001",
        )
        self.assertFalse(user.has_usable_password())

    def test_new_user_profile_is_created(self):
        user, _ = self.svc.get_or_create(
            email="sso@example.com",
            first_name="SSO",
            last_name="User",
            sso_provider=self.provider,
            sso_uid="uid-001",
        )
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_profile_stores_sso_uid(self):
        user, _ = self.svc.get_or_create(
            email="sso@example.com",
            first_name="SSO",
            last_name="User",
            sso_provider=self.provider,
            sso_uid="uid-abc",
        )
        self.assertEqual(user.profile.sso_uid, "uid-abc")

    def test_profile_stores_provider_object_id(self):
        user, _ = self.svc.get_or_create(
            email="sso@example.com",
            first_name="SSO",
            last_name="User",
            sso_provider=self.provider,
            sso_uid="uid-001",
        )
        self.assertEqual(user.profile.sso_provider_object_id, self.provider.pk)

    def test_user_is_persisted(self):
        user, _ = self.svc.get_or_create(
            email="sso@example.com",
            first_name="SSO",
            last_name="User",
            sso_provider=self.provider,
            sso_uid="uid-001",
        )
        self.assertTrue(User.objects.filter(pk=user.pk).exists())


# ---------------------------------------------------------------------------
# SSOUserService.get_or_create — returning user (SSO UID match)
# ---------------------------------------------------------------------------


class SSOUserServiceReturningUserTest(TestCase):
    def setUp(self):
        self.svc = SSOUserService()
        self.provider = make_provider()
        self.user, _ = self.svc.get_or_create(
            email="returning@example.com",
            first_name="Return",
            last_name="User",
            sso_provider=self.provider,
            sso_uid="uid-return",
        )

    def test_returns_same_user_on_repeat_login(self):
        user2, _ = self.svc.get_or_create(
            email="returning@example.com",
            first_name="Return",
            last_name="User",
            sso_provider=self.provider,
            sso_uid="uid-return",
        )
        self.assertEqual(self.user.pk, user2.pk)

    def test_created_flag_is_false_for_returning_user(self):
        _, created = self.svc.get_or_create(
            email="returning@example.com",
            first_name="Return",
            last_name="User",
            sso_provider=self.provider,
            sso_uid="uid-return",
        )
        self.assertFalse(created)

    def test_does_not_create_duplicate_user_in_db(self):
        self.svc.get_or_create(
            email="returning@example.com",
            first_name="Return",
            last_name="User",
            sso_provider=self.provider,
            sso_uid="uid-return",
        )
        self.assertEqual(User.objects.filter(email="returning@example.com").count(), 1)

    def test_does_not_create_duplicate_profile_in_db(self):
        self.svc.get_or_create(
            email="returning@example.com",
            first_name="Return",
            last_name="User",
            sso_provider=self.provider,
            sso_uid="uid-return",
        )
        self.assertEqual(UserProfile.objects.filter(user=self.user).count(), 1)


# ---------------------------------------------------------------------------
# SSOUserService.get_or_create — email-link path (admin-created user)
# ---------------------------------------------------------------------------


class SSOUserServiceEmailLinkTest(TestCase):
    def setUp(self):
        self.svc = SSOUserService()
        self.provider = make_provider()
        self.pre_existing = make_user("linked@example.com")
        UserProfile.objects.create(user=self.pre_existing)

    def test_returns_existing_user_when_email_matches(self):
        user, _ = self.svc.get_or_create(
            email="linked@example.com",
            first_name="Linked",
            last_name="User",
            sso_provider=self.provider,
            sso_uid="uid-linked",
        )
        self.assertEqual(user.pk, self.pre_existing.pk)

    def test_created_flag_is_false_when_linking_existing_user(self):
        _, created = self.svc.get_or_create(
            email="linked@example.com",
            first_name="Linked",
            last_name="User",
            sso_provider=self.provider,
            sso_uid="uid-linked",
        )
        self.assertFalse(created)

    def test_existing_user_profile_is_updated_with_sso_uid(self):
        self.svc.get_or_create(
            email="linked@example.com",
            first_name="Linked",
            last_name="User",
            sso_provider=self.provider,
            sso_uid="uid-linked",
        )
        self.pre_existing.profile.refresh_from_db()
        self.assertEqual(self.pre_existing.profile.sso_uid, "uid-linked")

    def test_existing_user_profile_is_updated_with_provider(self):
        self.svc.get_or_create(
            email="linked@example.com",
            first_name="Linked",
            last_name="User",
            sso_provider=self.provider,
            sso_uid="uid-linked",
        )
        self.pre_existing.profile.refresh_from_db()
        self.assertEqual(
            self.pre_existing.profile.sso_provider_object_id, self.provider.pk
        )

    def test_no_new_user_created_when_email_matches(self):
        self.svc.get_or_create(
            email="linked@example.com",
            first_name="Linked",
            last_name="User",
            sso_provider=self.provider,
            sso_uid="uid-linked",
        )
        self.assertEqual(User.objects.filter(email="linked@example.com").count(), 1)


# ---------------------------------------------------------------------------
# SSOUserService.get_or_create — isolation between providers
# ---------------------------------------------------------------------------


class SSOUserServiceProviderIsolationTest(TestCase):
    def setUp(self):
        self.svc = SSOUserService()
        self.provider_a = make_provider("Provider A")
        self.provider_b = make_provider("Provider B")

    def test_same_sso_uid_on_different_providers_creates_separate_users(self):
        user_a, _ = self.svc.get_or_create(
            email="userA@example.com",
            first_name="A",
            last_name="User",
            sso_provider=self.provider_a,
            sso_uid="uid-shared",
        )
        user_b, _ = self.svc.get_or_create(
            email="userB@example.com",
            first_name="B",
            last_name="User",
            sso_provider=self.provider_b,
            sso_uid="uid-shared",
        )
        self.assertNotEqual(user_a.pk, user_b.pk)

    def test_repeat_login_on_correct_provider_returns_correct_user(self):
        user_a, _ = self.svc.get_or_create(
            email="userA@example.com",
            first_name="A",
            last_name="User",
            sso_provider=self.provider_a,
            sso_uid="uid-only-a",
        )
        returning, _ = self.svc.get_or_create(
            email="userA@example.com",
            first_name="A",
            last_name="User",
            sso_provider=self.provider_a,
            sso_uid="uid-only-a",
        )
        self.assertEqual(user_a.pk, returning.pk)


# ---------------------------------------------------------------------------
# BaseUserService._assign_default_group — missing group (integration)
# ---------------------------------------------------------------------------


class BaseUserServiceGroupNotFoundTest(TestCase):
    def setUp(self):
        self.svc = BaseUserService()

    def test_user_created_even_when_guests_group_does_not_exist(self):
        Group.objects.filter(name="Guests").delete()
        user = self.svc._create_user(**USER_BASE)
        self.assertIsInstance(user, User)

    def test_user_is_persisted_when_guests_group_absent(self):
        Group.objects.filter(name="Guests").delete()
        user = self.svc._create_user(**USER_BASE)
        self.assertTrue(User.objects.filter(pk=user.pk).exists())

    def test_user_has_no_groups_when_guests_group_absent(self):
        Group.objects.filter(name="Guests").delete()
        user = self.svc._create_user(**USER_BASE)
        self.assertEqual(user.groups.count(), 0)

    def test_superuser_created_even_when_administrators_group_absent(self):
        Group.objects.filter(name="Administrators").delete()
        user = self.svc._create_user(**USER_BASE, is_superuser=True)
        self.assertIsInstance(user, User)

    def test_superuser_has_no_groups_when_administrators_group_absent(self):
        Group.objects.filter(name="Administrators").delete()
        user = self.svc._create_user(**USER_BASE, is_superuser=True)
        self.assertEqual(user.groups.count(), 0)


# ---------------------------------------------------------------------------
# SSOUserService — empty / None name fields
# ---------------------------------------------------------------------------


class SSOUserServiceEmptyNamesTest(TestCase):
    def setUp(self):
        self.svc = SSOUserService()
        self.provider = make_provider("Empty Names Provider")

    def test_sso_user_created_with_empty_first_and_last_name(self):
        user, _ = self.svc.get_or_create(
            email="noname@example.com",
            first_name="",
            last_name="",
            sso_provider=self.provider,
            sso_uid="uid-noname",
        )
        self.assertEqual(user.first_name, "")
        self.assertEqual(user.last_name, "")

    def test_sso_user_created_with_none_names_does_not_raise(self):
        user, _ = self.svc.get_or_create(
            email="nonename@example.com",
            first_name=None,
            last_name=None,
            sso_provider=self.provider,
            sso_uid="uid-none-names",
        )
        self.assertIsNotNone(user)
        self.assertTrue(User.objects.filter(pk=user.pk).exists())

    def test_sso_user_profile_created_with_empty_names(self):
        user, _ = self.svc.get_or_create(
            email="profileempty@example.com",
            first_name="",
            last_name="",
            sso_provider=self.provider,
            sso_uid="uid-profile-empty",
        )
        self.assertTrue(UserProfile.objects.filter(user=user).exists())


# ---------------------------------------------------------------------------
# GroupsAdminService helpers
# ---------------------------------------------------------------------------


def _make_service(user=None):
    if user is None:
        user = make_user("svc@example.com")
    return GroupsAdminService(user=user, request=None)


# ---------------------------------------------------------------------------
# GroupsAdminService.stats
# ---------------------------------------------------------------------------


class GroupsAdminServiceStatsTest(TestCase):
    def setUp(self):
        GroupProfile.objects.all().delete()
        self.svc = _make_service()

    def test_total_reflects_group_count(self):
        make_group_with_profile("G1")
        make_group_with_profile("G2")
        result = self.svc.stats()
        self.assertEqual(result["total"], 2)

    def test_active_count_counts_active_groups(self):
        _, gp = make_group_with_profile("Active")
        gp.is_active = True
        gp.save()
        make_group_with_profile("Inactive")[1].is_active = False
        GroupProfile.objects.filter(
            pk=make_group_with_profile("Inactive2")[1].pk
        ).update(is_active=False)
        result = self.svc.stats()
        self.assertGreaterEqual(result["active"], 1)

    def test_inactive_count_counts_inactive_groups(self):
        _, gp = make_group_with_profile("InactiveGroup")
        GroupProfile.objects.filter(pk=gp.pk).update(is_active=False)
        result = self.svc.stats()
        self.assertGreaterEqual(result["inactive"], 1)

    def test_admin_groups_count_counts_admin_groups(self):
        _, gp = make_group_with_profile("AdminGroup")
        GroupProfile.objects.filter(pk=gp.pk).update(is_admin_group=True)
        result = self.svc.stats()
        self.assertGreaterEqual(result["admin_groups"], 1)

    def test_returns_dict_with_required_keys(self):
        result = self.svc.stats()
        self.assertIn("total", result)
        self.assertIn("active", result)
        self.assertIn("inactive", result)
        self.assertIn("admin_groups", result)


# ---------------------------------------------------------------------------
# GroupsAdminService.create
# ---------------------------------------------------------------------------


class GroupsAdminServiceCreateTest(TestCase):
    def setUp(self):
        self.svc = _make_service()

    def test_returns_group_profile_instance(self):
        result = self.svc.create(name="New Group")
        self.assertIsInstance(result, GroupProfile)

    def test_creates_auth_group(self):
        self.svc.create(name="Auth Group")
        self.assertTrue(Group.objects.filter(name="Auth Group").exists())

    def test_creates_group_profile(self):
        result = self.svc.create(name="Profile Group")
        self.assertTrue(GroupProfile.objects.filter(pk=result.pk).exists())

    def test_code_auto_generated(self):
        result = self.svc.create(name="Coded Group")
        self.assertTrue(result.code.startswith("USRGRP-"))

    def test_description_stored_on_profile(self):
        result = self.svc.create(name="Desc Group", description="A test group")
        self.assertEqual(result.description, "A test group")

    def test_description_defaults_to_empty_string(self):
        result = self.svc.create(name="No Desc Group")
        self.assertEqual(result.description, "")

    def test_created_by_set_to_service_user(self):
        user = make_user("creator@example.com")
        svc = _make_service(user=user)
        result = svc.create(name="Audited Group")
        self.assertEqual(result.created_by, user)

    def test_raises_already_exists_for_duplicate_name(self):
        self.svc.create(name="Duplicate Group")
        with self.assertRaises(AlreadyExistsException):
            self.svc.create(name="Duplicate Group")

    def test_duplicate_does_not_create_second_group(self):
        self.svc.create(name="Once Group")
        try:
            self.svc.create(name="Once Group")
        except AlreadyExistsException:
            pass
        self.assertEqual(Group.objects.filter(name="Once Group").count(), 1)


# ---------------------------------------------------------------------------
# GroupsAdminService.get
# ---------------------------------------------------------------------------


class GroupsAdminServiceGetTest(TestCase):
    def setUp(self):
        self.svc = _make_service()

    def test_returns_group_profile_for_known_code(self):
        _, gp = make_group_with_profile("Get Group")
        result = self.svc.get(gp.code)
        self.assertEqual(result.pk, gp.pk)

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.get("USRGRP-99999")


# ---------------------------------------------------------------------------
# GroupsAdminService.update
# ---------------------------------------------------------------------------


class GroupsAdminServiceUpdateTest(TestCase):
    def setUp(self):
        self.svc = _make_service()
        _, self.gp = make_group_with_profile("Original Name")

    def test_updates_group_name(self):
        self.svc.update(self.gp.code, name="Updated Name")
        self.gp.group.refresh_from_db()
        self.assertEqual(self.gp.group.name, "Updated Name")

    def test_updates_description(self):
        self.svc.update(self.gp.code, description="New description")
        self.gp.refresh_from_db()
        self.assertEqual(self.gp.description, "New description")

    def test_returns_updated_group_profile(self):
        result = self.svc.update(self.gp.code, description="Updated")
        self.assertIsInstance(result, GroupProfile)

    def test_raises_already_exists_when_name_conflicts_with_another_group(self):
        make_group_with_profile("Existing Name")
        with self.assertRaises(AlreadyExistsException):
            self.svc.update(self.gp.code, name="Existing Name")

    def test_updating_to_same_name_does_not_raise(self):
        result = self.svc.update(self.gp.code, name="Original Name")
        self.gp.group.refresh_from_db()
        self.assertEqual(self.gp.group.name, "Original Name")
        self.assertIsInstance(result, GroupProfile)

    def test_updated_by_set_to_service_user(self):
        user = make_user("updater@example.com")
        svc = _make_service(user=user)
        svc.update(self.gp.code, description="Check updater")
        self.gp.refresh_from_db()
        self.assertEqual(self.gp.updated_by, user)

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.update("USRGRP-99999", name="X")


# ---------------------------------------------------------------------------
# GroupsAdminService.activate / deactivate
# ---------------------------------------------------------------------------


class GroupsAdminServiceActivateDeactivateTest(TestCase):
    def setUp(self):
        self.svc = _make_service()
        _, self.gp = make_group_with_profile("Toggle Group")

    def test_activate_sets_is_active_true(self):
        GroupProfile.objects.filter(pk=self.gp.pk).update(is_active=False)
        self.svc.activate(self.gp.code)
        self.gp.refresh_from_db()
        self.assertTrue(self.gp.is_active)

    def test_deactivate_sets_is_active_false(self):
        self.svc.deactivate(self.gp.code)
        self.gp.refresh_from_db()
        self.assertFalse(self.gp.is_active)

    def test_activate_returns_group_profile(self):
        result = self.svc.activate(self.gp.code)
        self.assertIsInstance(result, GroupProfile)

    def test_deactivate_returns_group_profile(self):
        result = self.svc.deactivate(self.gp.code)
        self.assertIsInstance(result, GroupProfile)

    def test_activate_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.activate("USRGRP-99999")

    def test_deactivate_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.deactivate("USRGRP-99999")


# ---------------------------------------------------------------------------
# GroupsAdminService.delete
# ---------------------------------------------------------------------------


class GroupsAdminServiceDeleteTest(TestCase):
    def setUp(self):
        self.svc = _make_service()

    def test_delete_removes_group_profile(self):
        _, gp = make_group_with_profile("Delete Me")
        code = gp.code
        self.svc.delete(code)
        self.assertFalse(GroupProfile.objects.filter(code=code).exists())

    def test_delete_removes_auth_group(self):
        group, gp = make_group_with_profile("Remove Group")
        group_pk = group.pk
        self.svc.delete(gp.code)
        self.assertFalse(Group.objects.filter(pk=group_pk).exists())

    def test_delete_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.delete("USRGRP-99999")


# ---------------------------------------------------------------------------
# GroupsAdminService.assign_member / unassign_member
# ---------------------------------------------------------------------------


class GroupsAdminServiceMemberAssignmentTest(TestCase):
    def setUp(self):
        self.svc = _make_service()
        self.group, self.gp = make_group_with_profile("Assignment Group")
        self.user, self.profile = make_user_with_profile("assignee@example.com")

    def test_assign_member_adds_user_to_group(self):
        self.svc.assign_member(self.gp.code, self.profile.code)
        self.assertIn(self.group, self.user.groups.all())

    def test_assign_member_raises_not_found_for_unknown_group(self):
        with self.assertRaises(NotFoundException):
            self.svc.assign_member("USRGRP-99999", self.profile.code)

    def test_assign_member_raises_not_found_for_unknown_member(self):
        with self.assertRaises(NotFoundException):
            self.svc.assign_member(self.gp.code, "USER-99999")

    def test_assign_member_raises_already_exists_when_already_in_group(self):
        self.group.user_set.add(self.user)
        with self.assertRaises(AlreadyExistsException):
            self.svc.assign_member(self.gp.code, self.profile.code)

    def test_unassign_member_removes_user_from_group(self):
        self.group.user_set.add(self.user)
        self.svc.unassign_member(self.gp.code, self.profile.code)
        self.assertNotIn(self.group, self.user.groups.all())

    def test_unassign_member_raises_not_found_for_unknown_group(self):
        with self.assertRaises(NotFoundException):
            self.svc.unassign_member("USRGRP-99999", self.profile.code)

    def test_unassign_member_raises_not_found_for_unknown_member(self):
        with self.assertRaises(NotFoundException):
            self.svc.unassign_member(self.gp.code, "USER-99999")
