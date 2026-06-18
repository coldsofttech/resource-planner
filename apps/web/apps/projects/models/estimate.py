from django.conf import settings
from django.db import models

from apps.core.models import (
    ActivatableModel,
    AuditableModel,
    CodeModel,
    unique_constraint,
)
from apps.projects.constants import (
    ProjectEstimateAction,
    ProjectEstimateStatus,
    ProjectSize,
)
from apps.users.models import User

from .project import Project


class ProjectEstimate(CodeModel, ActivatableModel, AuditableModel):
    MODEL_CODE = "PROJEST"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="estimates",
        db_index=True,
    )
    version = models.PositiveIntegerField(db_index=True)
    estimate_link = models.URLField(max_length=500, blank=True, default="")
    shared_by = models.ManyToManyField(
        User,
        related_name="shared_project_estimates",
        blank=True,
    )
    reviewed_by = models.ManyToManyField(
        User,
        related_name="reviewed_project_estimates",
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=ProjectEstimateStatus.choices,
        default=ProjectEstimateStatus.DRAFT,
        db_index=True,
    )
    estimate_days = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    contingency_percentage = models.DecimalField(
        max_digits=5, decimal_places=2, default=0
    )
    day_rate = models.PositiveIntegerField(default=0)
    approval_email_sent = models.BooleanField(default=False, db_index=True)

    @property
    def version_display(self) -> str:
        return f"v{self.version}"

    @property
    def total_cost(self) -> float:
        base = float(self.estimate_days) * float(self.day_rate)
        contingency = base * float(self.contingency_percentage) / 100
        return round(base + contingency, 2)

    @property
    def size(self) -> str:
        from apps.configurations.selectors import Project as ProjectConfig

        cost = self.total_cost
        if cost <= ProjectConfig.get_size_xs_max_amount():
            return ProjectSize.XS  # type: ignore[return-value]
        if cost <= ProjectConfig.get_size_s_max_amount():
            return ProjectSize.S  # type: ignore[return-value]
        if cost <= ProjectConfig.get_size_m_max_amount():
            return ProjectSize.M  # type: ignore[return-value]
        if cost <= ProjectConfig.get_size_l_max_amount():
            return ProjectSize.L  # type: ignore[return-value]
        return ProjectSize.XL  # type: ignore[return-value]

    class Meta:
        ordering = ["project", "-version"]
        constraints = [
            unique_constraint(
                app_label="projects",
                model="projectestimate",
                fields=["project", "version"],
            )
        ]
        permissions = [
            ("export_projectestimate", "Can export project estimates"),
        ]


class ProjectEstimateStatusHistory(models.Model):
    estimate = models.ForeignKey(
        ProjectEstimate,
        on_delete=models.CASCADE,
        related_name="status_history",
        db_index=True,
    )
    action = models.CharField(
        max_length=20,
        choices=ProjectEstimateAction.choices,
        db_index=True,
    )
    previous_status = models.CharField(
        max_length=20,
        choices=ProjectEstimateStatus.choices,
        null=True,
        blank=True,
    )
    new_status = models.CharField(
        max_length=20,
        choices=ProjectEstimateStatus.choices,
    )
    note = models.TextField(blank=True, default="")
    changed_on = models.DateTimeField(auto_now_add=True, db_index=True)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="project_estimate_status_changes",
    )

    class Meta:
        ordering = ["-changed_on"]
