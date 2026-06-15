from django.test import TestCase

from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.core.types import ListParams
from apps.projects.models import ProjectType
from apps.projects.services import (
    ProjectTypeExportService,
    ProjectTypeImportService,
    ProjectTypeService,
)
from apps.projects.tests.factories import make_csv_file, make_project_type
from apps.users.tests.factories import make_user


def make_service(user=None):
    return ProjectTypeService(user=user)


def make_import_service(user=None):
    return ProjectTypeImportService(user=user)


# ── list ──────────────────────────────────────────────────────────────────────


class ProjectTypeServiceListTest(TestCase):
    def setUp(self):
        self.svc = make_service()
        make_project_type("Alpha", is_active=True)
        make_project_type("Beta", is_active=True)
        make_project_type("Gamma", is_active=False)

    def test_defaults_to_active_only(self):
        result = self.svc.list(ListParams())
        names = [pt.name for pt in result.results]
        self.assertIn("Alpha", names)
        self.assertNotIn("Gamma", names)

    def test_is_active_false_returns_inactive(self):
        result = self.svc.list(ListParams(filters={"is_active": "false"}))
        names = [pt.name for pt in result.results]
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


class ProjectTypeServiceGetTest(TestCase):
    def test_returns_project_type_by_code(self):
        pt = make_project_type("Internal")
        svc = make_service()
        result = svc.get(code=pt.code)
        self.assertEqual(result, pt)

    def test_raises_not_found_for_unknown_code(self):
        svc = make_service()
        with self.assertRaises(NotFoundException):
            svc.get(code="PROJTYPE-99999")


# ── create ────────────────────────────────────────────────────────────────────


class ProjectTypeServiceCreateTest(TestCase):
    def test_creates_project_type_successfully(self):
        svc = make_service()
        pt = svc.create(name="Internal")
        self.assertIsNotNone(pt.pk)
        self.assertEqual(pt.name, "Internal")
        self.assertTrue(pt.is_active)
        self.assertFalse(pt.is_protected)

    def test_duplicate_name_raises_already_exists(self):
        make_project_type("Internal")
        svc = make_service()
        with self.assertRaises(AlreadyExistsException):
            svc.create(name="Internal")

    def test_creates_with_description(self):
        svc = make_service()
        pt = svc.create(name="Internal", description="An internal type")
        self.assertEqual(pt.description, "An internal type")

    def test_creates_inactive_when_specified(self):
        svc = make_service()
        pt = svc.create(name="Internal", is_active=False)
        self.assertFalse(pt.is_active)

    def test_sets_created_by(self):
        user = make_user()
        svc = make_service(user=user)
        pt = svc.create(name="Audited")
        self.assertEqual(pt.created_by, user)


# ── update ────────────────────────────────────────────────────────────────────


class ProjectTypeServiceUpdateTest(TestCase):
    def test_updates_name(self):
        pt = make_project_type("Old Name")
        svc = make_service()
        updated = svc.update(code=pt.code, name="New Name")
        self.assertEqual(updated.name, "New Name")

    def test_updates_description(self):
        pt = make_project_type("Internal")
        svc = make_service()
        updated = svc.update(code=pt.code, description="Updated description")
        self.assertEqual(updated.description, "Updated description")

    def test_duplicate_name_raises_already_exists(self):
        pt1 = make_project_type("Alpha")
        make_project_type("Beta")
        svc = make_service()
        with self.assertRaises(AlreadyExistsException):
            svc.update(code=pt1.code, name="Beta")

    def test_protected_raises_validation_error(self):
        pt = make_project_type("Protected", is_protected=True)
        svc = make_service()
        with self.assertRaises(ValidationException):
            svc.update(code=pt.code, name="Renamed")

    def test_raises_not_found_for_unknown_code(self):
        svc = make_service()
        with self.assertRaises(NotFoundException):
            svc.update(code="PROJTYPE-99999", name="X")


# ── activate / deactivate ─────────────────────────────────────────────────────


class ProjectTypeServiceToggleTest(TestCase):
    def test_activate_inactive_project_type(self):
        pt = make_project_type("Alpha", is_active=False)
        svc = make_service()
        result = svc.activate(code=pt.code)
        self.assertTrue(result.is_active)

    def test_deactivate_active_project_type(self):
        pt = make_project_type("Alpha", is_active=True)
        svc = make_service()
        result = svc.deactivate(code=pt.code)
        self.assertFalse(result.is_active)

    def test_activate_protected_raises_validation_error(self):
        pt = make_project_type("Protected", is_protected=True, is_active=False)
        svc = make_service()
        with self.assertRaises(ValidationException):
            svc.activate(code=pt.code)

    def test_deactivate_protected_raises_validation_error(self):
        pt = make_project_type("Protected", is_protected=True, is_active=True)
        svc = make_service()
        with self.assertRaises(ValidationException):
            svc.deactivate(code=pt.code)


# ── delete ────────────────────────────────────────────────────────────────────


class ProjectTypeServiceDeleteTest(TestCase):
    def test_deletes_project_type(self):
        pt = make_project_type("Temp")
        code = pt.code
        svc = make_service()
        svc.delete(code=code)
        self.assertFalse(ProjectType.objects.filter(code=code).exists())

    def test_protected_raises_validation_error(self):
        pt = make_project_type("Protected", is_protected=True)
        svc = make_service()
        with self.assertRaises(ValidationException):
            svc.delete(code=pt.code)

    def test_raises_not_found_for_unknown_code(self):
        svc = make_service()
        with self.assertRaises(NotFoundException):
            svc.delete(code="PROJTYPE-99999")


# ── options / stats ───────────────────────────────────────────────────────────


class ProjectTypeServiceMetaTest(TestCase):
    def test_options_returns_active_only(self):
        make_project_type("Active")
        make_project_type("Inactive", is_active=False)
        svc = make_service()
        names = [o["name"] for o in svc.options()]
        self.assertIn("Active", names)
        self.assertNotIn("Inactive", names)

    def test_options_include_code(self):
        make_project_type("Internal")
        svc = make_service()
        codes = [o["code"] for o in svc.options()]
        self.assertTrue(all(c.startswith("PROJTYPE-") for c in codes))

    def test_stats_returns_counts(self):
        make_project_type("A", is_active=True)
        make_project_type("B", is_active=False)
        svc = make_service()
        stats = svc.stats()
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["active"], 1)
        self.assertEqual(stats["inactive"], 1)


# ── import ────────────────────────────────────────────────────────────────────


class ProjectTypeImportServiceTest(TestCase):
    def test_imports_valid_csv(self):
        svc = make_import_service()
        f = make_csv_file(
            "name,description\nInternal,First\nExternal,Second\n", "project_types.csv"
        )
        result = svc.bulk_import(f)
        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["created_rows"]), 2)
        self.assertEqual(len(result["errors"]), 0)
        self.assertTrue(ProjectType.objects.filter(name="Internal").exists())

    def test_dry_run_does_not_persist(self):
        svc = make_import_service()
        f = make_csv_file("name\nInternal\n", "project_types.csv")
        result = svc.bulk_import(f, dry_run=True)
        self.assertEqual(len(result["created_rows"]), 1)
        self.assertFalse(ProjectType.objects.filter(name="Internal").exists())

    def test_skips_duplicate_names(self):
        make_project_type("Internal")
        svc = make_import_service()
        f = make_csv_file("name\nInternal\n", "project_types.csv")
        result = svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)

    def test_missing_name_column_raises_validation_error(self):
        svc = make_import_service()
        f = make_csv_file("description\nSomething\n", "project_types.csv")
        with self.assertRaises(ValidationException):
            svc.bulk_import(f)


# ── export ────────────────────────────────────────────────────────────────────


class ProjectTypeExportServiceTest(TestCase):
    def setUp(self):
        make_project_type("Internal")
        make_project_type("External")

    def test_csv_export_contains_name(self):
        svc = ProjectTypeExportService()
        response = svc.export(fields=["name"], export_format="csv")
        self.assertIn("Internal", response.content.decode())

    def test_search_filter_applies(self):
        svc = ProjectTypeExportService()
        response = svc.export(
            fields=["name"],
            export_format="csv",
            filters={"search": "Internal"},
        )
        content = response.content.decode()
        self.assertIn("Internal", content)
        self.assertNotIn("External", content)
