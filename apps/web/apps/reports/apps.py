import logging

from django.db.models.signals import post_migrate

from apps.core.apps import BaseAppConfig

logger = logging.getLogger(__name__)


def seed_standard_reports(sender, **kwargs):
    """Seeds/updates the standard report catalog rows registered by built-in reports."""
    from django.db import transaction

    from apps.reports.defaults import STANDARD_REPORT_DEFAULTS
    from apps.reports.models import Report

    with transaction.atomic():
        for slug, meta in STANDARD_REPORT_DEFAULTS.items():
            try:
                obj, created = Report.objects.get_or_create(
                    slug=slug,
                    defaults={
                        "name": meta["name"],
                        "description": meta["description"],
                        "category": meta.get("category", ""),
                        "icon": meta.get("icon", "bi-bar-chart"),
                        "sort_order": meta.get("sort_order", 0),
                        "is_active": True,
                    },
                )

                if not created:
                    # Update catalog metadata only; preserve is_active if an
                    # admin has deliberately deactivated the report.
                    obj.name = meta["name"]
                    obj.description = meta["description"]
                    obj.category = meta.get("category", "")
                    obj.icon = meta.get("icon", "bi-bar-chart")
                    obj.sort_order = meta.get("sort_order", 0)
                    obj.save(
                        update_fields=[
                            "name",
                            "description",
                            "category",
                            "icon",
                            "sort_order",
                        ]
                    )
            except Exception as exc:
                logger.error("Failed to seed standard report '%s': %s", slug, exc)


class ReportConfig(BaseAppConfig):
    name = "apps.reports"
    verbose_name = "Reports"

    def on_ready(self):
        post_migrate.connect(
            seed_standard_reports,
            sender=self,
            dispatch_uid="apps.reports.seed_standard_reports",
        )
