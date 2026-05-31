from django.db import IntegrityError
from django.test import TestCase

from apps.users.models import User, UserProfile


def make_user(email="user@example.com", **kwargs):
    return User.objects.create_user(
        username=email, email=email, password="StrongPass123!", **kwargs
    )


def make_profile(user=None, **kwargs):
    if user is None:
        user = make_user()
    return UserProfile.objects.create(user=user, **kwargs)


# ---------------------------------------------------------------------------
# CodeModel behaviour — auto-generated code
# ---------------------------------------------------------------------------


class UserProfileCodeTest(TestCase):
    def test_code_auto_generated_with_user_prefix(self):
        profile = make_profile()
        self.assertTrue(profile.code.startswith("USER-"))

    def test_code_contains_primary_key(self):
        profile = make_profile()
        self.assertEqual(profile.code, f"USER-{profile.pk}")

    def test_each_profile_gets_unique_code(self):
        p1 = make_profile(make_user("a@example.com"))
        p2 = make_profile(make_user("b@example.com"))
        self.assertNotEqual(p1.code, p2.code)


# ---------------------------------------------------------------------------
# Field defaults
# ---------------------------------------------------------------------------


class UserProfileFieldDefaultsTest(TestCase):
    def test_must_change_password_defaults_to_false(self):
        profile = make_profile()
        self.assertFalse(profile.must_change_password)

    def test_password_last_changed_defaults_to_none(self):
        profile = make_profile()
        self.assertIsNone(profile.password_last_changed)

    def test_sso_uid_defaults_to_none(self):
        profile = make_profile()
        self.assertIsNone(profile.sso_uid)

    def test_sso_provider_content_type_defaults_to_none(self):
        profile = make_profile()
        self.assertIsNone(profile.sso_provider_content_type)

    def test_sso_provider_object_id_defaults_to_none(self):
        profile = make_profile()
        self.assertIsNone(profile.sso_provider_object_id)

    def test_created_by_defaults_to_none(self):
        profile = make_profile()
        self.assertIsNone(profile.created_by)

    def test_created_at_is_set_on_creation(self):
        profile = make_profile()
        self.assertIsNotNone(profile.created_at)

    def test_updated_at_is_set_on_creation(self):
        profile = make_profile()
        self.assertIsNotNone(profile.updated_at)


# ---------------------------------------------------------------------------
# Explicit field assignments
# ---------------------------------------------------------------------------


class UserProfileFieldAssignmentTest(TestCase):
    def test_must_change_password_can_be_set_true(self):
        profile = make_profile(must_change_password=True)
        self.assertTrue(profile.must_change_password)

    def test_sso_uid_can_be_set(self):
        profile = make_profile(sso_uid="sub-12345")
        self.assertEqual(profile.sso_uid, "sub-12345")

    def test_created_by_can_be_set(self):
        admin = make_user("admin@example.com")
        user = make_user("other@example.com")
        profile = make_profile(user=user, created_by=admin)
        self.assertEqual(profile.created_by, admin)


# ---------------------------------------------------------------------------
# Relationship to User
# ---------------------------------------------------------------------------


class UserProfileUserRelationshipTest(TestCase):
    def test_profile_is_linked_to_user(self):
        user = make_user()
        profile = make_profile(user=user)
        self.assertEqual(profile.user, user)

    def test_user_profile_reverse_accessor_works(self):
        user = make_user()
        profile = make_profile(user=user)
        self.assertEqual(user.profile, profile)

    def test_deleting_user_cascades_to_profile(self):
        user = make_user()
        profile = make_profile(user=user)
        pk = profile.pk
        user.delete()
        self.assertFalse(UserProfile.objects.filter(pk=pk).exists())

    def test_one_user_cannot_have_two_profiles(self):
        user = make_user()
        UserProfile.objects.create(user=user)
        with self.assertRaises(IntegrityError):
            UserProfile.objects.create(user=user)

    def test_different_users_can_each_have_a_profile(self):
        u1 = make_user("a@example.com")
        u2 = make_user("b@example.com")
        p1 = make_profile(user=u1)
        p2 = make_profile(user=u2)
        self.assertNotEqual(p1.pk, p2.pk)
