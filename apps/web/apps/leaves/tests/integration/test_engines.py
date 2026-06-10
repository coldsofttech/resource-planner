import datetime

from django.test import TestCase

from apps.leaves.engine import LeaveEngine
from apps.locations.tests.factories import make_location
from apps.users.models import UserProfile
from apps.users.tests.factories import make_user


def _make_member_at_location(email: str, location=None):
    user = make_user(email=email)
    UserProfile.objects.create(user=user, location=location)
    return user


# ── LeaveEngine.get_working_dates ─────────────────────────────────────────────


class GetWorkingDatesNoHolidaysTest(TestCase):
    def setUp(self):
        self.member = make_user(email="engine@example.com")
        UserProfile.objects.create(user=self.member)

    def test_weekday_range_returns_correct_dates(self):
        # Mon–Fri = 5 working days
        dates = LeaveEngine.get_working_dates(
            member_id=self.member.pk,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 10),
        )
        self.assertEqual(len(dates), 5)
        self.assertEqual(dates[0], datetime.date(2025, 1, 6))
        self.assertEqual(dates[-1], datetime.date(2025, 1, 10))

    def test_single_weekday_returns_one_date(self):
        dates = LeaveEngine.get_working_dates(
            member_id=self.member.pk,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 6),
        )
        self.assertEqual(dates, [datetime.date(2025, 1, 6)])

    def test_weekend_only_range_returns_empty(self):
        # Sat 11 Jan – Sun 12 Jan 2025
        dates = LeaveEngine.get_working_dates(
            member_id=self.member.pk,
            start_date=datetime.date(2025, 1, 11),
            end_date=datetime.date(2025, 1, 12),
        )
        self.assertEqual(dates, [])

    def test_range_spanning_weekend_excludes_saturday_and_sunday(self):
        # Mon 6 Jan – Mon 13 Jan 2025 = 6 working days (6,7,8,9,10,13)
        dates = LeaveEngine.get_working_dates(
            member_id=self.member.pk,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 13),
        )
        self.assertEqual(len(dates), 6)
        self.assertNotIn(datetime.date(2025, 1, 11), dates)
        self.assertNotIn(datetime.date(2025, 1, 12), dates)

    def test_member_without_profile_returns_weekdays_only(self):
        bare_user = make_user(email="noprofile@example.com")
        dates = LeaveEngine.get_working_dates(
            member_id=bare_user.pk,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 10),
        )
        self.assertEqual(len(dates), 5)


class GetWorkingDatesWithHolidaysTest(TestCase):
    def setUp(self):
        self.location = make_location(city="Holiday City")
        self.member = _make_member_at_location("hol@example.com", self.location)

    def test_holiday_on_weekday_is_excluded(self):
        from apps.holidays.models import Holiday

        Holiday.objects.create(
            name="Bank Holiday",
            date=datetime.date(2025, 1, 8),
            location=self.location,
        )
        dates = LeaveEngine.get_working_dates(
            member_id=self.member.pk,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 10),
        )
        self.assertNotIn(datetime.date(2025, 1, 8), dates)
        self.assertEqual(len(dates), 4)

    def test_multiple_holidays_all_excluded(self):
        from apps.holidays.models import Holiday

        Holiday.objects.create(
            name="H1", date=datetime.date(2025, 1, 6), location=self.location
        )
        Holiday.objects.create(
            name="H2", date=datetime.date(2025, 1, 7), location=self.location
        )
        dates = LeaveEngine.get_working_dates(
            member_id=self.member.pk,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 10),
        )
        self.assertNotIn(datetime.date(2025, 1, 6), dates)
        self.assertNotIn(datetime.date(2025, 1, 7), dates)
        self.assertEqual(len(dates), 3)

    def test_holiday_on_weekend_does_not_reduce_count(self):
        from apps.holidays.models import Holiday

        Holiday.objects.create(
            name="Weekend Holiday",
            date=datetime.date(2025, 1, 11),
            location=self.location,
        )
        dates = LeaveEngine.get_working_dates(
            member_id=self.member.pk,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 10),
        )
        self.assertEqual(len(dates), 5)

    def test_holiday_outside_range_does_not_affect_result(self):
        from apps.holidays.models import Holiday

        Holiday.objects.create(
            name="Future Holiday",
            date=datetime.date(2025, 2, 3),
            location=self.location,
        )
        dates = LeaveEngine.get_working_dates(
            member_id=self.member.pk,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 10),
        )
        self.assertEqual(len(dates), 5)

    def test_holiday_at_different_location_not_excluded(self):
        from apps.holidays.models import Holiday

        other_location = make_location(city="Other City")
        Holiday.objects.create(
            name="Other Holiday",
            date=datetime.date(2025, 1, 8),
            location=other_location,
        )
        dates = LeaveEngine.get_working_dates(
            member_id=self.member.pk,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 10),
        )
        self.assertEqual(len(dates), 5)
