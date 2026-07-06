import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.products.models import Product

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Product)
def log_product_save(sender, instance, created, **kwargs):
    action = "Created" if created else "Updated"
    logger.debug("%s product: %s (%s).", action, instance.name, instance.code)


@receiver(post_delete, sender=Product)
def log_product_delete(sender, instance, **kwargs):
    logger.debug("Deleted product: %s (%s).", instance.name, instance.code)
