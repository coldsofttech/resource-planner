from django.test import TestCase

from apps.projects import selectors
from apps.projects.tests.factories import make_project_type


class GetAllProjectTypesTest(TestCase):
    def test_returns_all_project_types(self):
        make_project_type("Alpha")
        make_project_type("Beta", is_active=False)
        result = list(selectors.get_all_project_types())
        names = [pt.name for pt in result]
        self.assertIn("Alpha", names)
        self.assertIn("Beta", names)

    def test_returns_empty_when_no_records(self):
        result = list(selectors.get_all_project_types())
        self.assertEqual(result, [])


class GetActiveProjectTypesTest(TestCase):
    def test_returns_only_active(self):
        make_project_type("Active")
        make_project_type("Inactive", is_active=False)
        result = list(selectors.get_active_project_types())
        names = [pt.name for pt in result]
        self.assertIn("Active", names)
        self.assertNotIn("Inactive", names)

    def test_excludes_inactive(self):
        make_project_type("Inactive", is_active=False)
        result = list(selectors.get_active_project_types())
        self.assertEqual(result, [])


class GetProjectTypeByCodeTest(TestCase):
    def test_returns_project_type_for_matching_code(self):
        pt = make_project_type("Internal")
        result = selectors.get_project_type_by_code(pt.code)
        self.assertEqual(result, pt)

    def test_returns_none_for_unknown_code(self):
        result = selectors.get_project_type_by_code("PROJTYPE-99999")
        self.assertIsNone(result)


class ProjectTypeExistsTest(TestCase):
    def test_returns_true_for_existing_name(self):
        make_project_type("Internal")
        self.assertTrue(selectors.project_type_exists("Internal"))

    def test_case_insensitive_match(self):
        make_project_type("Internal")
        self.assertTrue(selectors.project_type_exists("internal"))

    def test_returns_false_for_unknown_name(self):
        self.assertFalse(selectors.project_type_exists("Ghost"))

    def test_excludes_pk_from_check(self):
        pt = make_project_type("Internal")
        self.assertFalse(selectors.project_type_exists("Internal", exclude_pk=pt.pk))


class GetProjectTypeOptionsTest(TestCase):
    def test_returns_only_active(self):
        make_project_type("Active")
        make_project_type("Inactive", is_active=False)
        result = list(selectors.get_project_type_options())
        names = [pt.name for pt in result]
        self.assertIn("Active", names)
        self.assertNotIn("Inactive", names)

    def test_ordered_by_name(self):
        make_project_type("Zeta")
        make_project_type("Alpha")
        result = list(selectors.get_project_type_options())
        names = [pt.name for pt in result]
        self.assertEqual(names, sorted(names))


class GetProjectTypeStatsTest(TestCase):
    def test_returns_counts(self):
        make_project_type("A", is_active=True)
        make_project_type("B", is_active=True)
        make_project_type("C", is_active=False)
        stats = selectors.get_project_type_stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["active"], 2)
        self.assertEqual(stats["inactive"], 1)

    def test_zero_counts_when_empty(self):
        stats = selectors.get_project_type_stats()
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["active"], 0)
        self.assertEqual(stats["inactive"], 0)
