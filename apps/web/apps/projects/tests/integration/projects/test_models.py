from django.db import IntegrityError
from django.test import TestCase

from apps.projects.models import Project, ProjectCollaborator
from apps.projects.tests.factories import (
    make_programme,
    make_project,
    make_project_collaborator,
    make_project_status,
    make_project_type,
)
from apps.teams.tests.factories import make_team
from apps.users.tests.factories import make_user


class ProjectCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        p = make_project()
        self.assertTrue(p.code.startswith("PROJ-"))

    def test_code_contains_pk(self):
        p = make_project()
        self.assertEqual(p.code, f"PROJ-{p.pk}")

    def test_codes_are_unique(self):
        p1 = make_project("Alpha")
        p2 = make_project("Beta")
        self.assertNotEqual(p1.code, p2.code)


class ProjectFieldDefaultsTest(TestCase):
    def setUp(self):
        self.project = make_project()

    def test_is_active_defaults_to_true(self):
        self.assertTrue(self.project.is_active)

    def test_description_defaults_to_empty(self):
        self.assertEqual(self.project.description, "")

    def test_efforts_issued_defaults_to_false(self):
        self.assertFalse(self.project.efforts_issued)

    def test_run_cost_applies_defaults_to_false(self):
        self.assertFalse(self.project.run_cost_applies)

    def test_confidence_defaults_to_none(self):
        self.assertIsNone(self.project.confidence)

    def test_priority_defaults_to_none(self):
        self.assertIsNone(self.project.priority)

    def test_start_date_defaults_to_none(self):
        self.assertIsNone(self.project.start_date)

    def test_end_date_defaults_to_none(self):
        self.assertIsNone(self.project.end_date)

    def test_commitment_date_defaults_to_none(self):
        self.assertIsNone(self.project.commitment_date)

    def test_programme_defaults_to_none(self):
        self.assertIsNone(self.project.programme)

    def test_assigned_team_defaults_to_none(self):
        self.assertIsNone(self.project.assigned_team)

    def test_sub_status_defaults_to_none(self):
        self.assertIsNone(self.project.sub_status)

    def test_created_by_defaults_to_none(self):
        self.assertIsNone(self.project.created_by)

    def test_updated_by_defaults_to_none(self):
        self.assertIsNone(self.project.updated_by)

    def test_str_returns_name(self):
        p = make_project("My Project")
        self.assertEqual(str(p), "My Project")


class ProjectDisplayNameSignalTest(TestCase):
    def test_display_name_set_to_name_without_programme(self):
        p = make_project("Alpha")
        self.assertEqual(p.display_name, "Alpha")

    def test_display_name_uses_programme_prefix(self):
        prog = make_programme("Core")
        p = make_project("Beta", programme=prog)
        self.assertEqual(p.display_name, "Core: Beta")

    def test_display_name_updates_on_name_change(self):
        prog = make_programme("Platform")
        p = make_project("Initial", programme=prog)
        p.name = "Updated"
        p.save()
        p.refresh_from_db()
        self.assertEqual(p.display_name, "Platform: Updated")

    def test_display_name_updates_when_programme_removed(self):
        prog = make_programme("Sales")
        p = make_project("Project X", programme=prog)
        p.programme = None
        p.save()
        p.refresh_from_db()
        self.assertEqual(p.display_name, "Project X")


class ProjectConstraintTest(TestCase):
    def test_duplicate_name_raises_integrity_error(self):
        make_project("Unique Project")
        with self.assertRaises(IntegrityError):
            make_project("Unique Project")

    def test_different_names_are_allowed(self):
        make_project("Alpha")
        p2 = make_project("Beta")
        self.assertIsNotNone(p2.pk)


class ProjectOrderingTest(TestCase):
    def test_ordered_by_name(self):
        make_project("Zeta")
        make_project("Alpha")
        make_project("Mu")
        names = list(Project.objects.values_list("name", flat=True))
        self.assertEqual(names, sorted(names))


class ProjectAuditableTest(TestCase):
    def test_created_at_is_set(self):
        p = make_project()
        self.assertIsNotNone(p.created_at)

    def test_updated_at_is_set(self):
        p = make_project()
        self.assertIsNotNone(p.updated_at)

    def test_created_by_stores_user(self):
        user = make_user()
        pt = make_project_type("T")
        st = make_project_status("S")
        p = Project.objects.create(
            name="Audited",
            project_type=pt,
            status=st,
            created_by=user,
            updated_by=user,
        )
        self.assertEqual(p.created_by, user)


class ProjectForeignKeyTest(TestCase):
    def test_project_type_linked(self):
        pt = make_project_type("Internal")
        p = make_project("FK Test", project_type=pt)
        self.assertEqual(p.project_type, pt)

    def test_status_linked(self):
        st = make_project_status("Live")
        p = make_project("Status Test", status=st)
        self.assertEqual(p.status, st)

    def test_assigned_team_linked(self):
        team = make_team("Dev Team")
        p = make_project("Team Test", assigned_team=team)
        self.assertEqual(p.assigned_team, team)

    def test_programme_linked(self):
        prog = make_programme("Initiative A")
        p = make_project("Prog Test", programme=prog)
        self.assertEqual(p.programme, prog)


class ProjectCollaboratorFieldDefaultsTest(TestCase):
    def test_added_on_is_set(self):
        p = make_project("Collab Project")
        team = make_team()
        pc = make_project_collaborator(p, team)
        self.assertIsNotNone(pc.added_on)

    def test_created_at_is_set(self):
        p = make_project("Collab Project 2")
        team = make_team("Team 2")
        pc = make_project_collaborator(p, team)
        self.assertIsNotNone(pc.created_at)


class ProjectCollaboratorConstraintTest(TestCase):
    def test_duplicate_project_team_raises_integrity_error(self):
        p = make_project("Dup Collab")
        team = make_team("Shared")
        make_project_collaborator(p, team)
        with self.assertRaises(IntegrityError):
            make_project_collaborator(p, team)

    def test_same_team_on_different_projects_is_allowed(self):
        p1 = make_project("Project One")
        p2 = make_project("Project Two")
        team = make_team("Shared Team")
        c1 = make_project_collaborator(p1, team)
        c2 = make_project_collaborator(p2, team)
        self.assertNotEqual(c1.pk, c2.pk)

    def test_different_teams_on_same_project_is_allowed(self):
        p = make_project("Multi Team Project")
        t1 = make_team("Team A")
        t2 = make_team("Team B")
        c1 = make_project_collaborator(p, t1)
        c2 = make_project_collaborator(p, t2)
        self.assertNotEqual(c1.pk, c2.pk)


class ProjectCollaboratorOrderingTest(TestCase):
    def test_ordered_by_added_on(self):
        p = make_project("Ordered Collab")
        t1 = make_team("First")
        t2 = make_team("Second")
        make_project_collaborator(p, t1)
        make_project_collaborator(p, t2)
        collab_pks = list(
            ProjectCollaborator.objects.filter(project=p).values_list("pk", flat=True)
        )
        self.assertEqual(collab_pks, sorted(collab_pks))
