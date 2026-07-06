from django.db import models

from apps.business_units.models import BusinessUnit
from apps.core.models import (
    ActivatableModel,
    AuditableModel,
    CodeModel,
    NamedModel,
    unique_constraint,
)


class Product(CodeModel, AuditableModel, NamedModel, ActivatableModel):
    MODEL_CODE = "PROD"

    name = models.CharField(max_length=255, db_index=True)
    short_name = models.CharField(max_length=10, db_index=True)
    business_unit = models.ForeignKey(
        BusinessUnit,
        on_delete=models.PROTECT,
        related_name="products",
        db_index=True,
    )

    class Meta:
        ordering = ["business_unit__name", "name"]
        constraints = [
            unique_constraint(
                app_label="products",
                model="product",
                fields=["name", "business_unit"],
            )
        ]
        permissions = [
            ("import_product", "Can import products"),
            ("export_product", "Can export products"),
        ]

    def __str__(self) -> str:
        return self.name
