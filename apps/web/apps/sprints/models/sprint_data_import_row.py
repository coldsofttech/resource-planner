from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from django.db import models

from apps.core.models import AuditableModel, CodeModel
from apps.sprints.models.sprint_data_import import SprintDataImport


class SprintDataImportRow(CodeModel, AuditableModel):
    MODEL_CODE = "SPTIMPRW"

    import_record = models.ForeignKey(
        SprintDataImport,
        on_delete=models.CASCADE,
        related_name="rows",
        db_index=True,
    )

    # ── CSV-imported fields (write-once at import time, never mutated) ────────
    story_type = models.CharField(max_length=255, blank=True, default="")
    jira_id = models.CharField(max_length=255, blank=True, default="")
    title = models.CharField(max_length=500, blank=True, default="")
    assignee = models.CharField(max_length=255, blank=True, default="")
    efforts = models.CharField(max_length=100, blank=True, default="")
    sprint = models.CharField(max_length=255, blank=True, default="")
    label = models.CharField(max_length=255, blank=True, default="")
    mapping = models.CharField(max_length=255, blank=True, default="")

    # FK lookups resolved from CSV plain-text values at import time
    assignee_code = models.ForeignKey(
        "users.UserProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sprint_import_rows_as_assignee",
        db_index=True,
    )
    label_code = models.ForeignKey(
        "projects.ProjectLabel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sprint_import_rows",
        db_index=True,
    )
    mapping_code = models.ForeignKey(
        "recharges.RechargeType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sprint_import_rows",
        db_index=True,
    )
    sprint_code = models.ForeignKey(
        "sprints.Sprint",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="import_rows",
        db_index=True,
    )

    # ── Override fields (NULL = no override; set on manual add or edit) ───────
    story_type_override = models.CharField(
        max_length=255, blank=True, null=True, default=None
    )
    jira_id_override = models.CharField(
        max_length=255, blank=True, null=True, default=None
    )
    title_override = models.CharField(
        max_length=500, blank=True, null=True, default=None
    )
    assignee_override = models.CharField(
        max_length=255, blank=True, null=True, default=None
    )
    efforts_override = models.CharField(
        max_length=100, blank=True, null=True, default=None
    )
    sprint_override = models.CharField(
        max_length=255, blank=True, null=True, default=None
    )
    label_override = models.CharField(
        max_length=255, blank=True, null=True, default=None
    )
    mapping_override = models.CharField(
        max_length=255, blank=True, null=True, default=None
    )

    # FK overrides resolved when override text is set
    assignee_code_override = models.ForeignKey(
        "users.UserProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sprint_import_rows_as_assignee_override",
        db_index=True,
    )
    label_code_override = models.ForeignKey(
        "projects.ProjectLabel",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sprint_import_rows_label_override",
        db_index=True,
    )
    mapping_code_override = models.ForeignKey(
        "recharges.RechargeType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sprint_import_rows_mapping_override",
        db_index=True,
    )
    sprint_code_override = models.ForeignKey(
        "sprints.Sprint",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="import_rows_override",
        db_index=True,
    )

    is_manually_added = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["pk"]

    def __str__(self) -> str:
        return f"{self.import_record} — {self.jira_id or self.code}"

    # ── Effective properties (override takes precedence over CSV value) ────────

    @property
    def effective_story_type(self) -> str:
        return (
            self.story_type_override
            if self.story_type_override is not None
            else self.story_type
        )

    @property
    def effective_jira_id(self) -> str:
        return (
            self.jira_id_override if self.jira_id_override is not None else self.jira_id
        )

    @property
    def effective_title(self) -> str:
        return self.title_override if self.title_override is not None else self.title

    @property
    def effective_assignee(self) -> str:
        return (
            self.assignee_override
            if self.assignee_override is not None
            else self.assignee
        )

    @property
    def effective_efforts(self) -> str:
        return (
            self.efforts_override if self.efforts_override is not None else self.efforts
        )

    @property
    def effective_sprint(self) -> str:
        return self.sprint_override if self.sprint_override is not None else self.sprint

    @property
    def effective_label(self) -> str:
        return self.label_override if self.label_override is not None else self.label

    @property
    def effective_mapping(self) -> str:
        return (
            self.mapping_override if self.mapping_override is not None else self.mapping
        )

    @property
    def effective_assignee_code(self):
        if self.assignee_override is not None:
            return self.assignee_code_override
        return self.assignee_code

    @property
    def effective_sprint_code(self):
        if self.sprint_override is not None:
            return self.sprint_code_override
        return self.sprint_code

    @property
    def effective_label_code(self):
        if self.label_override is not None:
            return self.label_code_override
        return self.label_code

    @property
    def effective_mapping_code(self):
        if self.mapping_override is not None:
            return self.mapping_code_override
        return self.mapping_code

    @property
    def days(self) -> Decimal:
        try:
            efforts_val = Decimal(str(self.effective_efforts))
        except Exception:
            return Decimal("0")

        if efforts_val <= 0:
            return Decimal("0")

        from apps.configurations.selectors import Sprint as SprintConfig

        hours_per_day = SprintConfig.get_hours_per_day()
        if hours_per_day <= 0:
            return Decimal("0")

        per_day = Decimal(str(hours_per_day * 3_600))
        return (efforts_val / per_day).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
