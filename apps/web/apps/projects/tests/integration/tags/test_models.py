from django.db import IntegrityError
from django.test import TestCase

from apps.projects.models import ProjectTag
from apps.projects.tests.factories import make_project, make_project_tag, make_tag


class ProjectTagCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        pt = make_project_tag()
        self.assertTrue(pt.code.startswith("PROJTAG-"))

    def test_code_contains_pk(self):
        pt = make_project_tag()
        self.assertEqual(pt.code, f"PROJTAG-{pt.pk}")

    def test_codes_are_unique(self):
        project = make_project("Unique Tag Test")
        pt1 = make_project_tag(project=project, tag=make_tag("#first"))
        pt2 = make_project_tag(project=project, tag=make_tag("#second"))
        self.assertNotEqual(pt1.code, pt2.code)


class ProjectTagFieldDefaultsTest(TestCase):
    def setUp(self):
        self.pt = make_project_tag()

    def test_created_at_is_set(self):
        self.assertIsNotNone(self.pt.created_at)

    def test_updated_at_is_set(self):
        self.assertIsNotNone(self.pt.updated_at)

    def test_created_by_defaults_to_none(self):
        self.assertIsNone(self.pt.created_by)

    def test_updated_by_defaults_to_none(self):
        self.assertIsNone(self.pt.updated_by)


class ProjectTagRelationshipsTest(TestCase):
    def test_project_fk_set(self):
        project = make_project("Omega")
        pt = make_project_tag(project=project)
        self.assertEqual(pt.project_id, project.pk)

    def test_tag_fk_set(self):
        tag = make_tag("#omega")
        pt = make_project_tag(tag=tag)
        self.assertEqual(pt.tag_id, tag.pk)

    def test_reverse_relation_from_project(self):
        project = make_project("Gamma")
        tag = make_tag("#gamma")
        make_project_tag(project=project, tag=tag)
        self.assertEqual(project.tags.count(), 1)

    def test_reverse_relation_from_tag(self):
        tag = make_tag("#delta")
        make_project_tag(tag=tag)
        self.assertEqual(tag.project_tags.count(), 1)


class ProjectTagUniqueConstraintTest(TestCase):
    def test_duplicate_project_tag_raises(self):
        project = make_project("Zeta")
        tag = make_tag("#zeta")
        make_project_tag(project=project, tag=tag)
        with self.assertRaises(IntegrityError):
            ProjectTag.objects.create(project=project, tag=tag)

    def test_same_tag_on_different_projects_is_allowed(self):
        tag = make_tag("#shared")
        p1 = make_project("P1")
        p2 = make_project("P2")
        pt1 = make_project_tag(project=p1, tag=tag)
        pt2 = make_project_tag(project=p2, tag=tag)
        self.assertNotEqual(pt1.pk, pt2.pk)

    def test_different_tags_on_same_project_is_allowed(self):
        project = make_project("Multi-Tag")
        t1 = make_tag("#one")
        t2 = make_tag("#two")
        pt1 = make_project_tag(project=project, tag=t1)
        pt2 = make_project_tag(project=project, tag=t2)
        self.assertNotEqual(pt1.pk, pt2.pk)


class ProjectTagCascadeTest(TestCase):
    def test_deleted_project_removes_tags(self):
        project = make_project("Cascade")
        make_project_tag(project=project)
        project.delete()
        self.assertEqual(ProjectTag.objects.count(), 0)

    def test_deleted_tag_removes_project_tags(self):
        tag = make_tag("#removeme")
        make_project_tag(tag=tag)
        tag.delete()
        self.assertEqual(ProjectTag.objects.count(), 0)
