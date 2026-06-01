import logging

from django.contrib.auth.models import Permission
from django.db.models.signals import post_delete, post_migrate, post_save
from django.dispatch import receiver

from apps.permissions.defaults import PERMISSION_CATEGORIES
from apps.permissions.models import (
    GroupPermissionCategory,
    PermissionCategory,
    UserPermissionCategory,
)

logger = logging.getLogger(__name__)

EXCLUDED_APP_LABELS = {"admin", "contenttypes", "sessions"}

EXCLUDED_MODEL_PERMISSIONS = {
    ("auth", "permission"),
    ("auth", "group"),
    ("permissions", "permissioncategory"),  # seeded, no user operations
}


def _clear_perm_cache(user) -> None:
    if hasattr(user, "_category_perm_cache"):
        del user._category_perm_cache


@receiver(post_save, sender=GroupPermissionCategory)
@receiver(post_delete, sender=GroupPermissionCategory)
def invalidate_group_permission_cache(sender, instance, **kwargs):
    for user in instance.group.user_set.all():
        _clear_perm_cache(user)


@receiver(post_save, sender=UserPermissionCategory)
@receiver(post_delete, sender=UserPermissionCategory)
def invalidate_user_permission_cache(sender, instance, **kwargs):
    _clear_perm_cache(instance.user)


@receiver(post_migrate)
def prune_system_permissions(sender, **kwargs):
    deleted_label, _ = Permission.objects.filter(
        content_type__app_label__in=EXCLUDED_APP_LABELS
    ).delete()

    deleted_model = 0
    for app_label, model in EXCLUDED_MODEL_PERMISSIONS:
        count, _ = Permission.objects.filter(
            content_type__app_label=app_label,
            content_type__model=model,
        ).delete()
        deleted_model += count

    total = deleted_label + deleted_model
    if total:
        logger.debug("Pruned %d system permission(s).", total)


@receiver(post_migrate)
def seed_permission_categories(sender, **kwargs):
    if sender.name != "apps.permissions":
        return

    for module_def in PERMISSION_CATEGORIES:
        module = module_def["module"]
        for entry in module_def["entries"]:
            cat, _ = PermissionCategory.objects.update_or_create(
                module=module,
                codename=entry["codename"],
                defaults={
                    "name": entry["name"],
                    "order": entry["order"],
                    "label": f"{entry['name']} {module.replace('_', ' ').title()}",
                },
            )

            perms = []
            for p in entry["perms"]:
                app_label, codename = p.split(".", 1)
                try:
                    perms.append(
                        Permission.objects.get(
                            content_type__app_label=app_label,
                            codename=codename,
                        )
                    )
                except Permission.DoesNotExist:
                    logger.warning(
                        "Permission %s not found — skipping for category %s.%s.",
                        p,
                        module,
                        entry["codename"],
                    )

            cat.permissions.set(perms)
            logger.debug(
                "Seeded permission category: %s.%s (%d permission(s)).",
                module,
                entry["codename"],
                len(perms),
            )
