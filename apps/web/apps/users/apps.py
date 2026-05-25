from apps.core.apps import BaseAppConfig


class UserConfig(BaseAppConfig):
    name = "apps.users"
    label = "users"
    verbose_name = "Users"
