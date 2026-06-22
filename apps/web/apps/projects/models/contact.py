from django.db import models

from apps.contacts.models import Contact
from apps.core.models import AuditableModel, CodeModel, unique_constraint
from apps.projects.constants import ContactRole
from apps.projects.models.project import Project


class ProjectContact(CodeModel, AuditableModel):
    MODEL_CODE = "PROJCT"

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="contacts",
        db_index=True,
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name="project_contacts",
        db_index=True,
    )
    role = models.CharField(
        max_length=20,
        choices=ContactRole.choices,
        db_index=True,
    )

    class Meta:
        ordering = ["contact__name"]
        constraints = [
            unique_constraint(
                app_label="projects",
                model="projectcontact",
                fields=["project", "contact"],
            )
        ]
