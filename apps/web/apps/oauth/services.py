from django.db import transaction

from apps.configurations.selectors import Infra
from apps.core.crypto import encrypt_value
from apps.core.exceptions import AlreadyExistsException
from apps.core.services import CommandService, ContextService
from apps.oauth.models import OAuth
from apps.oauth.selectors import provider_exists


class BaseOAuthService:
    def _create_provider(
        self,
        *,
        name,
        client_id,
        client_secret,
        auth_endpoint,
        token_endpoint,
        userinfo_endpoint,
        scope,
        created_by=None,
    ):
        if provider_exists(name):
            raise AlreadyExistsException(detail="Provider already exists.")

        secrets_prefix = Infra.get_secrets_prefix()
        safe_name = name.lower().replace(" ", "-")

        encrypted_client_id = encrypt_value(
            client_id,
            f"{secrets_prefix}/oauth/{safe_name}/client-id".lstrip("/"),
        )
        encrypted_client_secret = encrypt_value(
            client_secret,
            f"{secrets_prefix}/oauth/{safe_name}/client-secret".lstrip("/"),
        )

        real_created_by = created_by if getattr(created_by, "pk", None) else None
        data = {
            "name": name,
            "client_id": encrypted_client_id,
            "client_secret": encrypted_client_secret,
            "auth_endpoint": auth_endpoint,
            "token_endpoint": token_endpoint,
            "userinfo_endpoint": userinfo_endpoint,
            "scope": scope,
            "is_active": True,
            "created_by": real_created_by,
        }

        with transaction.atomic():
            provider = OAuth(**data)
            provider.full_clean()
            provider.save()

        return provider


class OAuthService(BaseOAuthService, CommandService):
    def create(
        self,
        *,
        name,
        client_id,
        client_secret,
        auth_endpoint,
        token_endpoint,
        userinfo_endpoint,
        scope,
    ):
        return self._create_provider(
            name=name,
            client_id=client_id,
            client_secret=client_secret,
            auth_endpoint=auth_endpoint,
            token_endpoint=token_endpoint,
            userinfo_endpoint=userinfo_endpoint,
            scope=scope,
            created_by=self.user,
        )

    def update(self, pk, *args, **kwargs):
        raise NotImplementedError

    def delete(self, pk, *args, **kwargs):
        raise NotImplementedError


class AdminOAuthService(BaseOAuthService, ContextService):
    def create(
        self,
        *,
        name,
        client_id,
        client_secret,
        auth_endpoint,
        token_endpoint,
        userinfo_endpoint,
        scope,
    ):
        return self._create_provider(
            name=name,
            client_id=client_id,
            client_secret=client_secret,
            auth_endpoint=auth_endpoint,
            token_endpoint=token_endpoint,
            userinfo_endpoint=userinfo_endpoint,
            scope=scope,
        )
