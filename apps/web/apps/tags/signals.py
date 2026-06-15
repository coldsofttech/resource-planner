import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver

from apps.tags.models import Tag

logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Tag)
def normalise_tag_name(sender, instance, **kwargs):
    """Lowercase the name and ensure it has a # prefix."""
    name = (instance.name or "").strip().lower()
    if name and not name.startswith("#"):
        name = f"#{name}"
    instance.name = name
