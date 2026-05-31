from django.test import TestCase

from apps.users.models import User
from apps.users.selectors import get_user, is_superuser, superuser_exists, user_exists


def make_user(email="user@example.com", **kwargs):
    return User.objects.create_user(
        username=email, email=email, password="StrongPass123!", **kwargs
    )


def make_superuser(email="admin@example.com"):
    return User.objects.create_superuser(
        username=email, email=email, password="StrongPass123!"
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
