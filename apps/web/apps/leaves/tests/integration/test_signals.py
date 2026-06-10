import datetime
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from apps.leaves.models import LeaveDayEntry
from apps.leaves.tests.factories import make_leave
from apps.locations.tests.factories import make_location
from apps.users.models import UserProfile
from apps.users.tests.factories import make_user


class HolidaySignalRecalculatesLeaveDaysTest(TestCase):
    def setUp(self):
        self.location = make_location(city="Test City")
        self.user = make_user(email="sig@example.com")
        UserProfile.objects.create(user=self.user, location=self.location)

        self.leave = make_leave(
            member=self.user,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 10),
            days="5",
        )

    def test_holiday_save_triggers_recalculation(self):
        from apps.holidays.models import Holiday

        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days",
            return_value=Decimal("4"),
        ):
            Holiday.objects.create(
                name="Test Holiday",
                date=datetime.date(2025, 1, 8),
                location=self.location,
            )

        self.leave.refresh_from_db()
        self.assertEqual(self.leave.days, Decimal("4"))

    def test_holiday_delete_triggers_recalculation(self):
        from apps.holidays.models import Holiday

        holiday = Holiday.objects.create(
            name="Test Holiday",
            date=datetime.date(2025, 1, 8),
            location=self.location,
        )
        self.leave.refresh_from_db()

        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days",
            return_value=Decimal("5"),
        ):
            holiday.delete()

        self.leave.refresh_from_db()
        self.assertEqual(self.leave.days, Decimal("5"))

    def test_unrelated_location_holiday_does_not_update_leave(self):
        from apps.holidays.models import Holiday

        other_location = make_location(city="Other City")
        self.leave.refresh_from_db()
        original_days = self.leave.days

        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days",
            return_value=Decimal("0"),
        ):
            Holiday.objects.create(
                name="Other Holiday",
                date=datetime.date(2025, 1, 8),
                location=other_location,
            )

        self.leave.refresh_from_db()
        self.assertEqual(self.leave.days, original_days)


class HolidaySignalResyncsLeaveDayEntriesTest(TestCase):
    def setUp(self):
        self.location = make_location(city="Sync City")
        self.user = make_user(email="syncsig@example.com")
        UserProfile.objects.create(user=self.user, location=self.location)

        self.leave = make_leave(
            member=self.user,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 10),
            days="5",
        )
        # Seed initial day entries (Mon–Fri)
        for day in range(6, 11):
            LeaveDayEntry.objects.create(
                leave=self.leave,
                date=datetime.date(2025, 1, day),
            )

    def test_holiday_save_resyncs_day_entries(self):
        from apps.holidays.models import Holiday

        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days",
            return_value=Decimal("4"),
        ):
            with patch(
                "apps.leaves.engine.LeaveEngine.get_working_dates",
                return_value=[
                    datetime.date(2025, 1, 6),
                    datetime.date(2025, 1, 7),
                    datetime.date(2025, 1, 9),
                    datetime.date(2025, 1, 10),
                ],
            ):
                Holiday.objects.create(
                    name="Test Holiday",
                    date=datetime.date(2025, 1, 8),
                    location=self.location,
                )

        entries = LeaveDayEntry.objects.filter(leave=self.leave).values_list(
            "date", flat=True
        )
        self.assertEqual(
            set(entries),
            {
                datetime.date(2025, 1, 6),
                datetime.date(2025, 1, 7),
                datetime.date(2025, 1, 9),
                datetime.date(2025, 1, 10),
            },
        )
        self.assertNotIn(datetime.date(2025, 1, 8), set(entries))

    def test_holiday_delete_resyncs_day_entries(self):
        from apps.holidays.models import Holiday

        holiday = Holiday.objects.create(
            name="Test Holiday",
            date=datetime.date(2025, 1, 8),
            location=self.location,
        )

        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days",
            return_value=Decimal("5"),
        ):
            with patch(
                "apps.leaves.engine.LeaveEngine.get_working_dates",
                return_value=[
                    datetime.date(2025, 1, 6),
                    datetime.date(2025, 1, 7),
                    datetime.date(2025, 1, 8),
                    datetime.date(2025, 1, 9),
                    datetime.date(2025, 1, 10),
                ],
            ):
                holiday.delete()

        entries = LeaveDayEntry.objects.filter(leave=self.leave).values_list(
            "date", flat=True
        )
        self.assertEqual(
            set(entries),
            {
                datetime.date(2025, 1, 6),
                datetime.date(2025, 1, 7),
                datetime.date(2025, 1, 8),
                datetime.date(2025, 1, 9),
                datetime.date(2025, 1, 10),
            },
        )
