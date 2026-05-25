from apps.core.apps import BaseAppConfig


class AuthConfig(BaseAppConfig):
    name = "apps.auth"
    label = "authentication"
    verbose_name = "Authentication"
