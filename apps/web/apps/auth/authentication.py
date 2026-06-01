from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class BearerTokenAuthentication(BaseAuthentication):
    """
    Authenticates requests carrying an Authorization: Bearer <key> header.
    Token must exist in UserToken and be active; the owning user must be active.
    Updates last_used_at on every successful authentication.
    """

    keyword = "Bearer"

    def authenticate(self, request):
        auth = request.META.get("HTTP_AUTHORIZATION", "").split()
        if not auth or auth[0].lower() != self.keyword.lower():
            return None
        if len(auth) != 2:
            raise AuthenticationFailed("Invalid token header.")
        return self._authenticate_key(auth[1])

    def _authenticate_key(self, key: str):
        from apps.auth.models import UserToken

        try:
            token = UserToken.objects.select_related("user").get(
                key=key, is_active=True
            )
        except UserToken.DoesNotExist as exc:
            raise AuthenticationFailed("Invalid or expired token.") from exc

        if not token.user.is_active:
            raise AuthenticationFailed("User account is disabled.")

        UserToken.objects.filter(pk=token.pk).update(last_used_at=timezone.now())
        return (token.user, token)

    def authenticate_header(self, request):
        return 'Bearer realm="api"'
