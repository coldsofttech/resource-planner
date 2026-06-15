from django.conf import settings
from django.db import models

from apps.core.models import (
    ActivatableModel,
    AuditableModel,
    CodeModel,
    CreatedAtModel,
    DefaultableModel,
    DescriptionModel,
    NamedModel,
    unique_constraint,
)
from apps.financial_years.models import FinancialYear
from apps.projects.constants import Confidence, Priority, ProjectEstimateStatus
from apps.tags.models import Tag
from apps.teams.models import Team
from apps.users.models import User


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


class Project(
    CodeModel, NamedModel, DescriptionModel, ActivatableModel, AuditableModel
):
    MODEL_CODE = "PROJ"

    display_name = models.CharField(max_length=255, blank=True, db_index=True)
    project_type = models.ForeignKey(
        ProjectType,
        on_delete=models.PROTECT,
        related_name="projects",
        db_index=True,
    )
    programme = models.ForeignKey(
        Programme,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
        db_index=True,
    )
    status = models.ForeignKey(
        ProjectStatus,
        on_delete=models.PROTECT,
        related_name="projects",
        db_index=True,
    )
    sub_status = models.ForeignKey(
        ProjectSubStatus,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
        db_index=True,
    )
    assigned_team = models.ForeignKey(
        Team,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_projects",
        db_index=True,
    )
    efforts_issued = models.BooleanField(default=False, db_index=True)
    commitment_date = models.DateField(null=True, blank=True)
    run_cost_applies = models.BooleanField(default=False, db_index=True)
    confidence = models.CharField(
        max_length=20,
        choices=Confidence.choices,
        null=True,
        blank=True,
        db_index=True,
    )
    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        null=True,
        blank=True,
        db_index=True,
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["name"]
        constraints = [
            unique_constraint(app_label="projects", model="project", fields=["name"])
        ]
        permissions = [
            ("import_project", "Can import projects"),
            ("export_project", "Can export projects"),
        ]


class ProjectCollaborator(CreatedAtModel):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="collaborators",
        db_index=True,
    )
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="collaborating_projects",
        db_index=True,
    )
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["added_on"]
        constraints = [
            unique_constraint(
                app_label="projects",
                model="projectcollaborator",
                fields=["project", "team"],
            )
        ]


class ProjectLabel(CodeModel, DefaultableModel, AuditableModel):
    MODEL_CODE = "PROJLBL"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="labels",
        db_index=True,
    )
    label = models.CharField(max_length=50, db_index=True)

    class Meta:
        ordering = ["-is_default", "label"]
        constraints = [
            unique_constraint(
                app_label="projects",
                model="projectlabel",
                fields=["project", "label"],
            )
        ]
        permissions = [
            ("import_projectlabel", "Can import project labels"),
            ("export_projectlabel", "Can export project labels"),
        ]


class ProjectTag(CodeModel, AuditableModel):
    MODEL_CODE = "PROJTAG"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tags",
        db_index=True,
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        related_name="project_tags",
        db_index=True,
    )

    class Meta:
        ordering = ["tag__name"]
        constraints = [
            unique_constraint(
                app_label="projects",
                model="projecttag",
                fields=["project", "tag"],
            )
        ]


class ProjectFollower(CodeModel, AuditableModel):
    MODEL_CODE = "PROJFLW"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="followers",
        db_index=True,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="followed_projects",
        db_index=True,
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            unique_constraint(
                app_label="projects",
                model="projectfollower",
                fields=["project", "user"],
            )
        ]


class ProjectCode(CodeModel, AuditableModel):
    MODEL_CODE = "PROJCODE"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="codes",
        db_index=True,
    )
    value = models.CharField(max_length=255, db_index=True)
    note = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            unique_constraint(
                app_label="projects",
                model="projectcode",
                fields=["project"],
            )
        ]


class ProjectCodeHistory(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="code_history",
        db_index=True,
    )
    previous_code = models.ForeignKey(
        ProjectCode,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="history_as_previous_code",
    )
    new_code = models.ForeignKey(
        ProjectCode,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="history_as_new_code",
    )
    note = models.TextField(blank=True, default="")
    changed_on = models.DateTimeField(auto_now_add=True, db_index=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="project_code_changes",
    )

    class Meta:
        ordering = ["-changed_on"]


class ProjectEstimate(CodeModel, ActivatableModel, AuditableModel):
    MODEL_CODE = "PROJEST"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="estimates",
        db_index=True,
    )
    version = models.PositiveIntegerField(db_index=True)
    estimate_link = models.URLField(max_length=500, blank=True, default="")
    shared_by = models.ManyToManyField(
        User,
        related_name="shared_project_estimates",
        blank=True,
    )
    reviewed_by = models.ManyToManyField(
        User,
        related_name="reviewed_project_estimates",
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=ProjectEstimateStatus.choices,
        default=ProjectEstimateStatus.DRAFT,
        db_index=True,
    )
    estimate_days = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    contingency_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    day_rate = models.PositiveIntegerField(default=0)
    approval_email_sent = models.BooleanField(default=False, db_index=True)

    @property
    def version_display(self) -> str:
        return f"v{self.version}"

    @property
    def total_cost(self) -> float:
        base = float(self.estimate_days) * float(self.day_rate)
        contingency = base * float(self.contingency_percentage) / 100
        return round(base + contingency, 2)

    class Meta:
        ordering = ["project", "-version"]
        constraints = [
            unique_constraint(
                app_label="projects",
                model="projectestimate",
                fields=["project", "version"],
            )
        ]
        permissions = [
            ("export_projectestimate", "Can export project estimates"),
        ]


class ProjectEstimateAction(models.TextChoices):
    CREATED = "CREATED", "Created"
    UPDATED = "UPDATED", "Updated"
    APPROVED = "APPROVED", "Approved"
    SUPERSEDED = "SUPERSEDED", "Superseded"


class ProjectEstimateStatusHistory(models.Model):
    estimate = models.ForeignKey(
        ProjectEstimate,
        on_delete=models.CASCADE,
        related_name="status_history",
        db_index=True,
    )
    action = models.CharField(
        max_length=20,
        choices=ProjectEstimateAction.choices,
        db_index=True,
    )
    previous_status = models.CharField(
        max_length=20,
        choices=ProjectEstimateStatus.choices,
        null=True,
        blank=True,
    )
    new_status = models.CharField(
        max_length=20,
        choices=ProjectEstimateStatus.choices,
    )
    note = models.TextField(blank=True, default="")
    changed_on = models.DateTimeField(auto_now_add=True, db_index=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="project_estimate_status_changes",
    )

    class Meta:
        ordering = ["-changed_on"]


class ProjectBudgetAction(models.TextChoices):
    CREATED = "CREATED", "Created"
    UPDATED = "UPDATED", "Updated"


class ProjectBudget(CodeModel, AuditableModel):
    MODEL_CODE = "PROJBGT"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="budgets",
        db_index=True,
    )
    financial_year = models.ForeignKey(
        FinancialYear,
        on_delete=models.PROTECT,
        related_name="project_budgets",
        db_index=True,
    )
    allocated_budget = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    refined_budget = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    estimate_version = models.ForeignKey(
        ProjectEstimate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="budgets",
        db_index=True,
    )
    note = models.TextField(blank=True, default="")

    @property
    def actual_budget(self) -> float:
        val = (
            self.refined_budget
            if self.refined_budget is not None
            else self.allocated_budget
        )
        return float(val)

    @property
    def remaining_budget(self) -> float | None:
        actual = self.actual_budget
        if actual is None:
            return None
        if self.estimate_version is None:
            return actual
        return round(actual - self.estimate_version.total_cost, 2)

    class Meta:
        ordering = ["project", "financial_year__start_date"]
        constraints = [
            unique_constraint(
                app_label="projects",
                model="projectbudget",
                fields=["project", "financial_year"],
            )
        ]
        permissions = [
            ("export_projectbudget", "Can export project budgets"),
        ]


class ProjectBudgetStatusHistory(models.Model):
    budget = models.ForeignKey(
        ProjectBudget,
        on_delete=models.CASCADE,
        related_name="status_history",
        db_index=True,
    )
    action = models.CharField(
        max_length=20,
        choices=ProjectBudgetAction.choices,
        db_index=True,
    )
    previous_allocated_budget = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    previous_refined_budget = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    previous_estimate_version = models.ForeignKey(
        ProjectEstimate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="budget_history_as_previous_estimate",
    )
    previous_total_cost = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    new_allocated_budget = models.DecimalField(max_digits=14, decimal_places=2)
    new_refined_budget = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    new_estimate_version = models.ForeignKey(
        ProjectEstimate,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="budget_history_as_new_estimate",
    )
    new_total_cost = models.DecimalField(
        max_digits=14, decimal_places=2, null=True, blank=True
    )
    note = models.TextField(blank=True, default="")
    changed_on = models.DateTimeField(auto_now_add=True, db_index=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="project_budget_status_changes",
    )

    class Meta:
        ordering = ["-changed_on"]


class ProjectStatusHistory(models.Model):
    project = models.ForeignKey(
        Project,
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
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="project_status_changes",
    )

    class Meta:
        ordering = ["-changed_on"]
