from django.db import models

from apps.core.models import (
    ActivatableModel,
    AuditableModel,
    CodeModel,
    DescriptionModel,
    NamedModel,
    unique_constraint,
)


class Programme(
    CodeModel, NamedModel, DescriptionModel, ActivatableModel, AuditableModel
):
    MODEL_CODE = "PROG"

    is_protected = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            unique_constraint(app_label="projects", model="programme", fields=["name"])
        ]
        permissions = [
            ("import_programme", "Can import programmes"),
            ("export_programme", "Can export programmes"),
        ]
