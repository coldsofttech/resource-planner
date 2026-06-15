import logging

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.sprints.models import Sprint

logger = logging.getLogger(__name__)

_SPRINT_CAPACITY_FIELDS = frozenset({"start_date", "end_date", "status", "is_active"})


def _rebuild_sprint(sprint: Sprint, actor=None) -> None:
    try:
        from apps.sprints.engine import SprintCapacityEngine

        SprintCapacityEngine.rebuild_for_sprint(sprint, actor=actor)
    except Exception:
        logger.exception("Capacity rebuild failed for sprint %s.", sprint.code)


@receiver(post_save, sender=Sprint)
def on_sprint_save(sender, instance, created, update_fields, **kwargs):
    if not created and update_fields is not None:
        if not _SPRINT_CAPACITY_FIELDS.intersection(update_fields):
            return
    _rebuild_sprint(instance)


@receiver(post_delete, sender=Sprint)
def on_sprint_delete(sender, instance, **kwargs):
    logger.debug("Deleted sprint: %s (%s).", instance, instance.code)


def _on_holiday_change(sender, instance, **kwargs):
    """Rebuild capacity for any sprint that overlaps this holiday's date."""
    from apps.sprints import selectors

    sprints = selectors.get_sprints_overlapping_date(instance.date)
    for sprint in sprints:
        _rebuild_sprint(sprint)


def _on_leave_change(sender, instance, **kwargs):
    """Rebuild capacity for any sprint overlapping this leave's date range."""
    from apps.sprints import selectors

    sprints = selectors.get_sprints_overlapping_range(
        instance.start_date, instance.end_date
    )
    for sprint in sprints:
        _rebuild_sprint(sprint)


def _on_assignment_change(sender, instance, **kwargs):
    """Rebuild active/future sprints when a team assignment changes."""
    from apps.sprints import selectors

    sprints = selectors.get_active_and_future_sprints()
    for sprint in sprints:
        _rebuild_sprint(sprint)


def _connect_cross_app_signals() -> None:
    from django.apps import apps

    try:
        Holiday = apps.get_model("holidays", "Holiday")
        post_save.connect(_on_holiday_change, sender=Holiday, weak=False)
        post_delete.connect(_on_holiday_change, sender=Holiday, weak=False)
    except LookupError:
        logger.debug("holidays app not available; skipping holiday capacity signals.")

    try:
        Leave = apps.get_model("leaves", "Leave")
        post_save.connect(_on_leave_change, sender=Leave, weak=False)
        post_delete.connect(_on_leave_change, sender=Leave, weak=False)
    except LookupError:
        logger.debug("leaves app not available; skipping leave capacity signals.")

    try:
        Assignment = apps.get_model("teams", "Assignment")
        post_save.connect(_on_assignment_change, sender=Assignment, weak=False)
        post_delete.connect(_on_assignment_change, sender=Assignment, weak=False)
    except LookupError:
        logger.debug("teams app not available; skipping assignment capacity signals.")


_connect_cross_app_signals()
