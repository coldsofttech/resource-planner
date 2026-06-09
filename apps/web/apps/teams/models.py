from django.db import models

from apps.core.models import (
    ActivatableModel,
    AuditableModel,
    CodeModel,
    DescriptionModel,
    NamedModel,
)


class Team(CodeModel, AuditableModel, NamedModel, DescriptionModel, ActivatableModel):
    MODEL_CODE = "TEAM"

    name = models.CharField(max_length=120, unique=True, db_index=True)

    class Meta:
        ordering = ["name"]
        permissions = [
            ("import_team", "Can import teams"),
            ("export_team", "Can export teams"),
        ]

    def __str__(self) -> str:
        return self.name
