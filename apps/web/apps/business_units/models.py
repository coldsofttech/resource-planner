from django.db import models

from apps.core.models import (
    ActivatableModel,
    AuditableModel,
    CodeModel,
    NamedModel,
)


class BusinessUnit(CodeModel, AuditableModel, NamedModel, ActivatableModel):
    MODEL_CODE = "BU"

    name = models.CharField(max_length=255, unique=True, db_index=True)
    short_name = models.CharField(max_length=10, db_index=True)

    class Meta:
        ordering = ["name"]
        permissions = [
            ("import_businessunit", "Can import business units"),
            ("export_businessunit", "Can export business units"),
        ]

    def __str__(self) -> str:
        return self.name
