from django.db import models

from apps.core.models import (
    ActivatableModel,
    AuditableModel,
    CodeModel,
    DefaultableModel,
    unique_constraint,
)


class EmploymentType(CodeModel, AuditableModel, ActivatableModel, DefaultableModel):
    MODEL_CODE = "EMPTYPE"

    name = models.CharField(max_length=100, db_index=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            unique_constraint(
                app_label="employment_types",
                model="employmenttype",
                fields=["name"],
            ),
        ]
        permissions = [
            ("import_employmenttype", "Can import employment types"),
            ("export_employmenttype", "Can export employment types"),
        ]

    def __str__(self) -> str:
        return self.name
