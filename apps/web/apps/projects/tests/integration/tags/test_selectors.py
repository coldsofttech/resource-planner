from django.test import TestCase

from apps.projects import selectors
from apps.projects.tests.factories import make_project, make_project_tag, make_tag


class GetAllProjectTagsTest(TestCase):
    def setUp(self):
        self.project = make_project("TagProject")
        self.tag1 = make_tag("#alpha")
        self.tag2 = make_tag("#beta")
        self.pt1 = make_project_tag(project=self.project, tag=self.tag1)
        self.pt2 = make_project_tag(project=self.project, tag=self.tag2)

    def test_returns_all_tags_for_project(self):
        result = list(selectors.get_all_project_tags(self.project))
        self.assertEqual(len(result), 2)

    def test_ordered_by_tag_name(self):
        result = list(selectors.get_all_project_tags(self.project))
        names = [pt.tag.name for pt in result]
        self.assertEqual(names, sorted(names))

    def test_excludes_tags_from_other_projects(self):
        other_project = make_project("Other")
        other_tag = make_tag("#other")
        make_project_tag(project=other_project, tag=other_tag)
        result = list(selectors.get_all_project_tags(self.project))
        self.assertEqual(len(result), 2)

    def test_uses_select_related_for_tag(self):
        result = list(selectors.get_all_project_tags(self.project))
        for pt in result:
            self.assertIsNotNone(pt.tag)

    def test_returns_empty_for_project_with_no_tags(self):
        empty_project = make_project("Empty")
        result = list(selectors.get_all_project_tags(empty_project))
        self.assertEqual(result, [])


class GetProjectTagByCodeTest(TestCase):
    def setUp(self):
        self.pt = make_project_tag()

    def test_returns_project_tag_for_valid_code(self):
        result = selectors.get_project_tag_by_code(self.pt.code)
        self.assertEqual(result.pk, self.pt.pk)

    def test_returns_none_for_invalid_code(self):
        result = selectors.get_project_tag_by_code("PROJTAG-999999")
        self.assertIsNone(result)

    def test_select_related_tag_is_loaded(self):
        result = selectors.get_project_tag_by_code(self.pt.code)
        self.assertIsNotNone(result.tag)

    def test_select_related_project_is_loaded(self):
        result = selectors.get_project_tag_by_code(self.pt.code)
        self.assertIsNotNone(result.project)


class ProjectTagExistsTest(TestCase):
    def setUp(self):
        self.project = make_project("ExistsProject")
        self.tag = make_tag("#exists")
        self.pt = make_project_tag(project=self.project, tag=self.tag)

    def test_returns_true_when_combination_exists(self):
        self.assertTrue(selectors.project_tag_exists(self.project, self.tag))

    def test_returns_false_for_different_tag(self):
        other_tag = make_tag("#other")
        self.assertFalse(selectors.project_tag_exists(self.project, other_tag))

    def test_returns_false_for_different_project(self):
        other_project = make_project("Other")
        self.assertFalse(selectors.project_tag_exists(other_project, self.tag))

    def test_exclude_pk_skips_own_record(self):
        self.assertFalse(
            selectors.project_tag_exists(self.project, self.tag, exclude_pk=self.pt.pk)
        )
