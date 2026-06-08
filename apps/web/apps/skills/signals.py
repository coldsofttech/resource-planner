import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.skills.models import Skill

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Skill)
def log_skill_save(sender, instance, created, **kwargs):
    action = "Created" if created else "Updated"
    logger.debug("%s skill: %s (%s).", action, instance.skill, instance.code)


@receiver(post_delete, sender=Skill)
def log_skill_delete(sender, instance, **kwargs):
    logger.debug("Deleted skill: %s (%s).", instance.skill, instance.code)
