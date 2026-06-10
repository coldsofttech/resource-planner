from django.db import models

from apps.core.models import AuditableModel, CodeModel, NamedModel, unique_constraint


class Holiday(CodeModel, NamedModel, AuditableModel):
    MODEL_CODE = "HOL"

    # Override NamedModel's max_length=255 to enforce 120-char limit
    name = models.CharField(max_length=120, db_index=True)
    date = models.DateField(db_index=True)
    location = models.ForeignKey(
        "locations.Location",
        on_delete=models.CASCADE,
        related_name="holidays",
        db_index=True,
    )

    class Meta:
        ordering = ["location", "date"]
        constraints = [
            unique_constraint(
                app_label="holidays",
                model="holiday",
                fields=["location", "date"],
            ),
        ]
        permissions = [
            ("import_holiday", "Can import holidays"),
            ("export_holiday", "Can export holidays"),
        ]
