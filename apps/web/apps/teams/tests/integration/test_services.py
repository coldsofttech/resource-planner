import json

from django.test import TestCase

from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.core.types import ListParams
from apps.teams.models import Team
from apps.teams.services import TeamExportService, TeamImportService, TeamService
from apps.teams.tests.factories import make_csv_file, make_team
from apps.users.tests.factories import make_user


def make_service(user=None):
    return TeamService(user=user)


def make_import_service(user=None):
    return TeamImportService(user=user)


# ── list ──────────────────────────────────────────────────────────────────────


class TeamServiceListTest(TestCase):
    def setUp(self):
        self.svc = make_service()
        make_team("Alpha", is_active=True)
        make_team("Beta", is_active=True)
        make_team("Inactive", is_active=False)

    def test_defaults_to_active_only(self):
        result = self.svc.list(ListParams())
        names = [t.name for t in result.results]
        self.assertIn("Alpha", names)
        self.assertNotIn("Inactive", names)

    def test_is_active_false_returns_inactive(self):
        result = self.svc.list(ListParams(filters={"is_active": "false"}))
        names = [t.name for t in result.results]
        self.assertIn("Inactive", names)
        self.assertNotIn("Alpha", names)

    def test_returns_paginated_result(self):
        result = self.svc.list(ListParams())
        self.assertIsNotNone(result.pagination)

    def test_search_by_name(self):
        result = self.svc.list(ListParams(search="Alpha"))
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0].name, "Alpha")

    def test_returns_empty_when_no_active_teams(self):
        Team.objects.all().delete()
        make_team("Only", is_active=False)
        result = self.svc.list(ListParams())
        self.assertEqual(len(result.results), 0)


# ── TeamExportService ─────────────────────────────────────────────────────────


class TeamExportServiceSearchFilterTest(TestCase):
    def setUp(self):
        make_team("Alpha", is_active=True)
        make_team("Beta", is_active=True)
        make_team("Gamma", is_active=True)
        self.svc = TeamExportService()

    def test_search_filter_includes_matching_team(self):
        response = self.svc.export(
            fields=["name"],
            export_format="csv",
            filters={"search": "Alpha"},
        )
        self.assertIn("Alpha", response.content.decode())

    def test_search_filter_excludes_non_matching_teams(self):
        response = self.svc.export(
            fields=["name"],
            export_format="csv",
            filters={"search": "Alpha"},
        )
        content = response.content.decode()
        self.assertNotIn("Beta", content)
        self.assertNotIn("Gamma", content)

    def test_empty_search_returns_all_active_teams(self):
        response = self.svc.export(
            fields=["name"],
            export_format="csv",
            filters={"search": ""},
        )
        content = response.content.decode()
        self.assertIn("Alpha", content)
        self.assertIn("Beta", content)
        self.assertIn("Gamma", content)

    def test_search_is_case_insensitive(self):
        response = self.svc.export(
            fields=["name"],
            export_format="csv",
            filters={"search": "alpha"},
        )
        content = response.content.decode()
        self.assertIn("Alpha", content)
        self.assertNotIn("Beta", content)


class TeamExportServiceIsActiveFilterTest(TestCase):
    def setUp(self):
        make_team("ActiveTeam", is_active=True)
        make_team("InactiveTeam", is_active=False)
        self.svc = TeamExportService()

    def test_empty_is_active_filter_returns_active_teams_only(self):
        # is_active="" triggers the active-only branch; filters={} is
        # falsy and skips all filtering
        response = self.svc.export(
            fields=["name"], export_format="csv", filters={"is_active": ""}
        )
        content = response.content.decode()
        self.assertIn("ActiveTeam", content)
        self.assertNotIn("InactiveTeam", content)

    def test_is_active_all_returns_all_teams(self):
        response = self.svc.export(
            fields=["name"], export_format="csv", filters={"is_active": "all"}
        )
        content = response.content.decode()
        self.assertIn("ActiveTeam", content)
        self.assertIn("InactiveTeam", content)

    def test_is_active_false_returns_inactive_teams(self):
        response = self.svc.export(
            fields=["name"], export_format="csv", filters={"is_active": "false"}
        )
        content = response.content.decode()
        self.assertNotIn("ActiveTeam", content)
        self.assertIn("InactiveTeam", content)

    def test_unsupported_format_raises_validation_exception(self):
        with self.assertRaises(ValidationException):
            self.svc.export(fields=["name"], export_format="xml", filters={})

    def test_json_format_returns_list(self):
        response = self.svc.export(fields=["name"], export_format="json", filters={})
        data = json.loads(response.content.decode())
        self.assertIsInstance(data, list)


# ── get ───────────────────────────────────────────────────────────────────────


class TeamServiceGetTest(TestCase):
    def setUp(self):
        self.svc = make_service()
        self.team = make_team("Alpha")

    def test_returns_team_by_code(self):
        result = self.svc.get(code=self.team.code)
        self.assertEqual(result, self.team)

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.get(code="TEAM-9999")


# ── create ────────────────────────────────────────────────────────────────────


class TeamServiceCreateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)

    def test_creates_team(self):
        team = self.svc.create(name="Alpha")
        self.assertIsNotNone(team.pk)
        self.assertEqual(team.name, "Alpha")

    def test_sets_created_by(self):
        team = self.svc.create(name="Alpha")
        self.assertEqual(team.created_by, self.user)

    def test_is_active_defaults_to_true(self):
        team = self.svc.create(name="Alpha")
        self.assertTrue(team.is_active)

    def test_creates_with_description(self):
        team = self.svc.create(name="Alpha", description="Frontend squad")
        self.assertEqual(team.description, "Frontend squad")

    def test_raises_conflict_on_duplicate_name(self):
        self.svc.create(name="Alpha")
        with self.assertRaises(AlreadyExistsException):
            self.svc.create(name="Alpha")

    def test_code_is_assigned(self):
        team = self.svc.create(name="Alpha")
        self.assertTrue(team.code.startswith("TEAM-"))


# ── update ────────────────────────────────────────────────────────────────────


class TeamServiceUpdateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)
        self.team = make_team("Alpha")

    def test_updates_name(self):
        updated = self.svc.update(code=self.team.code, name="Renamed")
        self.assertEqual(updated.name, "Renamed")

    def test_updates_description(self):
        updated = self.svc.update(code=self.team.code, description="New desc")
        self.assertEqual(updated.description, "New desc")

    def test_updates_is_active(self):
        updated = self.svc.update(code=self.team.code, is_active=False)
        self.assertFalse(updated.is_active)

    def test_sets_updated_by(self):
        updated = self.svc.update(code=self.team.code, name="Renamed")
        self.assertEqual(updated.updated_by, self.user)

    def test_raises_conflict_on_duplicate_name(self):
        make_team("Beta")
        with self.assertRaises(AlreadyExistsException):
            self.svc.update(code=self.team.code, name="Beta")

    def test_same_name_no_conflict(self):
        updated = self.svc.update(code=self.team.code, name="Alpha")
        self.assertEqual(updated.name, "Alpha")

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.update(code="TEAM-9999", name="X")


# ── activate / deactivate ─────────────────────────────────────────────────────


class TeamServiceActivateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)

    def test_activates_inactive_team(self):
        team = make_team("Alpha", is_active=False)
        result = self.svc.activate(code=team.code)
        self.assertTrue(result.is_active)

    def test_activate_is_idempotent(self):
        team = make_team("Alpha", is_active=True)
        result = self.svc.activate(code=team.code)
        self.assertTrue(result.is_active)

    def test_deactivates_active_team(self):
        team = make_team("Beta", is_active=True)
        result = self.svc.deactivate(code=team.code)
        self.assertFalse(result.is_active)

    def test_deactivate_is_idempotent(self):
        team = make_team("Beta", is_active=False)
        result = self.svc.deactivate(code=team.code)
        self.assertFalse(result.is_active)

    def test_activate_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            self.svc.activate(code="TEAM-9999")

    def test_deactivate_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            self.svc.deactivate(code="TEAM-9999")


# ── delete ────────────────────────────────────────────────────────────────────


class TeamServiceDeleteTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_deletes_team(self):
        team = make_team("Alpha")
        self.svc.delete(code=team.code)
        self.assertFalse(Team.objects.filter(pk=team.pk).exists())

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.delete(code="TEAM-9999")


# ── stats ─────────────────────────────────────────────────────────────────────


class TeamServiceStatsTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_returns_correct_counts(self):
        make_team("Alpha", is_active=True)
        make_team("Beta", is_active=False)
        result = self.svc.stats()
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["active"], 1)
        self.assertEqual(result["inactive"], 1)

    def test_returns_zeros_when_no_teams(self):
        result = self.svc.stats()
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["active"], 0)
        self.assertEqual(result["inactive"], 0)

    def test_fields_filter_limits_returned_keys(self):
        make_team("Alpha", is_active=True)
        result = self.svc.stats(fields=["total", "active"])
        self.assertIn("total", result)
        self.assertIn("active", result)
        self.assertNotIn("inactive", result)


# ── TeamImportService.bulk_import — structure ─────────────────────────────────


class TeamImportBulkImportStructureTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_import_service(user=self.user)

    def test_raises_if_name_column_missing(self):
        f = make_csv_file("description\nA squad")
        with self.assertRaises(ValidationException):
            self.svc.bulk_import(f)

    def test_raises_if_row_count_exceeds_limit(self):
        rows = ["name"] + [
            f"Team {i}" for i in range(TeamImportService.MAX_IMPORT_ROWS + 1)
        ]
        f = make_csv_file("\n".join(rows))
        with self.assertRaises(ValidationException):
            self.svc.bulk_import(f)

    def test_returns_expected_keys(self):
        f = make_csv_file("name\nAlpha")
        result = self.svc.bulk_import(f)
        self.assertIn("total", result)
        self.assertIn("created_rows", result)
        self.assertIn("errors", result)
        self.assertIn("dry_run", result)

    def test_total_reflects_row_count(self):
        f = make_csv_file("name\nAlpha\nBeta\nGamma")
        result = self.svc.bulk_import(f)
        self.assertEqual(result["total"], 3)


# ── TeamImportService.bulk_import — happy path ────────────────────────────────


class TeamImportBulkImportCreateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_import_service(user=self.user)

    def test_creates_team_from_csv(self):
        f = make_csv_file("name\nAlpha")
        self.svc.bulk_import(f)
        self.assertTrue(Team.objects.filter(name="Alpha").exists())

    def test_returns_correct_created_count(self):
        f = make_csv_file("name\nAlpha\nBeta")
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["created_rows"]), 2)
        self.assertEqual(result["total"], 2)

    def test_default_is_active_is_true(self):
        f = make_csv_file("name\nAlpha")
        self.svc.bulk_import(f)
        self.assertTrue(Team.objects.get(name="Alpha").is_active)

    def test_is_active_false_parsed(self):
        f = make_csv_file("name,is_active\nAlpha,false")
        self.svc.bulk_import(f)
        self.assertFalse(Team.objects.get(name="Alpha").is_active)

    def test_is_active_no_parsed_as_false(self):
        f = make_csv_file("name,is_active\nAlpha,no")
        self.svc.bulk_import(f)
        self.assertFalse(Team.objects.get(name="Alpha").is_active)

    def test_description_stored(self):
        f = make_csv_file("name,description\nAlpha,Core squad")
        self.svc.bulk_import(f)
        self.assertEqual(Team.objects.get(name="Alpha").description, "Core squad")

    def test_strips_whitespace_from_name(self):
        f = make_csv_file("name\n  Alpha  ")
        self.svc.bulk_import(f)
        self.assertTrue(Team.objects.filter(name="Alpha").exists())

    def test_created_by_set_to_user(self):
        f = make_csv_file("name\nAlpha")
        self.svc.bulk_import(f)
        team = Team.objects.get(name="Alpha")
        self.assertEqual(team.created_by, self.user)


# ── TeamImportService.bulk_import — skips and errors ─────────────────────────


class TeamImportBulkImportSkipTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_import_service(user=self.user)

    def test_skips_row_with_missing_name(self):
        f = make_csv_file("name\n ")  # whitespace-only strips to empty
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(len(result["created_rows"]), 0)

    def test_skips_duplicate_name(self):
        make_team("Alpha")
        f = make_csv_file("name\nAlpha")
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["field"], "name")

    def test_partial_import_skips_duplicates_only(self):
        make_team("Alpha")
        f = make_csv_file("name\nAlpha\nBeta")
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["created_rows"]), 1)
        self.assertEqual(len(result["errors"]), 1)

    def test_error_entry_includes_row_number(self):
        make_team("Alpha")
        f = make_csv_file("name\nAlpha")
        result = self.svc.bulk_import(f)
        self.assertEqual(result["errors"][0]["row"], 2)

    def test_invalid_row_not_created(self):
        f = make_csv_file("name\n")
        self.svc.bulk_import(f)
        self.assertEqual(Team.objects.count(), 0)


# ── TeamImportService.bulk_import — dry run ───────────────────────────────────


class TeamImportBulkImportDryRunTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_import_service(user=self.user)

    def test_dry_run_does_not_create_teams(self):
        f = make_csv_file("name\nAlpha\nBeta")
        self.svc.bulk_import(f, dry_run=True)
        self.assertEqual(Team.objects.count(), 0)

    def test_dry_run_reports_correct_created_count(self):
        f = make_csv_file("name\nAlpha\nBeta")
        result = self.svc.bulk_import(f, dry_run=True)
        self.assertEqual(len(result["created_rows"]), 2)
        self.assertTrue(result["dry_run"])

    def test_dry_run_skips_invalid_rows(self):
        f = make_csv_file("name\n \nBeta")  # whitespace row skipped, Beta counted
        result = self.svc.bulk_import(f, dry_run=True)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(len(result["created_rows"]), 1)
