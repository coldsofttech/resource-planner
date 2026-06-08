import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.employment_types.models import EmploymentType

logger = logging.getLogger(__name__)


@receiver(post_save, sender=EmploymentType)
def log_employment_type_save(sender, instance, created, **kwargs):
    action = "Created" if created else "Updated"
    logger.debug("%s employment type: %s (%s).", action, instance, instance.code)


@receiver(post_delete, sender=EmploymentType)
def log_employment_type_delete(sender, instance, **kwargs):
    logger.debug("Deleted employment type: %s (%s).", instance, instance.code)
