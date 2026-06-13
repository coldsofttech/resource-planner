import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.projects.models import Programme

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Programme)
def log_programme_save(sender, instance, created, **kwargs):
    action = "Created" if created else "Updated"
    logger.debug("%s programme: %s (%s).", action, instance, instance.code)


@receiver(post_delete, sender=Programme)
def log_programme_delete(sender, instance, **kwargs):
    logger.debug("Deleted programme: %s (%s).", instance, instance.code)
