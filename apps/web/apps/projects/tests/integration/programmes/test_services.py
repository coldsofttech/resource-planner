from django.test import TestCase

from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.core.types import ListParams
from apps.projects.models import Programme
from apps.projects.services import (
    ProgrammeExportService,
    ProgrammeImportService,
    ProgrammeService,
)
from apps.projects.tests.factories import make_csv_file, make_programme
from apps.users.tests.factories import make_user


def make_service(user=None):
    return ProgrammeService(user=user)


def make_import_service(user=None):
    return ProgrammeImportService(user=user)


# ── list ──────────────────────────────────────────────────────────────────────


class ProgrammeServiceListTest(TestCase):
    def setUp(self):
        self.svc = make_service()
        make_programme("Alpha", is_active=True)
        make_programme("Beta", is_active=True)
        make_programme("Gamma", is_active=False)

    def test_defaults_to_active_only(self):
        result = self.svc.list(ListParams())
        names = [p.name for p in result.results]
        self.assertIn("Alpha", names)
        self.assertNotIn("Gamma", names)

    def test_is_active_false_returns_inactive(self):
        result = self.svc.list(ListParams(filters={"is_active": "false"}))
        names = [p.name for p in result.results]
        self.assertIn("Gamma", names)
        self.assertNotIn("Alpha", names)

    def test_search_by_name(self):
        result = self.svc.list(ListParams(search="Alpha"))
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0].name, "Alpha")

    def test_returns_paginated_result(self):
        result = self.svc.list(ListParams())
        self.assertIsNotNone(result.pagination)


# ── get ───────────────────────────────────────────────────────────────────────


class ProgrammeServiceGetTest(TestCase):
    def test_returns_programme_by_code(self):
        p = make_programme("Alpha")
        svc = make_service()
        result = svc.get(code=p.code)
        self.assertEqual(result, p)

    def test_raises_not_found_for_unknown_code(self):
        svc = make_service()
        with self.assertRaises(NotFoundException):
            svc.get(code="PROG-99999")


# ── create ────────────────────────────────────────────────────────────────────


class ProgrammeServiceCreateTest(TestCase):
    def test_creates_programme_successfully(self):
        svc = make_service()
        p = svc.create(name="New Programme")
        self.assertIsNotNone(p.pk)
        self.assertEqual(p.name, "New Programme")
        self.assertTrue(p.is_active)
        self.assertFalse(p.is_protected)

    def test_duplicate_name_raises_already_exists(self):
        make_programme("Existing")
        svc = make_service()
        with self.assertRaises(AlreadyExistsException):
            svc.create(name="Existing")

    def test_creates_with_description(self):
        svc = make_service()
        p = svc.create(name="Alpha", description="A test")
        self.assertEqual(p.description, "A test")

    def test_creates_inactive_when_specified(self):
        svc = make_service()
        p = svc.create(name="Inactive Prog", is_active=False)
        self.assertFalse(p.is_active)

    def test_sets_created_by(self):
        user = make_user()
        svc = make_service(user=user)
        p = svc.create(name="Audited")
        self.assertEqual(p.created_by, user)


# ── update ────────────────────────────────────────────────────────────────────


class ProgrammeServiceUpdateTest(TestCase):
    def test_updates_name(self):
        p = make_programme("Old Name")
        svc = make_service()
        updated = svc.update(code=p.code, name="New Name")
        self.assertEqual(updated.name, "New Name")

    def test_updates_description(self):
        p = make_programme("Alpha")
        svc = make_service()
        updated = svc.update(code=p.code, description="Updated desc")
        self.assertEqual(updated.description, "Updated desc")

    def test_duplicate_name_raises_already_exists(self):
        p1 = make_programme("Alpha")
        make_programme("Beta")
        svc = make_service()
        with self.assertRaises(AlreadyExistsException):
            svc.update(code=p1.code, name="Beta")

    def test_protected_programme_raises_validation_error(self):
        p = Programme.objects.get(name="Others")
        svc = make_service()
        with self.assertRaises(ValidationException):
            svc.update(code=p.code, name="Renamed")

    def test_raises_not_found_for_unknown_code(self):
        svc = make_service()
        with self.assertRaises(NotFoundException):
            svc.update(code="PROG-99999", name="X")


# ── activate / deactivate ─────────────────────────────────────────────────────


class ProgrammeServiceToggleTest(TestCase):
    def test_activate_inactive_programme(self):
        p = make_programme("Alpha", is_active=False)
        svc = make_service()
        result = svc.activate(code=p.code)
        self.assertTrue(result.is_active)

    def test_deactivate_active_programme(self):
        p = make_programme("Alpha", is_active=True)
        svc = make_service()
        result = svc.deactivate(code=p.code)
        self.assertFalse(result.is_active)

    def test_activate_protected_raises_validation_error(self):
        p = Programme.objects.get(name="Others")
        p.is_active = False
        p.save()
        svc = make_service()
        with self.assertRaises(ValidationException):
            svc.activate(code=p.code)

    def test_deactivate_protected_raises_validation_error(self):
        p = Programme.objects.get(name="Others")
        svc = make_service()
        with self.assertRaises(ValidationException):
            svc.deactivate(code=p.code)


# ── delete ────────────────────────────────────────────────────────────────────


class ProgrammeServiceDeleteTest(TestCase):
    def test_deletes_programme(self):
        p = make_programme("Temp")
        code = p.code
        svc = make_service()
        svc.delete(code=code)
        self.assertFalse(Programme.objects.filter(code=code).exists())

    def test_protected_raises_validation_error(self):
        p = Programme.objects.get(name="Others")
        svc = make_service()
        with self.assertRaises(ValidationException):
            svc.delete(code=p.code)

    def test_raises_not_found_for_unknown_code(self):
        svc = make_service()
        with self.assertRaises(NotFoundException):
            svc.delete(code="PROG-99999")


# ── options / stats ───────────────────────────────────────────────────────────


class ProgrammeServiceMetaTest(TestCase):
    def test_options_returns_active_only(self):
        make_programme("Active")
        make_programme("Inactive", is_active=False)
        svc = make_service()
        codes = [o["code"] for o in svc.options()]
        names = [o["name"] for o in svc.options()]
        self.assertIn("Active", names)
        self.assertNotIn("Inactive", names)
        self.assertTrue(all(c.startswith("PROG-") for c in codes))

    def test_stats_returns_counts(self):
        make_programme("A", is_active=True)
        make_programme("B", is_active=False)
        svc = make_service()
        stats = svc.stats()
        # +1 total and +1 active for the seeded "Others" protected programme
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["active"], 2)
        self.assertEqual(stats["inactive"], 1)


# ── import ────────────────────────────────────────────────────────────────────


class ProgrammeImportServiceTest(TestCase):
    def test_imports_valid_csv(self):
        svc = make_import_service()
        f = make_csv_file("name,description\nAlpha,First\nBeta,Second\n")
        result = svc.bulk_import(f)
        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["created_rows"]), 2)
        self.assertEqual(len(result["errors"]), 0)
        self.assertTrue(Programme.objects.filter(name="Alpha").exists())

    def test_dry_run_does_not_persist(self):
        svc = make_import_service()
        f = make_csv_file("name\nAlpha\n")
        result = svc.bulk_import(f, dry_run=True)
        self.assertEqual(len(result["created_rows"]), 1)
        self.assertFalse(Programme.objects.filter(name="Alpha").exists())

    def test_skips_duplicate_names(self):
        make_programme("Alpha")
        svc = make_import_service()
        f = make_csv_file("name\nAlpha\n")
        result = svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)

    def test_missing_name_column_raises_validation_error(self):
        from apps.core.exceptions import ValidationException

        svc = make_import_service()
        f = make_csv_file("description\nSomething\n")
        with self.assertRaises(ValidationException):
            svc.bulk_import(f)


# ── export ────────────────────────────────────────────────────────────────────


class ProgrammeExportServiceTest(TestCase):
    def setUp(self):
        make_programme("Alpha")
        make_programme("Beta")

    def test_csv_export_contains_name(self):
        svc = ProgrammeExportService()
        response = svc.export(fields=["name"], export_format="csv")
        self.assertIn("Alpha", response.content.decode())

    def test_search_filter_applies(self):
        svc = ProgrammeExportService()
        response = svc.export(
            fields=["name"],
            export_format="csv",
            filters={"search": "Alpha"},
        )
        content = response.content.decode()
        self.assertIn("Alpha", content)
        self.assertNotIn("Beta", content)
