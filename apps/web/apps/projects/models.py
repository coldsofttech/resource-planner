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


class ProjectType(
    CodeModel, NamedModel, DescriptionModel, ActivatableModel, AuditableModel
):
    MODEL_CODE = "PROJTYPE"

    name = models.CharField(max_length=60, db_index=True)
    is_protected = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            unique_constraint(
                app_label="projects", model="projecttype", fields=["name"]
            )
        ]
        permissions = [
            ("import_projecttype", "Can import project types"),
            ("export_projecttype", "Can export project types"),
        ]


class ProjectStatus(CodeModel, NamedModel, ActivatableModel, AuditableModel):
    MODEL_CODE = "PROJSTAT"

    name = models.CharField(max_length=100, db_index=True)

    class Meta:
        ordering = ["name"]
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
