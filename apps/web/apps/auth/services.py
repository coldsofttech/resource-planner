import logging
import re
from datetime import timedelta

from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.utils import timezone
from otpcore import generate_otp, hash_otp

from apps.auth.models import RESET_CODE_EXPIRY_MINUTES
from apps.core.exceptions import (
    AuthFailedException,
    PermissionException,
    ValidationException,
)
from apps.core.services import ContextService
from apps.core.utils import build_email_sender

logger = logging.getLogger(__name__)


def _strip_html(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value).strip()


class AuthService(ContextService):
    def classic_login(self, email: str, password: str):
        """
        Authenticate a user with email/password.

        Superusers always have classic login available regardless of AUTH_MODE.
        Non-superusers require AUTH_MODE=classic.
        """
        from apps.auth.constants import AuthMode
        from apps.configurations.selectors import Auth
        from apps.users.selectors import get_user, is_superuser

        if not is_superuser(email) and Auth.get_auth_mode() != AuthMode.CLASSIC:
            raise ValidationException(
                "Classic login is not enabled. Use your configured identity provider."
            )

        user = authenticate(self.request, username=email, password=password)
        if user is None:
            candidate = get_user(email)
            if candidate is not None and not candidate.is_active:
                raise PermissionException(
                    "Your account has been deactivated. Contact your administrator."
                )
            raise AuthFailedException("Invalid email or password. Please try again.")

        if not user.is_active:
            raise PermissionException(
                "Your account has been deactivated. Contact your administrator."
            )

        auth_login(self.request, user)
        logger.info("User '%s' signed in via classic auth.", email)
        return user

    def get_me(self) -> dict:
        from apps.users.constants import ThemeChoices
        from apps.users.models import UserAvatar, UserProfile

        user = self.user
        profile: UserProfile | None = getattr(user, "profile", None)
        theme = profile.theme if profile else ThemeChoices.LIGHT

        is_sso = bool(profile and profile.sso_uid)
        sso_provider_name: str | None = None
        if is_sso and profile and profile.sso_provider:
            sso_provider_name = getattr(profile.sso_provider, "name", None)

        has_avatar = UserAvatar.objects.filter(user=user).exists()
        avatar_url = "/api/v1/users/me/avatar/" if has_avatar else None

        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "display_name": profile.display_name if profile else "",
            "theme": theme,
            "avatar_url": avatar_url,
            "is_sso": is_sso,
            "sso_provider_name": sso_provider_name,
        }


class UserTokenService(ContextService):
    def create_token(self, user):
        from apps.auth.models import UserToken

        return UserToken.objects.create(user=user, key=UserToken.generate_key())

    def revoke_current_token(self) -> None:
        from apps.auth.models import UserToken

        auth = self.request.META.get("HTTP_AUTHORIZATION", "").split()
        if len(auth) == 2 and auth[0].lower() == "bearer":
            UserToken.objects.filter(key=auth[1]).update(is_active=False)


class RegisterService(ContextService):
    def register(self, *, first_name: str, last_name: str, email: str, password: str):
        from apps.configurations.selectors import Auth
        from apps.users.services import BaseUserService

        if not Auth.is_self_registration_allowed():
            raise PermissionException("Registration is not available.")

        return BaseUserService()._create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
        )


class ForgotPasswordService(ContextService):
    def _generate_token(self, user):
        """Invalidate existing tokens and create a new one. Returns (code, token)."""
        from apps.auth.models import PasswordResetToken

        PasswordResetToken.objects.filter(user=user, is_used=False).update(is_used=True)
        code, code_hash = generate_otp()
        token = PasswordResetToken.objects.create(
            user=user,
            email=user.email,
            token_hash=code_hash,
            expires_at=timezone.now() + timedelta(minutes=RESET_CODE_EXPIRY_MINUTES),
        )
        return code, token

    def _find_token(self, email: str, code: str):
        """Return the matching active token or None."""
        from apps.auth.models import PasswordResetToken

        return (
            PasswordResetToken.objects.filter(
                email=email,
                token_hash=hash_otp(code),
                is_used=False,
                expires_at__gt=timezone.now(),
            )
            .select_related("user")
            .first()
        )

    def request_password_reset(self, email: str) -> None:
        """Send a 6-digit reset code. Raises a validation error for unknown emails."""
        from apps.configurations.selectors import General
        from apps.users.selectors import get_user

        user = get_user(email)
        if user is None or not user.is_active:
            raise ValidationException("No account found for that email address.")

        profile = getattr(user, "profile", None)
        if profile is not None and profile.sso_uid:
            raise ValidationException(
                "Password reset is not available for SSO accounts. "
                "Please sign in through your identity provider."
            )

        # Token creation must succeed — any DB error surfaces as a 500 so it is
        # immediately visible rather than swallowed silently.
        code, _token = self._generate_token(user)

        app_name = _strip_html(General.get_app_name())
        subject = f"[{app_name}] Your password reset code"
        body = (
            f"Your password reset code is: {code}\n\n"
            f"This code expires in 10 minutes.\n\n"
            f"If you did not request a password reset, "
            f"you can safely ignore this email."
        )
        try:
            build_email_sender().send(to=email, subject=subject, body=body)
        except Exception:
            # Log the full traceback so developers can diagnose delivery failures.
            logger.exception("Failed to send password reset email to '%s'.", email)

    def verify_reset_code(self, email: str, code: str) -> bool:
        """Return True if the code is valid and unexpired, without consuming it."""
        return self._find_token(email, code) is not None

    def reset_password(self, email: str, code: str, new_password: str) -> None:
        """Verify the code, reject if same as current, then set the new password."""
        token = self._find_token(email, code)
        if token is None:
            raise ValidationException("Invalid or expired reset code.")

        if token.user.check_password(new_password):
            raise ValidationException(
                "New password must be different from your current password."
            )

        token.is_used = True
        token.save(update_fields=["is_used", "updated_at"])

        user = token.user
        user.set_password(new_password)
        user.save(update_fields=["password"])
        logger.info("Password reset successfully for '%s'.", email)
