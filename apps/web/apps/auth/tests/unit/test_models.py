from django.test import SimpleTestCase

from apps.auth.models import UserToken

# ---------------------------------------------------------------------------
# UserToken.generate_key
# ---------------------------------------------------------------------------


class UserTokenGenerateKeyTest(SimpleTestCase):
    def test_returns_string(self):
        self.assertIsInstance(UserToken.generate_key(), str)

    def test_returns_64_characters(self):
        self.assertEqual(len(UserToken.generate_key()), 64)

    def test_generates_unique_values(self):
        keys = {UserToken.generate_key() for _ in range(20)}
        self.assertEqual(len(keys), 20)

    def test_key_contains_only_url_safe_characters(self):
        key = UserToken.generate_key()
        self.assertRegex(key, r"^[A-Za-z0-9_\-]+$")

    def test_successive_calls_never_repeat(self):
        k1 = UserToken.generate_key()
        k2 = UserToken.generate_key()
        self.assertNotEqual(k1, k2)
