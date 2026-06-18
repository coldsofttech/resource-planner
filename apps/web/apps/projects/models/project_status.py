from django.db import models

from apps.core.models import (
    ActivatableModel,
    AuditableModel,
    CodeModel,
    NamedModel,
    unique_constraint,
)
from apps.users.models import User


class ProjectStatus(CodeModel, NamedModel, ActivatableModel, AuditableModel):
    MODEL_CODE = "PROJSTAT"

    name = models.CharField(max_length=100, db_index=True)
    sort_order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["sort_order", "name"]
        constraints = [
            unique_constraint(
                app_label="projects", model="projectstatus", fields=["name"]
            )
        ]
        permissions = [
            ("export_projectstatus", "Can export project statuses"),
        ]


class ProjectSubStatus(CodeModel, NamedModel, ActivatableModel, AuditableModel):
    MODEL_CODE = "PROJSUBSTAT"

    name = models.CharField(max_length=100, db_index=True)
    main_status = models.ForeignKey(
        ProjectStatus,
        on_delete=models.CASCADE,
        related_name="sub_statuses",
        db_index=True,
    )
    order = models.PositiveIntegerField(default=0, db_index=True)

    class Meta:
        ordering = ["main_status", "order", "name"]
        constraints = [
            unique_constraint(
                app_label="projects",
                model="projectsubstatus",
                fields=["name", "main_status"],
            ),
            unique_constraint(
                app_label="projects",
                model="projectsubstatus",
                fields=["main_status", "order"],
            ),
        ]
        permissions = [
            ("import_projectsubstatus", "Can import project sub-statuses"),
            ("export_projectsubstatus", "Can export project sub-statuses"),
        ]


class ProjectStatusHistory(models.Model):
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="status_history",
        db_index=True,
    )
    previous_status = models.ForeignKey(
        ProjectStatus,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="history_as_previous_status",
    )
    new_status = models.ForeignKey(
        ProjectStatus,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="history_as_new_status",
    )
    previous_sub_status = models.ForeignKey(
        ProjectSubStatus,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="history_as_previous_sub_status",
    )
    new_sub_status = models.ForeignKey(
        ProjectSubStatus,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="history_as_new_sub_status",
    )
    note = models.TextField(blank=True, default="")
    changed_on = models.DateTimeField(auto_now_add=True, db_index=True)
    changed_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="project_status_changes",
    )

    class Meta:
        ordering = ["-changed_on"]
