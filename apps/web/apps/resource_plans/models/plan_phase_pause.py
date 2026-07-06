from django.db import models

from apps.core.models import AuditableModel, CodeModel, unique_constraint
from apps.resource_plans.constants import PauseInputMode


class PlanPhasePause(CodeModel, AuditableModel):
    MODEL_CODE = "RESPAUSE"

    phase = models.ForeignKey(
        "resource_plans.PlanPhase",
        on_delete=models.CASCADE,
        related_name="pauses",
    )
    pause_from = models.ForeignKey(
        "sprints.Sprint",
        on_delete=models.PROTECT,
        related_name="phase_pauses_started",
    )
    input_mode = models.CharField(
        max_length=20,
        choices=PauseInputMode.choices,
        db_index=True,
    )
    pause_until_sprint = models.ForeignKey(
        "sprints.Sprint",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="phase_pauses_paused_until",
    )
    pause_sprint_count = models.PositiveIntegerField(null=True, blank=True)
    # Always server-computed before save (from pause_until_sprint or
    # pause_sprint_count, depending on input_mode) — never client-writable.
    resume_sprint = models.ForeignKey(
        "sprints.Sprint",
        on_delete=models.PROTECT,
        related_name="phase_pauses_resumed",
    )
    notes = models.TextField(blank=True, default="")
    # Maintained via recompute_is_beyond_fy() — no automatic hook yet,
    # see #185.
    is_beyond_fy = models.BooleanField(default=False)

    class Meta:
        ordering = ["phase", "pause_from"]
        constraints = [
            unique_constraint(
                app_label="resource_plans",
                model="planphasepause",
                fields=["phase", "pause_from"],
            )
        ]

    def __str__(self) -> str:
        return f"{self.phase} paused from {self.pause_from}"

    def recompute_is_beyond_fy(self) -> None:
        plan_fy_id = (
            self.phase.plan_project_team.plan_project.version.plan.financial_year_id
        )
        beyond = self.resume_sprint.financial_year_id != plan_fy_id
        if beyond != self.is_beyond_fy:
            self.is_beyond_fy = beyond
            self.save(update_fields=["is_beyond_fy"])
