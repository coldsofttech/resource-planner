from datetime import timedelta

from django.utils import timezone

from apps.auth.models import RESET_CODE_EXPIRY_MINUTES, PasswordResetToken
from apps.users.models import User
from apps.users.tests.factories import make_user

_TOKEN_HASH = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"


def make_token(
    user: User | None = None,
    token_hash: str = _TOKEN_HASH,
    minutes_until_expiry: int = RESET_CODE_EXPIRY_MINUTES,
    is_used: bool = False,
    **overrides,
) -> PasswordResetToken:
    if user is None:
        user = make_user()
    defaults: dict = {
        "user": user,
        "email": user.email,
        "token_hash": token_hash,
        "expires_at": timezone.now() + timedelta(minutes=minutes_until_expiry),
        "is_used": is_used,
        **overrides,
    }
    return PasswordResetToken.objects.create(**defaults)
