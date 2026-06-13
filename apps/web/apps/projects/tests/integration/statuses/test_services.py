from django.test import TestCase

from apps.core.exceptions import AlreadyExistsException, NotFoundException
from apps.core.types import ListParams
from apps.projects.models import ProjectSubStatus
from apps.projects.services import (
    ProjectStatusExportService,
    ProjectStatusService,
    ProjectSubStatusExportService,
    ProjectSubStatusGlobalImportService,
    ProjectSubStatusImportService,
    ProjectSubStatusService,
)
from apps.projects.tests.factories import (
    make_csv_file,
    make_project_status,
    make_project_substatus,
)
from apps.users.tests.factories import make_user


def make_status_service(user=None):
    return ProjectStatusService(user=user)


def make_substatus_service(user=None):
    return ProjectSubStatusService(user=user)


def make_import_service(user=None):
    return ProjectSubStatusImportService(user=user)


def make_global_import_service(user=None):
    return ProjectSubStatusGlobalImportService(user=user)


# ── ProjectStatusService: list ────────────────────────────────────────────────


class ProjectStatusServiceListTest(TestCase):
    def setUp(self):
        self.svc = make_status_service()
        make_project_status("Alpha", is_active=True)
        make_project_status("Beta", is_active=True)
        make_project_status("Gamma", is_active=False)

    def test_defaults_to_active_only(self):
        result = self.svc.list(ListParams())
        names = [s.name for s in result.results]
        self.assertIn("Alpha", names)
        self.assertNotIn("Gamma", names)

    def test_is_active_false_returns_inactive(self):
        result = self.svc.list(ListParams(filters={"is_active": "false"}))
        names = [s.name for s in result.results]
        self.assertIn("Gamma", names)
        self.assertNotIn("Alpha", names)

    def test_search_by_name(self):
        result = self.svc.list(ListParams(search="Alpha"))
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0].name, "Alpha")

    def test_returns_paginated_result(self):
        result = self.svc.list(ListParams())
        self.assertIsNotNone(result.pagination)


# ── ProjectStatusService: get ─────────────────────────────────────────────────


class ProjectStatusServiceGetTest(TestCase):
    def test_returns_status_by_code(self):
        s = make_project_status("Alpha")
        svc = make_status_service()
        result = svc.get(code=s.code)
        self.assertEqual(result, s)

    def test_raises_not_found_for_unknown_code(self):
        svc = make_status_service()
        with self.assertRaises(NotFoundException):
            svc.get(code="PROJSTAT-99999")


# ── ProjectStatusService: options / stats ─────────────────────────────────────


class ProjectStatusServiceMetaTest(TestCase):
    def test_options_returns_active_only(self):
        make_project_status("Active")
        make_project_status("Inactive", is_active=False)
        svc = make_status_service()
        names = [o["name"] for o in svc.options()]
        self.assertIn("Active", names)
        self.assertNotIn("Inactive", names)

    def test_options_include_code(self):
        make_project_status("Active")
        svc = make_status_service()
        codes = [o["code"] for o in svc.options()]
        self.assertTrue(all(c.startswith("PROJSTAT-") for c in codes))

    def test_stats_returns_counts(self):
        svc = make_status_service()
        baseline = svc.stats()
        make_project_status("A", is_active=True)
        make_project_status("B", is_active=False)
        stats = svc.stats()
        self.assertEqual(stats["total"], baseline["total"] + 2)
        self.assertEqual(stats["active"], baseline["active"] + 1)
        self.assertEqual(stats["inactive"], baseline["inactive"] + 1)


# ── ProjectStatusExportService ────────────────────────────────────────────────


class ProjectStatusExportServiceTest(TestCase):
    def setUp(self):
        make_project_status("Alpha")
        make_project_status("Beta")

    def test_csv_export_contains_name(self):
        svc = ProjectStatusExportService()
        response = svc.export(fields=["name"], export_format="csv")
        self.assertIn("Alpha", response.content.decode())

    def test_search_filter_applies(self):
        svc = ProjectStatusExportService()
        response = svc.export(
            fields=["name"],
            export_format="csv",
            filters={"search": "Alpha"},
        )
        content = response.content.decode()
        self.assertIn("Alpha", content)
        self.assertNotIn("Beta", content)


# ── ProjectSubStatusService: list ─────────────────────────────────────────────


class ProjectSubStatusServiceListTest(TestCase):
    def setUp(self):
        self.status = make_project_status("Active")
        self.svc = make_substatus_service()
        make_project_substatus("Draft", status=self.status, is_active=True)
        make_project_substatus("Archived", status=self.status, is_active=False)

    def test_defaults_to_active_only(self):
        result = self.svc.list(ListParams())
        names = [ss.name for ss in result.results]
        self.assertIn("Draft", names)
        self.assertNotIn("Archived", names)

    def test_is_active_false_returns_inactive(self):
        result = self.svc.list(ListParams(filters={"is_active": "false"}))
        names = [ss.name for ss in result.results]
        self.assertIn("Archived", names)
        self.assertNotIn("Draft", names)

    def test_search_by_name(self):
        result = self.svc.list(ListParams(search="Draft"))
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0].name, "Draft")

    def test_returns_paginated_result(self):
        result = self.svc.list(ListParams())
        self.assertIsNotNone(result.pagination)

    def test_status_scope_filters_by_parent(self):
        s2 = make_project_status("Other")
        make_project_substatus("Other Draft", status=s2, is_active=True)
        self.svc._status_scope = self.status.code
        result = self.svc.list(ListParams(filters={"is_active": "all"}))
        names = [ss.name for ss in result.results]
        self.assertIn("Draft", names)
        self.assertNotIn("Other Draft", names)


# ── ProjectSubStatusService: get ──────────────────────────────────────────────


class ProjectSubStatusServiceGetTest(TestCase):
    def test_returns_substatus_by_code(self):
        ss = make_project_substatus("Draft")
        svc = make_substatus_service()
        result = svc.get(code=ss.code)
        self.assertEqual(result, ss)

    def test_raises_not_found_for_unknown_code(self):
        svc = make_substatus_service()
        with self.assertRaises(NotFoundException):
            svc.get(code="PROJSUBSTAT-99999")


# ── ProjectSubStatusService: create ───────────────────────────────────────────


class ProjectSubStatusServiceCreateTest(TestCase):
    def test_creates_substatus_successfully(self):
        status = make_project_status("Active")
        svc = make_substatus_service()
        ss = svc.create(name="Draft", status=status)
        self.assertIsNotNone(ss.pk)
        self.assertEqual(ss.name, "Draft")
        self.assertTrue(ss.is_active)
        self.assertEqual(ss.main_status, status)

    def test_order_starts_at_one(self):
        status = make_project_status("Active")
        svc = make_substatus_service()
        ss = svc.create(name="Draft", status=status)
        self.assertEqual(ss.order, 1)

    def test_order_increments_for_subsequent_substatuses(self):
        status = make_project_status("Active")
        svc = make_substatus_service()
        ss1 = svc.create(name="Draft", status=status)
        ss2 = svc.create(name="Review", status=status)
        self.assertEqual(ss2.order, ss1.order + 1)

    def test_duplicate_name_within_status_raises_already_exists(self):
        status = make_project_status("Active")
        make_project_substatus("Draft", status=status)
        svc = make_substatus_service()
        with self.assertRaises(AlreadyExistsException):
            svc.create(name="Draft", status=status)

    def test_creates_inactive_when_specified(self):
        status = make_project_status("Active")
        svc = make_substatus_service()
        ss = svc.create(name="Draft", status=status, is_active=False)
        self.assertFalse(ss.is_active)

    def test_sets_created_by(self):
        user = make_user()
        status = make_project_status("Active")
        svc = make_substatus_service(user=user)
        ss = svc.create(name="Audited", status=status)
        self.assertEqual(ss.created_by, user)

    def test_same_name_different_status_is_allowed(self):
        s1 = make_project_status("Alpha")
        s2 = make_project_status("Beta")
        svc = make_substatus_service()
        ss1 = svc.create(name="Draft", status=s1)
        ss2 = svc.create(name="Draft", status=s2)
        self.assertIsNotNone(ss1.pk)
        self.assertIsNotNone(ss2.pk)


# ── ProjectSubStatusService: update ───────────────────────────────────────────


class ProjectSubStatusServiceUpdateTest(TestCase):
    def test_updates_name(self):
        ss = make_project_substatus("Old Name")
        svc = make_substatus_service()
        updated = svc.update(code=ss.code, name="New Name")
        self.assertEqual(updated.name, "New Name")

    def test_updates_is_active(self):
        ss = make_project_substatus("Draft", is_active=True)
        svc = make_substatus_service()
        updated = svc.update(code=ss.code, is_active=False)
        self.assertFalse(updated.is_active)

    def test_duplicate_name_within_status_raises_already_exists(self):
        status = make_project_status("Active")
        ss1 = make_project_substatus("Draft", status=status)
        make_project_substatus("Review", status=status)
        svc = make_substatus_service()
        with self.assertRaises(AlreadyExistsException):
            svc.update(code=ss1.code, name="Review")

    def test_raises_not_found_for_unknown_code(self):
        svc = make_substatus_service()
        with self.assertRaises(NotFoundException):
            svc.update(code="PROJSUBSTAT-99999", name="X")

    def test_updating_name_to_same_value_does_not_raise(self):
        ss = make_project_substatus("Draft")
        svc = make_substatus_service()
        updated = svc.update(code=ss.code, name="Draft")
        self.assertEqual(updated.name, "Draft")


# ── ProjectSubStatusService: activate / deactivate ────────────────────────────


class ProjectSubStatusServiceToggleTest(TestCase):
    def test_activate_inactive_substatus(self):
        ss = make_project_substatus("Draft", is_active=False)
        svc = make_substatus_service()
        result = svc.activate(code=ss.code)
        self.assertTrue(result.is_active)

    def test_deactivate_active_substatus(self):
        ss = make_project_substatus("Draft", is_active=True)
        svc = make_substatus_service()
        result = svc.deactivate(code=ss.code)
        self.assertFalse(result.is_active)

    def test_activate_already_active_is_idempotent(self):
        ss = make_project_substatus("Draft", is_active=True)
        svc = make_substatus_service()
        result = svc.activate(code=ss.code)
        self.assertTrue(result.is_active)

    def test_deactivate_already_inactive_is_idempotent(self):
        ss = make_project_substatus("Draft", is_active=False)
        svc = make_substatus_service()
        result = svc.deactivate(code=ss.code)
        self.assertFalse(result.is_active)


# ── ProjectSubStatusService: delete ───────────────────────────────────────────


class ProjectSubStatusServiceDeleteTest(TestCase):
    def test_deletes_substatus(self):
        ss = make_project_substatus("Temp")
        code = ss.code
        svc = make_substatus_service()
        svc.delete(code=code)
        self.assertFalse(ProjectSubStatus.objects.filter(code=code).exists())

    def test_raises_not_found_for_unknown_code(self):
        svc = make_substatus_service()
        with self.assertRaises(NotFoundException):
            svc.delete(code="PROJSUBSTAT-99999")


# ── ProjectSubStatusService: reorder ──────────────────────────────────────────


class ProjectSubStatusServiceReorderTest(TestCase):
    def test_reorders_substatuses(self):
        status = make_project_status("Active")
        ss1 = make_project_substatus("Alpha", status=status, order=1)
        ss2 = make_project_substatus("Beta", status=status, order=2)
        ss3 = make_project_substatus("Gamma", status=status, order=3)
        svc = make_substatus_service()
        svc.reorder(status=status, codes=[ss3.code, ss1.code, ss2.code])
        ss1.refresh_from_db()
        ss2.refresh_from_db()
        ss3.refresh_from_db()
        self.assertEqual(ss3.order, 1)
        self.assertEqual(ss1.order, 2)
        self.assertEqual(ss2.order, 3)

    def test_raises_not_found_for_unknown_code_in_reorder(self):
        status = make_project_status("Active")
        svc = make_substatus_service()
        with self.assertRaises(NotFoundException):
            svc.reorder(status=status, codes=["PROJSUBSTAT-99999"])


# ── ProjectSubStatusService: options / stats ──────────────────────────────────


class ProjectSubStatusServiceMetaTest(TestCase):
    def test_options_returns_active_only(self):
        status = make_project_status("Active")
        make_project_substatus("Draft", status=status, is_active=True)
        make_project_substatus("Archived", status=status, is_active=False)
        svc = make_substatus_service()
        names = [o["name"] for o in svc.options()]
        self.assertIn("Draft", names)
        self.assertNotIn("Archived", names)

    def test_options_filtered_by_status_code(self):
        s1 = make_project_status("Alpha")
        s2 = make_project_status("Beta")
        make_project_substatus("Draft", status=s1)
        make_project_substatus("Review", status=s2)
        svc = make_substatus_service()
        names = [o["name"] for o in svc.options(status_code=s1.code)]
        self.assertIn("Draft", names)
        self.assertNotIn("Review", names)

    def test_stats_returns_counts(self):
        status = make_project_status("Active")
        make_project_substatus("A", status=status, is_active=True)
        make_project_substatus("B", status=status, is_active=False)
        svc = make_substatus_service()
        stats = svc.stats()
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["active"], 1)
        self.assertEqual(stats["inactive"], 1)

    def test_stats_filtered_by_status_code(self):
        s1 = make_project_status("Alpha")
        s2 = make_project_status("Beta")
        make_project_substatus("Draft", status=s1, is_active=True)
        make_project_substatus("Review", status=s2, is_active=True)
        svc = make_substatus_service()
        stats = svc.stats(status_code=s1.code)
        self.assertEqual(stats["total"], 1)
        self.assertEqual(stats["active"], 1)


# ── ProjectSubStatusImportService ─────────────────────────────────────────────


class ProjectSubStatusImportServiceTest(TestCase):
    def test_imports_valid_csv(self):
        status = make_project_status("Active")
        svc = make_import_service()
        f = make_csv_file("name\nDraft\nReview\n", name="sub.csv")
        result = svc.bulk_import(f, status=status)
        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["created_rows"]), 2)
        self.assertEqual(len(result["errors"]), 0)

    def test_dry_run_does_not_persist(self):
        status = make_project_status("Active")
        svc = make_import_service()
        f = make_csv_file("name\nDraft\n", name="sub.csv")
        result = svc.bulk_import(f, dry_run=True, status=status)
        self.assertEqual(len(result["created_rows"]), 1)
        self.assertFalse(ProjectSubStatus.objects.filter(name="Draft").exists())

    def test_skips_duplicate_names(self):
        status = make_project_status("Active")
        make_project_substatus("Draft", status=status)
        svc = make_import_service()
        f = make_csv_file("name\nDraft\n", name="sub.csv")
        result = svc.bulk_import(f, status=status)
        self.assertEqual(len(result["errors"]), 1)

    def test_missing_name_column_raises_validation_error(self):
        from apps.core.exceptions import ValidationException

        status = make_project_status("Active")
        svc = make_import_service()
        f = make_csv_file("description\nSomething\n", name="sub.csv")
        with self.assertRaises(ValidationException):
            svc.bulk_import(f, status=status)

    def test_no_parent_status_raises_validation_error(self):
        from apps.core.exceptions import ValidationException

        svc = make_import_service()
        f = make_csv_file("name\nDraft\n", name="sub.csv")
        with self.assertRaises(ValidationException):
            svc.bulk_import(f)


# ── ProjectSubStatusGlobalImportService ───────────────────────────────────────


class ProjectSubStatusGlobalImportServiceTest(TestCase):
    def test_imports_valid_csv_with_status_code_column(self):
        status = make_project_status("Active")
        svc = make_global_import_service()
        f = make_csv_file(
            f"main_status_code,name\n{status.code},Draft\n{status.code},Review\n",
            name="global_sub.csv",
        )
        result = svc.bulk_import(f)
        self.assertEqual(result["total"], 2)
        self.assertEqual(len(result["created_rows"]), 2)
        self.assertEqual(len(result["errors"]), 0)

    def test_unknown_status_code_produces_error(self):
        svc = make_global_import_service()
        f = make_csv_file(
            "main_status_code,name\nPROJSTAT-99999,Draft\n",
            name="global_sub.csv",
        )
        result = svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)

    def test_dry_run_does_not_persist(self):
        status = make_project_status("Active")
        svc = make_global_import_service()
        f = make_csv_file(
            f"main_status_code,name\n{status.code},Draft\n",
            name="global_sub.csv",
        )
        result = svc.bulk_import(f, dry_run=True)
        self.assertEqual(len(result["created_rows"]), 1)
        self.assertFalse(ProjectSubStatus.objects.filter(name="Draft").exists())

    def test_missing_required_columns_raises_validation_error(self):
        from apps.core.exceptions import ValidationException

        svc = make_global_import_service()
        f = make_csv_file("name\nDraft\n", name="global_sub.csv")
        with self.assertRaises(ValidationException):
            svc.bulk_import(f)


# ── ProjectSubStatusExportService ─────────────────────────────────────────────


class ProjectSubStatusExportServiceTest(TestCase):
    def setUp(self):
        status = make_project_status("Active")
        make_project_substatus("Alpha", status=status)
        make_project_substatus("Beta", status=status)

    def test_csv_export_contains_name(self):
        svc = ProjectSubStatusExportService()
        response = svc.export(fields=["name"], export_format="csv")
        self.assertIn("Alpha", response.content.decode())

    def test_search_filter_applies(self):
        svc = ProjectSubStatusExportService()
        response = svc.export(
            fields=["name"],
            export_format="csv",
            filters={"search": "Alpha"},
        )
        content = response.content.decode()
        self.assertIn("Alpha", content)
        self.assertNotIn("Beta", content)
