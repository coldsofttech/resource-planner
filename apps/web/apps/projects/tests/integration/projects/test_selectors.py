from django.test import TestCase

from apps.projects.selectors import (
    get_all_projects,
    get_project_by_code,
    get_project_collaborator,
    get_project_options,
    get_project_stats,
    project_name_exists,
)
from apps.projects.tests.factories import (
    make_project,
    make_project_collaborator,
)
from apps.teams.tests.factories import make_team

# ── get_all_projects ──────────────────────────────────────────────────────────


class GetAllProjectsTest(TestCase):
    def test_returns_all_projects(self):
        make_project("Alpha")
        make_project("Beta")
        qs = get_all_projects()
        self.assertEqual(qs.count(), 2)

    def test_returns_active_and_inactive(self):
        make_project("Active", is_active=True)
        make_project("Inactive", is_active=False)
        qs = get_all_projects()
        self.assertEqual(qs.count(), 2)

    def test_select_related_project_type(self):
        make_project("With Type")
        qs = list(get_all_projects())
        self.assertIsNotNone(qs[0].project_type)

    def test_select_related_status(self):
        make_project("With Status")
        qs = list(get_all_projects())
        self.assertIsNotNone(qs[0].status)

    def test_empty_returns_empty_queryset(self):
        qs = get_all_projects()
        self.assertEqual(qs.count(), 0)


# ── get_project_by_code ───────────────────────────────────────────────────────


class GetProjectByCodeTest(TestCase):
    def setUp(self):
        self.project = make_project("Known Project")

    def test_returns_project_for_valid_code(self):
        result = get_project_by_code(self.project.code)
        self.assertEqual(result, self.project)

    def test_returns_none_for_unknown_code(self):
        result = get_project_by_code("PROJ-99999")
        self.assertIsNone(result)

    def test_returns_inactive_project(self):
        p = make_project("Archived", is_active=False)
        result = get_project_by_code(p.code)
        self.assertEqual(result, p)

    def test_select_related_project_type(self):
        result = get_project_by_code(self.project.code)
        self.assertIsNotNone(result.project_type)

    def test_select_related_status(self):
        result = get_project_by_code(self.project.code)
        self.assertIsNotNone(result.status)


# ── project_name_exists ───────────────────────────────────────────────────────


class ProjectNameExistsTest(TestCase):
    def setUp(self):
        self.project = make_project("Existing Project")

    def test_returns_true_for_existing_name(self):
        self.assertTrue(project_name_exists("Existing Project"))

    def test_case_insensitive_match(self):
        self.assertTrue(project_name_exists("existing project"))
        self.assertTrue(project_name_exists("EXISTING PROJECT"))

    def test_returns_false_for_missing_name(self):
        self.assertFalse(project_name_exists("Ghost Project"))

    def test_exclude_pk_returns_false_for_same_record(self):
        self.assertFalse(
            project_name_exists("Existing Project", exclude_pk=self.project.pk)
        )

    def test_exclude_pk_still_detects_other_records(self):
        make_project("Other Project")
        self.assertTrue(
            project_name_exists("Other Project", exclude_pk=self.project.pk)
        )


# ── get_project_options ───────────────────────────────────────────────────────


class GetProjectOptionsTest(TestCase):
    def test_returns_only_active_projects(self):
        make_project("Active", is_active=True)
        make_project("Inactive", is_active=False)
        results = list(get_project_options())
        names = [p.name for p in results]
        self.assertIn("Active", names)
        self.assertNotIn("Inactive", names)

    def test_ordered_by_name(self):
        make_project("Zeta")
        make_project("Alpha")
        names = [p.name for p in get_project_options()]
        self.assertEqual(names, sorted(names))

    def test_returns_code_and_name_and_display_name(self):
        make_project("Options Test")
        result = get_project_options().first()
        self.assertTrue(hasattr(result, "code"))
        self.assertTrue(hasattr(result, "name"))
        self.assertTrue(hasattr(result, "display_name"))


# ── get_project_stats ─────────────────────────────────────────────────────────


class GetProjectStatsTest(TestCase):
    def test_returns_zero_counts_when_empty(self):
        stats = get_project_stats()
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["active"], 0)
        self.assertEqual(stats["inactive"], 0)

    def test_counts_total(self):
        make_project("Alpha")
        make_project("Beta", is_active=False)
        stats = get_project_stats()
        self.assertEqual(stats["total"], 2)

    def test_counts_active_separately(self):
        make_project("Active")
        make_project("Inactive", is_active=False)
        stats = get_project_stats()
        self.assertEqual(stats["active"], 1)

    def test_counts_inactive_separately(self):
        make_project("Active")
        make_project("Inactive", is_active=False)
        stats = get_project_stats()
        self.assertEqual(stats["inactive"], 1)

    def test_has_all_required_keys(self):
        stats = get_project_stats()
        self.assertIn("total", stats)
        self.assertIn("active", stats)
        self.assertIn("inactive", stats)


# ── get_project_collaborator ──────────────────────────────────────────────────


class GetProjectCollaboratorTest(TestCase):
    def setUp(self):
        self.project = make_project("Collab Test")
        self.team = make_team("Collab Team")
        self.collab = make_project_collaborator(self.project, self.team)

    def test_returns_collaborator_for_valid_team_code(self):
        result = get_project_collaborator(self.project, self.team.code)
        self.assertEqual(result, self.collab)

    def test_returns_none_for_unknown_team_code(self):
        result = get_project_collaborator(self.project, "TEAM-99999")
        self.assertIsNone(result)

    def test_returns_none_for_different_project(self):
        other = make_project("Other Project")
        result = get_project_collaborator(other, self.team.code)
        self.assertIsNone(result)

    def test_select_related_team(self):
        result = get_project_collaborator(self.project, self.team.code)
        self.assertIsNotNone(result.team)
        self.assertEqual(result.team.name, "Collab Team")
