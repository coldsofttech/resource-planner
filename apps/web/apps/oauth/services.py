import urllib.error
import urllib.parse

from django.db import transaction

from apps.configurations.selectors import Infra
from apps.core.crypto import decrypt_value, encrypt_value
from apps.core.exceptions import (
    AlreadyExistsException,
    ServiceUnavailableException,
    ValidationException,
)
from apps.core.services import CommandService, ContextService
from apps.oauth.helpers import exchange_code, fetch_userinfo, parse_userinfo
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


class OAuthFlowService(ContextService):
    """Handles the stateless parts of the OAuth 2.0 authorization code flow."""

    def build_authorize_url(self, *, provider, redirect_uri: str, state: str) -> str:
        client_id = decrypt_value(provider.client_id)
        params = urllib.parse.urlencode(
            {
                "client_id": client_id,
                "redirect_uri": redirect_uri,
                "scope": provider.scope,
                "state": state,
                "response_type": "code",
            }
        )
        return f"{provider.auth_endpoint}?{params}"

    def complete_login(self, *, provider, code: str, redirect_uri: str):
        from apps.users.services import SSOUserService

        client_id = decrypt_value(provider.client_id)
        client_secret = decrypt_value(provider.client_secret)

        try:
            token_data = exchange_code(
                token_endpoint=provider.token_endpoint,
                code=code,
                redirect_uri=redirect_uri,
                client_id=client_id,
                client_secret=client_secret,
            )
        except urllib.error.HTTPError as exc:
            raise ServiceUnavailableException(
                detail=f"Token exchange failed ({exc.code} {exc.reason})."
            ) from exc
        except Exception as exc:
            raise ServiceUnavailableException(
                detail=f"Token exchange error: {exc}"
            ) from exc

        access_token = token_data.get("access_token")
        if not access_token:
            raise ServiceUnavailableException(
                detail="Provider did not return an access token."
            )

        try:
            raw_userinfo = fetch_userinfo(
                userinfo_endpoint=provider.userinfo_endpoint,
                access_token=access_token,
            )
        except Exception as exc:
            raise ServiceUnavailableException(
                detail=f"Failed to fetch user info: {exc}"
            ) from exc

        info = parse_userinfo(raw_userinfo)
        if not info.email:
            raise ValidationException("Provider did not return an email address.")

        user, _ = SSOUserService().get_or_create(
            email=info.email,
            first_name=info.first_name,
            last_name=info.last_name,
            sso_provider=provider,
            sso_uid=info.sso_uid,
        )
        return user
