import logging

from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from apps.projects.models import Programme, Project

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Programme)
def log_programme_save(sender, instance, created, **kwargs):
    action = "Created" if created else "Updated"
    logger.debug("%s programme: %s (%s).", action, instance, instance.code)


@receiver(post_delete, sender=Programme)
def log_programme_delete(sender, instance, **kwargs):
    logger.debug("Deleted programme: %s (%s).", instance, instance.code)


@receiver(pre_save, sender=Project)
def set_project_display_name(sender, instance, **kwargs):
    """
    Auto-populate display_name before saving a Project.
    Format: "{programme.name}: {project.name}" if a programme is linked,
    otherwise just "{project.name}".
    """
    if instance.programme_id:
        # Use the already-loaded relation if available, otherwise fetch from DB.
        programme = instance.programme
        if programme is not None:
            instance.display_name = f"{programme.name}: {instance.name}"
        else:
            instance.display_name = instance.name
    else:
        instance.display_name = instance.name
