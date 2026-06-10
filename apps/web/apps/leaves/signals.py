from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver


@receiver(post_save, sender="holidays.Holiday")
def on_holiday_saved(sender, instance, **kwargs):
    _recalculate_leaves_for_location_date(
        location_id=instance.location_id,
        date=instance.date,
    )


@receiver(post_delete, sender="holidays.Holiday")
def on_holiday_deleted(sender, instance, **kwargs):
    _recalculate_leaves_for_location_date(
        location_id=instance.location_id,
        date=instance.date,
    )


def _recalculate_leaves_for_location_date(location_id: int, date) -> None:
    """Recalculate `days` and resync LeaveDayEntry rows for every leave whose
    member is at `location_id` and whose date range includes `date`."""
    from apps.leaves.engine import LeaveEngine
    from apps.leaves.models import Leave
    from apps.leaves.selectors import get_leaves_affected_by_location_date_range

    leaves = get_leaves_affected_by_location_date_range(
        location_id=location_id,
        start_date=date,
        end_date=date,
    )
    for leave in leaves:
        new_days = LeaveEngine.calculate_days(
            member_id=leave.member_id,
            start_date=leave.start_date,
            end_date=leave.end_date,
            is_half_day=leave.is_half_day,
        )
        if leave.days != new_days:
            Leave.objects.filter(pk=leave.pk).update(days=new_days)
            leave.days = new_days
        LeaveEngine.sync_day_entries(leave)
