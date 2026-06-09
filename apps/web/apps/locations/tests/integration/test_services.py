import json

from django.test import TestCase

from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.core.types import ListParams
from apps.locations.models import Location
from apps.locations.services import (
    LocationExportService,
    LocationImportService,
    LocationService,
)
from apps.locations.tests.factories import make_csv_file, make_location
from apps.users.tests.factories import make_user


def make_service(user=None):
    return LocationService(user=user)


def make_import_service(user=None):
    return LocationImportService(user=user)


# ── list ──────────────────────────────────────────────────────────────────────


class LocationServiceListTest(TestCase):
    def setUp(self):
        self.svc = make_service()
        make_location("London", "United Kingdom", is_active=True)
        make_location("Paris", "France", is_active=True)
        make_location("Berlin", "Germany", is_active=False)

    def test_defaults_to_active_only(self):
        result = self.svc.list(ListParams())
        cities = [loc.city for loc in result.results]
        self.assertIn("London", cities)
        self.assertNotIn("Berlin", cities)

    def test_is_active_false_returns_inactive(self):
        result = self.svc.list(ListParams(filters={"is_active": "false"}))
        cities = [loc.city for loc in result.results]
        self.assertIn("Berlin", cities)
        self.assertNotIn("London", cities)

    def test_returns_paginated_result(self):
        result = self.svc.list(ListParams())
        self.assertIsNotNone(result.pagination)

    def test_search_by_city(self):
        result = self.svc.list(ListParams(search="London"))
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0].city, "London")

    def test_search_by_country(self):
        result = self.svc.list(ListParams(search="France"))
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0].country, "France")

    def test_returns_empty_when_no_active_locations(self):
        Location.objects.all().delete()
        make_location("Berlin", "Germany", is_active=False)
        result = self.svc.list(ListParams())
        self.assertEqual(len(result.results), 0)


# ── get ───────────────────────────────────────────────────────────────────────


class LocationServiceGetTest(TestCase):
    def setUp(self):
        self.svc = make_service()
        self.loc = make_location()

    def test_returns_location_by_code(self):
        result = self.svc.get(code=self.loc.code)
        self.assertEqual(result, self.loc)

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.get(code="LOC-9999")


# ── create ────────────────────────────────────────────────────────────────────


class LocationServiceCreateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)

    def test_creates_location(self):
        loc = self.svc.create(city="London", country="United Kingdom")
        self.assertIsNotNone(loc.pk)
        self.assertEqual(loc.city, "London")
        self.assertEqual(loc.country, "United Kingdom")

    def test_sets_created_by(self):
        loc = self.svc.create(city="London", country="United Kingdom")
        self.assertEqual(loc.created_by, self.user)

    def test_is_active_defaults_to_true(self):
        loc = self.svc.create(city="London", country="United Kingdom")
        self.assertTrue(loc.is_active)

    def test_is_default_defaults_to_false(self):
        loc = self.svc.create(city="London", country="United Kingdom")
        self.assertFalse(loc.is_default)

    def test_creates_with_is_default_true(self):
        loc = self.svc.create(city="London", country="United Kingdom", is_default=True)
        self.assertTrue(loc.is_default)

    def test_raises_conflict_on_duplicate_city_country(self):
        self.svc.create(city="London", country="United Kingdom")
        with self.assertRaises(AlreadyExistsException):
            self.svc.create(city="London", country="United Kingdom")

    def test_same_city_different_country_no_conflict(self):
        self.svc.create(city="London", country="United Kingdom")
        loc = self.svc.create(city="London", country="Canada")
        self.assertIsNotNone(loc.pk)

    def test_code_is_assigned(self):
        loc = self.svc.create(city="London", country="United Kingdom")
        self.assertTrue(loc.code.startswith("LOC-"))


# ── update ────────────────────────────────────────────────────────────────────


class LocationServiceUpdateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)
        self.loc = make_location("London", "United Kingdom")

    def test_updates_city(self):
        updated = self.svc.update(code=self.loc.code, city="Manchester")
        self.assertEqual(updated.city, "Manchester")

    def test_updates_country(self):
        updated = self.svc.update(code=self.loc.code, country="Ireland")
        self.assertEqual(updated.country, "Ireland")

    def test_updates_is_active(self):
        updated = self.svc.update(code=self.loc.code, is_active=False)
        self.assertFalse(updated.is_active)

    def test_updates_is_default(self):
        updated = self.svc.update(code=self.loc.code, is_default=True)
        self.assertTrue(updated.is_default)

    def test_sets_updated_by(self):
        updated = self.svc.update(code=self.loc.code, city="Manchester")
        self.assertEqual(updated.updated_by, self.user)

    def test_raises_conflict_on_duplicate_city_country(self):
        make_location("Paris", "France")
        with self.assertRaises(AlreadyExistsException):
            self.svc.update(code=self.loc.code, city="Paris", country="France")

    def test_same_values_no_conflict(self):
        updated = self.svc.update(
            code=self.loc.code, city="London", country="United Kingdom"
        )
        self.assertEqual(updated.city, "London")

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.update(code="LOC-9999", city="X")


# ── activate / deactivate ─────────────────────────────────────────────────────


class LocationServiceActivateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)

    def test_activates_inactive_location(self):
        loc = make_location(is_active=False)
        result = self.svc.activate(code=loc.code)
        self.assertTrue(result.is_active)

    def test_activate_is_idempotent(self):
        loc = make_location(is_active=True)
        result = self.svc.activate(code=loc.code)
        self.assertTrue(result.is_active)

    def test_deactivates_active_location(self):
        loc = make_location(is_active=True)
        result = self.svc.deactivate(code=loc.code)
        self.assertFalse(result.is_active)

    def test_deactivate_is_idempotent(self):
        loc = make_location(is_active=False)
        result = self.svc.deactivate(code=loc.code)
        self.assertFalse(result.is_active)

    def test_activate_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            self.svc.activate(code="LOC-9999")

    def test_deactivate_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            self.svc.deactivate(code="LOC-9999")


# ── delete ────────────────────────────────────────────────────────────────────


class LocationServiceDeleteTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_deletes_location(self):
        loc = make_location()
        self.svc.delete(code=loc.code)
        self.assertFalse(Location.objects.filter(pk=loc.pk).exists())

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.delete(code="LOC-9999")


# ── stats ─────────────────────────────────────────────────────────────────────


class LocationServiceStatsTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_returns_correct_counts(self):
        make_location("London", "United Kingdom", is_active=True)
        make_location("Paris", "France", is_active=False)
        result = self.svc.stats()
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["active"], 1)
        self.assertEqual(result["inactive"], 1)

    def test_returns_zeros_when_no_locations(self):
        result = self.svc.stats()
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["active"], 0)
        self.assertEqual(result["inactive"], 0)

    def test_fields_filter_limits_returned_keys(self):
        make_location(is_active=True)
        result = self.svc.stats(fields=["total", "active"])
        self.assertIn("total", result)
        self.assertIn("active", result)
        self.assertNotIn("inactive", result)


# ── options ───────────────────────────────────────────────────────────────────


class LocationServiceOptionsTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_returns_list(self):
        result = self.svc.options()
        self.assertIsInstance(result, list)

    def test_returns_empty_when_no_active_locations(self):
        make_location(is_active=False)
        self.assertEqual(self.svc.options(), [])

    def test_returns_only_active_locations(self):
        make_location("London", "United Kingdom", is_active=True)
        make_location("Paris", "France", is_active=False)
        result = self.svc.options()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["city"], "London")

    def test_each_entry_has_code_city_country_keys(self):
        loc = make_location("London", "United Kingdom", is_active=True)
        result = self.svc.options()
        entry = result[0]
        self.assertIn("code", entry)
        self.assertIn("city", entry)
        self.assertIn("country", entry)
        self.assertEqual(entry["code"], loc.code)
        self.assertEqual(entry["city"], "London")
        self.assertEqual(entry["country"], "United Kingdom")


# ── LocationExportService ─────────────────────────────────────────────────────


class LocationExportServiceSearchFilterTest(TestCase):
    def setUp(self):
        make_location("London", "United Kingdom", is_active=True)
        make_location("Paris", "France", is_active=True)
        make_location("Berlin", "Germany", is_active=True)
        self.svc = LocationExportService()

    def test_search_filter_includes_matching_city(self):
        response = self.svc.export(
            fields=["city"],
            export_format="csv",
            filters={"search": "London"},
        )
        self.assertIn("London", response.content.decode())

    def test_search_filter_excludes_non_matching_locations(self):
        response = self.svc.export(
            fields=["city"],
            export_format="csv",
            filters={"search": "London"},
        )
        content = response.content.decode()
        self.assertNotIn("Paris", content)
        self.assertNotIn("Berlin", content)

    def test_search_by_country(self):
        response = self.svc.export(
            fields=["city", "country"],
            export_format="csv",
            filters={"search": "France"},
        )
        content = response.content.decode()
        self.assertIn("Paris", content)
        self.assertNotIn("London", content)

    def test_empty_search_returns_all_active(self):
        response = self.svc.export(
            fields=["city"],
            export_format="csv",
            filters={"search": ""},
        )
        content = response.content.decode()
        self.assertIn("London", content)
        self.assertIn("Paris", content)
        self.assertIn("Berlin", content)

    def test_unsupported_format_raises_validation_exception(self):
        with self.assertRaises(ValidationException):
            self.svc.export(fields=["city"], export_format="xml", filters={})

    def test_json_format_returns_list(self):
        response = self.svc.export(fields=["city"], export_format="json", filters={})
        data = json.loads(response.content.decode())
        self.assertIsInstance(data, list)


# ── LocationImportService.bulk_import ────────────────────────────────────────


class LocationImportBulkImportStructureTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_import_service(user=self.user)

    def test_raises_if_city_column_missing(self):
        f = make_csv_file("country\nUnited Kingdom")
        with self.assertRaises(ValidationException):
            self.svc.bulk_import(f)

    def test_raises_if_country_column_missing(self):
        f = make_csv_file("city\nLondon")
        with self.assertRaises(ValidationException):
            self.svc.bulk_import(f)

    def test_raises_if_row_count_exceeds_limit(self):
        rows = ["city,country"] + [
            f"City{i:05d},Country{i:05d}"
            for i in range(LocationImportService.MAX_IMPORT_ROWS + 1)
        ]
        f = make_csv_file("\n".join(rows))
        with self.assertRaises(ValidationException):
            self.svc.bulk_import(f)

    def test_returns_expected_keys(self):
        f = make_csv_file("city,country\nLondon,United Kingdom")
        result = self.svc.bulk_import(f)
        self.assertIn("total", result)
        self.assertIn("created_rows", result)
        self.assertIn("errors", result)
        self.assertIn("dry_run", result)

    def test_total_reflects_row_count(self):
        f = make_csv_file("city,country\nLondon,UK\nParis,France\nBerlin,Germany")
        result = self.svc.bulk_import(f)
        self.assertEqual(result["total"], 3)


class LocationImportBulkImportCreateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_import_service(user=self.user)

    def test_creates_location_from_csv(self):
        f = make_csv_file("city,country\nLondon,United Kingdom")
        self.svc.bulk_import(f)
        self.assertTrue(
            Location.objects.filter(city="London", country="United Kingdom").exists()
        )

    def test_returns_correct_created_count(self):
        f = make_csv_file("city,country\nLondon,UK\nParis,France")
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["created_rows"]), 2)

    def test_default_is_active_is_true(self):
        f = make_csv_file("city,country\nLondon,UK")
        self.svc.bulk_import(f)
        self.assertTrue(Location.objects.get(city="London").is_active)

    def test_is_active_false_parsed(self):
        f = make_csv_file("city,country,is_active\nLondon,UK,false")
        self.svc.bulk_import(f)
        self.assertFalse(Location.objects.get(city="London").is_active)

    def test_is_default_true_parsed(self):
        f = make_csv_file("city,country,is_default\nLondon,UK,true")
        self.svc.bulk_import(f)
        self.assertTrue(Location.objects.get(city="London").is_default)

    def test_strips_whitespace_from_city(self):
        f = make_csv_file("city,country\n  London  ,UK")
        self.svc.bulk_import(f)
        self.assertTrue(Location.objects.filter(city="London").exists())

    def test_created_by_set_to_user(self):
        f = make_csv_file("city,country\nLondon,UK")
        self.svc.bulk_import(f)
        loc = Location.objects.get(city="London")
        self.assertEqual(loc.created_by, self.user)


class LocationImportBulkImportSkipTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_import_service(user=self.user)

    def test_skips_row_with_missing_city(self):
        f = make_csv_file("city,country\n ,UK")
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(len(result["created_rows"]), 0)

    def test_skips_duplicate_location(self):
        make_location("London", "United Kingdom")
        f = make_csv_file("city,country\nLondon,United Kingdom")
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)

    def test_partial_import_skips_duplicates_only(self):
        make_location("London", "United Kingdom")
        f = make_csv_file("city,country\nLondon,United Kingdom\nParis,France")
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["created_rows"]), 1)
        self.assertEqual(len(result["errors"]), 1)

    def test_error_entry_includes_row_number(self):
        make_location("London", "United Kingdom")
        f = make_csv_file("city,country\nLondon,United Kingdom")
        result = self.svc.bulk_import(f)
        self.assertEqual(result["errors"][0]["row"], 2)


class LocationImportBulkImportDryRunTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_import_service(user=self.user)

    def test_dry_run_does_not_create_locations(self):
        f = make_csv_file("city,country\nLondon,UK\nParis,France")
        self.svc.bulk_import(f, dry_run=True)
        self.assertEqual(Location.objects.count(), 0)

    def test_dry_run_reports_correct_created_count(self):
        f = make_csv_file("city,country\nLondon,UK\nParis,France")
        result = self.svc.bulk_import(f, dry_run=True)
        self.assertEqual(len(result["created_rows"]), 2)
        self.assertTrue(result["dry_run"])
