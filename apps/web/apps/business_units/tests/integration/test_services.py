import json

from django.test import TestCase

from apps.business_units.models import BusinessUnit
from apps.business_units.services import (
    BusinessUnitExportService,
    BusinessUnitImportService,
    BusinessUnitService,
)
from apps.business_units.tests.factories import make_business_unit, make_csv_file
from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.core.types import ListParams
from apps.users.tests.factories import make_user


def make_service(user=None):
    return BusinessUnitService(user=user)


def make_import_service(user=None):
    return BusinessUnitImportService(user=user)


# ── list ──────────────────────────────────────────────────────────────────────


class BusinessUnitServiceListTest(TestCase):
    def setUp(self):
        self.svc = make_service()
        make_business_unit("Finance", "FIN", is_active=True)
        make_business_unit("Technology", "TECH", is_active=True)
        make_business_unit("Operations", "OPS", is_active=False)

    def test_defaults_to_active_only(self):
        result = self.svc.list(ListParams())
        names = [bu.name for bu in result.results]
        self.assertIn("Finance", names)
        self.assertNotIn("Operations", names)

    def test_is_active_false_returns_inactive(self):
        result = self.svc.list(ListParams(filters={"is_active": "false"}))
        names = [bu.name for bu in result.results]
        self.assertIn("Operations", names)
        self.assertNotIn("Finance", names)

    def test_returns_paginated_result(self):
        result = self.svc.list(ListParams())
        self.assertIsNotNone(result.pagination)

    def test_search_by_name(self):
        result = self.svc.list(ListParams(search="Finance"))
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0].name, "Finance")

    def test_search_by_short_name(self):
        result = self.svc.list(ListParams(search="FIN"))
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0].short_name, "FIN")

    def test_returns_empty_when_no_active_units(self):
        BusinessUnit.objects.all().delete()
        make_business_unit("Inactive", "INA", is_active=False)
        result = self.svc.list(ListParams())
        self.assertEqual(len(result.results), 0)


# ── get ───────────────────────────────────────────────────────────────────────


class BusinessUnitServiceGetTest(TestCase):
    def setUp(self):
        self.svc = make_service()
        self.bu = make_business_unit("Finance", "FIN")

    def test_returns_unit_by_code(self):
        result = self.svc.get(code=self.bu.code)
        self.assertEqual(result, self.bu)

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.get(code="BU-9999")


# ── create ────────────────────────────────────────────────────────────────────


class BusinessUnitServiceCreateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)

    def test_creates_business_unit(self):
        bu = self.svc.create(name="Finance", short_name="FIN")
        self.assertIsNotNone(bu.pk)
        self.assertEqual(bu.name, "Finance")
        self.assertEqual(bu.short_name, "FIN")

    def test_sets_created_by(self):
        bu = self.svc.create(name="Finance", short_name="FIN")
        self.assertEqual(bu.created_by, self.user)

    def test_is_active_defaults_to_true(self):
        bu = self.svc.create(name="Finance", short_name="FIN")
        self.assertTrue(bu.is_active)

    def test_creates_with_is_active_false(self):
        bu = self.svc.create(name="Finance", short_name="FIN", is_active=False)
        self.assertFalse(bu.is_active)

    def test_raises_conflict_on_duplicate_name(self):
        self.svc.create(name="Finance", short_name="FIN")
        with self.assertRaises(AlreadyExistsException):
            self.svc.create(name="Finance", short_name="FIN2")

    def test_code_is_assigned(self):
        bu = self.svc.create(name="Finance", short_name="FIN")
        self.assertTrue(bu.code.startswith("BU-"))


# ── update ────────────────────────────────────────────────────────────────────


class BusinessUnitServiceUpdateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)
        self.bu = make_business_unit("Finance", "FIN")

    def test_updates_name(self):
        updated = self.svc.update(code=self.bu.code, name="Renamed")
        self.assertEqual(updated.name, "Renamed")

    def test_updates_short_name(self):
        updated = self.svc.update(code=self.bu.code, short_name="RNM")
        self.assertEqual(updated.short_name, "RNM")

    def test_updates_is_active(self):
        updated = self.svc.update(code=self.bu.code, is_active=False)
        self.assertFalse(updated.is_active)

    def test_sets_updated_by(self):
        updated = self.svc.update(code=self.bu.code, name="Renamed")
        self.assertEqual(updated.updated_by, self.user)

    def test_raises_conflict_on_duplicate_name(self):
        make_business_unit("Technology", "TECH")
        with self.assertRaises(AlreadyExistsException):
            self.svc.update(code=self.bu.code, name="Technology")

    def test_same_name_no_conflict(self):
        updated = self.svc.update(code=self.bu.code, name="Finance")
        self.assertEqual(updated.name, "Finance")

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.update(code="BU-9999", name="X")


# ── activate / deactivate ─────────────────────────────────────────────────────


class BusinessUnitServiceActivateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)

    def test_activates_inactive_unit(self):
        bu = make_business_unit("Finance", "FIN", is_active=False)
        result = self.svc.activate(code=bu.code)
        self.assertTrue(result.is_active)

    def test_activate_is_idempotent(self):
        bu = make_business_unit("Finance", "FIN", is_active=True)
        result = self.svc.activate(code=bu.code)
        self.assertTrue(result.is_active)

    def test_deactivates_active_unit(self):
        bu = make_business_unit("Technology", "TECH", is_active=True)
        result = self.svc.deactivate(code=bu.code)
        self.assertFalse(result.is_active)

    def test_deactivate_is_idempotent(self):
        bu = make_business_unit("Technology", "TECH", is_active=False)
        result = self.svc.deactivate(code=bu.code)
        self.assertFalse(result.is_active)

    def test_activate_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            self.svc.activate(code="BU-9999")

    def test_deactivate_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            self.svc.deactivate(code="BU-9999")


# ── delete ────────────────────────────────────────────────────────────────────


class BusinessUnitServiceDeleteTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_deletes_unit(self):
        bu = make_business_unit("Finance", "FIN")
        self.svc.delete(code=bu.code)
        self.assertFalse(BusinessUnit.objects.filter(pk=bu.pk).exists())

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.delete(code="BU-9999")


# ── stats ─────────────────────────────────────────────────────────────────────


class BusinessUnitServiceStatsTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_returns_correct_counts(self):
        make_business_unit("Finance", "FIN", is_active=True)
        make_business_unit("Technology", "TECH", is_active=False)
        result = self.svc.stats()
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["active"], 1)
        self.assertEqual(result["inactive"], 1)

    def test_returns_zeros_when_empty(self):
        result = self.svc.stats()
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["active"], 0)
        self.assertEqual(result["inactive"], 0)

    def test_fields_filter_limits_returned_keys(self):
        make_business_unit("Finance", "FIN", is_active=True)
        result = self.svc.stats(fields=["total", "active"])
        self.assertIn("total", result)
        self.assertIn("active", result)
        self.assertNotIn("inactive", result)


# ── options ───────────────────────────────────────────────────────────────────


class BusinessUnitServiceOptionsTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_returns_only_active_units(self):
        make_business_unit("Finance", "FIN", is_active=True)
        make_business_unit("Inactive", "INA", is_active=False)
        options = self.svc.options()
        names = [o["name"] for o in options]
        self.assertIn("Finance", names)
        self.assertNotIn("Inactive", names)

    def test_each_option_has_code_and_name(self):
        make_business_unit("Finance", "FIN")
        options = self.svc.options()
        self.assertIn("code", options[0])
        self.assertIn("name", options[0])


# ── BusinessUnitExportService ─────────────────────────────────────────────────


class BusinessUnitExportServiceSearchFilterTest(TestCase):
    def setUp(self):
        make_business_unit("Finance", "FIN", is_active=True)
        make_business_unit("Technology", "TECH", is_active=True)
        make_business_unit("Operations", "OPS", is_active=True)
        self.svc = BusinessUnitExportService()

    def test_search_filter_includes_matching_unit(self):
        response = self.svc.export(
            fields=["name"], export_format="csv", filters={"search": "Finance"}
        )
        self.assertIn("Finance", response.content.decode())

    def test_search_filter_excludes_non_matching_units(self):
        response = self.svc.export(
            fields=["name"], export_format="csv", filters={"search": "Finance"}
        )
        content = response.content.decode()
        self.assertNotIn("Technology", content)
        self.assertNotIn("Operations", content)

    def test_empty_search_returns_all_active(self):
        response = self.svc.export(
            fields=["name"], export_format="csv", filters={"search": ""}
        )
        content = response.content.decode()
        self.assertIn("Finance", content)
        self.assertIn("Technology", content)
        self.assertIn("Operations", content)

    def test_search_is_case_insensitive(self):
        response = self.svc.export(
            fields=["name"], export_format="csv", filters={"search": "finance"}
        )
        content = response.content.decode()
        self.assertIn("Finance", content)
        self.assertNotIn("Technology", content)

    def test_unsupported_format_raises_validation_exception(self):
        with self.assertRaises(ValidationException):
            self.svc.export(fields=["name"], export_format="xml", filters={})

    def test_json_format_returns_list(self):
        response = self.svc.export(fields=["name"], export_format="json", filters={})
        data = json.loads(response.content.decode())
        self.assertIsInstance(data, list)


class BusinessUnitExportServiceIsActiveFilterTest(TestCase):
    def setUp(self):
        make_business_unit("ActiveUnit", "ACT", is_active=True)
        make_business_unit("InactiveUnit", "INA", is_active=False)
        self.svc = BusinessUnitExportService()

    def test_empty_is_active_filter_returns_active_only(self):
        response = self.svc.export(
            fields=["name"], export_format="csv", filters={"is_active": ""}
        )
        content = response.content.decode()
        self.assertIn("ActiveUnit", content)
        self.assertNotIn("InactiveUnit", content)

    def test_is_active_all_returns_all_units(self):
        response = self.svc.export(
            fields=["name"], export_format="csv", filters={"is_active": "all"}
        )
        content = response.content.decode()
        self.assertIn("ActiveUnit", content)
        self.assertIn("InactiveUnit", content)

    def test_is_active_false_returns_inactive_only(self):
        response = self.svc.export(
            fields=["name"], export_format="csv", filters={"is_active": "false"}
        )
        content = response.content.decode()
        self.assertNotIn("ActiveUnit", content)
        self.assertIn("InactiveUnit", content)


# ── BusinessUnitImportService.bulk_import — structure ────────────────────────


class BusinessUnitImportBulkImportStructureTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_import_service(user=self.user)

    def test_raises_if_name_column_missing(self):
        f = make_csv_file("short_name\nFIN")
        with self.assertRaises(ValidationException):
            self.svc.bulk_import(f)

    def test_raises_if_short_name_column_missing(self):
        f = make_csv_file("name\nFinance")
        with self.assertRaises(ValidationException):
            self.svc.bulk_import(f)

    def test_raises_if_row_count_exceeds_limit(self):
        rows = ["name,short_name"] + [
            f"Unit {i},U{i}"
            for i in range(BusinessUnitImportService.MAX_IMPORT_ROWS + 1)
        ]
        f = make_csv_file("\n".join(rows))
        with self.assertRaises(ValidationException):
            self.svc.bulk_import(f)

    def test_returns_expected_keys(self):
        f = make_csv_file("name,short_name\nFinance,FIN")
        result = self.svc.bulk_import(f)
        self.assertIn("total", result)
        self.assertIn("created_rows", result)
        self.assertIn("errors", result)
        self.assertIn("dry_run", result)

    def test_total_reflects_row_count(self):
        f = make_csv_file("name,short_name\nFinance,FIN\nTechnology,TECH")
        result = self.svc.bulk_import(f)
        self.assertEqual(result["total"], 2)


# ── BusinessUnitImportService.bulk_import — happy path ───────────────────────


class BusinessUnitImportBulkImportCreateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_import_service(user=self.user)

    def test_creates_unit_from_csv(self):
        f = make_csv_file("name,short_name\nFinance,FIN")
        self.svc.bulk_import(f)
        self.assertTrue(BusinessUnit.objects.filter(name="Finance").exists())

    def test_returns_correct_created_count(self):
        f = make_csv_file("name,short_name\nFinance,FIN\nTechnology,TECH")
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["created_rows"]), 2)
        self.assertEqual(result["total"], 2)

    def test_default_is_active_is_true(self):
        f = make_csv_file("name,short_name\nFinance,FIN")
        self.svc.bulk_import(f)
        self.assertTrue(BusinessUnit.objects.get(name="Finance").is_active)

    def test_is_active_false_parsed(self):
        f = make_csv_file("name,short_name,is_active\nFinance,FIN,false")
        self.svc.bulk_import(f)
        self.assertFalse(BusinessUnit.objects.get(name="Finance").is_active)

    def test_is_active_no_parsed_as_false(self):
        f = make_csv_file("name,short_name,is_active\nFinance,FIN,no")
        self.svc.bulk_import(f)
        self.assertFalse(BusinessUnit.objects.get(name="Finance").is_active)

    def test_strips_whitespace_from_name(self):
        f = make_csv_file("name,short_name\n  Finance  ,FIN")
        self.svc.bulk_import(f)
        self.assertTrue(BusinessUnit.objects.filter(name="Finance").exists())

    def test_created_by_set_to_user(self):
        f = make_csv_file("name,short_name\nFinance,FIN")
        self.svc.bulk_import(f)
        bu = BusinessUnit.objects.get(name="Finance")
        self.assertEqual(bu.created_by, self.user)


# ── BusinessUnitImportService.bulk_import — skips and errors ─────────────────


class BusinessUnitImportBulkImportSkipTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_import_service(user=self.user)

    def test_skips_row_with_missing_name(self):
        f = make_csv_file("name,short_name\n ,FIN")
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(len(result["created_rows"]), 0)

    def test_skips_row_with_missing_short_name(self):
        f = make_csv_file("name,short_name\nFinance, ")
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(len(result["created_rows"]), 0)

    def test_skips_duplicate_name(self):
        make_business_unit("Finance", "FIN")
        f = make_csv_file("name,short_name\nFinance,FIN2")
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["field"], "name")

    def test_partial_import_skips_duplicates_only(self):
        make_business_unit("Finance", "FIN")
        f = make_csv_file("name,short_name\nFinance,FIN2\nTechnology,TECH")
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["created_rows"]), 1)
        self.assertEqual(len(result["errors"]), 1)

    def test_error_entry_includes_row_number(self):
        make_business_unit("Finance", "FIN")
        f = make_csv_file("name,short_name\nFinance,FIN2")
        result = self.svc.bulk_import(f)
        self.assertEqual(result["errors"][0]["row"], 2)


# ── BusinessUnitImportService.bulk_import — dry run ──────────────────────────


class BusinessUnitImportBulkImportDryRunTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_import_service(user=self.user)

    def test_dry_run_does_not_create_units(self):
        f = make_csv_file("name,short_name\nFinance,FIN\nTechnology,TECH")
        self.svc.bulk_import(f, dry_run=True)
        self.assertEqual(BusinessUnit.objects.count(), 0)

    def test_dry_run_reports_correct_created_count(self):
        f = make_csv_file("name,short_name\nFinance,FIN\nTechnology,TECH")
        result = self.svc.bulk_import(f, dry_run=True)
        self.assertEqual(len(result["created_rows"]), 2)
        self.assertTrue(result["dry_run"])

    def test_dry_run_skips_invalid_rows(self):
        f = make_csv_file("name,short_name\n ,FIN\nTechnology,TECH")
        result = self.svc.bulk_import(f, dry_run=True)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(len(result["created_rows"]), 1)
