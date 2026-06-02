from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.auth.models import RESET_CODE_EXPIRY_MINUTES, PasswordResetToken
from apps.users.models import User


def make_user(email="user@example.com"):
    return User.objects.create_user(
        username=email, email=email, password="StrongPass123!"
    )


_TOKEN_HASH = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"


def make_token(user=None, **overrides):
    if user is None:
        user = make_user()
    defaults = {
        "user": user,
        "email": user.email,
        "token_hash": _TOKEN_HASH,
        "expires_at": timezone.now() + timedelta(minutes=RESET_CODE_EXPIRY_MINUTES),
    }
    defaults.update(overrides)
    return PasswordResetToken.objects.create(**defaults)


# ---------------------------------------------------------------------------
# Field defaults
# ---------------------------------------------------------------------------


class PasswordResetTokenFieldDefaultsTest(TestCase):
    def test_is_used_defaults_to_false(self):
        token = make_token()
        self.assertFalse(token.is_used)

    def test_created_at_is_set_on_creation(self):
        token = make_token()
        self.assertIsNotNone(token.created_at)

    def test_updated_at_is_set_on_creation(self):
        token = make_token()
        self.assertIsNotNone(token.updated_at)

    def test_expires_at_is_stored_correctly(self):
        future = timezone.now() + timedelta(minutes=10)
        token = make_token(expires_at=future)
        self.assertIsNotNone(token.expires_at)

    def test_email_field_stores_correct_value(self):
        user = make_user("token@example.com")
        token = make_token(user=user)
        self.assertEqual(token.email, "token@example.com")

    def test_token_hash_is_stored(self):
        token = make_token(token_hash="deadbeef" * 8)
        self.assertEqual(token.token_hash, "deadbeef" * 8)


# ---------------------------------------------------------------------------
# Explicit field assignment
# ---------------------------------------------------------------------------


class PasswordResetTokenFieldAssignmentTest(TestCase):
    def test_is_used_can_be_set_true(self):
        token = make_token(is_used=True)
        self.assertTrue(token.is_used)

    def test_is_used_can_be_updated(self):
        token = make_token()
        token.is_used = True
        token.save(update_fields=["is_used", "updated_at"])
        token.refresh_from_db()
        self.assertTrue(token.is_used)


# ---------------------------------------------------------------------------
# Relationship to User
# ---------------------------------------------------------------------------


class PasswordResetTokenUserRelationshipTest(TestCase):
    def test_token_is_linked_to_user(self):
        user = make_user()
        token = make_token(user=user)
        self.assertEqual(token.user, user)

    def test_user_can_have_multiple_tokens(self):
        user = make_user()
        t1 = make_token(user=user, token_hash="a" * 64)
        t2 = make_token(user=user, token_hash="b" * 64)
        self.assertNotEqual(t1.pk, t2.pk)

    def test_deleting_user_cascades_to_tokens(self):
        user = make_user()
        token = make_token(user=user)
        pk = token.pk
        user.delete()
        self.assertFalse(PasswordResetToken.objects.filter(pk=pk).exists())

    def test_reverse_accessor_returns_all_user_tokens(self):
        user = make_user()
        make_token(user=user, token_hash="a" * 64)
        make_token(user=user, token_hash="b" * 64)
        self.assertEqual(user.password_reset_tokens.count(), 2)


# ---------------------------------------------------------------------------
# Default ordering
# ---------------------------------------------------------------------------


class PasswordResetTokenOrderingTest(TestCase):
    def test_default_ordering_is_newest_first(self):
        user = make_user()
        older = make_token(user=user, token_hash="a" * 64)
        newer = make_token(user=user, token_hash="b" * 64)
        tokens = list(PasswordResetToken.objects.filter(user=user))
        self.assertEqual(tokens[0].pk, newer.pk)
        self.assertEqual(tokens[1].pk, older.pk)
