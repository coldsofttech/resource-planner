import logging

from django.db.models.signals import post_migrate

from apps.core.apps import BaseAppConfig

logger = logging.getLogger(__name__)


_PROJECT_STATUS_SEEDS = [
    "New",
    "In Progress",
    "On Hold",
    "Completed",
    "Cancelled",
]


def seed_default_programme(sender, **kwargs):
    """Seeds the protected 'Others' programme on every migrate run."""
    from django.db import transaction

    from apps.projects.models import Programme

    with transaction.atomic():
        try:
            Programme.objects.get_or_create(
                name="Others",
                defaults={
                    "description": "Default programme for unclassified projects.",
                    "is_active": True,
                    "is_protected": True,
                },
            )
        except Exception as exc:
            logger.error("Failed to seed default programme: %s", exc)


def seed_project_statuses(sender, **kwargs):
    """Seeds the default project statuses on every migrate run."""
    from django.db import transaction

    from apps.projects.models import ProjectStatus

    with transaction.atomic():
        try:
            for name in _PROJECT_STATUS_SEEDS:
                ProjectStatus.objects.get_or_create(
                    name=name,
                    defaults={"is_active": True},
                )
        except Exception as exc:
            logger.error("Failed to seed project statuses: %s", exc)


class ProjectConfig(BaseAppConfig):
    name = "apps.projects"
    label = "projects"
    verbose_name = "Projects"

    def on_ready(self):
        post_migrate.connect(
            seed_default_programme,
            sender=self,
            dispatch_uid="apps.projects.seed_default_programme",
        )
        post_migrate.connect(
            seed_project_statuses,
            sender=self,
            dispatch_uid="apps.projects.seed_project_statuses",
        )
