from django.test import TestCase

from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.core.types import ListParams
from apps.projects.models import Programme, Project, ProjectCollaborator
from apps.projects.services import ProjectImportService, ProjectService
from apps.projects.tests.factories import (
    make_csv_file,
    make_programme,
    make_project,
    make_project_collaborator,
    make_project_status,
    make_project_type,
)
from apps.sprints.tests.factories import make_sprint
from apps.teams.tests.factories import make_team
from apps.users.tests.factories import make_user


def make_service(user=None):
    return ProjectService(user=user)


def make_import_service(user=None):
    return ProjectImportService(user=user)


class ProjectServiceListTest(TestCase):
    def setUp(self):
        self.svc = make_service()
        make_project("Alpha", is_active=True)
        make_project("Beta", is_active=True)
        make_project("Gamma", is_active=False)

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


class ProjectServiceGetTest(TestCase):
    def test_returns_project_by_code(self):
        p = make_project("Known")
        svc = make_service()
        result = svc.get(code=p.code)
        self.assertEqual(result, p)

    def test_raises_not_found_for_unknown_code(self):
        svc = make_service()
        with self.assertRaises(NotFoundException):
            svc.get(code="PROJ-99999")


class ProjectServiceStatsTest(TestCase):
    def test_returns_stats_dict(self):
        make_project("Active")
        make_project("Inactive", is_active=False)
        svc = make_service()
        stats = svc.stats()
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["active"], 1)
        self.assertEqual(stats["inactive"], 1)

    def test_fields_filter_returned_keys(self):
        make_project("X")
        svc = make_service()
        stats = svc.stats(fields=["total"])
        self.assertIn("total", stats)
        self.assertNotIn("active", stats)


class ProjectServiceOptionsTest(TestCase):
    def test_returns_list_of_dicts(self):
        make_project("Option One")
        svc = make_service()
        result = svc.options()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertIn("code", result[0])
        self.assertIn("name", result[0])
        self.assertIn("display_name", result[0])

    def test_inactive_not_included(self):
        make_project("Hidden", is_active=False)
        svc = make_service()
        result = svc.options()
        self.assertEqual(len(result), 0)


class ProjectServiceCreateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)
        self.pt = make_project_type("Standard")
        self.st = make_project_status("Active")

    def test_creates_project_successfully(self):
        p = self.svc.create(
            name="New Project",
            project_type_code=self.pt.code,
            status_code=self.st.code,
        )
        self.assertIsNotNone(p.pk)
        self.assertEqual(p.name, "New Project")

    def test_display_name_set_without_programme(self):
        Programme.objects.filter(name="Others", is_protected=True).delete()
        p = self.svc.create(
            name="No Programme",
            project_type_code=self.pt.code,
            status_code=self.st.code,
        )
        self.assertEqual(p.display_name, "No Programme")

    def test_display_name_uses_programme_prefix(self):
        prog = make_programme("Core")
        p = self.svc.create(
            name="With Prog",
            project_type_code=self.pt.code,
            status_code=self.st.code,
            programme_code=prog.code,
        )
        self.assertEqual(p.display_name, "Core: With Prog")

    def test_defaults_programme_to_others_when_protected_exists(self):
        others, _ = Programme.objects.get_or_create(
            name="Others",
            defaults={"is_protected": True, "is_active": True},
        )
        p = self.svc.create(
            name="No Code Given",
            project_type_code=self.pt.code,
            status_code=self.st.code,
        )
        self.assertEqual(p.programme, others)

    def test_programme_is_none_when_others_not_found(self):
        Programme.objects.filter(name="Others", is_protected=True).delete()
        p = self.svc.create(
            name="No Others",
            project_type_code=self.pt.code,
            status_code=self.st.code,
        )
        self.assertIsNone(p.programme)

    def test_raises_already_exists_on_duplicate_name(self):
        make_project("Duplicate")
        with self.assertRaises(AlreadyExistsException):
            self.svc.create(
                name="Duplicate",
                project_type_code=self.pt.code,
                status_code=self.st.code,
            )

    def test_raises_not_found_for_unknown_type(self):
        with self.assertRaises(NotFoundException):
            self.svc.create(
                name="Bad Type",
                project_type_code="PROJTYPE-99999",
                status_code=self.st.code,
            )

    def test_raises_not_found_for_unknown_status(self):
        with self.assertRaises(NotFoundException):
            self.svc.create(
                name="Bad Status",
                project_type_code=self.pt.code,
                status_code="PROJSTAT-99999",
            )

    def test_raises_not_found_for_unknown_programme(self):
        with self.assertRaises(NotFoundException):
            self.svc.create(
                name="Bad Prog",
                project_type_code=self.pt.code,
                status_code=self.st.code,
                programme_code="PROG-99999",
            )

    def test_sets_created_by(self):
        p = self.svc.create(
            name="Audited Create",
            project_type_code=self.pt.code,
            status_code=self.st.code,
        )
        self.assertEqual(p.created_by, self.user)

    def test_assigned_team_linked(self):
        team = make_team()
        p = self.svc.create(
            name="Assigned",
            project_type_code=self.pt.code,
            status_code=self.st.code,
            assigned_team_code=team.code,
        )
        self.assertEqual(p.assigned_team, team)

    def test_raises_not_found_for_unknown_team(self):
        with self.assertRaises(NotFoundException):
            self.svc.create(
                name="Bad Team",
                project_type_code=self.pt.code,
                status_code=self.st.code,
                assigned_team_code="TEAM-99999",
            )

    def test_optional_fields_stored(self):
        p = self.svc.create(
            name="Full Fields",
            project_type_code=self.pt.code,
            status_code=self.st.code,
            confidence="high",
            priority="medium",
            efforts_issued=True,
            run_cost_applies=True,
        )
        self.assertEqual(p.confidence, "high")
        self.assertEqual(p.priority, "medium")
        self.assertTrue(p.efforts_issued)
        self.assertTrue(p.run_cost_applies)

    def test_creates_with_sprint_started_in(self):
        sprint = make_sprint(sprint_number=201, name="Sprint 201")
        p = self.svc.create(
            name="Sprint Start Project",
            project_type_code=self.pt.code,
            status_code=self.st.code,
            sprint_started_in_code=sprint.code,
        )
        self.assertEqual(p.sprint_started_in, sprint)

    def test_creates_with_sprint_completed_in(self):
        sprint = make_sprint(sprint_number=202, name="Sprint 202")
        p = self.svc.create(
            name="Sprint Complete Project",
            project_type_code=self.pt.code,
            status_code=self.st.code,
            sprint_completed_in_code=sprint.code,
        )
        self.assertEqual(p.sprint_completed_in, sprint)

    def test_raises_not_found_for_unknown_sprint_started_in(self):
        with self.assertRaises(NotFoundException):
            self.svc.create(
                name="Bad Sprint Start",
                project_type_code=self.pt.code,
                status_code=self.st.code,
                sprint_started_in_code="SPRINT-99999",
            )

    def test_raises_not_found_for_unknown_sprint_completed_in(self):
        with self.assertRaises(NotFoundException):
            self.svc.create(
                name="Bad Sprint Complete",
                project_type_code=self.pt.code,
                status_code=self.st.code,
                sprint_completed_in_code="SPRINT-99999",
            )


class ProjectServiceUpdateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)
        self.pt = make_project_type("Standard")
        self.st = make_project_status("Active")
        self.project = make_project("Original")

    def test_updates_name(self):
        updated = self.svc.update(code=self.project.code, name="Renamed")
        self.assertEqual(updated.name, "Renamed")

    def test_updates_description(self):
        updated = self.svc.update(code=self.project.code, description="New description")
        self.assertEqual(updated.description, "New description")

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.update(code="PROJ-99999", name="Ghost")

    def test_raises_already_exists_on_name_conflict(self):
        make_project("Taken Name")
        with self.assertRaises(AlreadyExistsException):
            self.svc.update(code=self.project.code, name="Taken Name")

    def test_same_name_update_is_idempotent(self):
        updated = self.svc.update(code=self.project.code, name="Original")
        self.assertEqual(updated.name, "Original")

    def test_updates_is_active(self):
        updated = self.svc.update(code=self.project.code, is_active=False)
        self.assertFalse(updated.is_active)

    def test_display_name_refreshed_after_name_update(self):
        prog = make_programme("Initiative")
        p = make_project("Old Name", programme=prog)
        self.svc.update(code=p.code, name="New Name")
        p.refresh_from_db()
        self.assertEqual(p.display_name, "Initiative: New Name")

    def test_updates_sprint_started_in(self):
        sprint = make_sprint(sprint_number=211, name="Sprint 211")
        p = make_project("Sprint Start Update")
        self.svc.update(code=p.code, sprint_started_in_code=sprint.code)
        p.refresh_from_db()
        self.assertEqual(p.sprint_started_in, sprint)

    def test_updates_sprint_completed_in(self):
        sprint = make_sprint(sprint_number=212, name="Sprint 212")
        p = make_project("Sprint Complete Update")
        self.svc.update(code=p.code, sprint_completed_in_code=sprint.code)
        p.refresh_from_db()
        self.assertEqual(p.sprint_completed_in, sprint)

    def test_clears_sprint_started_in_when_none_passed(self):
        sprint = make_sprint(sprint_number=213, name="Sprint 213")
        p = make_project("Sprint Start Clear", sprint_started_in=sprint)
        self.svc.update(code=p.code, sprint_started_in_code=None)
        p.refresh_from_db()
        self.assertIsNone(p.sprint_started_in)

    def test_clears_sprint_completed_in_when_none_passed(self):
        sprint = make_sprint(sprint_number=214, name="Sprint 214")
        p = make_project("Sprint Complete Clear", sprint_completed_in=sprint)
        self.svc.update(code=p.code, sprint_completed_in_code=None)
        p.refresh_from_db()
        self.assertIsNone(p.sprint_completed_in)

    def test_raises_not_found_for_unknown_sprint_started_in_on_update(self):
        p = make_project("Bad Sprint Start Update")
        with self.assertRaises(NotFoundException):
            self.svc.update(code=p.code, sprint_started_in_code="SPRINT-99999")

    def test_raises_not_found_for_unknown_sprint_completed_in_on_update(self):
        p = make_project("Bad Sprint Complete Update")
        with self.assertRaises(NotFoundException):
            self.svc.update(code=p.code, sprint_completed_in_code="SPRINT-99999")


class ProjectServiceActivateDeactivateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)

    def test_activate_sets_is_active(self):
        p = make_project("Dormant", is_active=False)
        result = self.svc.activate(code=p.code)
        self.assertTrue(result.is_active)

    def test_deactivate_clears_is_active(self):
        p = make_project("Running")
        result = self.svc.deactivate(code=p.code)
        self.assertFalse(result.is_active)

    def test_activate_already_active_is_noop(self):
        p = make_project("Already Active")
        result = self.svc.activate(code=p.code)
        self.assertTrue(result.is_active)

    def test_deactivate_already_inactive_is_noop(self):
        p = make_project("Already Inactive", is_active=False)
        result = self.svc.deactivate(code=p.code)
        self.assertFalse(result.is_active)

    def test_activate_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.activate(code="PROJ-99999")

    def test_deactivate_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.deactivate(code="PROJ-99999")


class ProjectServiceDeleteTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)

    def test_deletes_project(self):
        p = make_project("To Delete")
        code = p.code
        self.svc.delete(code=code)
        self.assertFalse(Project.objects.filter(code=code).exists())

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.delete(code="PROJ-99999")


class ProjectServiceAddCollaboratorTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)
        self.project = make_project("Collab Project")
        self.team = make_team("Collab Team")

    def test_adds_collaborator(self):
        c = self.svc.add_collaborator(
            project_code=self.project.code, team_code=self.team.code
        )
        self.assertIsNotNone(c.pk)
        self.assertEqual(c.project, self.project)
        self.assertEqual(c.team, self.team)

    def test_raises_already_exists_for_duplicate(self):
        self.svc.add_collaborator(
            project_code=self.project.code, team_code=self.team.code
        )
        with self.assertRaises(AlreadyExistsException):
            self.svc.add_collaborator(
                project_code=self.project.code, team_code=self.team.code
            )

    def test_raises_validation_error_when_team_is_assigned_team(self):
        pt = make_project_type("T")
        st = make_project_status("S")
        p = Project.objects.create(
            name="Assigned Same",
            project_type=pt,
            status=st,
            assigned_team=self.team,
        )
        with self.assertRaises(ValidationException):
            self.svc.add_collaborator(project_code=p.code, team_code=self.team.code)

    def test_raises_not_found_for_unknown_project(self):
        with self.assertRaises(NotFoundException):
            self.svc.add_collaborator(
                project_code="PROJ-99999", team_code=self.team.code
            )

    def test_raises_not_found_for_unknown_team(self):
        with self.assertRaises(NotFoundException):
            self.svc.add_collaborator(
                project_code=self.project.code, team_code="TEAM-99999"
            )


class ProjectServiceRemoveCollaboratorTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)
        self.project = make_project("Remove Collab Project")
        self.team = make_team("Remove Team")
        make_project_collaborator(self.project, self.team)

    def test_removes_collaborator(self):
        self.svc.remove_collaborator(
            project_code=self.project.code, team_code=self.team.code
        )
        self.assertFalse(
            ProjectCollaborator.objects.filter(
                project=self.project, team=self.team
            ).exists()
        )

    def test_raises_not_found_for_missing_collaborator(self):
        other_team = make_team("Other Team")
        with self.assertRaises(NotFoundException):
            self.svc.remove_collaborator(
                project_code=self.project.code, team_code=other_team.code
            )

    def test_raises_not_found_for_unknown_project(self):
        with self.assertRaises(NotFoundException):
            self.svc.remove_collaborator(
                project_code="PROJ-99999", team_code=self.team.code
            )


class ProjectImportServiceTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_import_service(user=self.user)
        self.pt = make_project_type("CSV Type")
        self.st = make_project_status("CSV Status")

    def _make_csv(self, rows: list[str]) -> object:
        header = "name,project_type_code,status_code"
        content = "\n".join([header] + rows)
        return make_csv_file(content, "projects.csv")

    def test_imports_valid_row(self):
        f = self._make_csv([f"CSV Project,{self.pt.code},{self.st.code}"])
        result = self.svc.bulk_import(f)
        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["errors"]), 0)
        self.assertTrue(Project.objects.filter(name="CSV Project").exists())

    def test_dry_run_does_not_create_project(self):
        f = self._make_csv([f"Dry Run,{self.pt.code},{self.st.code}"])
        result = self.svc.bulk_import(f, dry_run=True)
        self.assertEqual(result["dry_run"], True)
        self.assertFalse(Project.objects.filter(name="Dry Run").exists())

    def test_missing_name_produces_error(self):
        f = self._make_csv([f",{self.pt.code},{self.st.code}"])
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["field"], "name")

    def test_missing_project_type_code_produces_error(self):
        f = self._make_csv([f"No Type,,{self.st.code}"])
        result = self.svc.bulk_import(f)
        self.assertGreater(len(result["errors"]), 0)

    def test_missing_status_code_produces_error(self):
        f = self._make_csv([f"No Status,{self.pt.code},"])
        result = self.svc.bulk_import(f)
        self.assertGreater(len(result["errors"]), 0)

    def test_duplicate_name_skips_row(self):
        make_project("Already Exists")
        f = self._make_csv([f"Already Exists,{self.pt.code},{self.st.code}"])
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)

    def test_missing_required_column_raises_validation_error(self):
        f = make_csv_file("name,description\nProject A,desc", "bad.csv")
        from apps.core.exceptions import ValidationException

        with self.assertRaises(ValidationException):
            self.svc.bulk_import(f)
