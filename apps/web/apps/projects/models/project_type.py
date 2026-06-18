from django.db import models

from apps.core.models import (
    ActivatableModel,
    AuditableModel,
    CodeModel,
    DescriptionModel,
    NamedModel,
    unique_constraint,
)


class ProjectType(
    CodeModel, NamedModel, DescriptionModel, ActivatableModel, AuditableModel
):
    MODEL_CODE = "PROJTYPE"

    name = models.CharField(max_length=60, db_index=True)
    is_protected = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            unique_constraint(
                app_label="projects", model="projecttype", fields=["name"]
            )
        ]
        permissions = [
            ("import_projecttype", "Can import project types"),
            ("export_projecttype", "Can export project types"),
        ]
