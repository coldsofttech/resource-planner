from django.test import TestCase

from apps.projects import selectors
from apps.projects.tests.factories import make_project, make_project_attachment


class GetAttachmentByCodeTest(TestCase):
    def test_returns_attachment_for_valid_code(self):
        attachment = make_project_attachment()
        result = selectors.get_attachment_by_code(attachment.code)
        self.assertIsNotNone(result)
        self.assertEqual(result.pk, attachment.pk)

    def test_returns_none_for_unknown_code(self):
        result = selectors.get_attachment_by_code("PROJAT-999999")
        self.assertIsNone(result)

    def test_select_related_project_is_loaded(self):
        attachment = make_project_attachment()
        result = selectors.get_attachment_by_code(attachment.code)
        with self.assertNumQueries(0):
            _ = result.project.code

    def test_select_related_created_by_is_loaded(self):
        attachment = make_project_attachment()
        result = selectors.get_attachment_by_code(attachment.code)
        with self.assertNumQueries(0):
            _ = result.created_by


class GetAttachmentsForProjectTest(TestCase):
    def setUp(self):
        self.project = make_project()

    def test_returns_attachments_for_project(self):
        make_project_attachment(project=self.project, file_name="a.pdf")
        make_project_attachment(project=self.project, file_name="b.pdf")
        result = selectors.get_attachments_for_project(self.project)
        self.assertEqual(result.count(), 2)

    def test_excludes_attachments_from_other_projects(self):
        other = make_project("Other Project")
        make_project_attachment(project=self.project, file_name="mine.pdf")
        make_project_attachment(project=other, file_name="theirs.pdf")
        result = selectors.get_attachments_for_project(self.project)
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().file_name, "mine.pdf")

    def test_returns_empty_queryset_when_no_attachments(self):
        result = selectors.get_attachments_for_project(self.project)
        self.assertEqual(result.count(), 0)

    def test_ordered_by_created_at_descending(self):
        a1 = make_project_attachment(project=self.project, file_name="first.pdf")
        a2 = make_project_attachment(project=self.project, file_name="second.pdf")
        result = list(selectors.get_attachments_for_project(self.project))
        self.assertEqual(result[0].pk, a2.pk)
        self.assertEqual(result[1].pk, a1.pk)


class ProjectAttachmentFilenameExistsTest(TestCase):
    def setUp(self):
        self.project = make_project()

    def test_returns_true_when_filename_exists(self):
        make_project_attachment(project=self.project, file_name="existing.pdf")
        self.assertTrue(
            selectors.project_attachment_filename_exists(self.project, "existing.pdf")
        )

    def test_returns_false_when_filename_does_not_exist(self):
        self.assertFalse(
            selectors.project_attachment_filename_exists(self.project, "missing.pdf")
        )

    def test_returns_false_when_filename_exists_on_other_project(self):
        other = make_project("Other")
        make_project_attachment(project=other, file_name="shared.pdf")
        self.assertFalse(
            selectors.project_attachment_filename_exists(self.project, "shared.pdf")
        )

    def test_exclude_pk_allows_same_record(self):
        attachment = make_project_attachment(project=self.project, file_name="doc.pdf")
        self.assertFalse(
            selectors.project_attachment_filename_exists(
                self.project, "doc.pdf", exclude_pk=attachment.pk
            )
        )

    def test_exclude_pk_still_detects_other_duplicate(self):
        make_project_attachment(project=self.project, file_name="doc.pdf")
        a2 = make_project_attachment(project=self.project, file_name="other.pdf")
        self.assertTrue(
            selectors.project_attachment_filename_exists(
                self.project, "doc.pdf", exclude_pk=a2.pk
            )
        )
