from django.db import IntegrityError
from django.test import TestCase

from apps.projects.models import ProjectAttachment
from apps.projects.tests.factories import make_project, make_project_attachment


class ProjectAttachmentModelTest(TestCase):
    def test_code_is_auto_generated(self):
        attachment = make_project_attachment()
        self.assertTrue(attachment.code.startswith("PROJAT-"))

    def test_code_is_unique_across_attachments(self):
        project = make_project()
        a1 = make_project_attachment(project=project, file_name="file1.pdf")
        a2 = make_project_attachment(project=project, file_name="file2.pdf")
        self.assertNotEqual(a1.code, a2.code)

    def test_file_name_max_length_255(self):
        field = ProjectAttachment._meta.get_field("file_name")
        self.assertEqual(field.max_length, 255)

    def test_content_type_defaults_to_empty_string(self):
        project = make_project()
        attachment = ProjectAttachment.objects.create(
            project=project,
            file_name="nodoc.bin",
            file_path="file:///tmp/nodoc.bin",
        )
        self.assertEqual(attachment.content_type, "")

    def test_file_size_defaults_to_zero(self):
        project = make_project()
        attachment = ProjectAttachment.objects.create(
            project=project,
            file_name="empty.pdf",
            file_path="file:///tmp/empty.pdf",
        )
        self.assertEqual(attachment.file_size, 0)

    def test_created_by_defaults_to_none(self):
        attachment = make_project_attachment()
        self.assertIsNone(attachment.created_by)

    def test_updated_by_defaults_to_none(self):
        attachment = make_project_attachment()
        self.assertIsNone(attachment.updated_by)

    def test_created_at_is_set_on_creation(self):
        attachment = make_project_attachment()
        self.assertIsNotNone(attachment.created_at)

    def test_updated_at_is_set_on_creation(self):
        attachment = make_project_attachment()
        self.assertIsNotNone(attachment.updated_at)

    def test_unique_constraint_on_project_and_file_name(self):
        project = make_project()
        make_project_attachment(project=project, file_name="report.pdf")
        with self.assertRaises(IntegrityError):
            make_project_attachment(project=project, file_name="report.pdf")

    def test_same_file_name_on_different_projects_is_allowed(self):
        p1 = make_project("Project A")
        p2 = make_project("Project B")
        a1 = make_project_attachment(project=p1, file_name="shared.pdf")
        a2 = make_project_attachment(project=p2, file_name="shared.pdf")
        self.assertNotEqual(a1.pk, a2.pk)

    def test_cascade_delete_when_project_is_deleted(self):
        project = make_project()
        attachment = make_project_attachment(project=project)
        pk = attachment.pk
        project.delete()
        self.assertFalse(ProjectAttachment.objects.filter(pk=pk).exists())

    def test_ordering_latest_first(self):
        project = make_project()
        a1 = make_project_attachment(project=project, file_name="first.pdf")
        a2 = make_project_attachment(project=project, file_name="second.pdf")
        queryset = list(ProjectAttachment.objects.filter(project=project))
        self.assertEqual(queryset[0].pk, a2.pk)
        self.assertEqual(queryset[1].pk, a1.pk)

    def test_project_relationship(self):
        project = make_project()
        attachment = make_project_attachment(project=project)
        self.assertEqual(attachment.project_id, project.pk)

    def test_file_path_is_stored(self):
        attachment = make_project_attachment(file_path="file:///tmp/doc.pdf")
        self.assertEqual(attachment.file_path, "file:///tmp/doc.pdf")
