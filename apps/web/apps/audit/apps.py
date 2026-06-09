from apps.core.apps import BaseAppConfig


class AuditConfig(BaseAppConfig):
    name = "apps.audit"
    label = "audit"
    verbose_name = "Audit"
