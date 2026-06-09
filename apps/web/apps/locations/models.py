from django.db import models

from apps.core.models import (
    ActivatableModel,
    AuditableModel,
    CodeModel,
    DefaultableModel,
    unique_constraint,
)


class Location(CodeModel, AuditableModel, ActivatableModel, DefaultableModel):
    MODEL_CODE = "LOC"

    city = models.CharField(max_length=100, db_index=True)
    country = models.CharField(max_length=100, db_index=True)

    class Meta:
        ordering = ["country", "city"]
        constraints = [
            unique_constraint(
                app_label="locations",
                model="location",
                fields=["city", "country"],
            ),
        ]
        permissions = [
            ("import_location", "Can import locations"),
            ("export_location", "Can export locations"),
        ]

    def __str__(self):
        return f"{self.city}, {self.country}"
