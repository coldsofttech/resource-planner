import xml.etree.ElementTree as ET  # nosec B405
from unittest.mock import patch

from django.test import TestCase

from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.saml.models import SAML
from apps.saml.services import AdminSAMLService, SAMLFlowService, SAMLService
from apps.users.models import User

PROVIDER_DEFAULTS = {
    "name": "Test SAML IdP",
    "idp_entity_id": "https://idp.example.com/entity",
    "idp_sso_url": "https://idp.example.com/sso",
    "idp_x509_cert": "MIICERT...",
    "sp_entity_id": "https://sp.example.com/entity",
    "sp_assertion_url": "https://sp.example.com/acs",
}

PROVIDER_BASE = {
    "idp_entity_id": "https://idp.example.com/entity",
    "idp_sso_url": "https://idp.example.com/sso",
    "idp_x509_cert": "MIICERT...",
    "sp_entity_id": "https://sp.example.com/entity",
    "sp_assertion_url": "https://sp.example.com/acs",
}


def make_provider(name="Flow Provider", **overrides):
    return SAML.objects.create(name=name, **{**PROVIDER_BASE, **overrides})


# ---------------------------------------------------------------------------
# SAMLService
# ---------------------------------------------------------------------------


class SAMLServiceCreateTest(TestCase):
    @patch("apps.saml.services.encrypt_value", side_effect=lambda v, _: v)
    def test_create_returns_saml_instance(self, _enc):
        svc = SAMLService()
        provider = svc.create(**PROVIDER_DEFAULTS)
        self.assertIsInstance(provider, SAML)

    @patch("apps.saml.services.encrypt_value", side_effect=lambda v, _: v)
    def test_create_stores_provider_name(self, _enc):
        svc = SAMLService()
        provider = svc.create(**PROVIDER_DEFAULTS)
        self.assertEqual(provider.name, "Test SAML IdP")

    @patch("apps.saml.services.encrypt_value", side_effect=lambda v, _: v)
    def test_create_generates_saml_code(self, _enc):
        svc = SAMLService()
        provider = svc.create(**PROVIDER_DEFAULTS)
        self.assertTrue(provider.code.startswith("SAML-"))

    @patch("apps.saml.services.encrypt_value", side_effect=lambda v, _: v)
    def test_create_sets_is_active_true(self, _enc):
        svc = SAMLService()
        provider = svc.create(**PROVIDER_DEFAULTS)
        self.assertTrue(provider.is_active)

    @patch("apps.saml.services.encrypt_value", side_effect=lambda v, _: v)
    def test_create_sets_created_by_from_user(self, _enc):
        user = User.objects.create_user(
            username="admin@example.com", email="admin@example.com", password="pass"
        )
        svc = SAMLService(user=user)
        provider = svc.create(**PROVIDER_DEFAULTS)
        self.assertEqual(provider.created_by, user)

    @patch("apps.saml.services.encrypt_value", side_effect=lambda v, _: v)
    def test_create_raises_already_exists_for_duplicate_name(self, _enc):
        svc = SAMLService()
        svc.create(**PROVIDER_DEFAULTS)
        with self.assertRaises(AlreadyExistsException):
            svc.create(**PROVIDER_DEFAULTS)

    @patch("apps.saml.services.encrypt_value", side_effect=lambda v, _: v)
    def test_create_persists_provider_to_database(self, _enc):
        svc = SAMLService()
        provider = svc.create(**PROVIDER_DEFAULTS)
        self.assertTrue(SAML.objects.filter(pk=provider.pk).exists())


# ---------------------------------------------------------------------------
# AdminSAMLService
# ---------------------------------------------------------------------------


class AdminSAMLServiceCreateTest(TestCase):
    @patch("apps.saml.services.encrypt_value", side_effect=lambda v, _: v)
    def test_admin_create_succeeds_without_user(self, _enc):
        svc = AdminSAMLService()
        provider = svc.create(**PROVIDER_DEFAULTS)
        self.assertIsInstance(provider, SAML)

    @patch("apps.saml.services.encrypt_value", side_effect=lambda v, _: v)
    def test_admin_create_sets_created_by_to_none(self, _enc):
        svc = AdminSAMLService()
        provider = svc.create(**PROVIDER_DEFAULTS)
        self.assertIsNone(provider.created_by)

    @patch("apps.saml.services.encrypt_value", side_effect=lambda v, _: v)
    def test_admin_create_raises_already_exists_for_duplicate_name(self, _enc):
        svc = AdminSAMLService()
        svc.create(**PROVIDER_DEFAULTS)
        with self.assertRaises(AlreadyExistsException):
            svc.create(**PROVIDER_DEFAULTS)


# ---------------------------------------------------------------------------
# SAMLFlowService — build_authorize_url
# ---------------------------------------------------------------------------


class SAMLFlowServiceBuildAuthorizeUrlTest(TestCase):
    def test_url_starts_with_idp_sso_url(self):
        provider = make_provider()
        svc = SAMLFlowService()
        url = svc.build_authorize_url(provider=provider)
        self.assertTrue(url.startswith("https://idp.example.com/sso"))

    def test_url_contains_saml_request_param(self):
        provider = make_provider()
        svc = SAMLFlowService()
        url = svc.build_authorize_url(provider=provider)
        self.assertIn("SAMLRequest=", url)

    def test_relay_state_included_when_provided(self):
        provider = make_provider()
        svc = SAMLFlowService()
        url = svc.build_authorize_url(provider=provider, relay_state="my-relay")
        self.assertIn("RelayState=", url)
        self.assertIn("my-relay", url)

    def test_relay_state_absent_when_empty(self):
        provider = make_provider()
        svc = SAMLFlowService()
        url = svc.build_authorize_url(provider=provider, relay_state="")
        self.assertNotIn("RelayState", url)

    def test_uses_sp_assertion_url_as_entity_id_when_sp_entity_id_blank(self):
        provider = make_provider(sp_entity_id="")
        svc = SAMLFlowService()
        url = svc.build_authorize_url(provider=provider)
        self.assertIn("SAMLRequest=", url)


# ---------------------------------------------------------------------------
# SAMLFlowService — complete_login
# ---------------------------------------------------------------------------

_ROOT_STUB = ET.fromstring("<root/>")  # nosec B314
_PATCHED = "apps.saml.services"


class SAMLFlowServiceCompleteLoginTest(TestCase):
    @patch(f"{_PATCHED}.get_attributes", return_value={})
    @patch(f"{_PATCHED}.get_name_id", return_value="user@example.com")
    @patch(f"{_PATCHED}.verify_signature", return_value=True)
    @patch(f"{_PATCHED}.decrypt_value", return_value="cert-pem")
    @patch(f"{_PATCHED}.get_provider_by_entity_id")
    @patch(f"{_PATCHED}.get_issuer", return_value="https://idp.example.com/entity")
    @patch(f"{_PATCHED}.check_status_success", return_value=True)
    @patch(f"{_PATCHED}.parse_saml_response")
    def test_creates_new_user_on_first_login(
        self, mock_parse, _status, _issuer, mock_lookup, _dec, _sig, _name_id, _attrs
    ):
        provider = make_provider(name="Login Provider")
        mock_lookup.return_value = provider
        mock_parse.return_value = (_ROOT_STUB, b"xml")

        user = SAMLFlowService().complete_login(saml_response_b64="dGVzdA==")
        self.assertEqual(user.email, "user@example.com")

    @patch(f"{_PATCHED}.get_attributes", return_value={})
    @patch(f"{_PATCHED}.get_name_id", return_value="returning@example.com")
    @patch(f"{_PATCHED}.verify_signature", return_value=True)
    @patch(f"{_PATCHED}.decrypt_value", return_value="cert-pem")
    @patch(f"{_PATCHED}.get_provider_by_entity_id")
    @patch(f"{_PATCHED}.get_issuer", return_value="https://idp.example.com/entity")
    @patch(f"{_PATCHED}.check_status_success", return_value=True)
    @patch(f"{_PATCHED}.parse_saml_response")
    def test_returns_same_user_on_repeat_login(
        self, mock_parse, _status, _issuer, mock_lookup, _dec, _sig, _name_id, _attrs
    ):
        provider = make_provider(name="Repeat Login Provider")
        mock_lookup.return_value = provider
        mock_parse.return_value = (_ROOT_STUB, b"xml")

        svc = SAMLFlowService()
        user1 = svc.complete_login(saml_response_b64="dGVzdA==")
        user2 = svc.complete_login(saml_response_b64="dGVzdA==")
        self.assertEqual(user1.pk, user2.pk)

    @patch(f"{_PATCHED}.parse_saml_response", side_effect=Exception("bad base64"))
    def test_raises_validation_error_on_parse_failure(self, _parse):
        with self.assertRaises(ValidationException):
            SAMLFlowService().complete_login(saml_response_b64="!bad!")

    @patch(f"{_PATCHED}.check_status_success", return_value=False)
    @patch(f"{_PATCHED}.parse_saml_response")
    def test_raises_validation_error_when_status_not_success(self, mock_parse, _status):
        mock_parse.return_value = (_ROOT_STUB, b"xml")
        with self.assertRaises(ValidationException):
            SAMLFlowService().complete_login(saml_response_b64="dGVzdA==")

    @patch(f"{_PATCHED}.get_issuer", return_value="")
    @patch(f"{_PATCHED}.check_status_success", return_value=True)
    @patch(f"{_PATCHED}.parse_saml_response")
    def test_raises_validation_error_when_issuer_missing(
        self, mock_parse, _status, _issuer
    ):
        mock_parse.return_value = (_ROOT_STUB, b"xml")
        with self.assertRaises(ValidationException):
            SAMLFlowService().complete_login(saml_response_b64="dGVzdA==")

    @patch(f"{_PATCHED}.get_provider_by_entity_id", return_value=None)
    @patch(f"{_PATCHED}.get_issuer", return_value="https://unknown.example.com/entity")
    @patch(f"{_PATCHED}.check_status_success", return_value=True)
    @patch(f"{_PATCHED}.parse_saml_response")
    def test_raises_not_found_when_provider_unknown(
        self, mock_parse, _status, _issuer, _lookup
    ):
        mock_parse.return_value = (_ROOT_STUB, b"xml")
        with self.assertRaises(NotFoundException):
            SAMLFlowService().complete_login(saml_response_b64="dGVzdA==")

    @patch(f"{_PATCHED}.verify_signature", return_value=False)
    @patch(f"{_PATCHED}.decrypt_value", return_value="cert-pem")
    @patch(f"{_PATCHED}.get_provider_by_entity_id")
    @patch(f"{_PATCHED}.get_issuer", return_value="https://idp.example.com/entity")
    @patch(f"{_PATCHED}.check_status_success", return_value=True)
    @patch(f"{_PATCHED}.parse_saml_response")
    def test_raises_validation_error_when_signature_invalid(
        self, mock_parse, _status, _issuer, mock_lookup, _dec, _sig
    ):
        provider = make_provider(name="Sig Fail Provider")
        mock_lookup.return_value = provider
        mock_parse.return_value = (_ROOT_STUB, b"xml")
        with self.assertRaises(ValidationException):
            SAMLFlowService().complete_login(saml_response_b64="dGVzdA==")

    @patch(f"{_PATCHED}.get_name_id", return_value="")
    @patch(f"{_PATCHED}.verify_signature", return_value=True)
    @patch(f"{_PATCHED}.decrypt_value", return_value="cert-pem")
    @patch(f"{_PATCHED}.get_provider_by_entity_id")
    @patch(f"{_PATCHED}.get_issuer", return_value="https://idp.example.com/entity")
    @patch(f"{_PATCHED}.check_status_success", return_value=True)
    @patch(f"{_PATCHED}.parse_saml_response")
    def test_raises_validation_error_when_name_id_missing(
        self, mock_parse, _status, _issuer, mock_lookup, _dec, _sig, _name_id
    ):
        provider = make_provider(name="No NameID Provider")
        mock_lookup.return_value = provider
        mock_parse.return_value = (_ROOT_STUB, b"xml")
        with self.assertRaises(ValidationException):
            SAMLFlowService().complete_login(saml_response_b64="dGVzdA==")


# ---------------------------------------------------------------------------
# SAMLFlowService — _extract_identity attribute mapping
# ---------------------------------------------------------------------------


class SAMLFlowServiceExtractIdentityTest(TestCase):
    def _svc(self):
        return SAMLFlowService()

    def _root(self):
        return _ROOT_STUB

    @patch(f"{_PATCHED}.get_name_id", return_value="user@example.com")
    @patch(f"{_PATCHED}.get_attributes", return_value={})
    def test_uses_name_id_as_email_when_it_contains_at_sign(self, _attrs, _name_id):
        email, first_name, last_name, name_id = self._svc()._extract_identity(
            self._root()
        )
        self.assertEqual(email, "user@example.com")
        self.assertEqual(name_id, "user@example.com")

    @patch(f"{_PATCHED}.get_name_id", return_value="uid-123")
    @patch(f"{_PATCHED}.get_attributes", return_value={"email": "attr@example.com"})
    def test_falls_back_to_email_attribute_when_name_id_not_an_email(
        self, _attrs, _name_id
    ):
        email, _, _, _ = self._svc()._extract_identity(self._root())
        self.assertEqual(email, "attr@example.com")

    @patch(f"{_PATCHED}.get_name_id", return_value="uid-123")
    @patch(f"{_PATCHED}.get_attributes", return_value={})
    def test_falls_back_to_name_id_when_no_email_attribute(self, _attrs, _name_id):
        email, _, _, _ = self._svc()._extract_identity(self._root())
        self.assertEqual(email, "uid-123")

    @patch(f"{_PATCHED}.get_name_id", return_value="user@example.com")
    @patch(
        f"{_PATCHED}.get_attributes",
        return_value={"first_name": "Alice", "last_name": "Smith"},
    )
    def test_extracts_first_and_last_name_from_attributes(self, _attrs, _name_id):
        _, first_name, last_name, _ = self._svc()._extract_identity(self._root())
        self.assertEqual(first_name, "Alice")
        self.assertEqual(last_name, "Smith")

    @patch(f"{_PATCHED}.get_name_id", return_value="user@example.com")
    @patch(f"{_PATCHED}.get_attributes", return_value={})
    def test_empty_first_and_last_name_when_attributes_absent(self, _attrs, _name_id):
        _, first_name, last_name, _ = self._svc()._extract_identity(self._root())
        self.assertEqual(first_name, "")
        self.assertEqual(last_name, "")


# ---------------------------------------------------------------------------
# SAMLFlowService._extract_identity — alternate IdP attribute names
# ---------------------------------------------------------------------------


class SAMLFlowServiceExtractIdentityAltNamesTest(TestCase):
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
        _, first_name, _, _ = self._svc()._extract_identity(self._root())
        self.assertEqual(first_name, "Bob")

    @patch(f"{_PATCHED}.get_name_id", return_value="uid-sn")
    @patch(
        f"{_PATCHED}.get_attributes",
        return_value={"sn": "Wilson", "email": "wilson@example.com"},
    )
    def test_extracts_last_name_from_sn_attribute(self, _attrs, _name_id):
        _, _, last_name, _ = self._svc()._extract_identity(self._root())
        self.assertEqual(last_name, "Wilson")

    @patch(f"{_PATCHED}.get_name_id", return_value="uid-mail")
    @patch(
        f"{_PATCHED}.get_attributes",
        return_value={"mail": "mail@example.com"},
    )
    def test_extracts_email_from_mail_attribute_when_name_id_not_email(
        self, _attrs, _name_id
    ):
        email, _, _, _ = self._svc()._extract_identity(self._root())
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
        email, first_name, last_name, _ = self._svc()._extract_identity(self._root())
        self.assertEqual(email, "carol@example.com")
        self.assertEqual(first_name, "Carol")
        self.assertEqual(last_name, "Brown")

    @patch(f"{_PATCHED}.get_name_id", return_value="uid-lastname")
    @patch(
        f"{_PATCHED}.get_attributes",
        return_value={"lastName": "Jones", "email": "jones@example.com"},
    )
    def test_extracts_last_name_from_last_name_attribute(self, _attrs, _name_id):
        _, _, last_name, _ = self._svc()._extract_identity(self._root())
        self.assertEqual(last_name, "Jones")


# ---------------------------------------------------------------------------
# SAMLService / AdminSAMLService — deactivation of existing providers
# ---------------------------------------------------------------------------


class SAMLServiceDeactivationTest(TestCase):
    @patch("apps.saml.services.encrypt_value", side_effect=lambda v, _: v)
    def test_creating_provider_deactivates_existing_active_providers(self, _enc):
        from apps.saml.models import SAML

        existing = SAML.objects.create(
            name="Old SAML Provider", is_active=True, **PROVIDER_BASE
        )
        self.assertTrue(existing.is_active)

        svc = SAMLService()
        svc.create(**PROVIDER_DEFAULTS)

        existing.refresh_from_db()
        self.assertFalse(existing.is_active)

    @patch("apps.saml.services.encrypt_value", side_effect=lambda v, _: v)
    def test_new_provider_is_active_after_creation(self, _enc):
        from apps.saml.models import SAML

        SAML.objects.create(name="Old SAML Active", is_active=True, **PROVIDER_BASE)
        svc = SAMLService()
        new_provider = svc.create(**PROVIDER_DEFAULTS)
        self.assertTrue(new_provider.is_active)

    @patch("apps.saml.services.encrypt_value", side_effect=lambda v, _: v)
    def test_only_one_active_provider_after_creation(self, _enc):
        from apps.saml.models import SAML

        SAML.objects.create(name="Old SAML A", is_active=True, **PROVIDER_BASE)
        svc = SAMLService()
        svc.create(**PROVIDER_DEFAULTS)
        active_count = SAML.objects.filter(is_active=True).count()
        self.assertEqual(active_count, 1)
