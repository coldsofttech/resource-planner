from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from rest_framework.exceptions import AuthenticationFailed

from apps.auth.authentication import BearerTokenAuthentication


def _request(auth_header: str | None = None) -> MagicMock:
    req = MagicMock()
    req.META = {"HTTP_AUTHORIZATION": auth_header} if auth_header else {}
    return req


# ---------------------------------------------------------------------------
# Header parsing — returns None when scheme is not Bearer
# ---------------------------------------------------------------------------


class BearerTokenAuthReturnsNoneTest(SimpleTestCase):
    def setUp(self):
        self.auth = BearerTokenAuthentication()

    def test_returns_none_when_no_auth_header(self):
        self.assertIsNone(self.auth.authenticate(_request()))

    def test_returns_none_when_header_is_empty_string(self):
        self.assertIsNone(self.auth.authenticate(_request("")))

    def test_returns_none_when_scheme_is_basic(self):
        self.assertIsNone(self.auth.authenticate(_request("Basic dXNlcjpwYXNz")))

    def test_returns_none_when_scheme_is_token(self):
        self.assertIsNone(self.auth.authenticate(_request("Token abc123")))


# ---------------------------------------------------------------------------
# Header parsing — raises AuthenticationFailed for malformed Bearer header
# ---------------------------------------------------------------------------


class BearerTokenAuthMalformedHeaderTest(SimpleTestCase):
    def setUp(self):
        self.auth = BearerTokenAuthentication()

    def test_raises_for_bearer_keyword_alone(self):
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(_request("Bearer"))

    def test_raises_for_bearer_with_three_parts(self):
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(_request("Bearer token extra"))

    def test_raises_for_bearer_with_empty_token_part(self):
        with self.assertRaises(AuthenticationFailed):
            self.auth.authenticate(_request("Bearer  "))


# ---------------------------------------------------------------------------
# Header parsing — valid Bearer header delegates to _authenticate_key
# ---------------------------------------------------------------------------


class BearerTokenAuthDelegationTest(SimpleTestCase):
    def setUp(self):
        self.auth = BearerTokenAuthentication()

    @patch.object(BearerTokenAuthentication, "_authenticate_key")
    def test_calls_authenticate_key_with_token_value(self, mock_key):
        mock_key.return_value = (MagicMock(), MagicMock())
        self.auth.authenticate(_request("Bearer mysecrettoken1234567890abcdef"))
        mock_key.assert_called_once_with("mysecrettoken1234567890abcdef")

    @patch.object(BearerTokenAuthentication, "_authenticate_key")
    def test_returns_authenticate_key_result(self, mock_key):
        sentinel = (MagicMock(), MagicMock())
        mock_key.return_value = sentinel
        result = self.auth.authenticate(_request("Bearer sometoken"))
        self.assertEqual(result, sentinel)


# ---------------------------------------------------------------------------
# authenticate_header
# ---------------------------------------------------------------------------


class BearerTokenAuthHeaderTest(SimpleTestCase):
    def test_authenticate_header_returns_bearer_realm(self):
        auth = BearerTokenAuthentication()
        self.assertEqual(auth.authenticate_header(MagicMock()), 'Bearer realm="api"')
