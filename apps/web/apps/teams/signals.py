import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.teams.models import Team

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Team)
def log_team_save(sender, instance, created, **kwargs):
    action = "Created" if created else "Updated"
    logger.debug("%s team: %s (%s).", action, instance.name, instance.code)


@receiver(post_delete, sender=Team)
def log_team_delete(sender, instance, **kwargs):
    logger.debug("Deleted team: %s (%s).", instance.name, instance.code)
