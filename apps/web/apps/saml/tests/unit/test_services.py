import xml.etree.ElementTree as ET  # nosec B405
from unittest.mock import patch

from django.test import SimpleTestCase

from apps.saml.api_views import SAMLViewSet
from apps.saml.services import SAMLFlowService

_ROOT_STUB = ET.fromstring("<root/>")  # nosec B314
_PATCHED = "apps.saml.services"


# ---------------------------------------------------------------------------
# SAMLFlowService._extract_identity — standard attribute mapping
# ---------------------------------------------------------------------------


class SAMLFlowServiceExtractIdentityTest(SimpleTestCase):
    def _svc(self):
        return SAMLFlowService()

    def _root(self):
        return _ROOT_STUB

    @patch(f"{_PATCHED}.get_name_id", return_value="user@example.com")
    @patch(f"{_PATCHED}.get_attributes", return_value={})
    def test_uses_name_id_as_email_when_it_contains_at_sign(self, _attrs, _name_id):
        email, first_name, last_name, name_id, _ = self._svc()._extract_identity(
            self._root()
        )
        self.assertEqual(email, "user@example.com")
        self.assertEqual(name_id, "user@example.com")

    @patch(f"{_PATCHED}.get_name_id", return_value="uid-123")
    @patch(f"{_PATCHED}.get_attributes", return_value={"email": "attr@example.com"})
    def test_falls_back_to_email_attribute_when_name_id_not_an_email(
        self, _attrs, _name_id
    ):
        email, _, _, _, _ = self._svc()._extract_identity(self._root())
        self.assertEqual(email, "attr@example.com")

    @patch(f"{_PATCHED}.get_name_id", return_value="uid-123")
    @patch(f"{_PATCHED}.get_attributes", return_value={})
    def test_falls_back_to_name_id_when_no_email_attribute(self, _attrs, _name_id):
        email, _, _, _, _ = self._svc()._extract_identity(self._root())
        self.assertEqual(email, "uid-123")

    @patch(f"{_PATCHED}.get_name_id", return_value="user@example.com")
    @patch(
        f"{_PATCHED}.get_attributes",
        return_value={"first_name": "Alice", "last_name": "Smith"},
    )
    def test_extracts_first_and_last_name_from_attributes(self, _attrs, _name_id):
        _, first_name, last_name, _, _ = self._svc()._extract_identity(self._root())
        self.assertEqual(first_name, "Alice")
        self.assertEqual(last_name, "Smith")

    @patch(f"{_PATCHED}.get_name_id", return_value="user@example.com")
    @patch(f"{_PATCHED}.get_attributes", return_value={})
    def test_empty_first_and_last_name_when_attributes_absent(self, _attrs, _name_id):
        _, first_name, last_name, _, _ = self._svc()._extract_identity(self._root())
        self.assertEqual(first_name, "")
        self.assertEqual(last_name, "")


# ---------------------------------------------------------------------------
# SAMLFlowService._extract_identity — alternate IdP attribute names
# ---------------------------------------------------------------------------


class SAMLFlowServiceExtractIdentityAltNamesTest(SimpleTestCase):
    def _svc(self):
        return SAMLFlowService()

    def _root(self):
        return _ROOT_STUB

    @patch(f"{_PATCHED}.get_name_id", return_value="uid-givenname")
    @patch(
        f"{_PATCHED}.get_attributes",
        return_value={"givenName": "Bob", "email": "bob@example.com"},
    )
    def test_extracts_first_name_from_given_name_attribute(self, _attrs, _name_id):
        _, first_name, _, _, _ = self._svc()._extract_identity(self._root())
        self.assertEqual(first_name, "Bob")

    @patch(f"{_PATCHED}.get_name_id", return_value="uid-sn")
    @patch(
        f"{_PATCHED}.get_attributes",
        return_value={"sn": "Wilson", "email": "wilson@example.com"},
    )
    def test_extracts_last_name_from_sn_attribute(self, _attrs, _name_id):
        _, _, last_name, _, _ = self._svc()._extract_identity(self._root())
        self.assertEqual(last_name, "Wilson")

    @patch(f"{_PATCHED}.get_name_id", return_value="uid-mail")
    @patch(
        f"{_PATCHED}.get_attributes",
        return_value={"mail": "mail@example.com"},
    )
    def test_extracts_email_from_mail_attribute_when_name_id_not_email(
        self, _attrs, _name_id
    ):
        email, _, _, _, _ = self._svc()._extract_identity(self._root())
        self.assertEqual(email, "mail@example.com")

    @patch(f"{_PATCHED}.get_name_id", return_value="uid-wsfed")
    @patch(
        f"{_PATCHED}.get_attributes",
        return_value={
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname": "Carol",
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname": "Brown",
            "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress": (
                "carol@example.com"
            ),
        },
    )
    def test_extracts_identity_using_ws_federation_claim_uris(self, _attrs, _name_id):
        email, first_name, last_name, _, _ = self._svc()._extract_identity(self._root())
        self.assertEqual(email, "carol@example.com")
        self.assertEqual(first_name, "Carol")
        self.assertEqual(last_name, "Brown")

    @patch(f"{_PATCHED}.get_name_id", return_value="uid-lastname")
    @patch(
        f"{_PATCHED}.get_attributes",
        return_value={"lastName": "Jones", "email": "jones@example.com"},
    )
    def test_extracts_last_name_from_last_name_attribute(self, _attrs, _name_id):
        _, _, last_name, _, _ = self._svc()._extract_identity(self._root())
        self.assertEqual(last_name, "Jones")


# ---------------------------------------------------------------------------
# SAMLViewSet._safe_redirect
# ---------------------------------------------------------------------------


class SafeRedirectTest(SimpleTestCase):
    def _redirect(self, relay_state: str) -> str:
        return SAMLViewSet._safe_redirect(relay_state)

    def test_returns_dashboard_for_empty_relay_state(self):
        self.assertEqual(self._redirect(""), "/dashboard/")

    def test_returns_local_path_unchanged(self):
        self.assertEqual(self._redirect("/projects/"), "/projects/")

    def test_returns_root_path(self):
        self.assertEqual(self._redirect("/"), "/")

    def test_returns_dashboard_for_external_url(self):
        self.assertEqual(self._redirect("https://evil.example.com"), "/dashboard/")

    def test_returns_dashboard_for_protocol_relative_url(self):
        self.assertEqual(self._redirect("//evil.example.com"), "/dashboard/")

    def test_returns_dashboard_for_path_without_leading_slash(self):
        self.assertEqual(self._redirect("dashboard"), "/dashboard/")

    def test_returns_nested_local_path_unchanged(self):
        self.assertEqual(self._redirect("/teams/42/"), "/teams/42/")

    def test_returns_dashboard_for_http_url(self):
        self.assertEqual(self._redirect("http://evil.example.com/"), "/dashboard/")
