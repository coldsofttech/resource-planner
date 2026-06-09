from apps.oauth.models import OAuth
from apps.users.tests.factories import make_superuser, make_user  # noqa: F401

_PROVIDER_BASE: dict = {
    "client_id": "cid",
    "client_secret": "csecret",
    "auth_endpoint": "https://idp.example.com/auth",
    "token_endpoint": "https://idp.example.com/token",
    "userinfo_endpoint": "https://idp.example.com/userinfo",
    "scope": "openid email",
}


def make_provider(name: str = "Test Provider", **overrides) -> OAuth:
    return OAuth.objects.create(name=name, **{**_PROVIDER_BASE, **overrides})
