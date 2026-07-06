from decimal import Decimal

from django.db import models

from apps.core.models import AuditableModel, CodeModel, unique_constraint
from apps.resource_plans.constants import AllocationType, Basis, Confidence, Priority


class PlanVersionProject(CodeModel, AuditableModel):
    MODEL_CODE = "RESVERP"

    version = models.ForeignKey(
        "resource_plans.PlanVersion",
        on_delete=models.PROTECT,
        related_name="projects",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.PROTECT,
        related_name="resource_plan_versions",
    )
    basis = models.CharField(
        max_length=20,
        choices=Basis.choices,
        db_index=True,
    )
    basis_amount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    basis_synced_at = models.DateTimeField(null=True, blank=True)
    snapshotted_budget = models.ForeignKey(
        "projects.ProjectBudget",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resource_plan_versions",
    )
    snapshotted_estimate = models.ForeignKey(
        "projects.ProjectEstimate",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resource_plan_versions",
    )
    days_required = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    priority_snapshot = models.CharField(
        max_length=20,
        choices=Priority.choices,
        null=True,
        blank=True,
    )
    priority_override = models.CharField(
        max_length=20,
        choices=Priority.choices,
        null=True,
        blank=True,
    )
    confidence_snapshot = models.CharField(
        max_length=20,
        choices=Confidence.choices,
        null=True,
        blank=True,
    )
    confidence_override = models.CharField(
        max_length=20,
        choices=Confidence.choices,
        null=True,
        blank=True,
    )
    start_sprint = models.ForeignKey(
        "sprints.Sprint",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resource_plan_versions_started",
    )
    end_sprint = models.ForeignKey(
        "sprints.Sprint",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resource_plan_versions_ended",
    )
    dates_strict = models.BooleanField(default=False)
    # Stored/recomputed flags — maintained via recompute_flags(). No
    # automatic hook wired to PlanVersionTeamService yet, see #185.
    is_over_threshold = models.BooleanField(default=False)
    is_under_threshold = models.BooleanField(default=False)
    is_team_budget_mismatch = models.BooleanField(default=False)
    is_percent_incomplete = models.BooleanField(default=False)

    @property
    def effective_priority(self) -> str | None:
        return self.priority_override or self.priority_snapshot

    @property
    def effective_confidence(self) -> str | None:
        return self.confidence_override or self.confidence_snapshot

    def recompute_flags(self) -> None:
        from apps.configurations.selectors import Sprint as SprintConfig

        teams = list(self.teams.all())
        total_allocated_days = sum((t.allocated_days for t in teams), Decimal("0"))

        if self.basis == Basis.BUDGET and self.basis_amount:
            day_rate = Decimal(SprintConfig.get_sprint_point_price())
            required_days = self.basis_amount / day_rate if day_rate else Decimal("0")
        else:
            required_days = self.days_required

        percent_teams = [
            t for t in teams if t.allocation_type == AllocationType.PERCENT
        ]
        if percent_teams:
            percent_total = sum(
                (t.allocation_percentage or Decimal("0")) for t in percent_teams
            )
            self.is_percent_incomplete = abs(percent_total - Decimal("100")) > Decimal(
                "0.01"
            )
        else:
            self.is_percent_incomplete = False

        threshold = self.version.threshold_percentage or Decimal("0")
        if required_days:
            diff_pct = abs(total_allocated_days - required_days) / required_days * 100
            self.is_over_threshold = (
                total_allocated_days > required_days and diff_pct > threshold
            )
            self.is_under_threshold = (
                total_allocated_days < required_days and diff_pct > threshold
            )
        else:
            self.is_over_threshold = False
            self.is_under_threshold = False

        self.is_team_budget_mismatch = self.is_over_threshold or self.is_under_threshold

        self.save(
            update_fields=[
                "is_over_threshold",
                "is_under_threshold",
                "is_team_budget_mismatch",
                "is_percent_incomplete",
            ]
        )

    class Meta:
        ordering = ["version", "project"]
        constraints = [
            unique_constraint(
                app_label="resource_plans",
                model="planversionproject",
                fields=["version", "project"],
            )
        ]

    def __str__(self) -> str:
        return f"{self.version} — {self.project}"
