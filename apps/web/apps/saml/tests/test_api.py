from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.saml.models import SAML
from apps.users.models import User

CREATE_URL = "/api/v1/auth/saml/"
ACS_URL = "/api/v1/auth/saml/acs/"

PROVIDER_PAYLOAD = {
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


def make_provider(name="Test Provider", is_active=True, **overrides):
    return SAML.objects.create(
        name=name, is_active=is_active, **{**PROVIDER_BASE, **overrides}
    )


def make_user(email="user@example.com"):
    return User.objects.create_user(username=email, email=email, password="pass")


# ---------------------------------------------------------------------------
# POST /api/v1/auth/saml/ — create provider
# ---------------------------------------------------------------------------


class SAMLCreateAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch("apps.saml.services.encrypt_value", side_effect=lambda v, _: v)
    def test_create_response_contains_idp_x509_cert(self, _enc):
        response = self.client.post(CREATE_URL, PROVIDER_PAYLOAD, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("idp_x509_cert", response.data.get("data", {}))

    @patch("apps.saml.services.encrypt_value", side_effect=lambda v, _: v)
    def test_create_returns_201(self, _enc):
        response = self.client.post(CREATE_URL, PROVIDER_PAYLOAD, format="json")
        self.assertEqual(response.status_code, 201)

    @patch("apps.saml.services.encrypt_value", side_effect=lambda v, _: v)
    def test_create_response_success_flag_is_true(self, _enc):
        response = self.client.post(CREATE_URL, PROVIDER_PAYLOAD, format="json")
        self.assertTrue(response.data["success"])

    @patch("apps.saml.services.encrypt_value", side_effect=lambda v, _: v)
    def test_create_response_contains_provider_name(self, _enc):
        response = self.client.post(CREATE_URL, PROVIDER_PAYLOAD, format="json")
        self.assertEqual(response.data["data"]["name"], "Test SAML IdP")

    @patch("apps.saml.services.encrypt_value", side_effect=lambda v, _: v)
    def test_create_response_contains_saml_code(self, _enc):
        response = self.client.post(CREATE_URL, PROVIDER_PAYLOAD, format="json")
        self.assertTrue(response.data["data"]["code"].startswith("SAML-"))

    @patch("apps.saml.services.encrypt_value", side_effect=lambda v, _: v)
    def test_duplicate_provider_name_returns_409(self, _enc):
        self.client.post(CREATE_URL, PROVIDER_PAYLOAD, format="json")
        response = self.client.post(CREATE_URL, PROVIDER_PAYLOAD, format="json")
        self.assertEqual(response.status_code, 409)

    def test_missing_required_fields_returns_error(self):
        response = self.client.post(CREATE_URL, {"name": "Incomplete"}, format="json")
        self.assertIn(response.status_code, [400, 422])

    def test_empty_payload_returns_error(self):
        response = self.client.post(CREATE_URL, {}, format="json")
        self.assertIn(response.status_code, [400, 422])


# ---------------------------------------------------------------------------
# GET /api/v1/auth/saml/<code>/authorize/ — begin SAML login
# ---------------------------------------------------------------------------


class SAMLAuthorizeAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _authorize_url(self, provider):
        return f"/api/v1/auth/saml/{provider.code}/authorize/"

    def test_authorize_returns_200(self):
        provider = make_provider(name="Active Provider")
        response = self.client.get(self._authorize_url(provider))
        self.assertEqual(response.status_code, 200)

    def test_authorize_response_contains_redirect_url(self):
        provider = make_provider(name="Redirect URL Provider")
        response = self.client.get(self._authorize_url(provider))
        self.assertIn("redirect_url", response.data["data"])

    def test_authorize_redirect_url_starts_with_idp_sso_url(self):
        provider = make_provider(name="SSO URL Provider")
        response = self.client.get(self._authorize_url(provider))
        redirect_url = response.data["data"]["redirect_url"]
        self.assertIn("https://idp.example.com/sso", redirect_url)

    def test_authorize_redirect_url_contains_saml_request(self):
        provider = make_provider(name="SAMLRequest Provider")
        response = self.client.get(self._authorize_url(provider))
        redirect_url = response.data["data"]["redirect_url"]
        self.assertIn("SAMLRequest=", redirect_url)

    def test_authorize_with_relay_state_echoes_it_in_redirect_url(self):
        provider = make_provider(name="Relay State Provider")
        response = self.client.get(
            self._authorize_url(provider), {"relay_state": "my-state"}
        )
        redirect_url = response.data["data"]["redirect_url"]
        self.assertIn("my-state", redirect_url)

    def test_authorize_with_unknown_provider_code_returns_404(self):
        response = self.client.get("/api/v1/auth/saml/SAML-99999/authorize/")
        self.assertEqual(response.status_code, 404)

    def test_authorize_with_inactive_provider_returns_404(self):
        provider = make_provider(name="Inactive Provider", is_active=False)
        response = self.client.get(self._authorize_url(provider))
        self.assertEqual(response.status_code, 404)

    def test_authorize_response_contains_success_message(self):
        provider = make_provider(name="Message Provider")
        response = self.client.get(self._authorize_url(provider))
        self.assertIn("message", response.data)


# ---------------------------------------------------------------------------
# POST /api/v1/auth/saml/acs/ — assertion consumer service
# ---------------------------------------------------------------------------


class SAMLACSAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def _post_acs(self, saml_response="dGVzdA==", relay_state=""):
        return self.client.post(
            ACS_URL,
            {"SAMLResponse": saml_response, "RelayState": relay_state},
        )

    def test_acs_without_saml_response_returns_error(self):
        response = self.client.post(ACS_URL, {})
        self.assertIn(response.status_code, [400, 422])

    def test_acs_with_empty_saml_response_returns_error(self):
        response = self.client.post(ACS_URL, {"SAMLResponse": ""})
        self.assertIn(response.status_code, [400, 422])

    @patch("apps.saml.api_views.SAMLFlowService.complete_login")
    def test_acs_returns_200_on_successful_login(self, mock_login):
        mock_login.return_value = make_user()
        response = self._post_acs()
        self.assertEqual(response.status_code, 200)

    @patch("apps.saml.api_views.SAMLFlowService.complete_login")
    def test_acs_response_contains_user_email(self, mock_login):
        mock_login.return_value = make_user(email="saml@example.com")
        response = self._post_acs()
        self.assertEqual(response.data["data"]["user"]["email"], "saml@example.com")

    @patch("apps.saml.api_views.SAMLFlowService.complete_login")
    def test_acs_response_user_has_expected_fields(self, mock_login):
        mock_login.return_value = make_user()
        response = self._post_acs()
        user_data = response.data["data"]["user"]
        for field in ["id", "email", "first_name", "last_name", "is_superuser"]:
            self.assertIn(field, user_data)

    @patch("apps.saml.api_views.SAMLFlowService.complete_login")
    def test_acs_response_echoes_relay_state(self, mock_login):
        mock_login.return_value = make_user()
        response = self.client.post(
            ACS_URL,
            {
                "SAMLResponse": "dGVzdA==",
                "RelayState": "https://app.example.com/dashboard",
            },
        )
        self.assertEqual(
            response.data["data"]["relay_state"], "https://app.example.com/dashboard"
        )

    @patch("apps.saml.api_views.SAMLFlowService.complete_login")
    def test_acs_response_success_flag_is_true(self, mock_login):
        mock_login.return_value = make_user()
        response = self._post_acs()
        self.assertTrue(response.data["success"])

    @patch(
        "apps.saml.api_views.SAMLFlowService.complete_login",
        side_effect=__import__(
            "apps.core.exceptions", fromlist=["ValidationException"]
        ).ValidationException("SAML authentication was not successful."),
    )
    def test_acs_returns_error_when_service_raises_validation_exception(self, _login):
        response = self._post_acs()
        self.assertIn(response.status_code, [400, 422])

    @patch(
        "apps.saml.api_views.SAMLFlowService.complete_login",
        side_effect=__import__(
            "apps.core.exceptions", fromlist=["NotFoundException"]
        ).NotFoundException(
            resource="SAML provider",
            lookup_field="idp_entity_id",
            lookup_value="https://unknown.example.com",
        ),
    )
    def test_acs_returns_404_when_provider_not_found(self, _login):
        response = self._post_acs()
        self.assertEqual(response.status_code, 404)

    @patch("apps.saml.api_views.SAMLFlowService.complete_login")
    def test_acs_establishes_session_after_successful_login(self, mock_login):
        mock_login.return_value = make_user()
        self._post_acs()
        self.assertIn("_auth_user_id", self.client.session)
