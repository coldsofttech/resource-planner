from django.db import models

from apps.core.models import (
    ActivatableModel,
    AuditableModel,
    CodeModel,
    DefaultableModel,
)


class Role(CodeModel, AuditableModel, DefaultableModel, ActivatableModel):
    MODEL_CODE = "ROLE"

    role = models.CharField(max_length=100, unique=True, db_index=True)
    is_assignable = models.BooleanField(default=False, db_index=True)
    is_leadership = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["role"]
        permissions = [
            ("import_role", "Can import roles"),
            ("export_role", "Can export roles"),
        ]

    def __str__(self):
        return self.role
