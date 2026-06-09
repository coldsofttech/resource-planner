from django.test import TestCase

from apps.core.exceptions import AlreadyExistsException, NotFoundException
from apps.core.types import ListParams
from apps.employment_types.models import EmploymentType
from apps.employment_types.services import (
    EmploymentTypeExportService,
    EmploymentTypeImportService,
    EmploymentTypeService,
)
from apps.employment_types.tests.factories import make_csv_file, make_employment_type


def make_service(user=None):
    return EmploymentTypeService(user=user)


def make_import_service(user=None):
    return EmploymentTypeImportService(user=user)


# ── list ──────────────────────────────────────────────────────────────────────


class EmploymentTypeServiceListTest(TestCase):
    def setUp(self):
        self.svc = make_service()
        make_employment_type("Full-time", is_active=True)
        make_employment_type("Part-time", is_active=True)
        make_employment_type("Casual", is_active=False)

    def test_defaults_to_active_only(self):
        result = self.svc.list(ListParams())
        names = [et.name for et in result.results]
        self.assertIn("Full-time", names)
        self.assertNotIn("Casual", names)

    def test_is_active_false_returns_inactive(self):
        result = self.svc.list(ListParams(filters={"is_active": "false"}))
        names = [et.name for et in result.results]
        self.assertIn("Casual", names)
        self.assertNotIn("Full-time", names)

    def test_returns_paginated_result(self):
        result = self.svc.list(ListParams())
        self.assertIsNotNone(result.pagination)

    def test_search_by_name(self):
        result = self.svc.list(ListParams(search="Full"))
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0].name, "Full-time")

    def test_returns_empty_when_no_active(self):
        EmploymentType.objects.all().delete()
        make_employment_type("Casual", is_active=False)
        result = self.svc.list(ListParams())
        self.assertEqual(len(result.results), 0)


# ── get ───────────────────────────────────────────────────────────────────────


class EmploymentTypeServiceGetTest(TestCase):
    def setUp(self):
        self.svc = make_service()
        self.et = make_employment_type("Full-time")

    def test_returns_employment_type_by_code(self):
        result = self.svc.get(code=self.et.code)
        self.assertEqual(result, self.et)

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.get(code="EMPTYPE-9999")


# ── create ────────────────────────────────────────────────────────────────────


class EmploymentTypeServiceCreateTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_creates_employment_type(self):
        et = self.svc.create(name="Full-time")
        self.assertIsNotNone(et.pk)
        self.assertEqual(et.name, "Full-time")

    def test_creates_with_is_default_true(self):
        et = self.svc.create(name="Full-time", is_default=True)
        self.assertTrue(et.is_default)

    def test_creates_with_is_active_false(self):
        et = self.svc.create(name="Full-time", is_active=False)
        self.assertFalse(et.is_active)

    def test_raises_already_exists_on_duplicate_name(self):
        self.svc.create(name="Full-time")
        with self.assertRaises(AlreadyExistsException):
            self.svc.create(name="Full-time")

    def test_code_is_assigned(self):
        et = self.svc.create(name="Full-time")
        self.assertTrue(et.code.startswith("EMPTYPE-"))


# ── update ────────────────────────────────────────────────────────────────────


class EmploymentTypeServiceUpdateTest(TestCase):
    def setUp(self):
        self.svc = make_service()
        self.et = make_employment_type("Full-time")

    def test_updates_name(self):
        updated = self.svc.update(code=self.et.code, name="Full Time Employment")
        self.assertEqual(updated.name, "Full Time Employment")

    def test_updates_is_default(self):
        updated = self.svc.update(code=self.et.code, is_default=True)
        self.assertTrue(updated.is_default)

    def test_updates_is_active(self):
        updated = self.svc.update(code=self.et.code, is_active=False)
        self.assertFalse(updated.is_active)

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.update(code="EMPTYPE-9999", name="Anything")

    def test_raises_already_exists_on_name_conflict(self):
        make_employment_type("Part-time")
        with self.assertRaises(AlreadyExistsException):
            self.svc.update(code=self.et.code, name="Part-time")


# ── activate / deactivate ─────────────────────────────────────────────────────


class EmploymentTypeServiceToggleTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_activate_sets_is_active_true(self):
        et = make_employment_type(is_active=False)
        result = self.svc.activate(code=et.code)
        self.assertTrue(result.is_active)

    def test_deactivate_sets_is_active_false(self):
        et = make_employment_type(is_active=True)
        result = self.svc.deactivate(code=et.code)
        self.assertFalse(result.is_active)

    def test_activate_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            self.svc.activate(code="EMPTYPE-9999")

    def test_deactivate_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            self.svc.deactivate(code="EMPTYPE-9999")


# ── delete ────────────────────────────────────────────────────────────────────


class EmploymentTypeServiceDeleteTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_deletes_employment_type(self):
        et = make_employment_type()
        code = et.code
        self.svc.delete(code=code)
        self.assertFalse(EmploymentType.objects.filter(code=code).exists())

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.delete(code="EMPTYPE-9999")


# ── options ───────────────────────────────────────────────────────────────────


class EmploymentTypeServiceOptionsTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_returns_active_types_only(self):
        make_employment_type("Full-time", is_active=True)
        make_employment_type("Casual", is_active=False)
        options = self.svc.options()
        names = [o["name"] for o in options]
        self.assertIn("Full-time", names)
        self.assertNotIn("Casual", names)

    def test_option_contains_code_name_is_default(self):
        make_employment_type("Full-time", is_active=True, is_default=True)
        options = self.svc.options()
        self.assertEqual(len(options), 1)
        self.assertIn("code", options[0])
        self.assertIn("name", options[0])
        self.assertIn("is_default", options[0])
        self.assertTrue(options[0]["is_default"])


# ── import ────────────────────────────────────────────────────────────────────


class EmploymentTypeImportServiceBulkImportTest(TestCase):
    def setUp(self):
        self.svc = make_import_service()

    def test_imports_valid_csv(self):
        f = make_csv_file("name\nFull-time\nPart-time")
        result = self.svc.bulk_import(f)
        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["errors"]), 0)
        self.assertTrue(EmploymentType.objects.filter(name="Full-time").exists())

    def test_skips_duplicate_names(self):
        make_employment_type("Full-time")
        f = make_csv_file("name\nFull-time")
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)

    def test_dry_run_does_not_create_records(self):
        f = make_csv_file("name\nFull-time")
        self.svc.bulk_import(f, dry_run=True)
        self.assertFalse(EmploymentType.objects.filter(name="Full-time").exists())

    def test_raises_on_missing_name_column(self):
        from apps.core.exceptions import ValidationException

        f = make_csv_file("employment_type\nFull-time")
        with self.assertRaises(ValidationException):
            self.svc.bulk_import(f)

    def test_respects_is_default_column(self):
        f = make_csv_file("name,is_default\nFull-time,true")
        self.svc.bulk_import(f)
        et = EmploymentType.objects.get(name="Full-time")
        self.assertTrue(et.is_default)


# ── export ────────────────────────────────────────────────────────────────────


class EmploymentTypeExportServiceSearchFilterTest(TestCase):
    def setUp(self):
        make_employment_type("Full-time", is_active=True)
        make_employment_type("Part-time", is_active=True)
        make_employment_type("Casual", is_active=True)
        self.svc = EmploymentTypeExportService()

    def test_search_filter_includes_matching_name(self):
        response = self.svc.export(
            fields=["name"],
            export_format="csv",
            filters={"search": "Full"},
        )
        self.assertIn("Full-time", response.content.decode())

    def test_search_filter_excludes_non_matching(self):
        response = self.svc.export(
            fields=["name"],
            export_format="csv",
            filters={"search": "Full"},
        )
        self.assertNotIn("Part-time", response.content.decode())
