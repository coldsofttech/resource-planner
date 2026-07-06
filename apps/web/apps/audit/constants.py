from __future__ import annotations

from django.db import models


class Action(models.TextChoices):
    CREATE = "create", "Create"
    UPDATE = "update", "Update"
    DELETE = "delete", "Delete"
    ACTIVATE = "activate", "Activate"
    DEACTIVATE = "deactivate", "Deactivate"
    SET_DEFAULT = "set_default", "Set Default"
    RESTORE = "restore", "Restore"
    LOCK = "lock", "Lock"
