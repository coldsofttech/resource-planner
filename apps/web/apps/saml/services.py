import os
import xml.etree.ElementTree as ET  # nosec B405

from django.db import transaction

from apps.core.crypto import decrypt_value, encrypt_value
from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.core.services import CommandService, ContextService
from apps.saml.helpers import first_match
from apps.saml.models import SAML
from apps.saml.selectors import get_provider_by_entity_id, provider_exists
from apps.saml.utils import (
    build_authn_request_redirect_url,
    check_status_success,
    get_attributes,
    get_issuer,
    get_name_id,
    parse_saml_response,
    verify_signature,
)


class BaseSAMLService:
    def _create_provider(
        self,
        *,
        name,
        idp_entity_id,
        idp_sso_url,
        idp_x509_cert,
        sp_entity_id,
        sp_assertion_url,
        created_by=None,
    ):
        if provider_exists(name):
            raise AlreadyExistsException(detail="Provider already exists.")

        secrets_prefix = os.environ.get("SECRETS_PREFIX", "").rstrip("/")
        safe_name = name.lower().replace(" ", "-")

        encrypted_x509_cert = encrypt_value(
            idp_x509_cert,
            f"{secrets_prefix}/saml/{safe_name}/x509-certificate".lstrip("'/"),
        )

        real_created_by = created_by if getattr(created_by, "pk", None) else None

        data = {
            "name": name,
            "idp_entity_id": idp_entity_id,
            "idp_sso_url": idp_sso_url,
            "idp_x509_cert": encrypted_x509_cert,
            "sp_entity_id": sp_entity_id or "",
            "sp_assertion_url": sp_assertion_url,
            "is_active": True,
            "created_by": real_created_by,
        }

        with transaction.atomic():
            provider = SAML(**data)
            provider.full_clean()
            provider.save()

        return provider


class SAMLService(BaseSAMLService, CommandService):
    def create(
        self,
        *,
        name,
        idp_entity_id,
        idp_sso_url,
        idp_x509_cert,
        sp_entity_id,
        sp_assertion_url,
    ):
        return self._create_provider(
            name=name,
            idp_entity_id=idp_entity_id,
            idp_sso_url=idp_sso_url,
            idp_x509_cert=idp_x509_cert,
            sp_entity_id=sp_entity_id,
            sp_assertion_url=sp_assertion_url,
            created_by=self.user,
        )

    def update(self, pk, *args, **kwargs):
        raise NotImplementedError

    def delete(self, pk, *args, **kwargs):
        raise NotImplementedError


class AdminSAMLService(BaseSAMLService, ContextService):
    def create(
        self,
        *,
        name,
        idp_entity_id,
        idp_sso_url,
        idp_x509_cert,
        sp_entity_id,
        sp_assertion_url,
    ):
        return self._create_provider(
            name=name,
            idp_entity_id=idp_entity_id,
            idp_sso_url=idp_sso_url,
            idp_x509_cert=idp_x509_cert,
            sp_entity_id=sp_entity_id,
            sp_assertion_url=sp_assertion_url,
        )


class SAMLFlowService(ContextService):
    """Handles the stateless parts of the SAML 2.0 SSO flow."""

    # Common attribute names used by major IdPs — checked in order.
    _FIRST_NAME_ATTRS = (
        "first_name",
        "givenName",
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname",
    )
    _LAST_NAME_ATTRS = (
        "last_name",
        "lastName",
        "sn",
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname",
    )
    _EMAIL_ATTRS = (
        "email",
        "mail",
        "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
    )

    def build_authorize_url(self, *, provider, relay_state: str = "") -> str:
        acs_url = provider.sp_assertion_url
        sp_entity_id = provider.sp_entity_id or acs_url
        return build_authn_request_redirect_url(
            idp_sso_url=provider.idp_sso_url,
            sp_entity_id=sp_entity_id,
            acs_url=acs_url,
            relay_state=relay_state,
        )

    def complete_login(self, *, saml_response_b64: str):
        root, xml_bytes = self._parse_response(saml_response_b64)
        self._validate_status(root)
        provider = self._resolve_provider(root, xml_bytes)
        email, first_name, last_name, name_id = self._extract_identity(root)

        from apps.users.services import SSOUserService

        user, _ = SSOUserService().get_or_create(
            email=email,
            first_name=first_name,
            last_name=last_name,
            sso_provider=provider,
            sso_uid=name_id,
        )
        return user

    def _parse_response(self, saml_response_b64: str) -> tuple[ET.Element, bytes]:
        try:
            return parse_saml_response(saml_response_b64)
        except Exception as exc:
            raise ValidationException(f"Failed to parse SAMLResponse: {exc}") from exc

    def _validate_status(self, root: ET.Element) -> None:
        if not check_status_success(root):
            raise ValidationException("SAML authentication was not successful.")

    def _resolve_provider(self, root: ET.Element, xml_bytes: bytes):
        issuer = get_issuer(root)
        if not issuer:
            raise ValidationException("SAMLResponse is missing the Issuer element.")

        provider = get_provider_by_entity_id(issuer)
        if provider is None:
            raise NotFoundException(
                resource="SAML provider",
                lookup_field="idp_entity_id",
                lookup_value=issuer,
            )

        idp_cert = decrypt_value(provider.idp_x509_cert)
        if not verify_signature(xml_bytes, idp_cert):
            raise ValidationException("SAMLResponse signature verification failed.")

        return provider

    def _extract_identity(self, root: ET.Element) -> tuple[str, str, str, str]:
        name_id = get_name_id(root)
        if not name_id:
            raise ValidationException("SAMLResponse Assertion is missing NameID.")

        attributes = get_attributes(root)
        email = (
            name_id
            if "@" in name_id
            else (first_match(attributes, self._EMAIL_ATTRS) or name_id)
        )
        first_name = first_match(attributes, self._FIRST_NAME_ATTRS) or ""
        last_name = first_match(attributes, self._LAST_NAME_ATTRS) or ""

        return email, first_name, last_name, name_id
