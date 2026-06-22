from django.test import TestCase

from apps.projects import selectors
from apps.projects.tests.factories import make_project, make_project_link


class GetLinkByCodeTest(TestCase):
    def setUp(self):
        self.link = make_project_link()

    def test_returns_link_for_valid_code(self):
        result = selectors.get_link_by_code(self.link.code)
        self.assertIsNotNone(result)
        self.assertEqual(result.pk, self.link.pk)

    def test_returns_none_for_invalid_code(self):
        result = selectors.get_link_by_code("PROJLNK-999999")
        self.assertIsNone(result)

    def test_select_related_project_is_loaded(self):
        result = selectors.get_link_by_code(self.link.code)
        self.assertIsNotNone(result.project)

    def test_select_related_created_by_accessible(self):
        result = selectors.get_link_by_code(self.link.code)
        self.assertIsNone(result.created_by)

    def test_select_related_updated_by_accessible(self):
        result = selectors.get_link_by_code(self.link.code)
        self.assertIsNone(result.updated_by)


class GetLinksForProjectTest(TestCase):
    def setUp(self):
        self.project = make_project("LinkListProject")
        self.l1 = make_project_link(project=self.project, title="Bravo")
        self.l2 = make_project_link(project=self.project, title="Alpha")

    def test_returns_all_links_for_project(self):
        result = list(selectors.get_links_for_project(self.project))
        self.assertEqual(len(result), 2)

    def test_ordered_by_title_ascending(self):
        result = list(selectors.get_links_for_project(self.project))
        titles = [lnk.title for lnk in result]
        self.assertEqual(titles, sorted(titles))

    def test_excludes_links_from_other_projects(self):
        other = make_project("Other")
        make_project_link(project=other, title="External")
        result = list(selectors.get_links_for_project(self.project))
        self.assertEqual(len(result), 2)

    def test_returns_empty_for_project_with_no_links(self):
        empty = make_project("Empty")
        result = list(selectors.get_links_for_project(empty))
        self.assertEqual(result, [])

    def test_select_related_project_is_loaded(self):
        result = list(selectors.get_links_for_project(self.project))
        for lnk in result:
            self.assertIsNotNone(lnk.project)


class ProjectLinkTitleExistsTest(TestCase):
    def setUp(self):
        self.project = make_project("TitleExistsProject")
        self.link = make_project_link(project=self.project, title="Existing")

    def test_returns_true_when_title_exists(self):
        self.assertTrue(selectors.project_link_title_exists(self.project, "Existing"))

    def test_returns_false_for_different_title(self):
        self.assertFalse(
            selectors.project_link_title_exists(self.project, "Nonexistent")
        )

    def test_returns_false_for_same_title_on_different_project(self):
        other = make_project("Other")
        self.assertFalse(selectors.project_link_title_exists(other, "Existing"))

    def test_exclude_pk_skips_own_record(self):
        self.assertFalse(
            selectors.project_link_title_exists(
                self.project, "Existing", exclude_pk=self.link.pk
            )
        )

    def test_exclude_pk_of_unrelated_record_still_detects_title(self):
        # "Duplicate" exists once; excluding a different record must not hide it
        other_link = make_project_link(project=self.project, title="Duplicate")
        self.assertTrue(
            selectors.project_link_title_exists(
                self.project, "Duplicate", exclude_pk=self.link.pk
            )
        )
        # Excluding the only "Duplicate" record must return False
        self.assertFalse(
            selectors.project_link_title_exists(
                self.project, "Duplicate", exclude_pk=other_link.pk
            )
        )
