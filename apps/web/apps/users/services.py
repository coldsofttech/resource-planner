import logging

from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from apps.core.exceptions import AlreadyExistsException, ConflictException
from apps.core.services import ContextService
from apps.users.models import User, UserProfile
from apps.users.selectors import (
    get_administrators_group,
    get_guests_group,
    superuser_exists,
    user_exists,
)

logger = logging.getLogger(__name__)


class BaseUserService:
    def _assign_default_group(self, user: User, *, is_admin: bool = False) -> None:
        group = get_administrators_group() if is_admin else get_guests_group()
        if group is not None:
            user.groups.add(group)
        else:
            logger.warning(
                "System group '%s' not found; skipping group assignment for user '%s'.",
                "Administrators" if is_admin else "Guests",
                user.email,
            )

    def _create_user(
        self,
        *,
        first_name,
        last_name,
        email,
        is_superuser=False,
        password=None,
        created_by=None,
    ):
        from apps.auth.constants import AuthMode
        from apps.configurations.selectors import Auth

        if user_exists(email):
            raise AlreadyExistsException(detail="User already exists.")

        if is_superuser and superuser_exists():
            raise ConflictException(detail="An admin user already exists.")

        user_data = {
            "username": email,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
        }

        if is_superuser:
            user = User.objects.create_superuser(**user_data, password=password)
            UserProfile.objects.create(user=user, created_by=created_by)
            self._assign_default_group(user, is_admin=True)
            return user

        auth_mode = Auth.get_auth_mode()
        if auth_mode == AuthMode.CLASSIC:
            user = User.objects.create_user(**user_data, password=password)
            UserProfile.objects.create(user=user, created_by=created_by)
        elif auth_mode == AuthMode.SAML or auth_mode == AuthMode.OAUTH:
            user = User.objects.create_user(**user_data)
            user.set_unusable_password()
            user.save()
            UserProfile.objects.create(user=user, created_by=created_by)

        self._assign_default_group(user, is_admin=False)
        return user

    def _create_sso_user(
        self,
        *,
        first_name,
        last_name,
        email,
        sso_provider,
        sso_uid,
        created_by=None,
    ):
        """Create a new user and link them to an SSO provider."""
        if user_exists(email):
            raise AlreadyExistsException(detail="User already exists.")

        ct = ContentType.objects.get_for_model(sso_provider)

        with transaction.atomic():
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=first_name or "",
                last_name=last_name or "",
            )
            user.set_unusable_password()
            user.save()

            UserProfile.objects.create(
                user=user,
                sso_provider_content_type=ct,
                sso_provider_object_id=sso_provider.pk,
                sso_uid=sso_uid,
                created_by=created_by,
            )
            self._assign_default_group(user, is_admin=False)

        return user

    def _get_or_create_sso_user(
        self,
        *,
        email,
        first_name,
        last_name,
        sso_provider,
        sso_uid,
        created_by=None,
    ):
        """Find or create a user for an SSO login. Returns (user, created)."""
        ct = ContentType.objects.get_for_model(sso_provider)

        # 1. Lookup by SSO UID + provider — fastest path for returning users.
        profile = (
            UserProfile.objects.filter(
                sso_provider_content_type=ct,
                sso_provider_object_id=sso_provider.pk,
                sso_uid=sso_uid,
            )
            .select_related("user")
            .first()
        )
        if profile:
            return profile.user, False

        # 2. Existing user (created by admin) with matching email — link them.
        try:
            user = User.objects.get(email=email)
            profile = user.profile
            profile.sso_provider_content_type = ct
            profile.sso_provider_object_id = sso_provider.pk
            profile.sso_uid = sso_uid
            profile.save()
            return user, False
        except User.DoesNotExist:
            pass

        # 3. Brand-new SSO user.
        user = self._create_sso_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            sso_provider=sso_provider,
            sso_uid=sso_uid,
            created_by=created_by,
        )
        return user, True


class AdminUserService(BaseUserService, ContextService):
    def create(self, *, first_name, last_name, email, password):
        return self._create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_superuser=True,
            password=password,
        )


class SSOUserService(BaseUserService, ContextService):
    def get_or_create(self, *, email, first_name, last_name, sso_provider, sso_uid):
        return self._get_or_create_sso_user(
            email=email,
            first_name=first_name,
            last_name=last_name,
            sso_provider=sso_provider,
            sso_uid=sso_uid,
        )
