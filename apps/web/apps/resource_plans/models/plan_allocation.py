from decimal import Decimal

from django.db import models

from apps.core.models import CodeModel, TimeStampedModel
from apps.resource_plans.constants import AssignmentType
from apps.users.models import User


class Allocation(CodeModel, TimeStampedModel):
    MODEL_CODE = "RESALLOC"

    allocation_set = models.ForeignKey(
        "resource_plans.AllocationSet",
        on_delete=models.CASCADE,
        related_name="allocations",
    )
    programme = models.ForeignKey(
        "projects.Programme",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="resource_plan_allocations",
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.PROTECT,
        related_name="resource_plan_allocations",
    )
    team = models.ForeignKey(
        "teams.Team",
        on_delete=models.PROTECT,
        related_name="resource_plan_allocations",
    )
    # Exactly one of member / placeholder_engineer is set — a real employee
    # vs. an unfilled placeholder slot.
    member = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="resource_plan_allocations",
    )
    placeholder_engineer = models.ForeignKey(
        "resource_plans.PlaceholderEngineer",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="allocations",
    )
    sprint = models.ForeignKey(
        "sprints.Sprint",
        on_delete=models.PROTECT,
        related_name="resource_plan_allocations",
    )
    phase = models.ForeignKey(
        "resource_plans.PlanPhase",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="allocations",
    )
    assignment = models.ForeignKey(
        "resource_plans.PlanAssignment",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="allocations",
    )
    assignment_type = models.CharField(
        max_length=20,
        choices=AssignmentType.choices,
        db_index=True,
    )
    includes_in_budget = models.BooleanField(default=True)
    engine_days = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    override_days = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    override_notes = models.TextField(blank=True, default="")
    overridden_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["allocation_set", "sprint"]

    @property
    def effective_days(self) -> Decimal:
        if self.override_days is not None:
            return self.override_days
        return self.engine_days

    def __str__(self) -> str:
        return f"{self.allocation_set} — {self.sprint}"
