import logging

from django.db.models.signals import post_migrate

from apps.core.apps import BaseAppConfig

logger = logging.getLogger(__name__)


def seed_defaults(sender, **kwargs):
    """Seeds default configuration values."""
    from django.db import transaction

    from apps.configurations.constants import DataType, Module
    from apps.configurations.defaults import CONFIGURATION_DEFAULTS
    from apps.configurations.models import Configuration

    with transaction.atomic():
        for code, meta in CONFIGURATION_DEFAULTS.items():
            try:
                obj, created = Configuration.objects.get_or_create(
                    config_code=code,
                    defaults={
                        "label": meta["label"],
                        "value": meta["value"],
                        "description": meta["description"],
                        "data_type": meta.get("data_type", DataType.STRING),
                        "is_secret": meta.get("is_secret", False),
                        "is_admin": meta.get("is_admin", False),
                        "module": meta.get("module", Module.GENERAL),
                    },
                )

                if not created:
                    # Update metadata fields only; preserve user-set/encrypted values.
                    obj.label = meta["label"]
                    obj.description = meta["description"]
                    obj.data_type = meta.get("data_type", DataType.STRING)
                    obj.is_secret = meta.get("is_secret", False)
                    obj.is_admin = meta.get("is_admin", False)
                    obj.module = meta.get("module", Module.GENERAL)
                    obj.save(
                        update_fields=[
                            "label",
                            "description",
                            "data_type",
                            "is_secret",
                            "is_admin",
                            "module",
                        ]
                    )
            except Exception as exc:
                logger.error(
                    "Failed to seed default configurations for %s: %s", code, exc
                )


class ConfigurationConfig(BaseAppConfig):
    name = "apps.configurations"
    label = "configurations"
    verbose_name = "Configurations"

    def on_ready(self):
        post_migrate.connect(
            seed_defaults, sender=self, dispatch_uid="apps.configurations.seed_defaults"
        )
