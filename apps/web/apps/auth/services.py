import hashlib
import logging
import re
import secrets
from datetime import timedelta

from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib.auth.hashers import check_password
from django.contrib.auth.password_validation import (
    validate_password as _validate_password,
)
from django.core.exceptions import ValidationError as DjangoValidationError
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

        PasswordPolicyService.flag_rotation_if_due(user)

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

    def force_change_password(self, new_password: str) -> None:
        """Set a new password for the current session user without requiring
        their current password — used only when profile.must_change_password
        is set (e.g. overdue password rotation)."""
        user = self.user
        PasswordPolicyService.validate_new_password(new_password, user=user)
        PasswordPolicyService.apply_new_password(user, new_password)
        logger.info("Forced password change completed for '%s'.", user.email)


class UserTokenService(ContextService):
    def create_token(self, user):
        from apps.auth.models import UserToken

        return UserToken.objects.create(user=user, key=UserToken.generate_key())

    def revoke_current_token(self) -> None:
        from apps.auth.models import UserToken

        auth = self.request.META.get("HTTP_AUTHORIZATION", "").split()
        if len(auth) == 2 and auth[0].lower() == "bearer":
            UserToken.objects.filter(key=auth[1]).update(is_active=False)


class PasswordPolicyService:
    """Config-driven password complexity, reuse, and rotation enforcement.

    Applies whenever the target user is a superuser or AUTH_MODE=classic,
    matching the classic-auth-only scope of the PASSWORD_* configurations.
    """

    @staticmethod
    def _applies_to(user) -> bool:
        from apps.auth.constants import AuthMode
        from apps.configurations.selectors import Auth

        if user is None:
            return True
        return bool(user.is_superuser) or Auth.get_auth_mode() == AuthMode.CLASSIC

    @staticmethod
    def validate_new_password(new_password: str, *, user=None) -> None:
        """Raise ValidationException if new_password violates the password policy."""
        from apps.configurations.selectors import PasswordPolicy

        try:
            _validate_password(new_password, user)
        except DjangoValidationError as exc:
            msg = (
                exc.messages[0]
                if exc.messages
                else "Password does not meet requirements."
            )
            raise ValidationException(msg) from exc

        if not PasswordPolicyService._applies_to(user):
            return

        min_length = PasswordPolicy.get_min_length()
        if len(new_password) < min_length:
            raise ValidationException(
                f"Password must be at least {min_length} characters long."
            )
        if PasswordPolicy.require_uppercase() and not re.search(r"[A-Z]", new_password):
            raise ValidationException(
                "Password must contain at least one uppercase letter."
            )
        if PasswordPolicy.require_lowercase() and not re.search(r"[a-z]", new_password):
            raise ValidationException(
                "Password must contain at least one lowercase letter."
            )
        if PasswordPolicy.require_digits() and not re.search(r"[0-9]", new_password):
            raise ValidationException("Password must contain at least one digit.")
        if PasswordPolicy.require_special() and not re.search(
            r"[^A-Za-z0-9]", new_password
        ):
            raise ValidationException(
                "Password must contain at least one special character."
            )

        if user is None or not user.pk:
            return

        if user.has_usable_password() and user.check_password(new_password):
            raise ValidationException(
                "New password must be different from your current password."
            )

        history_count = PasswordPolicy.get_history_count()
        if history_count > 0:
            from apps.auth.models import PasswordHistory

            recent = PasswordHistory.objects.filter(user=user).order_by("-created_at")[
                :history_count
            ]
            for entry in recent:
                if check_password(new_password, entry.password_hash):
                    raise ValidationException(
                        f"New password must not match any of your last "
                        f"{history_count} password(s)."
                    )

    @staticmethod
    def apply_new_password(user, new_password: str) -> None:
        """Set new_password, record history, and clear rotation/must-change flags."""
        from apps.auth.models import PasswordHistory
        from apps.configurations.selectors import PasswordPolicy

        old_hash = user.password if user.has_usable_password() else ""
        user.set_password(new_password)
        user.save(update_fields=["password"])

        history_count = PasswordPolicy.get_history_count()
        if old_hash and history_count > 0:
            PasswordHistory.objects.create(user=user, password_hash=old_hash)
            stale_ids = list(
                PasswordHistory.objects.filter(user=user)
                .order_by("-created_at")
                .values_list("pk", flat=True)[history_count:]
            )
            if stale_ids:
                PasswordHistory.objects.filter(pk__in=stale_ids).delete()

        profile = getattr(user, "profile", None)
        if profile is not None:
            profile.password_last_changed = timezone.now()
            profile.must_change_password = False
            profile.save(
                update_fields=[
                    "password_last_changed",
                    "must_change_password",
                    "updated_at",
                ]
            )

    @staticmethod
    def is_rotation_due(user) -> bool:
        from apps.configurations.selectors import PasswordPolicy

        if not PasswordPolicyService._applies_to(user):
            return False

        rotation_days = PasswordPolicy.get_rotation_days()
        if rotation_days <= 0:
            return False

        profile = getattr(user, "profile", None)
        last_changed = getattr(profile, "password_last_changed", None) or getattr(
            user, "date_joined", None
        )
        if last_changed is None:
            return False

        return timezone.now() - last_changed >= timedelta(days=rotation_days)

    @staticmethod
    def flag_rotation_if_due(user) -> None:
        """Set profile.must_change_password when the configured rotation is overdue."""
        profile = getattr(user, "profile", None)
        if profile is None or profile.must_change_password:
            return

        if PasswordPolicyService.is_rotation_due(user):
            profile.must_change_password = True
            profile.save(update_fields=["must_change_password", "updated_at"])


class RegisterService(ContextService):
    def register(self, *, first_name: str, last_name: str, email: str, password: str):
        from apps.configurations.selectors import Auth
        from apps.users.models import User
        from apps.users.services import BaseUserService

        if not Auth.is_self_registration_allowed():
            raise PermissionException("Registration is not available.")

        transient_user = User(
            username=email, email=email, first_name=first_name, last_name=last_name
        )
        PasswordPolicyService.validate_new_password(password, user=transient_user)

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
        """Verify the code, reject if same/reused, then set the new password."""
        token = self._find_token(email, code)
        if token is None:
            raise ValidationException("Invalid or expired reset code.")

        PasswordPolicyService.validate_new_password(new_password, user=token.user)

        token.is_used = True
        token.save(update_fields=["is_used", "updated_at"])

        PasswordPolicyService.apply_new_password(token.user, new_password)
        logger.info("Password reset successfully for '%s'.", email)


class AdminPasswordResetService:
    """Admin-initiated password reset via tokenized link (not OTP)."""

    @staticmethod
    def _hash_token(raw_token: str) -> str:
        return hashlib.sha256(raw_token.encode()).hexdigest()

    def send_reset_link(self, user) -> None:
        from apps.auth.models import AdminPasswordResetToken
        from apps.configurations.selectors import General, Users

        timeout_minutes = Users.get_password_reset_timeout()

        AdminPasswordResetToken.objects.filter(user=user, is_used=False).update(
            is_used=True
        )

        raw_token = secrets.token_urlsafe(48)
        token_hash = self._hash_token(raw_token)
        AdminPasswordResetToken.objects.create(
            user=user,
            token_hash=token_hash,
            expires_at=timezone.now() + timedelta(minutes=timeout_minutes),
        )

        app_url = General.get_app_url().rstrip("/")
        app_name = _strip_html(General.get_app_name())
        reset_url = f"{app_url}/auth/set-password/?token={raw_token}"

        subject = f"[{app_name}] Set your password"
        body = (
            f"An administrator has requested a password reset for your account.\n\n"
            f"Click the link below to set a new password:\n{reset_url}\n\n"
            f"This link expires in {timeout_minutes} minutes.\n\n"
            f"If you did not expect this email, please contact your administrator."
        )
        try:
            build_email_sender().send(to=user.email, subject=subject, body=body)
        except Exception:
            logger.exception(
                "Failed to send admin password reset email to '%s'.", user.email
            )

    def validate_token(self, raw_token: str):
        """Return the AdminPasswordResetToken for the raw token, or None."""
        from apps.auth.models import AdminPasswordResetToken

        token_hash = self._hash_token(raw_token)
        return (
            AdminPasswordResetToken.objects.filter(
                token_hash=token_hash,
                is_used=False,
                expires_at__gt=timezone.now(),
            )
            .select_related("user")
            .first()
        )

    def complete_reset(self, raw_token: str, new_password: str) -> None:
        token = self.validate_token(raw_token)
        if token is None:
            raise ValidationException("Invalid or expired reset link.")

        user = token.user
        PasswordPolicyService.validate_new_password(new_password, user=user)

        token.is_used = True
        token.save(update_fields=["is_used", "updated_at"])

        PasswordPolicyService.apply_new_password(user, new_password)
        logger.info("Admin-initiated password reset completed for '%s'.", user.email)
