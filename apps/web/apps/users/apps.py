import logging

from django.db.models.signals import post_migrate

from apps.core.apps import BaseAppConfig

logger = logging.getLogger(__name__)


def seed_system_groups(sender, **kwargs):
    """Seeds the Administrators and Guests system groups."""
    from django.contrib.auth.models import Group
    from django.db import transaction

    from apps.users.models import GROUP_ADMINISTRATORS, GROUP_GUESTS, GroupProfile

    system_groups = [
        {
            "name": GROUP_ADMINISTRATORS,
            "description": "Full administrative access to the platform.",
            "is_admin_group": True,
            "is_system": True,
        },
        {
            "name": GROUP_GUESTS,
            "description": "Standard read-only guest access.",
            "is_admin_group": False,
            "is_system": True,
        },
    ]

    with transaction.atomic():
        for spec in system_groups:
            try:
                group, _ = Group.objects.get_or_create(name=spec["name"])
                GroupProfile.objects.get_or_create(
                    group=group,
                    defaults={
                        "description": spec["description"],
                        "is_admin_group": spec["is_admin_group"],
                        "is_system": spec["is_system"],
                    },
                )
            except Exception as exc:
                logger.error("Failed to seed system group '%s': %s", spec["name"], exc)


class UserConfig(BaseAppConfig):
    name = "apps.users"
    label = "users"
    verbose_name = "Users"

    def on_ready(self):
        post_migrate.connect(
            seed_system_groups,
            sender=self,
            dispatch_uid="apps.users.seed_system_groups",
        )
