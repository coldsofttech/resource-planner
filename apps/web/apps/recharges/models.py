from decimal import Decimal

from django.db import models

from apps.core.models import (
    ActivatableModel,
    AuditableModel,
    CodeModel,
    CreatedAtModel,
    DescriptionModel,
    NamedModel,
    unique_constraint,
)
from apps.projects.models.project_type import ProjectType
from apps.recharges.constants import RechargeType as RechargeTypeChoice
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


class RechargeDetail(AuditableModel, CodeModel):
    MODEL_CODE = "RECDET"

    sprint = models.ForeignKey(
        "sprints.Sprint",
        on_delete=models.CASCADE,
        related_name="recharge_details",
        db_index=True,
    )
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.CASCADE,
        related_name="recharge_details",
        db_index=True,
    )
    assignee = models.ForeignKey(
        "users.UserProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recharge_details",
        db_index=True,
    )
    programme = models.ForeignKey(
        "projects.Programme",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recharge_details",
        db_index=True,
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recharge_details",
        db_index=True,
    )
    label = models.ForeignKey(
        "projects.ProjectLabel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recharge_details",
        db_index=True,
    )
    type = models.CharField(
        max_length=20,
        choices=RechargeTypeChoice.choices,
        default=RechargeTypeChoice.FORECAST,
        db_index=True,
    )
    jira_id = models.CharField(max_length=255, blank=True, default="")
    title = models.CharField(max_length=500, blank=True, default="")
    total_days = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0")
    )
    total_cost = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0")
    )
    import_record = models.ForeignKey(
        "sprints.SprintDataImport",
        on_delete=models.CASCADE,
        related_name="recharge_details",
        db_index=True,
    )

    class Meta:
        ordering = ["sprint", "team", "assignee"]


class Recharge(CreatedAtModel, CodeModel):
    MODEL_CODE = "RECH"

    sprint = models.ForeignKey(
        "sprints.Sprint",
        on_delete=models.CASCADE,
        related_name="recharges",
        db_index=True,
    )
    type = models.CharField(
        max_length=20,
        choices=RechargeTypeChoice.choices,
        default=RechargeTypeChoice.FORECAST,
        db_index=True,
    )
    programme = models.ForeignKey(
        "projects.Programme",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recharges",
        db_index=True,
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recharges",
        db_index=True,
    )
    total_days = models.DecimalField(
        max_digits=10, decimal_places=2, default=Decimal("0")
    )
    total_cost = models.DecimalField(
        max_digits=15, decimal_places=2, default=Decimal("0")
    )
    finance_contacts = models.ManyToManyField(
        "projects.ProjectContact",
        related_name="recharge_finance_set",
        blank=True,
        limit_choices_to={"role": "finance"},
    )
    project_contacts = models.ManyToManyField(
        "projects.ProjectContact",
        related_name="recharge_project_set",
        blank=True,
        limit_choices_to={"role": "project"},
    )

    class Meta:
        ordering = ["sprint", "type", "programme", "project"]
        constraints = [
            unique_constraint(
                app_label="recharges",
                model="recharge",
                fields=["sprint", "type", "programme", "project"],
            )
        ]
