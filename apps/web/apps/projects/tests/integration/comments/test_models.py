from django.test import TestCase

from apps.projects.models import ProjectComment
from apps.projects.tests.factories import make_project, make_project_comment


class ProjectCommentCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        pc = make_project_comment()
        self.assertTrue(pc.code.startswith("PROJCOMMENT-"))

    def test_code_contains_pk(self):
        pc = make_project_comment()
        self.assertEqual(pc.code, f"PROJCOMMENT-{pc.pk}")

    def test_codes_are_unique_across_records(self):
        project_a = make_project("Project A For Code Test")
        project_b = make_project("Project B For Code Test")
        pc1 = make_project_comment(project=project_a, comment_text="First")
        pc2 = make_project_comment(project=project_b, comment_text="Second")
        self.assertNotEqual(pc1.code, pc2.code)

    def test_code_not_editable_directly(self):
        self.assertFalse(ProjectComment._meta.get_field("code").editable)


class ProjectCommentStrTest(TestCase):
    def test_str_contains_project_and_comment_id(self):
        project = make_project("My Project")
        pc = make_project_comment(project=project, comment_text="Hello.")
        result = str(pc)
        self.assertIn(str(project), result)
        self.assertIn(str(pc.comment_id), result)


class ProjectCommentFieldDefaultsTest(TestCase):
    def setUp(self):
        self.pc = make_project_comment()

    def test_created_at_is_set(self):
        self.assertIsNotNone(self.pc.created_at)

    def test_updated_at_is_set(self):
        self.assertIsNotNone(self.pc.updated_at)

    def test_created_by_defaults_to_none(self):
        self.assertIsNone(self.pc.created_by)

    def test_updated_by_defaults_to_none(self):
        self.assertIsNone(self.pc.updated_by)


class ProjectCommentRelationshipsTest(TestCase):
    def test_project_fk_set(self):
        project = make_project()
        pc = make_project_comment(project=project)
        self.assertEqual(pc.project_id, project.pk)

    def test_comment_fk_set(self):
        pc = make_project_comment()
        self.assertIsNotNone(pc.comment_id)

    def test_reverse_relation_from_project(self):
        project = make_project()
        make_project_comment(project=project, comment_text="First")
        make_project_comment(project=project, comment_text="Second")
        self.assertEqual(project.project_comments.count(), 2)

    def test_comment_is_onetoone(self):
        pc = make_project_comment()
        comment = pc.comment
        self.assertEqual(comment.project_link, pc)

    def test_cascade_delete_when_project_deleted(self):
        project = make_project()
        pc = make_project_comment(project=project)
        pk = pc.pk
        project.delete()
        self.assertFalse(ProjectComment.objects.filter(pk=pk).exists())

    def test_cascade_delete_of_project_comment_when_comment_deleted(self):
        pc = make_project_comment()
        pc_pk = pc.pk
        pc.comment.delete()
        self.assertFalse(ProjectComment.objects.filter(pk=pc_pk).exists())

    def test_comments_from_different_projects_are_isolated(self):
        project_a = make_project("Project A")
        project_b = make_project("Project B")
        make_project_comment(project=project_a)
        make_project_comment(project=project_b)
        self.assertEqual(project_a.project_comments.count(), 1)
        self.assertEqual(project_b.project_comments.count(), 1)
