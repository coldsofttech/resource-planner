from django.db import IntegrityError
from django.test import TestCase

from apps.projects.models import ProjectLink
from apps.projects.tests.factories import make_project, make_project_link


class ProjectLinkCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        link = make_project_link()
        self.assertTrue(link.code.startswith("PROJLNK-"))

    def test_code_contains_pk(self):
        link = make_project_link()
        self.assertEqual(link.code, f"PROJLNK-{link.pk}")

    def test_codes_are_unique(self):
        project = make_project("Code Unique Test")
        l1 = make_project_link(project=project, title="First")
        l2 = make_project_link(project=project, title="Second")
        self.assertNotEqual(l1.code, l2.code)


class ProjectLinkFieldDefaultsTest(TestCase):
    def setUp(self):
        self.link = make_project_link()

    def test_created_at_is_set(self):
        self.assertIsNotNone(self.link.created_at)

    def test_updated_at_is_set(self):
        self.assertIsNotNone(self.link.updated_at)

    def test_created_by_defaults_to_none(self):
        self.assertIsNone(self.link.created_by)

    def test_updated_by_defaults_to_none(self):
        self.assertIsNone(self.link.updated_by)

    def test_title_is_stored(self):
        self.assertEqual(self.link.title, "Test Link")

    def test_url_is_stored(self):
        self.assertEqual(self.link.url, "https://example.com")


class ProjectLinkRelationshipsTest(TestCase):
    def test_project_fk_set(self):
        project = make_project("FK Project")
        link = make_project_link(project=project)
        self.assertEqual(link.project_id, project.pk)

    def test_reverse_relation_from_project(self):
        project = make_project("Reverse Test")
        make_project_link(project=project, title="Link A")
        make_project_link(project=project, title="Link B")
        self.assertEqual(project.links.count(), 2)

    def test_cascade_delete_removes_links(self):
        project = make_project("Cascade Project")
        make_project_link(project=project)
        project.delete()
        self.assertEqual(ProjectLink.objects.count(), 0)


class ProjectLinkUniqueConstraintTest(TestCase):
    def test_duplicate_project_and_title_raises(self):
        project = make_project("Dup Test")
        make_project_link(project=project, title="Shared Title")
        with self.assertRaises(IntegrityError):
            ProjectLink.objects.create(
                project=project,
                title="Shared Title",
                url="https://other.com",
            )

    def test_same_title_on_different_projects_is_allowed(self):
        p1 = make_project("P1")
        p2 = make_project("P2")
        l1 = make_project_link(project=p1, title="Docs")
        l2 = make_project_link(project=p2, title="Docs")
        self.assertNotEqual(l1.pk, l2.pk)

    def test_different_titles_on_same_project_is_allowed(self):
        project = make_project("Multi Link")
        l1 = make_project_link(project=project, title="Wiki")
        l2 = make_project_link(project=project, title="Jira")
        self.assertNotEqual(l1.pk, l2.pk)


class ProjectLinkOrderingTest(TestCase):
    def test_ordered_by_title_ascending(self):
        project = make_project("Order Test")
        make_project_link(project=project, title="Zebra")
        make_project_link(project=project, title="Alpha")
        make_project_link(project=project, title="Mango")
        titles = list(
            ProjectLink.objects.filter(project=project).values_list("title", flat=True)
        )
        self.assertEqual(titles, sorted(titles))
