import json

from django.test import TestCase

from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.core.types import ListParams
from apps.roles.models import Role
from apps.roles.services import RoleExportService, RoleImportService, RoleService
from apps.roles.tests.factories import make_csv_file, make_role
from apps.users.tests.factories import make_user


def make_service(user=None):
    return RoleService(user=user)


def make_import_service(user=None):
    return RoleImportService(user=user)


# ── list ──────────────────────────────────────────────────────────────────────


class RoleServiceListTest(TestCase):
    def setUp(self):
        self.svc = make_service()
        make_role("Developer", is_active=True)
        make_role("Analyst", is_active=True)
        make_role("COBOL Guru", is_active=False)

    def test_defaults_to_active_only(self):
        result = self.svc.list(ListParams())
        names = [r.role for r in result.results]
        self.assertIn("Developer", names)
        self.assertNotIn("COBOL Guru", names)

    def test_is_active_false_returns_inactive(self):
        result = self.svc.list(ListParams(filters={"is_active": "false"}))
        names = [r.role for r in result.results]
        self.assertIn("COBOL Guru", names)
        self.assertNotIn("Developer", names)

    def test_returns_paginated_result(self):
        result = self.svc.list(ListParams())
        self.assertIsNotNone(result.pagination)

    def test_search_by_role(self):
        result = self.svc.list(ListParams(search="Developer"))
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0].role, "Developer")

    def test_returns_empty_when_no_active_roles(self):
        Role.objects.all().delete()
        make_role("COBOL Guru", is_active=False)
        result = self.svc.list(ListParams())
        self.assertEqual(len(result.results), 0)


# ── get ───────────────────────────────────────────────────────────────────────


class RoleServiceGetTest(TestCase):
    def setUp(self):
        self.svc = make_service()
        self.role = make_role("Developer")

    def test_returns_role_by_code(self):
        result = self.svc.get(code=self.role.code)
        self.assertEqual(result, self.role)

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.get(code="ROLE-9999")


# ── create ────────────────────────────────────────────────────────────────────


class RoleServiceCreateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)

    def test_creates_role(self):
        role = self.svc.create(role="Developer")
        self.assertIsNotNone(role.pk)
        self.assertEqual(role.role, "Developer")

    def test_sets_created_by(self):
        role = self.svc.create(role="Developer")
        self.assertEqual(role.created_by, self.user)

    def test_is_active_defaults_to_true(self):
        role = self.svc.create(role="Developer")
        self.assertTrue(role.is_active)

    def test_is_default_defaults_to_false(self):
        role = self.svc.create(role="Developer")
        self.assertFalse(role.is_default)

    def test_is_assignable_defaults_to_false(self):
        role = self.svc.create(role="Developer")
        self.assertFalse(role.is_assignable)

    def test_is_leadership_defaults_to_false(self):
        role = self.svc.create(role="Developer")
        self.assertFalse(role.is_leadership)

    def test_creates_with_is_assignable_true(self):
        role = self.svc.create(role="Developer", is_assignable=True)
        self.assertTrue(role.is_assignable)

    def test_creates_with_is_leadership_true(self):
        role = self.svc.create(role="Tech Lead", is_leadership=True)
        self.assertTrue(role.is_leadership)

    def test_raises_conflict_on_duplicate_role(self):
        self.svc.create(role="Developer")
        with self.assertRaises(AlreadyExistsException):
            self.svc.create(role="Developer")

    def test_code_is_assigned(self):
        role = self.svc.create(role="Developer")
        self.assertTrue(role.code.startswith("ROLE-"))


# ── update ────────────────────────────────────────────────────────────────────


class RoleServiceUpdateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)
        self.role = make_role("Developer")

    def test_updates_role_name(self):
        updated = self.svc.update(code=self.role.code, role="Senior Developer")
        self.assertEqual(updated.role, "Senior Developer")

    def test_updates_is_active(self):
        updated = self.svc.update(code=self.role.code, is_active=False)
        self.assertFalse(updated.is_active)

    def test_updates_is_assignable(self):
        updated = self.svc.update(code=self.role.code, is_assignable=True)
        self.assertTrue(updated.is_assignable)

    def test_updates_is_leadership(self):
        updated = self.svc.update(code=self.role.code, is_leadership=True)
        self.assertTrue(updated.is_leadership)

    def test_sets_updated_by(self):
        updated = self.svc.update(code=self.role.code, role="Senior Developer")
        self.assertEqual(updated.updated_by, self.user)

    def test_raises_conflict_on_duplicate_role_name(self):
        make_role("Analyst")
        with self.assertRaises(AlreadyExistsException):
            self.svc.update(code=self.role.code, role="Analyst")

    def test_same_role_name_no_conflict(self):
        updated = self.svc.update(code=self.role.code, role="Developer")
        self.assertEqual(updated.role, "Developer")

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.update(code="ROLE-9999", role="X")


# ── activate / deactivate ─────────────────────────────────────────────────────


class RoleServiceActivateDeactivateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)

    def test_activates_inactive_role(self):
        role = make_role("Developer", is_active=False)
        result = self.svc.activate(code=role.code)
        self.assertTrue(result.is_active)

    def test_activate_is_idempotent(self):
        role = make_role("Developer", is_active=True)
        result = self.svc.activate(code=role.code)
        self.assertTrue(result.is_active)

    def test_deactivates_active_role(self):
        role = make_role("Analyst", is_active=True)
        result = self.svc.deactivate(code=role.code)
        self.assertFalse(result.is_active)

    def test_deactivate_is_idempotent(self):
        role = make_role("Analyst", is_active=False)
        result = self.svc.deactivate(code=role.code)
        self.assertFalse(result.is_active)

    def test_activate_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            self.svc.activate(code="ROLE-9999")

    def test_deactivate_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            self.svc.deactivate(code="ROLE-9999")


# ── set_default ───────────────────────────────────────────────────────────────


class RoleServiceSetDefaultTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)

    def test_sets_role_as_default(self):
        role = make_role("Developer")
        result = self.svc.set_default(code=role.code)
        self.assertTrue(result.is_default)

    def test_clears_previous_default(self):
        old = make_role("Analyst", is_default=True)
        new = make_role("Developer")
        self.svc.set_default(code=new.code)
        old.refresh_from_db()
        self.assertFalse(old.is_default)

    def test_only_one_default_at_a_time(self):
        make_role("Analyst", is_default=True)
        new = make_role("Developer")
        self.svc.set_default(code=new.code)
        self.assertEqual(Role.objects.filter(is_default=True).count(), 1)

    def test_set_default_is_idempotent(self):
        role = make_role("Developer", is_default=True)
        result = self.svc.set_default(code=role.code)
        self.assertTrue(result.is_default)

    def test_set_default_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            self.svc.set_default(code="ROLE-9999")


# ── delete ────────────────────────────────────────────────────────────────────


class RoleServiceDeleteTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_deletes_role(self):
        role = make_role("Developer")
        self.svc.delete(code=role.code)
        self.assertFalse(Role.objects.filter(pk=role.pk).exists())

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.delete(code="ROLE-9999")


# ── stats ─────────────────────────────────────────────────────────────────────


class RoleServiceStatsTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_returns_correct_counts(self):
        make_role("Developer", is_active=True)
        make_role("COBOL Guru", is_active=False)
        result = self.svc.stats()
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["active"], 1)
        self.assertEqual(result["inactive"], 1)

    def test_returns_zeros_when_no_roles(self):
        result = self.svc.stats()
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["active"], 0)
        self.assertEqual(result["inactive"], 0)

    def test_fields_filter_limits_returned_keys(self):
        make_role("Developer", is_active=True)
        result = self.svc.stats(fields=["total", "active"])
        self.assertIn("total", result)
        self.assertIn("active", result)
        self.assertNotIn("inactive", result)


# ── options ───────────────────────────────────────────────────────────────────


class RoleServiceOptionsTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_returns_list(self):
        self.assertIsInstance(self.svc.options(), list)

    def test_returns_empty_when_no_active_roles(self):
        make_role("COBOL Guru", is_active=False)
        self.assertEqual(self.svc.options(), [])

    def test_returns_only_active_roles(self):
        make_role("Developer", is_active=True)
        make_role("COBOL Guru", is_active=False)
        result = self.svc.options()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["role"], "Developer")

    def test_each_entry_has_expected_keys(self):
        role = make_role("Developer", is_active=True)
        result = self.svc.options()
        entry = result[0]
        for key in ("code", "role", "is_default", "is_assignable", "is_leadership"):
            self.assertIn(key, entry)
        self.assertEqual(entry["code"], role.code)

    def test_ordered_alphabetically_by_role(self):
        make_role("Tester", is_active=True)
        make_role("Analyst", is_active=True)
        make_role("Developer", is_active=True)
        names = [e["role"] for e in self.svc.options()]
        self.assertEqual(names, sorted(names))


# ── RoleExportService ─────────────────────────────────────────────────────────


class RoleExportServiceSearchFilterTest(TestCase):
    def setUp(self):
        make_role("Developer", is_active=True)
        make_role("Analyst", is_active=True)
        make_role("Tester", is_active=True)
        self.svc = RoleExportService()

    def test_search_filter_includes_matching_role(self):
        response = self.svc.export(
            fields=["role"],
            export_format="csv",
            filters={"search": "Developer"},
        )
        self.assertIn("Developer", response.content.decode())

    def test_search_filter_excludes_non_matching_roles(self):
        response = self.svc.export(
            fields=["role"],
            export_format="csv",
            filters={"search": "Developer"},
        )
        content = response.content.decode()
        self.assertNotIn("Analyst", content)
        self.assertNotIn("Tester", content)

    def test_empty_search_returns_all_active_roles(self):
        response = self.svc.export(
            fields=["role"],
            export_format="csv",
            filters={"search": ""},
        )
        content = response.content.decode()
        self.assertIn("Developer", content)
        self.assertIn("Analyst", content)

    def test_search_is_case_insensitive(self):
        response = self.svc.export(
            fields=["role"],
            export_format="csv",
            filters={"search": "developer"},
        )
        self.assertIn("Developer", response.content.decode())


class RoleExportServiceIsActiveFilterTest(TestCase):
    def setUp(self):
        make_role("Developer", is_active=True)
        make_role("COBOL Guru", is_active=False)
        self.svc = RoleExportService()

    def test_empty_is_active_returns_active_roles_only(self):
        response = self.svc.export(
            fields=["role"], export_format="csv", filters={"is_active": ""}
        )
        content = response.content.decode()
        self.assertIn("Developer", content)
        self.assertNotIn("COBOL Guru", content)

    def test_is_active_all_returns_all_roles(self):
        response = self.svc.export(
            fields=["role"], export_format="csv", filters={"is_active": "all"}
        )
        content = response.content.decode()
        self.assertIn("Developer", content)
        self.assertIn("COBOL Guru", content)

    def test_is_active_false_returns_inactive_roles(self):
        response = self.svc.export(
            fields=["role"], export_format="csv", filters={"is_active": "false"}
        )
        content = response.content.decode()
        self.assertNotIn("Developer", content)
        self.assertIn("COBOL Guru", content)

    def test_unsupported_format_raises_validation_exception(self):
        with self.assertRaises(ValidationException):
            self.svc.export(fields=["role"], export_format="xml", filters={})

    def test_json_format_returns_list(self):
        response = self.svc.export(fields=["role"], export_format="json", filters={})
        data = json.loads(response.content.decode())
        self.assertIsInstance(data, list)


# ── RoleImportService — validation ────────────────────────────────────────────


class RoleImportBulkImportStructureTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_import_service(user=self.user)

    def test_raises_if_role_column_missing(self):
        f = make_csv_file("is_active\ntrue")
        with self.assertRaises(ValidationException):
            self.svc.bulk_import(f)

    def test_raises_if_row_count_exceeds_limit(self):
        rows = ["role"] + [
            f"Role{i:05d}" for i in range(RoleImportService.MAX_IMPORT_ROWS + 1)
        ]
        f = make_csv_file("\n".join(rows))
        with self.assertRaises(ValidationException):
            self.svc.bulk_import(f)

    def test_returns_expected_keys(self):
        f = make_csv_file("role\nDeveloper")
        result = self.svc.bulk_import(f)
        for key in ("total", "created_rows", "errors", "dry_run"):
            self.assertIn(key, result)

    def test_total_reflects_row_count(self):
        f = make_csv_file("role\nDeveloper\nAnalyst\nTester")
        result = self.svc.bulk_import(f)
        self.assertEqual(result["total"], 3)


# ── RoleImportService — happy path ────────────────────────────────────────────


class RoleImportBulkImportCreateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_import_service(user=self.user)

    def test_creates_role_from_csv(self):
        f = make_csv_file("role\nDeveloper")
        self.svc.bulk_import(f)
        self.assertTrue(Role.objects.filter(role="Developer").exists())

    def test_returns_correct_created_count(self):
        f = make_csv_file("role\nDeveloper\nAnalyst")
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["created_rows"]), 2)

    def test_default_is_active_is_true(self):
        f = make_csv_file("role\nDeveloper")
        self.svc.bulk_import(f)
        self.assertTrue(Role.objects.get(role="Developer").is_active)

    def test_is_active_false_parsed(self):
        f = make_csv_file("role,is_active\nDeveloper,false")
        self.svc.bulk_import(f)
        self.assertFalse(Role.objects.get(role="Developer").is_active)

    def test_is_active_no_parsed_as_false(self):
        f = make_csv_file("role,is_active\nDeveloper,no")
        self.svc.bulk_import(f)
        self.assertFalse(Role.objects.get(role="Developer").is_active)

    def test_is_assignable_true_parsed(self):
        f = make_csv_file("role,is_assignable\nDeveloper,true")
        self.svc.bulk_import(f)
        self.assertTrue(Role.objects.get(role="Developer").is_assignable)

    def test_is_leadership_true_parsed(self):
        f = make_csv_file("role,is_leadership\nTech Lead,yes")
        self.svc.bulk_import(f)
        self.assertTrue(Role.objects.get(role="Tech Lead").is_leadership)

    def test_strips_whitespace_from_role(self):
        f = make_csv_file("role\n  Developer  ")
        self.svc.bulk_import(f)
        self.assertTrue(Role.objects.filter(role="Developer").exists())

    def test_created_by_set_to_user(self):
        f = make_csv_file("role\nDeveloper")
        self.svc.bulk_import(f)
        role = Role.objects.get(role="Developer")
        self.assertEqual(role.created_by, self.user)


# ── RoleImportService — skips and errors ──────────────────────────────────────


class RoleImportBulkImportSkipTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_import_service(user=self.user)

    def test_skips_row_with_missing_role(self):
        f = make_csv_file("role\n ")
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(len(result["created_rows"]), 0)

    def test_skips_duplicate_role(self):
        make_role("Developer")
        f = make_csv_file("role\nDeveloper")
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["field"], "role")

    def test_partial_import_skips_duplicates_only(self):
        make_role("Developer")
        f = make_csv_file("role\nDeveloper\nAnalyst")
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["created_rows"]), 1)
        self.assertEqual(len(result["errors"]), 1)

    def test_error_entry_includes_row_number(self):
        make_role("Developer")
        f = make_csv_file("role\nDeveloper")
        result = self.svc.bulk_import(f)
        self.assertEqual(result["errors"][0]["row"], 2)

    def test_invalid_row_not_created(self):
        f = make_csv_file("role\n")
        self.svc.bulk_import(f)
        self.assertEqual(Role.objects.count(), 0)


# ── RoleImportService — dry run ───────────────────────────────────────────────


class RoleImportBulkImportDryRunTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_import_service(user=self.user)

    def test_dry_run_does_not_create_roles(self):
        f = make_csv_file("role\nDeveloper\nAnalyst")
        self.svc.bulk_import(f, dry_run=True)
        self.assertEqual(Role.objects.count(), 0)

    def test_dry_run_reports_correct_created_count(self):
        f = make_csv_file("role\nDeveloper\nAnalyst")
        result = self.svc.bulk_import(f, dry_run=True)
        self.assertEqual(len(result["created_rows"]), 2)
        self.assertTrue(result["dry_run"])

    def test_dry_run_skips_invalid_rows(self):
        f = make_csv_file("role\n \nAnalyst")
        result = self.svc.bulk_import(f, dry_run=True)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(len(result["created_rows"]), 1)
