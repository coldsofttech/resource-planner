from django.db import models

from apps.configurations.constants import DataType, Module
from apps.configurations.validators import CONFIG_CODE_VALIDATOR
from apps.core.models import AuditableModel, CodeModel, DescriptionModel


class Configuration(AuditableModel, CodeModel, DescriptionModel):
    """Standard configurations."""

    MODEL_CODE = "CONFIG"

    config_code = models.CharField(
        max_length=50, unique=True, db_index=True, validators=[CONFIG_CODE_VALIDATOR]
    )
    label = models.CharField(max_length=120)
    value = models.CharField(blank=True)
    data_type = models.CharField(
        max_length=10, choices=DataType.choices, default=DataType.STRING
    )
    is_secret = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    module = models.CharField(
        max_length=30, choices=Module.choices, default=Module.GENERAL
    )

    class Meta:
        ordering = ["config_code"]

    def __str__(self):
        if self.is_secret and self.value:
            return f"{self.code} = ••••••••"

        return f"{self.code} = {self.value}"
