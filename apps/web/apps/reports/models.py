from django.db import models

from apps.core.models import (
    ActivatableModel,
    AuditableModel,
    CodeModel,
    DescriptionModel,
    NamedModel,
    unique_constraint,
)
from apps.reports.constants import ReportVisualization, SharePermission
from apps.users.models import User


class Report(CodeModel, NamedModel, DescriptionModel, ActivatableModel, AuditableModel):
    """Catalog entry for a standard (built-in) report.

    Rows are registered by the feature that implements the report (e.g.
    Weekly Wins, Sprint Forecast vs. Actuals) — this app only owns the
    catalog/listing structure, not report execution.
    """

    MODEL_CODE = "RPT"

    slug = models.SlugField(max_length=100, unique=True, db_index=True)
    category = models.CharField(max_length=100, blank=True, default="")
    icon = models.CharField(max_length=50, blank=True, default="bi-bar-chart")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        constraints = [
            unique_constraint(app_label="reports", model="report", fields=["slug"])
        ]


class CustomReport(CodeModel, NamedModel, DescriptionModel, AuditableModel):
    """User-owned custom report backed by the data-source/query-engine
    builder (see `apps.reports.data_sources` and `apps.reports.engine`).

    `data_source` is blank for a freshly created draft — the builder UI
    walks the user through picking a source before `config` becomes
    meaningful. `config` holds the builder state: selected `fields`,
    `filters`, aggregated `values`, and chart `axis`/`legend` — see
    `apps.reports.engine.execute()` for the exact shape consumed.
    """

    MODEL_CODE = "CRPT"

    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="owned_custom_reports"
    )
    data_source = models.CharField(max_length=50, blank=True, default="")
    visualization = models.CharField(
        max_length=20,
        choices=ReportVisualization.CHOICES,
        default=ReportVisualization.TABLE,
    )
    config = models.JSONField(default=dict, blank=True)
    is_shared = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-updated_at"]

    def is_owner(self, user: User) -> bool:
        return bool(user and user.is_authenticated and self.owner_id == user.id)

    def can_view(self, user: User) -> bool:
        if self.is_owner(user) or getattr(user, "is_staff", False):
            return True
        if self.is_shared:
            return True
        return self.shares.filter(user=user).exists()

    def can_edit(self, user: User) -> bool:
        if self.is_owner(user) or getattr(user, "is_staff", False):
            return True
        return self.shares.filter(user=user, permission=SharePermission.EDIT).exists()


class CustomReportShare(AuditableModel):
    """Grants a specific user view/edit access to a `CustomReport` that is
    not owned by them. Independent of `CustomReport.is_shared`, which is a
    coarse "visible to every authenticated user" flag."""

    report = models.ForeignKey(
        CustomReport, on_delete=models.CASCADE, related_name="shares"
    )
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="custom_report_shares"
    )
    permission = models.CharField(
        max_length=10, choices=SharePermission.CHOICES, default=SharePermission.VIEW
    )

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            unique_constraint(
                app_label="reports",
                model="customreportshare",
                fields=["report", "user"],
            )
        ]

    def __str__(self) -> str:
        return f"{self.report} — {self.user} ({self.permission})"


class DemandCapacityReportConfig(CodeModel, AuditableModel):
    """Maps a Programme to a display category for the Demand vs. Capacity
    standard report, scoped to a single Resource Plan version.

    A programme may only belong to one category within a given plan version
    (enforced below) — this keeps the report's category rows unambiguous.
    """

    MODEL_CODE = "DVCCFG"

    plan = models.ForeignKey(
        "resource_plans.Plan",
        on_delete=models.CASCADE,
        related_name="demand_capacity_configs",
    )
    plan_version = models.ForeignKey(
        "resource_plans.PlanVersion",
        on_delete=models.CASCADE,
        related_name="demand_capacity_configs",
    )
    programme = models.ForeignKey(
        "projects.Programme",
        on_delete=models.CASCADE,
        related_name="demand_capacity_configs",
    )
    category = models.CharField(max_length=100, db_index=True)

    class Meta:
        ordering = ["plan_version", "category", "programme"]
        constraints = [
            unique_constraint(
                app_label="reports",
                model="demandcapacityreportconfig",
                fields=["plan_version", "programme"],
            )
        ]

    def __str__(self) -> str:
        return f"{self.plan_version} — {self.programme} — {self.category}"


class KPIEstimateAccuracyConfig(CodeModel, AuditableModel):
    """Records an exception comment against a completed project for a given
    month on the KPI Report — Estimate % Accuracy standard report.

    A project may only have one comment per month (enforced below); the
    presence of a comment reclassifies that project's accuracy band as
    "Exception" regardless of its computed % accuracy.
    """

    MODEL_CODE = "KPICFG"

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="kpi_estimate_accuracy_configs",
    )
    month = models.CharField(max_length=7, db_index=True)
    comment = models.TextField()

    class Meta:
        ordering = ["month", "project__name"]
        constraints = [
            unique_constraint(
                app_label="reports",
                model="kpiestimateaccuracyconfig",
                fields=["project", "month"],
            )
        ]

    def __str__(self) -> str:
        return f"{self.project} — {self.month}"
