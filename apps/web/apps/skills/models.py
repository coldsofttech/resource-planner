from django.db import models

from apps.core.models import (
    ActivatableModel,
    AuditableModel,
    CodeModel,
    DescriptionModel,
)


class Skill(CodeModel, AuditableModel, DescriptionModel, ActivatableModel):
    MODEL_CODE = "SKILL"

    skill = models.CharField(max_length=20, unique=True, db_index=True)

    class Meta:
        ordering = ["skill"]
        permissions = [
            ("import_skill", "Can import skills"),
            ("export_skill", "Can export skills"),
        ]

    def __str__(self):
        return self.skill
