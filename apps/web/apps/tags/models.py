from django.db import models

from apps.core.models import AuditableModel, CodeModel, NamedModel, unique_constraint


class Tag(CodeModel, NamedModel, AuditableModel):
    MODEL_CODE = "TAG"

    name = models.CharField(max_length=50, db_index=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            unique_constraint(app_label="tags", model="tag", fields=["name"])
        ]
        permissions = [
            ("export_tag", "Can export tags"),
        ]
