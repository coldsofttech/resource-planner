import datetime

from django.db import IntegrityError
from django.test import TestCase

from apps.holidays.models import Holiday
from apps.holidays.tests.factories import make_holiday
from apps.locations.tests.factories import make_location
from apps.users.tests.factories import make_user


class HolidayCodeTest(TestCase):
    def test_code_starts_with_hol(self):
        holiday = make_holiday()
        self.assertTrue(holiday.code.startswith("HOL-"))

    def test_code_contains_pk(self):
        holiday = make_holiday()
        self.assertEqual(holiday.code, f"HOL-{holiday.pk}")

    def test_codes_are_unique(self):
        loc1 = make_location(city="London")
        loc2 = make_location(city="Paris")
        h1 = make_holiday(location=loc1, date=datetime.date(2025, 1, 1))
        h2 = make_holiday(location=loc2, date=datetime.date(2025, 1, 1))
        self.assertNotEqual(h1.code, h2.code)


class HolidayStrTest(TestCase):
    def test_str_returns_name(self):
        holiday = make_holiday(name="Christmas Day")
        self.assertEqual(str(holiday), "Christmas Day")


class HolidayAuditableTest(TestCase):
    def test_created_at_is_set(self):
        holiday = make_holiday()
        self.assertIsNotNone(holiday.created_at)

    def test_updated_at_is_set(self):
        holiday = make_holiday()
        self.assertIsNotNone(holiday.updated_at)

    def test_created_by_defaults_to_none(self):
        holiday = make_holiday()
        self.assertIsNone(holiday.created_by)

    def test_created_by_stores_user(self):
        actor = make_user(email="actor@example.com")
        location = make_location(city="Dublin")
        holiday = Holiday.objects.create(
            name="St Patrick's Day",
            date=datetime.date(2025, 3, 17),
            location=location,
            created_by=actor,
            updated_by=actor,
        )
        self.assertEqual(holiday.created_by, actor)


class HolidayConstraintTest(TestCase):
    def test_duplicate_location_and_date_raises_integrity_error(self):
        location = make_location()
        make_holiday(location=location, date=datetime.date(2025, 12, 25))
        with self.assertRaises(IntegrityError):
            Holiday.objects.create(
                name="Another Holiday",
                date=datetime.date(2025, 12, 25),
                location=location,
            )

    def test_same_date_different_location_allowed(self):
        loc1 = make_location(city="London")
        loc2 = make_location(city="Paris")
        make_holiday(location=loc1, date=datetime.date(2025, 12, 25))
        make_holiday(location=loc2, date=datetime.date(2025, 12, 25))
        self.assertEqual(Holiday.objects.count(), 2)

    def test_same_location_different_date_allowed(self):
        location = make_location()
        make_holiday(location=location, date=datetime.date(2025, 12, 25))
        make_holiday(location=location, date=datetime.date(2025, 12, 26))
        self.assertEqual(Holiday.objects.count(), 2)


class HolidayOrderingTest(TestCase):
    def test_ordered_by_date_ascending_within_location(self):
        loc = make_location()
        make_holiday(location=loc, date=datetime.date(2025, 12, 26))
        make_holiday(location=loc, date=datetime.date(2025, 12, 25))
        dates = list(
            Holiday.objects.filter(location=loc).values_list("date", flat=True)
        )
        self.assertEqual(dates, sorted(dates))
