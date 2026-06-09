import json

from django.test import TestCase

from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.core.types import ListParams
from apps.skills.models import Skill
from apps.skills.services import SkillExportService, SkillImportService, SkillService
from apps.skills.tests.factories import make_csv_file, make_skill
from apps.users.tests.factories import make_user


def make_service(user=None):
    return SkillService(user=user)


def make_import_service(user=None):
    return SkillImportService(user=user)


# ── list ──────────────────────────────────────────────────────────────────────


class SkillServiceListTest(TestCase):
    def setUp(self):
        self.svc = make_service()
        make_skill("Python", is_active=True)
        make_skill("Java", is_active=True)
        make_skill("COBOL", is_active=False)

    def test_defaults_to_active_only(self):
        result = self.svc.list(ListParams())
        names = [s.skill for s in result.results]
        self.assertIn("Python", names)
        self.assertNotIn("COBOL", names)

    def test_is_active_false_returns_inactive(self):
        result = self.svc.list(ListParams(filters={"is_active": "false"}))
        names = [s.skill for s in result.results]
        self.assertIn("COBOL", names)
        self.assertNotIn("Python", names)

    def test_returns_paginated_result(self):
        result = self.svc.list(ListParams())
        self.assertIsNotNone(result.pagination)

    def test_search_by_skill(self):
        result = self.svc.list(ListParams(search="Python"))
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0].skill, "Python")

    def test_returns_empty_when_no_active_skills(self):
        Skill.objects.all().delete()
        make_skill("Only", is_active=False)
        result = self.svc.list(ListParams())
        self.assertEqual(len(result.results), 0)


# ── SkillExportService ────────────────────────────────────────────────────────


class SkillExportServiceSearchFilterTest(TestCase):
    def setUp(self):
        make_skill("Python", is_active=True)
        make_skill("Java", is_active=True)
        make_skill("Go", is_active=True)
        self.svc = SkillExportService()

    def test_search_filter_includes_matching_skill(self):
        response = self.svc.export(
            fields=["skill"],
            export_format="csv",
            filters={"search": "Python"},
        )
        self.assertIn("Python", response.content.decode())

    def test_search_filter_excludes_non_matching_skills(self):
        response = self.svc.export(
            fields=["skill"],
            export_format="csv",
            filters={"search": "Python"},
        )
        content = response.content.decode()
        self.assertNotIn("Java", content)
        self.assertNotIn("Go", content)

    def test_empty_search_returns_all_active_skills(self):
        response = self.svc.export(
            fields=["skill"],
            export_format="csv",
            filters={"search": ""},
        )
        content = response.content.decode()
        self.assertIn("Python", content)
        self.assertIn("Java", content)
        self.assertIn("Go", content)

    def test_search_is_case_insensitive(self):
        response = self.svc.export(
            fields=["skill"],
            export_format="csv",
            filters={"search": "python"},
        )
        content = response.content.decode()
        self.assertIn("Python", content)
        self.assertNotIn("Java", content)


class SkillExportServiceIsActiveFilterTest(TestCase):
    def setUp(self):
        make_skill("Python", is_active=True)
        make_skill("COBOL", is_active=False)
        self.svc = SkillExportService()

    def test_empty_is_active_filter_returns_active_skills_only(self):
        response = self.svc.export(
            fields=["skill"], export_format="csv", filters={"is_active": ""}
        )
        content = response.content.decode()
        self.assertIn("Python", content)
        self.assertNotIn("COBOL", content)

    def test_is_active_all_returns_all_skills(self):
        response = self.svc.export(
            fields=["skill"], export_format="csv", filters={"is_active": "all"}
        )
        content = response.content.decode()
        self.assertIn("Python", content)
        self.assertIn("COBOL", content)

    def test_is_active_false_returns_inactive_skills(self):
        response = self.svc.export(
            fields=["skill"], export_format="csv", filters={"is_active": "false"}
        )
        content = response.content.decode()
        self.assertNotIn("Python", content)
        self.assertIn("COBOL", content)

    def test_unsupported_format_raises_validation_exception(self):
        with self.assertRaises(ValidationException):
            self.svc.export(fields=["skill"], export_format="xml", filters={})

    def test_json_format_returns_list(self):
        response = self.svc.export(fields=["skill"], export_format="json", filters={})
        data = json.loads(response.content.decode())
        self.assertIsInstance(data, list)


# ── get ───────────────────────────────────────────────────────────────────────


class SkillServiceGetTest(TestCase):
    def setUp(self):
        self.svc = make_service()
        self.skill = make_skill("Python")

    def test_returns_skill_by_code(self):
        result = self.svc.get(code=self.skill.code)
        self.assertEqual(result, self.skill)

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.get(code="SKILL-9999")


# ── create ────────────────────────────────────────────────────────────────────


class SkillServiceCreateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)

    def test_creates_skill(self):
        skill = self.svc.create(skill="Python")
        self.assertIsNotNone(skill.pk)
        self.assertEqual(skill.skill, "Python")

    def test_sets_created_by(self):
        skill = self.svc.create(skill="Python")
        self.assertEqual(skill.created_by, self.user)

    def test_is_active_defaults_to_true(self):
        skill = self.svc.create(skill="Python")
        self.assertTrue(skill.is_active)

    def test_creates_with_description(self):
        skill = self.svc.create(skill="Python", description="Core language")
        self.assertEqual(skill.description, "Core language")

    def test_raises_conflict_on_duplicate_skill(self):
        self.svc.create(skill="Python")
        with self.assertRaises(AlreadyExistsException):
            self.svc.create(skill="Python")

    def test_code_is_assigned(self):
        skill = self.svc.create(skill="Python")
        self.assertTrue(skill.code.startswith("SKILL-"))


# ── update ────────────────────────────────────────────────────────────────────


class SkillServiceUpdateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)
        self.skill = make_skill("Python")

    def test_updates_skill(self):
        updated = self.svc.update(code=self.skill.code, skill="Rust")
        self.assertEqual(updated.skill, "Rust")

    def test_updates_description(self):
        updated = self.svc.update(code=self.skill.code, description="Systems lang")
        self.assertEqual(updated.description, "Systems lang")

    def test_updates_is_active(self):
        updated = self.svc.update(code=self.skill.code, is_active=False)
        self.assertFalse(updated.is_active)

    def test_sets_updated_by(self):
        updated = self.svc.update(code=self.skill.code, skill="Rust")
        self.assertEqual(updated.updated_by, self.user)

    def test_raises_conflict_on_duplicate_skill(self):
        make_skill("Java")
        with self.assertRaises(AlreadyExistsException):
            self.svc.update(code=self.skill.code, skill="Java")

    def test_same_skill_no_conflict(self):
        updated = self.svc.update(code=self.skill.code, skill="Python")
        self.assertEqual(updated.skill, "Python")

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.update(code="SKILL-9999", skill="X")


# ── activate / deactivate ─────────────────────────────────────────────────────


class SkillServiceActivateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)

    def test_activates_inactive_skill(self):
        skill = make_skill("Python", is_active=False)
        result = self.svc.activate(code=skill.code)
        self.assertTrue(result.is_active)

    def test_activate_is_idempotent(self):
        skill = make_skill("Python", is_active=True)
        result = self.svc.activate(code=skill.code)
        self.assertTrue(result.is_active)

    def test_deactivates_active_skill(self):
        skill = make_skill("Java", is_active=True)
        result = self.svc.deactivate(code=skill.code)
        self.assertFalse(result.is_active)

    def test_deactivate_is_idempotent(self):
        skill = make_skill("Java", is_active=False)
        result = self.svc.deactivate(code=skill.code)
        self.assertFalse(result.is_active)

    def test_activate_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            self.svc.activate(code="SKILL-9999")

    def test_deactivate_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            self.svc.deactivate(code="SKILL-9999")


# ── delete ────────────────────────────────────────────────────────────────────


class SkillServiceDeleteTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_deletes_skill(self):
        skill = make_skill("Python")
        self.svc.delete(code=skill.code)
        self.assertFalse(Skill.objects.filter(pk=skill.pk).exists())

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.delete(code="SKILL-9999")


# ── stats ─────────────────────────────────────────────────────────────────────


class SkillServiceStatsTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_returns_correct_counts(self):
        make_skill("Python", is_active=True)
        make_skill("COBOL", is_active=False)
        result = self.svc.stats()
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["active"], 1)
        self.assertEqual(result["inactive"], 1)

    def test_returns_zeros_when_no_skills(self):
        result = self.svc.stats()
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["active"], 0)
        self.assertEqual(result["inactive"], 0)

    def test_fields_filter_limits_returned_keys(self):
        make_skill("Python", is_active=True)
        result = self.svc.stats(fields=["total", "active"])
        self.assertIn("total", result)
        self.assertIn("active", result)
        self.assertNotIn("inactive", result)


# ── options ───────────────────────────────────────────────────────────────────


class SkillServiceOptionsTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_returns_list(self):
        result = self.svc.options()
        self.assertIsInstance(result, list)

    def test_returns_empty_when_no_active_skills(self):
        make_skill("COBOL", is_active=False)
        self.assertEqual(self.svc.options(), [])

    def test_returns_only_active_skills(self):
        make_skill("Python", is_active=True)
        make_skill("COBOL", is_active=False)
        result = self.svc.options()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["skill"], "Python")

    def test_each_entry_has_code_and_skill_keys(self):
        skill = make_skill("Python", is_active=True)
        result = self.svc.options()
        self.assertEqual(len(result), 1)
        entry = result[0]
        self.assertIn("code", entry)
        self.assertIn("skill", entry)
        self.assertEqual(entry["code"], skill.code)
        self.assertEqual(entry["skill"], "Python")

    def test_ordered_alphabetically_by_skill_name(self):
        make_skill("Rust", is_active=True)
        make_skill("Go", is_active=True)
        make_skill("Python", is_active=True)
        names = [e["skill"] for e in self.svc.options()]
        self.assertEqual(names, sorted(names))


# ── SkillImportService.bulk_import — structure ────────────────────────────────


class SkillImportBulkImportStructureTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_import_service(user=self.user)

    def test_raises_if_skill_column_missing(self):
        f = make_csv_file("description\nA language")
        with self.assertRaises(ValidationException):
            self.svc.bulk_import(f)

    def test_raises_if_row_count_exceeds_limit(self):
        rows = ["skill"] + [
            f"Sk{i:05d}" for i in range(SkillImportService.MAX_IMPORT_ROWS + 1)
        ]
        f = make_csv_file("\n".join(rows))
        with self.assertRaises(ValidationException):
            self.svc.bulk_import(f)

    def test_returns_expected_keys(self):
        f = make_csv_file("skill\nPython")
        result = self.svc.bulk_import(f)
        self.assertIn("total", result)
        self.assertIn("created_rows", result)
        self.assertIn("errors", result)
        self.assertIn("dry_run", result)

    def test_total_reflects_row_count(self):
        f = make_csv_file("skill\nPython\nJava\nGo")
        result = self.svc.bulk_import(f)
        self.assertEqual(result["total"], 3)


# ── SkillImportService.bulk_import — happy path ───────────────────────────────


class SkillImportBulkImportCreateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_import_service(user=self.user)

    def test_creates_skill_from_csv(self):
        f = make_csv_file("skill\nPython")
        self.svc.bulk_import(f)
        self.assertTrue(Skill.objects.filter(skill="Python").exists())

    def test_returns_correct_created_count(self):
        f = make_csv_file("skill\nPython\nJava")
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["created_rows"]), 2)
        self.assertEqual(result["total"], 2)

    def test_default_is_active_is_true(self):
        f = make_csv_file("skill\nPython")
        self.svc.bulk_import(f)
        self.assertTrue(Skill.objects.get(skill="Python").is_active)

    def test_is_active_false_parsed(self):
        f = make_csv_file("skill,is_active\nPython,false")
        self.svc.bulk_import(f)
        self.assertFalse(Skill.objects.get(skill="Python").is_active)

    def test_is_active_no_parsed_as_false(self):
        f = make_csv_file("skill,is_active\nPython,no")
        self.svc.bulk_import(f)
        self.assertFalse(Skill.objects.get(skill="Python").is_active)

    def test_description_stored(self):
        f = make_csv_file("skill,description\nPython,Core language")
        self.svc.bulk_import(f)
        self.assertEqual(Skill.objects.get(skill="Python").description, "Core language")

    def test_strips_whitespace_from_skill(self):
        f = make_csv_file("skill\n  Python  ")
        self.svc.bulk_import(f)
        self.assertTrue(Skill.objects.filter(skill="Python").exists())

    def test_created_by_set_to_user(self):
        f = make_csv_file("skill\nPython")
        self.svc.bulk_import(f)
        skill = Skill.objects.get(skill="Python")
        self.assertEqual(skill.created_by, self.user)


# ── SkillImportService.bulk_import — skips and errors ────────────────────────


class SkillImportBulkImportSkipTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_import_service(user=self.user)

    def test_skips_row_with_missing_skill(self):
        f = make_csv_file("skill\n ")
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(len(result["created_rows"]), 0)

    def test_skips_duplicate_skill(self):
        make_skill("Python")
        f = make_csv_file("skill\nPython")
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["field"], "skill")

    def test_partial_import_skips_duplicates_only(self):
        make_skill("Python")
        f = make_csv_file("skill\nPython\nJava")
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["created_rows"]), 1)
        self.assertEqual(len(result["errors"]), 1)

    def test_error_entry_includes_row_number(self):
        make_skill("Python")
        f = make_csv_file("skill\nPython")
        result = self.svc.bulk_import(f)
        self.assertEqual(result["errors"][0]["row"], 2)

    def test_invalid_row_not_created(self):
        f = make_csv_file("skill\n")
        self.svc.bulk_import(f)
        self.assertEqual(Skill.objects.count(), 0)


# ── SkillImportService.bulk_import — dry run ──────────────────────────────────


class SkillImportBulkImportDryRunTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_import_service(user=self.user)

    def test_dry_run_does_not_create_skills(self):
        f = make_csv_file("skill\nPython\nJava")
        self.svc.bulk_import(f, dry_run=True)
        self.assertEqual(Skill.objects.count(), 0)

    def test_dry_run_reports_correct_created_count(self):
        f = make_csv_file("skill\nPython\nJava")
        result = self.svc.bulk_import(f, dry_run=True)
        self.assertEqual(len(result["created_rows"]), 2)
        self.assertTrue(result["dry_run"])

    def test_dry_run_skips_invalid_rows(self):
        f = make_csv_file("skill\n \nJava")
        result = self.svc.bulk_import(f, dry_run=True)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(len(result["created_rows"]), 1)
