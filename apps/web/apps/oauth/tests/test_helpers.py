import json
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase

from apps.oauth.helpers import (
    OAuthUserInfo,
    exchange_code,
    fetch_userinfo,
    parse_userinfo,
)


class ParseUserinfoTest(SimpleTestCase):
    def test_parses_standard_oidc_fields(self):
        raw = {
            "email": "user@example.com",
            "sub": "uid-123",
            "given_name": "Alice",
            "family_name": "Smith",
        }
        info = parse_userinfo(raw)
        self.assertEqual(info.email, "user@example.com")
        self.assertEqual(info.sso_uid, "uid-123")
        self.assertEqual(info.first_name, "Alice")
        self.assertEqual(info.last_name, "Smith")

    def test_returns_oauth_user_info_dataclass(self):
        info = parse_userinfo({"email": "u@example.com", "sub": "s"})
        self.assertIsInstance(info, OAuthUserInfo)

    def test_falls_back_to_mail_for_email(self):
        info = parse_userinfo({"mail": "user@example.com", "sub": "uid"})
        self.assertEqual(info.email, "user@example.com")

    def test_falls_back_to_upn_for_email(self):
        info = parse_userinfo({"upn": "user@example.com", "sub": "uid"})
        self.assertEqual(info.email, "user@example.com")

    def test_email_field_takes_priority_over_mail_and_upn(self):
        info = parse_userinfo(
            {"email": "primary@example.com", "mail": "other@example.com", "sub": "s"}
        )
        self.assertEqual(info.email, "primary@example.com")

    def test_empty_email_when_no_email_fields_present(self):
        info = parse_userinfo({"sub": "s"})
        self.assertEqual(info.email, "")

    def test_email_is_stripped_of_whitespace(self):
        info = parse_userinfo({"email": "  user@example.com  ", "sub": "s"})
        self.assertEqual(info.email, "user@example.com")

    def test_uses_sub_as_sso_uid(self):
        info = parse_userinfo({"email": "u@example.com", "sub": "uid-abc"})
        self.assertEqual(info.sso_uid, "uid-abc")

    def test_falls_back_to_id_when_sub_missing(self):
        info = parse_userinfo({"email": "u@example.com", "id": "id-456"})
        self.assertEqual(info.sso_uid, "id-456")

    def test_falls_back_to_email_as_sso_uid_when_no_sub_or_id(self):
        info = parse_userinfo({"email": "user@example.com"})
        self.assertEqual(info.sso_uid, "user@example.com")

    def test_uses_given_name_and_family_name(self):
        info = parse_userinfo(
            {
                "email": "u@example.com",
                "sub": "s",
                "given_name": "Bob",
                "family_name": "Jones",
            }
        )
        self.assertEqual(info.first_name, "Bob")
        self.assertEqual(info.last_name, "Jones")

    def test_falls_back_to_first_name_and_last_name_keys(self):
        info = parse_userinfo(
            {
                "email": "u@example.com",
                "sub": "s",
                "first_name": "Carol",
                "last_name": "White",
            }
        )
        self.assertEqual(info.first_name, "Carol")
        self.assertEqual(info.last_name, "White")

    def test_splits_full_name_into_first_and_last(self):
        info = parse_userinfo(
            {"email": "u@example.com", "sub": "s", "name": "John Doe"}
        )
        self.assertEqual(info.first_name, "John")
        self.assertEqual(info.last_name, "Doe")

    def test_single_word_name_sets_empty_last_name(self):
        info = parse_userinfo(
            {"email": "u@example.com", "sub": "s", "name": "Mononymous"}
        )
        self.assertEqual(info.first_name, "Mononymous")
        self.assertEqual(info.last_name, "")

    def test_given_name_takes_priority_over_name_field(self):
        info = parse_userinfo(
            {
                "email": "u@example.com",
                "sub": "s",
                "given_name": "First",
                "name": "Full Name",
            }
        )
        self.assertEqual(info.first_name, "First")

    def test_empty_first_and_last_when_no_name_fields(self):
        info = parse_userinfo({"email": "u@example.com", "sub": "s"})
        self.assertEqual(info.first_name, "")
        self.assertEqual(info.last_name, "")


class ExchangeCodeTest(SimpleTestCase):
    def _make_mock_response(self, payload: dict):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(payload).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    @patch("apps.oauth.helpers.urllib.request.urlopen")
    def test_returns_parsed_json_from_token_endpoint(self, mock_urlopen):
        mock_urlopen.return_value = self._make_mock_response(
            {"access_token": "tok-abc"}
        )
        result = exchange_code(
            token_endpoint="https://idp.example.com/token",
            code="auth-code",
            redirect_uri="https://app.example.com/callback",
            client_id="cid",
            client_secret="csecret",
        )
        self.assertEqual(result["access_token"], "tok-abc")

    @patch("apps.oauth.helpers.urllib.request.urlopen")
    def test_sends_post_request(self, mock_urlopen):
        mock_urlopen.return_value = self._make_mock_response({})
        exchange_code(
            token_endpoint="https://idp.example.com/token",
            code="code",
            redirect_uri="https://app.example.com/cb",
            client_id="cid",
            client_secret="csecret",
        )
        args, _ = mock_urlopen.call_args
        request_obj = args[0]
        self.assertEqual(request_obj.get_method(), "POST")


class FetchUserinfoTest(SimpleTestCase):
    def _make_mock_response(self, payload: dict):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(payload).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        return mock_resp

    @patch("apps.oauth.helpers.urllib.request.urlopen")
    def test_returns_parsed_userinfo(self, mock_urlopen):
        mock_urlopen.return_value = self._make_mock_response(
            {"email": "user@example.com", "sub": "uid-1"}
        )
        result = fetch_userinfo(
            userinfo_endpoint="https://idp.example.com/userinfo",
            access_token="tok-abc",
        )
        self.assertEqual(result["email"], "user@example.com")

    @patch("apps.oauth.helpers.urllib.request.urlopen")
    def test_includes_bearer_token_in_request(self, mock_urlopen):
        mock_urlopen.return_value = self._make_mock_response({})
        fetch_userinfo(
            userinfo_endpoint="https://idp.example.com/userinfo",
            access_token="tok-xyz",
        )
        args, _ = mock_urlopen.call_args
        request_obj = args[0]
        self.assertEqual(request_obj.get_header("Authorization"), "Bearer tok-xyz")
