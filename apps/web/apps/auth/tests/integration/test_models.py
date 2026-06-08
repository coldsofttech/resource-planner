from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from apps.auth.models import PasswordResetToken, UserToken
from apps.auth.tests.factories import make_token
from apps.users.tests.factories import make_user

# ---------------------------------------------------------------------------
# PasswordResetToken — field defaults
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
# PasswordResetToken — explicit field assignment
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
# PasswordResetToken — relationship to User
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
# PasswordResetToken — default ordering
# ---------------------------------------------------------------------------


class PasswordResetTokenOrderingTest(TestCase):
    def test_default_ordering_is_newest_first(self):
        user = make_user()
        older = make_token(user=user, token_hash="a" * 64)
        newer = make_token(user=user, token_hash="b" * 64)
        tokens = list(PasswordResetToken.objects.filter(user=user))
        self.assertEqual(tokens[0].pk, newer.pk)
        self.assertEqual(tokens[1].pk, older.pk)


# ---------------------------------------------------------------------------
# UserToken — field defaults
# ---------------------------------------------------------------------------


class UserTokenFieldDefaultsTest(TestCase):
    def setUp(self):
        self.user = make_user()

    def _make_token(self):
        return UserToken.objects.create(user=self.user, key=UserToken.generate_key())

    def test_is_active_defaults_to_true(self):
        token = self._make_token()
        self.assertTrue(token.is_active)

    def test_last_used_at_defaults_to_none(self):
        token = self._make_token()
        self.assertIsNone(token.last_used_at)

    def test_created_at_is_set_on_creation(self):
        token = self._make_token()
        self.assertIsNotNone(token.created_at)

    def test_updated_at_is_set_on_creation(self):
        token = self._make_token()
        self.assertIsNotNone(token.updated_at)

    def test_key_is_stored_correctly(self):
        key = UserToken.generate_key()
        token = UserToken.objects.create(user=self.user, key=key)
        self.assertEqual(token.key, key)


# ---------------------------------------------------------------------------
# UserToken — relationship to User
# ---------------------------------------------------------------------------


class UserTokenUserRelationshipTest(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_token_is_linked_to_user(self):
        token = UserToken.objects.create(user=self.user, key=UserToken.generate_key())
        self.assertEqual(token.user, self.user)

    def test_deleting_user_cascades_to_tokens(self):
        token = UserToken.objects.create(user=self.user, key=UserToken.generate_key())
        pk = token.pk
        self.user.delete()
        self.assertFalse(UserToken.objects.filter(pk=pk).exists())

    def test_reverse_accessor_auth_tokens_returns_all_user_tokens(self):
        UserToken.objects.create(user=self.user, key=UserToken.generate_key())
        UserToken.objects.create(user=self.user, key=UserToken.generate_key())
        self.assertEqual(self.user.auth_tokens.count(), 2)


# ---------------------------------------------------------------------------
# UserToken — key uniqueness
# ---------------------------------------------------------------------------


class UserTokenKeyUniquenessTest(TestCase):
    def test_duplicate_key_raises_integrity_error(self):
        from django.db import IntegrityError

        user = make_user()
        key = UserToken.generate_key()
        UserToken.objects.create(user=user, key=key)
        with self.assertRaises(IntegrityError):
            UserToken.objects.create(user=user, key=key)


# ---------------------------------------------------------------------------
# UserToken — default ordering
# ---------------------------------------------------------------------------


class UserTokenOrderingTest(TestCase):
    def test_default_ordering_is_newest_first(self):
        user = make_user()
        older = UserToken.objects.create(user=user, key=UserToken.generate_key())
        newer = UserToken.objects.create(user=user, key=UserToken.generate_key())
        tokens = list(UserToken.objects.filter(user=user))
        self.assertEqual(tokens[0].pk, newer.pk)
        self.assertEqual(tokens[1].pk, older.pk)
