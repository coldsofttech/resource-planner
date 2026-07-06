from django.db import models

from apps.core.models import AuditableModel, CodeModel
from apps.resource_plans.constants import AssignmentType, SnapshotStatus


class Snapshot(CodeModel, AuditableModel):
    """Point-in-time denormalized capture of a plan version's active
    allocation set — generated asynchronously (see engine/snapshot.py),
    polled via status like EngineJob."""

    MODEL_CODE = "RESSNAP"

    plan = models.ForeignKey(
        "resource_plans.Plan",
        on_delete=models.CASCADE,
        related_name="snapshots",
    )
    version = models.ForeignKey(
        "resource_plans.PlanVersion",
        on_delete=models.CASCADE,
        related_name="snapshots",
    )
    label = models.CharField(max_length=255)
    notes = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=SnapshotStatus.choices,
        default=SnapshotStatus.PENDING,
        db_index=True,
    )
    total_allocation_days = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    total_members = models.PositiveIntegerField(default=0)
    total_projects = models.PositiveIntegerField(default=0)
    total_sprints = models.PositiveIntegerField(default=0)
    initiated_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_milliseconds = models.PositiveIntegerField(null=True, blank=True)
    error_log = models.JSONField(default=list, blank=True)

    class Meta:
        ordering = ["-initiated_at"]

    def __str__(self) -> str:
        return f"{self.label} ({self.status})"


class SnapshotAllocation(models.Model):
    """One denormalized allocation row within a Snapshot — bulk-inserted,
    no FK references beyond `snapshot`, no code/audit fields (nothing
    addresses these rows individually; see Snapshot for the parent record
    that is polled/audited)."""

    snapshot = models.ForeignKey(
        Snapshot,
        on_delete=models.CASCADE,
        related_name="allocations",
        db_index=True,
    )
    sprint_number = models.PositiveIntegerField(db_index=True)
    sprint_name = models.CharField(max_length=100)
    member_name = models.CharField(max_length=255, db_index=True)
    team_name = models.CharField(max_length=100)
    project_name = models.CharField(max_length=255)
    programme_name = models.CharField(max_length=255, blank=True, default="")
    phase_name = models.CharField(max_length=255, blank=True, default="")
    assignment_type = models.CharField(max_length=20, choices=AssignmentType.choices)
    includes_in_budget = models.BooleanField(default=True)
    days = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_override = models.BooleanField(default=False)
    is_placeholder = models.BooleanField(default=False)

    class Meta:
        ordering = ["sprint_number", "member_name"]

    def __str__(self) -> str:
        return f"{self.snapshot} — {self.sprint_name} — {self.member_name}"


class SnapshotCapacity(models.Model):
    """One denormalized member-capacity row within a Snapshot — same
    bulk-insert, FK-less-beyond-parent shape as SnapshotAllocation."""

    snapshot = models.ForeignKey(
        Snapshot,
        on_delete=models.CASCADE,
        related_name="capacities",
        db_index=True,
    )
    sprint_number = models.PositiveIntegerField(db_index=True)
    sprint_name = models.CharField(max_length=100)
    member_name = models.CharField(max_length=255, db_index=True)
    team_name = models.CharField(max_length=100)
    working_days = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    holiday_days = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    leave_days = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    placeholder_leave_days = models.DecimalField(
        max_digits=10, decimal_places=2, default=0
    )
    net_capacity = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ["sprint_number", "member_name"]

    def __str__(self) -> str:
        return f"{self.snapshot} — {self.sprint_name} — {self.member_name}"
