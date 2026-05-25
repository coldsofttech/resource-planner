from apps.core.exceptions import AlreadyExistsException, ConflictException
from apps.core.services import ContextService
from apps.users.models import User, UserProfile
from apps.users.selectors import superuser_exists, user_exists


class BaseUserService:
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

        return user


class AdminUserService(BaseUserService, ContextService):
    def create(self, *, first_name, last_name, email, password):
        return self._create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            is_superuser=True,
            password=password,
        )
