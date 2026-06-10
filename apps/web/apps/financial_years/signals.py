import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.financial_years.models import FinancialYear

logger = logging.getLogger(__name__)


@receiver(post_save, sender=FinancialYear)
def log_financial_year_save(sender, instance, created, **kwargs):
    action = "Created" if created else "Updated"
    logger.debug("%s financial year: %s (%s).", action, instance, instance.code)


@receiver(post_delete, sender=FinancialYear)
def log_financial_year_delete(sender, instance, **kwargs):
    logger.debug("Deleted financial year: %s (%s).", instance, instance.code)
