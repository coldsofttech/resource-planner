import datetime

from django.test import TestCase

from apps.holidays.selectors import (
    get_all_holidays,
    get_holiday_by_code,
    get_holiday_options,
    get_holiday_stats,
    get_holiday_year_range,
    holiday_exists,
)
from apps.holidays.tests.factories import make_holiday
from apps.locations.tests.factories import make_location


class GetAllHolidaysTest(TestCase):
    def test_returns_all_holidays(self):
        loc1 = make_location(city="London")
        loc2 = make_location(city="Paris")
        make_holiday(location=loc1, date=datetime.date(2025, 12, 25))
        make_holiday(location=loc2, date=datetime.date(2025, 12, 25))
        self.assertEqual(get_all_holidays().count(), 2)

    def test_empty_returns_no_holidays(self):
        self.assertEqual(get_all_holidays().count(), 0)

    def test_select_related_location_avoids_extra_queries(self):
        make_holiday()
        qs = list(get_all_holidays())
        with self.assertNumQueries(0):
            for h in qs:
                _ = h.location.city


class GetHolidayByCodeTest(TestCase):
    def test_returns_holiday_for_valid_code(self):
        holiday = make_holiday()
        found = get_holiday_by_code(holiday.code)
        self.assertEqual(found, holiday)

    def test_returns_none_for_unknown_code(self):
        result = get_holiday_by_code("HOL-99999")
        self.assertIsNone(result)

    def test_select_related_location_on_result(self):
        holiday = make_holiday()
        found = get_holiday_by_code(holiday.code)
        with self.assertNumQueries(0):
            _ = found.location.city


class HolidayExistsTest(TestCase):
    def setUp(self):
        self.location = make_location()
        self.holiday = make_holiday(
            location=self.location, date=datetime.date(2025, 12, 25)
        )

    def test_returns_true_for_existing(self):
        self.assertTrue(holiday_exists(self.location.pk, datetime.date(2025, 12, 25)))

    def test_returns_false_for_nonexistent_date(self):
        self.assertFalse(holiday_exists(self.location.pk, datetime.date(2025, 12, 26)))

    def test_exclude_pk_allows_self_overlap(self):
        result = holiday_exists(
            self.location.pk,
            datetime.date(2025, 12, 25),
            exclude_pk=self.holiday.pk,
        )
        self.assertFalse(result)

    def test_different_location_returns_false(self):
        other_loc = make_location(city="Paris")
        result = holiday_exists(other_loc.pk, datetime.date(2025, 12, 25))
        self.assertFalse(result)


class GetHolidayOptionsTest(TestCase):
    def test_returns_holidays_in_queryset(self):
        make_holiday()
        self.assertEqual(get_holiday_options().count(), 1)

    def test_empty_returns_empty_queryset(self):
        self.assertEqual(get_holiday_options().count(), 0)


class GetHolidayStatsTest(TestCase):
    def test_returns_total_count(self):
        loc1 = make_location(city="London")
        loc2 = make_location(city="Paris")
        make_holiday(location=loc1, date=datetime.date(2025, 12, 25))
        make_holiday(location=loc2, date=datetime.date(2025, 12, 25))
        stats = get_holiday_stats()
        self.assertEqual(stats["total"], 2)

    def test_returns_zero_when_empty(self):
        stats = get_holiday_stats()
        self.assertEqual(stats["total"], 0)


class GetHolidayYearRangeTest(TestCase):
    def test_returns_min_and_max_year(self):
        loc1 = make_location(city="London")
        loc2 = make_location(city="Paris")
        make_holiday(location=loc1, date=datetime.date(2023, 12, 25))
        make_holiday(location=loc2, date=datetime.date(2025, 12, 25))
        result = get_holiday_year_range()
        self.assertEqual(result, (2023, 2025))

    def test_returns_none_when_empty(self):
        result = get_holiday_year_range()
        self.assertIsNone(result)

    def test_returns_same_year_for_single_entry(self):
        make_holiday(date=datetime.date(2025, 12, 25))
        result = get_holiday_year_range()
        self.assertEqual(result, (2025, 2025))
