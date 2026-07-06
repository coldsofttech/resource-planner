from django.db import models

from apps.core.models import (
    ActivatableModel,
    AuditableModel,
    CodeModel,
    DescriptionModel,
    NamedModel,
    unique_constraint,
)
from apps.resource_plans.constants import PlanType


class Plan(CodeModel, NamedModel, DescriptionModel, ActivatableModel, AuditableModel):
    MODEL_CODE = "RES"

    plan_type = models.CharField(
        max_length=50,
        choices=PlanType.choices,
        db_index=True,
    )
    financial_year = models.ForeignKey(
        "financial_years.FinancialYear",
        on_delete=models.PROTECT,
        related_name="resource_plans",
    )
    is_head = models.BooleanField(default=False, db_index=True)
    cloned_from = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="clones",
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            unique_constraint(
                app_label="resource_plans",
                model="plan",
                fields=["name"],
            )
        ]
