from django.db import models

from apps.core.models import (
    ActivatableModel,
    AuditableModel,
    CodeModel,
    DescriptionModel,
    NamedModel,
    unique_constraint,
)
from apps.projects.models.project_type import ProjectType
from apps.recharges.validators import RECHARGE_TYPE_VALIDATOR


class RechargeType(
    CodeModel, NamedModel, DescriptionModel, ActivatableModel, AuditableModel
):
    MODEL_CODE = "RECHTY"

    name = models.CharField(
        max_length=50,
        validators=[RECHARGE_TYPE_VALIDATOR],
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            unique_constraint(
                app_label="recharges", model="rechargetype", fields=["name"]
            )
        ]
        permissions = [
            ("import_rechargetype", "Can import recharge types"),
            ("export_rechargetype", "Can export recharge types"),
        ]


class ProjectTypeMapping(AuditableModel):
    project_type = models.ForeignKey(
        ProjectType, on_delete=models.CASCADE, related_name="recharge_type_mappings"
    )
    recharge_type = models.ForeignKey(
        RechargeType, on_delete=models.CASCADE, related_name="project_type_mappings"
    )

    class Meta:
        ordering = ["project_type__name"]
        constraints = [
            unique_constraint(
                app_label="recharges",
                model="projecttypemapping",
                fields=["recharge_type", "project_type"],
            )
        ]
        permissions = [
            ("import_projecttypemapping", "Can import project type mappings"),
            ("export_projecttypemapping", "Can export project type mappings"),
        ]

    def __str__(self):
        return f"{self.project_type} → {self.recharge_type}"
