import datetime

from django.test import TestCase

from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.holidays.models import Holiday
from apps.holidays.services import HolidayImportService, HolidayService
from apps.holidays.tests.factories import make_csv_file, make_holiday
from apps.locations.tests.factories import make_location
from apps.users.tests.factories import make_user


def _make_service(user=None):
    if user is None:
        user = make_user(email="actor@example.com")
    return HolidayService(user=user)


# ── HolidayService.get ────────────────────────────────────────────────────────


class HolidayServiceGetTest(TestCase):
    def test_returns_holiday_for_valid_code(self):
        holiday = make_holiday()
        result = _make_service().get(code=holiday.code)
        self.assertEqual(result, holiday)

    def test_unknown_code_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            _make_service().get(code="HOL-99999")


# ── HolidayService.create ─────────────────────────────────────────────────────


class HolidayServiceCreateTest(TestCase):
    def test_creates_holiday_with_valid_data(self):
        location = make_location()
        holiday = _make_service().create(
            name="Christmas Day",
            date=datetime.date(2025, 12, 25),
            location_code=location.code,
        )
        self.assertIsNotNone(holiday.pk)
        self.assertEqual(holiday.name, "Christmas Day")
        self.assertEqual(holiday.location, location)

    def test_unknown_location_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            _make_service().create(
                name="Test Holiday",
                date=datetime.date(2025, 12, 25),
                location_code="LOC-99999",
            )

    def test_duplicate_location_date_raises_already_exists(self):
        location = make_location()
        make_holiday(location=location, date=datetime.date(2025, 12, 25))
        with self.assertRaises(AlreadyExistsException):
            _make_service().create(
                name="Another",
                date=datetime.date(2025, 12, 25),
                location_code=location.code,
            )

    def test_created_by_is_set(self):
        actor = make_user(email="creator@example.com")
        location = make_location(city="Paris")
        holiday = HolidayService(user=actor).create(
            name="New Year",
            date=datetime.date(2025, 1, 1),
            location_code=location.code,
        )
        self.assertEqual(holiday.created_by, actor)

    def test_code_is_assigned(self):
        location = make_location()
        holiday = _make_service().create(
            name="Boxing Day",
            date=datetime.date(2025, 12, 26),
            location_code=location.code,
        )
        self.assertTrue(holiday.code.startswith("HOL-"))


# ── HolidayService.update ─────────────────────────────────────────────────────


class HolidayServiceUpdateTest(TestCase):
    def setUp(self):
        self.location = make_location()
        self.holiday = make_holiday(
            location=self.location, date=datetime.date(2025, 12, 25)
        )

    def test_updates_name(self):
        updated = _make_service().update(code=self.holiday.code, name="New Name")
        self.assertEqual(updated.name, "New Name")

    def test_unknown_code_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            _make_service().update(code="HOL-99999", name="X")

    def test_unknown_location_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            _make_service().update(code=self.holiday.code, location_code="LOC-99999")

    def test_conflict_location_date_raises_already_exists(self):
        other_loc = make_location(city="Paris")
        make_holiday(location=other_loc, date=datetime.date(2025, 12, 26))
        with self.assertRaises(AlreadyExistsException):
            _make_service().update(
                code=self.holiday.code,
                location_code=other_loc.code,
                date=datetime.date(2025, 12, 26),
            )

    def test_update_same_location_date_does_not_raise(self):
        updated = _make_service().update(
            code=self.holiday.code,
            location_code=self.location.code,
            date=datetime.date(2025, 12, 25),
        )
        self.assertEqual(updated.code, self.holiday.code)


# ── HolidayService.delete ─────────────────────────────────────────────────────


class HolidayServiceDeleteTest(TestCase):
    def test_deletes_holiday(self):
        holiday = make_holiday()
        _make_service().delete(code=holiday.code)
        self.assertFalse(Holiday.objects.filter(pk=holiday.pk).exists())

    def test_unknown_code_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            _make_service().delete(code="HOL-99999")


# ── HolidayService.options ────────────────────────────────────────────────────


class HolidayServiceOptionsTest(TestCase):
    def test_returns_items_list(self):
        make_holiday()
        result = _make_service().options()
        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 1)

    def test_item_has_expected_keys(self):
        make_holiday()
        result = _make_service().options()
        item = result["items"][0]
        for key in ["code", "name", "date", "location"]:
            self.assertIn(key, item)

    def test_returns_year_range(self):
        make_holiday(date=datetime.date(2025, 12, 25))
        result = _make_service().options()
        self.assertEqual(result["min_year"], 2025)
        self.assertEqual(result["max_year"], 2025)

    def test_empty_returns_empty_items_and_null_years(self):
        result = _make_service().options()
        self.assertEqual(result["items"], [])
        self.assertIsNone(result["min_year"])
        self.assertIsNone(result["max_year"])


# ── HolidayService.stats ──────────────────────────────────────────────────────


class HolidayServiceStatsTest(TestCase):
    def test_returns_total_count(self):
        loc1 = make_location(city="London")
        loc2 = make_location(city="Paris")
        make_holiday(location=loc1, date=datetime.date(2025, 12, 25))
        make_holiday(location=loc2, date=datetime.date(2025, 12, 25))
        result = _make_service().stats()
        self.assertEqual(result["total"], 2)

    def test_returns_zero_when_empty(self):
        result = _make_service().stats()
        self.assertEqual(result["total"], 0)


# ── HolidayImportService.bulk_import ──────────────────────────────────────────


class HolidayImportServiceBulkImportTest(TestCase):
    def setUp(self):
        self.location = make_location(city="London")
        self.actor = make_user(email="importer@example.com")

    def _make_import_service(self):
        return HolidayImportService(user=self.actor)

    def test_valid_csv_creates_holiday(self):
        csv_content = (
            f"name,date,location_code\nChristmas Day,2025-12-25,{self.location.code}\n"
        )
        result = self._make_import_service().bulk_import(make_csv_file(csv_content))
        self.assertEqual(Holiday.objects.count(), 1)
        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["created_rows"]), 1)
        self.assertEqual(result["errors"], [])

    def test_missing_required_column_raises_validation_error(self):
        csv_content = "name,date\nChristmas Day,2025-12-25\n"
        with self.assertRaises(ValidationException):
            self._make_import_service().bulk_import(make_csv_file(csv_content))

    def test_unknown_location_code_reported_as_error(self):
        csv_content = "name,date,location_code\nChristmas Day,2025-12-25,LOC-99999\n"
        result = self._make_import_service().bulk_import(make_csv_file(csv_content))
        self.assertEqual(Holiday.objects.count(), 0)
        self.assertEqual(len(result["errors"]), 1)

    def test_duplicate_location_date_reported_as_error(self):
        make_holiday(location=self.location, date=datetime.date(2025, 12, 25))
        csv_content = (
            f"name,date,location_code\nChristmas Day,2025-12-25,{self.location.code}\n"
        )
        result = self._make_import_service().bulk_import(make_csv_file(csv_content))
        self.assertEqual(len(result["errors"]), 1)

    def test_dry_run_does_not_persist_holidays(self):
        csv_content = (
            f"name,date,location_code\nChristmas Day,2025-12-25,{self.location.code}\n"
        )
        result = self._make_import_service().bulk_import(
            make_csv_file(csv_content), dry_run=True
        )
        self.assertEqual(Holiday.objects.count(), 0)
        self.assertTrue(result["dry_run"])
        self.assertEqual(len(result["created_rows"]), 1)

    def test_invalid_date_row_reported_as_error(self):
        csv_content = (
            f"name,date,location_code\nChristmas Day,25-12-2025,{self.location.code}\n"
        )
        result = self._make_import_service().bulk_import(make_csv_file(csv_content))
        self.assertEqual(Holiday.objects.count(), 0)
        self.assertEqual(len(result["errors"]), 1)
