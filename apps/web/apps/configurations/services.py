import logging

from django.db import transaction

from apps.configurations.defaults import CONFIGURATION_DEFAULTS
from apps.configurations.models import Configuration
from apps.configurations.selectors import Infra
from apps.core.crypto import encrypt_value
from apps.core.exceptions import NotFoundException
from apps.core.services import CommandService, ContextService

logger = logging.getLogger(__name__)


class BaseConfigurationService:
    def _set_config(self, *, config_code, value, created_by=None, updated_by=None):
        if config_code not in CONFIGURATION_DEFAULTS:
            raise NotFoundException(
                resource="Configuration",
                lookup_field="config_code",
                lookup_value=config_code,
            )

        default_meta = CONFIGURATION_DEFAULTS[config_code]

        if default_meta.get("is_secret") and value not in (None, ""):
            secrets_prefix = Infra.get_secrets_prefix()
            secret_name = f"{secrets_prefix}/{config_code}".lstrip("/")
            value = encrypt_value(str(value), secret_name)

        defaults = {
            "label": default_meta["label"],
            "description": default_meta.get("description", ""),
            "value": str(value) if value is not None else "",
            "data_type": default_meta["data_type"],
            "is_secret": default_meta["is_secret"],
            "is_admin": default_meta["is_admin"],
            "module": default_meta["module"],
        }

        with transaction.atomic():
            obj, created = Configuration.objects.update_or_create(
                config_code=config_code,
                defaults=defaults,
            )
            real_created_by = created_by if getattr(created_by, "pk", None) else None
            real_updated_by = updated_by if getattr(updated_by, "pk", None) else None
            if created and real_created_by:
                obj.created_by = real_created_by
                obj.save(update_fields=["created_by"])
            elif not created and real_updated_by:
                obj.updated_by = real_updated_by
                obj.save(update_fields=["updated_by"])

        logger.debug("Configuration '%s' set.", config_code)
        return obj


class AdminConfigurationService(BaseConfigurationService, ContextService):
    def set_config(self, *, config_code, value):
        return self._set_config(
            config_code=config_code,
            value=value,
            created_by=self.user,
            updated_by=self.user,
        )


class ConfigurationService(BaseConfigurationService, CommandService):
    def create(self, *args, **kwargs):
        raise NotImplementedError

    def update(self, pk, *args, **kwargs):
        raise NotImplementedError

    def delete(self, pk, *args, **kwargs):
        raise NotImplementedError
