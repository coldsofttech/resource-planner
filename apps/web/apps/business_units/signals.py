import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.business_units.models import BusinessUnit

logger = logging.getLogger(__name__)


@receiver(post_save, sender=BusinessUnit)
def log_business_unit_save(sender, instance, created, **kwargs):
    action = "Created" if created else "Updated"
    logger.debug("%s business unit: %s (%s).", action, instance.name, instance.code)


@receiver(post_delete, sender=BusinessUnit)
def log_business_unit_delete(sender, instance, **kwargs):
    logger.debug("Deleted business unit: %s (%s).", instance.name, instance.code)
