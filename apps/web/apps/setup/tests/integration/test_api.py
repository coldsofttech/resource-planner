"""Integration tests for apps.setup API endpoints."""

from unittest.mock import patch

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.exceptions import ConflictException, ValidationException

pytestmark = pytest.mark.django_db


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _client():
    return APIClient()


def _valid_fernet_key():
    from cryptography.fernet import Fernet

    return Fernet.generate_key().decode()


def _valid_x509_body():
    return "A" * 100


def _valid_setup_payload():
    return {
        "admin": {
            "first_name": "Alice",
            "last_name": "Admin",
            "email": "alice@example.com",
            "password": "SecurePass123!",
        },
        "app": {
            "app_name": "TestPlanner",
            "app_url": "https://planner.example.com",
        },
        "infra": {
            "deployment_type": "local",
            "fernet_key": _valid_fernet_key(),
        },
        "db": {
            "engine": "sqlite",
        },
        "auth": {
            "auth_type": "classic",
            "self_register": True,
        },
        "storage": {
            "storage_type": "database",
        },
        "email": {
            "email_type": "console",
            "from_address": "noreply@example.com",
            "from_name": "Planner",
        },
        "logging": {
            "log_destination": "local",
            "log_name": "application",
            "log_path": "/tmp/logs",  # nosec B108
        },
    }


# ---------------------------------------------------------------------------
# GET /api/v1/setup/ — list / defaults
# ---------------------------------------------------------------------------


class TestSetupListEndpoint:
    def test_returns_200(self):
        client = _client()
        with patch(
            "apps.configurations.selectors.Setup.get_setup_complete", return_value=False
        ):
            response = client.get("/api/v1/setup/")
        assert response.status_code == status.HTTP_200_OK

    def test_returns_setup_complete_false_when_not_configured(self):
        client = _client()
        with patch(
            "apps.configurations.selectors.Setup.get_setup_complete", return_value=False
        ):
            response = client.get("/api/v1/setup/")
        assert response.data["data"]["setup_complete"] is False

    def test_returns_setup_complete_true_when_configured(self):
        client = _client()
        with patch(
            "apps.configurations.selectors.Setup.get_setup_complete", return_value=True
        ):
            response = client.get("/api/v1/setup/")
        assert response.data["data"]["setup_complete"] is True

    def test_response_includes_defaults(self):
        client = _client()
        with patch(
            "apps.configurations.selectors.Setup.get_setup_complete", return_value=False
        ):
            response = client.get("/api/v1/setup/")
        defaults = response.data["data"]["defaults"]
        assert "app_name" in defaults
        assert "self_register" in defaults
        assert "storage_type" in defaults
        assert "log_name" in defaults
        assert "log_rotation" in defaults

    def test_response_has_standard_success_structure(self):
        client = _client()
        with patch(
            "apps.configurations.selectors.Setup.get_setup_complete", return_value=False
        ):
            response = client.get("/api/v1/setup/")
        assert response.data["success"] is True
        assert "data" in response.data


# ---------------------------------------------------------------------------
# POST /api/v1/setup/ — create / run setup
# ---------------------------------------------------------------------------


class TestSetupCreateEndpoint:
    def test_returns_201_on_valid_payload(self):
        client = _client()
        payload = _valid_setup_payload()

        with patch(
            "apps.configurations.selectors.Setup.get_setup_complete", return_value=False
        ):
            with patch("apps.setup.services.SetupService.create") as mock_create:
                mock_create.return_value = None
                response = client.post("/api/v1/setup/", payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED

    def test_returns_custom_message_on_success(self):
        client = _client()
        payload = _valid_setup_payload()

        with patch(
            "apps.configurations.selectors.Setup.get_setup_complete", return_value=False
        ):
            with patch("apps.setup.services.SetupService.create") as mock_create:
                mock_create.return_value = None
                response = client.post("/api/v1/setup/", payload, format="json")

        assert response.data["message"] == "Setup completed successfully."

    def test_returns_400_on_missing_required_fields(self):
        client = _client()
        with patch(
            "apps.configurations.selectors.Setup.get_setup_complete", return_value=False
        ):
            response = client.post("/api/v1/setup/", {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_409_when_setup_already_complete(self):
        client = _client()
        payload = _valid_setup_payload()

        with patch(
            "apps.configurations.selectors.Setup.get_setup_complete", return_value=False
        ):
            with patch(
                "apps.setup.services.SetupService.create",
                side_effect=ConflictException("Already done"),
            ):
                response = client.post("/api/v1/setup/", payload, format="json")

        assert response.status_code == status.HTTP_409_CONFLICT

    def test_returns_400_on_invalid_admin_email(self):
        client = _client()
        payload = _valid_setup_payload()
        payload["admin"]["email"] = "not-an-email"

        with patch(
            "apps.configurations.selectors.Setup.get_setup_complete", return_value=False
        ):
            response = client.post("/api/v1/setup/", payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_400_on_invalid_infra_deployment_type(self):
        client = _client()
        payload = _valid_setup_payload()
        payload["infra"]["deployment_type"] = "gcp"

        with patch(
            "apps.configurations.selectors.Setup.get_setup_complete", return_value=False
        ):
            response = client.post("/api/v1/setup/", payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_success_response_has_standard_structure(self):
        client = _client()
        payload = _valid_setup_payload()

        with patch(
            "apps.configurations.selectors.Setup.get_setup_complete", return_value=False
        ):
            with patch("apps.setup.services.SetupService.create") as mock_create:
                mock_create.return_value = None
                response = client.post("/api/v1/setup/", payload, format="json")

        assert response.data["success"] is True

    def test_returns_400_for_weak_password(self):
        client = _client()
        payload = _valid_setup_payload()
        payload["admin"]["password"] = "123"

        with patch(
            "apps.configurations.selectors.Setup.get_setup_complete", return_value=False
        ):
            response = client.post("/api/v1/setup/", payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# POST /api/v1/setup/test/db/ — database connection test
# ---------------------------------------------------------------------------


class TestSetupDbTestEndpoint:
    def test_returns_200_on_valid_connection(self):
        client = _client()
        payload = {
            "host": "localhost",
            "port": "5432",
            "db_name": "mydb",
            "user_name": "admin",
            "password": "secret",
        }

        with patch("apps.setup.services.TestService.test_db_connection"):
            response = client.post("/api/v1/setup/test/db/", payload, format="json")

        assert response.status_code == status.HTTP_200_OK

    def test_returns_200_message_on_success(self):
        client = _client()
        payload = {
            "host": "localhost",
            "port": "5432",
            "db_name": "mydb",
            "user_name": "admin",
            "password": "secret",
        }

        with patch("apps.setup.services.TestService.test_db_connection"):
            response = client.post("/api/v1/setup/test/db/", payload, format="json")

        assert response.data["message"] == "Connection successful."

    def test_returns_400_on_missing_field(self):
        client = _client()
        response = client.post(
            "/api/v1/setup/test/db/", {"host": "localhost"}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_422_on_connection_failure(self):
        client = _client()
        payload = {
            "host": "bad-host",
            "port": "5432",
            "db_name": "mydb",
            "user_name": "admin",
            "password": "wrong",
        }

        with patch(
            "apps.setup.services.TestService.test_db_connection",
            side_effect=ValidationException("connection refused"),
        ):
            response = client.post("/api/v1/setup/test/db/", payload, format="json")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_returns_400_on_empty_payload(self):
        client = _client()
        response = client.post("/api/v1/setup/test/db/", {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# POST /api/v1/setup/test/email/ — email connection test
# ---------------------------------------------------------------------------


class TestSetupEmailTestEndpoint:
    def test_returns_200_on_successful_send(self):
        client = _client()
        payload = {
            "email_type": "console",
            "from_address": "test@example.com",
        }

        with patch("apps.setup.services.TestService.test_email_connection"):
            response = client.post("/api/v1/setup/test/email/", payload, format="json")

        assert response.status_code == status.HTTP_200_OK

    def test_returns_200_message_on_success(self):
        client = _client()
        payload = {
            "email_type": "console",
            "from_address": "test@example.com",
        }

        with patch("apps.setup.services.TestService.test_email_connection"):
            response = client.post("/api/v1/setup/test/email/", payload, format="json")

        assert response.data["message"] == "Test email sent successfully."

    def test_returns_400_on_missing_from_address(self):
        client = _client()
        response = client.post(
            "/api/v1/setup/test/email/",
            {"email_type": "console"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_422_on_send_failure(self):
        client = _client()
        payload = {
            "email_type": "smtp",
            "from_address": "test@example.com",
            "smtp_host": "bad-host",
            "smtp_port": 587,
            "smtp_enc_type": "none",
        }

        with patch(
            "apps.setup.services.TestService.test_email_connection",
            side_effect=ValidationException("SMTP error"),
        ):
            response = client.post("/api/v1/setup/test/email/", payload, format="json")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_returns_400_on_invalid_from_address(self):
        client = _client()
        response = client.post(
            "/api/v1/setup/test/email/",
            {"email_type": "console", "from_address": "not-email"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# POST /api/v1/setup/test/saml/ — SAML connection test
# ---------------------------------------------------------------------------


class TestSetupSamlTestEndpoint:
    def test_returns_200_on_valid_saml_config(self):
        client = _client()
        payload = {
            "idp_sso_url": "https://idp.example.com/sso",
            "idp_x509_cert": "A" * 100,
        }

        with patch("apps.setup.services.TestService.test_saml_connection"):
            response = client.post("/api/v1/setup/test/saml/", payload, format="json")

        assert response.status_code == status.HTTP_200_OK

    def test_returns_message_on_success(self):
        client = _client()
        payload = {
            "idp_sso_url": "https://idp.example.com/sso",
            "idp_x509_cert": "A" * 100,
        }

        with patch("apps.setup.services.TestService.test_saml_connection"):
            response = client.post("/api/v1/setup/test/saml/", payload, format="json")

        assert "SAML" in response.data["message"] or response.data["message"]

    def test_returns_400_on_missing_idp_sso_url(self):
        client = _client()
        response = client.post(
            "/api/v1/setup/test/saml/",
            {"idp_x509_cert": "A" * 100},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_400_on_missing_cert(self):
        client = _client()
        response = client.post(
            "/api/v1/setup/test/saml/",
            {"idp_sso_url": "https://idp.example.com/sso"},
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_422_on_connection_failure(self):
        client = _client()
        payload = {
            "idp_sso_url": "https://unreachable.example.com/sso",
            "idp_x509_cert": "A" * 100,
        }

        with patch(
            "apps.setup.services.TestService.test_saml_connection",
            side_effect=ValidationException("Cannot reach IdP SSO URL"),
        ):
            response = client.post("/api/v1/setup/test/saml/", payload, format="json")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_returns_400_on_empty_payload(self):
        client = _client()
        response = client.post("/api/v1/setup/test/saml/", {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# POST /api/v1/setup/test/oauth/ — OAuth connection test
# ---------------------------------------------------------------------------


class TestSetupOAuthTestEndpoint:
    def test_returns_200_on_valid_oauth_config(self):
        client = _client()
        payload = {
            "client_id": "my-client-id",
            "client_secret": "my-client-secret",
            "auth_endpoint": "https://idp.example.com/auth",
            "token_endpoint": "https://idp.example.com/token",
        }

        with patch("apps.setup.services.TestService.test_oauth_connection"):
            response = client.post("/api/v1/setup/test/oauth/", payload, format="json")

        assert response.status_code == status.HTTP_200_OK

    def test_returns_message_on_success(self):
        client = _client()
        payload = {
            "client_id": "my-client-id",
            "client_secret": "my-client-secret",
            "auth_endpoint": "https://idp.example.com/auth",
            "token_endpoint": "https://idp.example.com/token",
        }

        with patch("apps.setup.services.TestService.test_oauth_connection"):
            response = client.post("/api/v1/setup/test/oauth/", payload, format="json")

        assert response.data["message"] == "OAuth endpoints are reachable."

    def test_returns_400_on_missing_client_id(self):
        client = _client()
        payload = {
            "client_secret": "secret",
            "auth_endpoint": "https://idp.example.com/auth",
            "token_endpoint": "https://idp.example.com/token",
        }
        response = client.post("/api/v1/setup/test/oauth/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_400_on_missing_token_endpoint(self):
        client = _client()
        payload = {
            "client_id": "cid",
            "client_secret": "secret",
            "auth_endpoint": "https://idp.example.com/auth",
        }
        response = client.post("/api/v1/setup/test/oauth/", payload, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_returns_422_on_connection_failure(self):
        client = _client()
        payload = {
            "client_id": "bad-id",
            "client_secret": "bad-secret",
            "auth_endpoint": "https://unreachable.example.com/auth",
            "token_endpoint": "https://unreachable.example.com/token",
        }

        with patch(
            "apps.setup.services.TestService.test_oauth_connection",
            side_effect=ValidationException("Cannot reach token endpoint"),
        ):
            response = client.post("/api/v1/setup/test/oauth/", payload, format="json")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_returns_400_on_empty_payload(self):
        client = _client()
        response = client.post("/api/v1/setup/test/oauth/", {}, format="json")
        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ---------------------------------------------------------------------------
# GET /api/v1/setup/status/ — setup progress status
# ---------------------------------------------------------------------------


class TestSetupStatusEndpoint:
    def test_returns_200(self):
        client = _client()
        response = client.get("/api/v1/setup/status/")
        assert response.status_code == status.HTTP_200_OK

    def test_idle_status_by_default(self):
        from apps.setup import status as _status

        _status._state["status"] = "idle"
        _status._state["current_step"] = None
        _status._state["steps"] = []
        _status._state["error"] = None

        client = _client()
        response = client.get("/api/v1/setup/status/")
        assert response.data["data"]["status"] == "idle"

    def test_response_includes_steps(self):
        from apps.setup import status as _status

        _status.start()

        client = _client()
        response = client.get("/api/v1/setup/status/")
        assert "steps" in response.data["data"]
        assert isinstance(response.data["data"]["steps"], list)

        _status._state["status"] = "idle"
        _status._state["steps"] = []

    def test_response_has_standard_structure(self):
        client = _client()
        response = client.get("/api/v1/setup/status/")
        assert "success" in response.data
        assert "data" in response.data
        data = response.data["data"]
        assert "status" in data
        assert "current_step" in data
        assert "steps" in data
        assert "error" in data

    def test_status_shows_running_when_in_progress(self):
        from apps.setup import status as _status

        _status._state["status"] = "running"
        _status._state["current_step"] = "database"
        _status._state["steps"] = []
        _status._state["error"] = None

        try:
            client = _client()
            response = client.get("/api/v1/setup/status/")
            assert response.data["data"]["status"] == "running"
        finally:
            _status._state["status"] = "idle"
            _status._state["current_step"] = None

    def test_status_shows_error_when_failed(self):
        from apps.setup import status as _status

        _status._state["status"] = "error"
        _status._state["current_step"] = None
        _status._state["steps"] = []
        _status._state["error"] = "Something went wrong"

        try:
            client = _client()
            response = client.get("/api/v1/setup/status/")
            assert response.data["data"]["status"] == "error"
            assert response.data["data"]["error"] == "Something went wrong"
        finally:
            _status._state["status"] = "idle"
            _status._state["error"] = None


# ---------------------------------------------------------------------------
# POST /api/v1/setup/gen-key/ — Fernet key generation
# ---------------------------------------------------------------------------


class TestSetupGenKeyEndpoint:
    def test_returns_201(self):
        client = _client()
        response = client.post("/api/v1/setup/gen-key/")
        assert response.status_code == status.HTTP_201_CREATED

    def test_returns_key_in_response(self):
        client = _client()
        response = client.post("/api/v1/setup/gen-key/")
        assert "key" in response.data["data"]

    def test_returned_key_is_valid_fernet_key(self):
        from cryptography.fernet import Fernet

        client = _client()
        response = client.post("/api/v1/setup/gen-key/")
        key = response.data["data"]["key"]
        Fernet(key.encode())

    def test_each_call_returns_unique_key(self):
        client = _client()
        r1 = client.post("/api/v1/setup/gen-key/")
        r2 = client.post("/api/v1/setup/gen-key/")
        assert r1.data["data"]["key"] != r2.data["data"]["key"]

    def test_returns_custom_message(self):
        client = _client()
        response = client.post("/api/v1/setup/gen-key/")
        assert response.data["message"] == "Key generated."
