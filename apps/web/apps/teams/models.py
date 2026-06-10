from django.db import models

from apps.core.models import (
    ActivatableModel,
    AuditableModel,
    CodeModel,
    DescriptionModel,
    NamedModel,
    unique_constraint,
)
from apps.teams.constants import AssignmentAction
from apps.users.models import User


class Team(CodeModel, AuditableModel, NamedModel, DescriptionModel, ActivatableModel):
    MODEL_CODE = "TEAM"

    name = models.CharField(max_length=120, unique=True, db_index=True)

    class Meta:
        ordering = ["name"]
        permissions = [
            ("import_team", "Can import teams"),
            ("export_team", "Can export teams"),
        ]

    def __str__(self) -> str:
        return self.name


class Assignment(AuditableModel):
    team = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name="assignments",
        db_index=True,
    )
    member = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="team_assignments",
        db_index=True,
    )
    note = models.TextField(blank=True, default="")

    class Meta:
        constraints = [
            unique_constraint(
                app_label="teams",
                model="assignment",
                fields=["member", "team"],
            ),
        ]
        permissions = [
            ("assign_team", "Can assign members to teams"),
            ("unassign_team", "Can unassign members from teams"),
        ]

    def __str__(self) -> str:
        return f"{self.member_id} → {self.team}"


class AssignmentHistory(models.Model):
    member = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="team_assignment_history",
        db_index=True,
    )
    from_team = models.ForeignKey(
        Team,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assignment_history_from",
    )
    to_team = models.ForeignKey(
        Team,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assignment_history_to",
    )
    moved_on = models.DateTimeField(auto_now_add=True, db_index=True)
    action = models.CharField(
        max_length=10,
        choices=AssignmentAction.choices,
        db_index=True,
    )
    actor = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="team_assignment_actions",
    )

    class Meta:
        ordering = ["-moved_on"]

    def __str__(self) -> str:
        return f"{self.action} {self.member_id} on {self.moved_on}"
