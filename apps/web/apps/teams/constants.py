from __future__ import annotations

from django.db import models


class AssignmentAction(models.TextChoices):
    ASSIGN = "ASSIGN", "Assign"
    UNASSIGN = "UNASSIGN", "Unassign"
    MOVE = "MOVE", "Move"
