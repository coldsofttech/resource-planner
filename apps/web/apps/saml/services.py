import os

from django.db import transaction

from apps.core.crypto import encrypt_value
from apps.core.exceptions import AlreadyExistsException
from apps.core.services import CommandService, ContextService
from apps.saml.models import SAML
from apps.saml.selectors import provider_exists


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

        data = {
            "name": name,
            "idp_entity_id": idp_entity_id,
            "idp_sso_url": idp_sso_url,
            "idp_x509_cert": encrypted_x509_cert,
            "sp_entity_id": sp_entity_id or "",
            "sp_assertion_url": sp_assertion_url,
            "is_active": True,
            "created_by": created_by,
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
