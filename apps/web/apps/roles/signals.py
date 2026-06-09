import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.roles.models import Role

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Role)
def log_role_save(sender, instance, created, **kwargs):
    action = "Created" if created else "Updated"
    logger.debug("%s role: %s (%s).", action, instance, instance.code)


@receiver(post_delete, sender=Role)
def log_role_delete(sender, instance, **kwargs):
    logger.debug("Deleted role: %s (%s).", instance, instance.code)
