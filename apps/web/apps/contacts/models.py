from django.db import models

from apps.core.models import AuditableModel, CodeModel, NamedModel, unique_constraint


class Contact(CodeModel, NamedModel, AuditableModel):
    MODEL_CODE = "CONT"

    email = models.EmailField(blank=True, db_index=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            unique_constraint(
                app_label="contacts",
                model="contact",
                fields=["name", "email"],
            )
        ]

    def __str__(self) -> str:
        return self.name
