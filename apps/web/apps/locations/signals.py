import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.locations.models import Location

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Location)
def log_location_save(sender, instance, created, **kwargs):
    action = "Created" if created else "Updated"
    logger.debug("%s location: %s (%s).", action, instance, instance.code)


@receiver(post_delete, sender=Location)
def log_location_delete(sender, instance, **kwargs):
    logger.debug("Deleted location: %s (%s).", instance, instance.code)
