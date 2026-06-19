from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.projects.models import ProjectAttachment
from apps.projects.services import ProjectAttachmentService
from apps.projects.tests.factories import make_project, make_project_attachment
from apps.users.tests.factories import make_user

_STORE_PATH = "storagecore.store"
_RETRIEVE_PATH = "storagecore.retrieve"
_DELETE_PATH = "storagecore.delete"
_INFRA_TYPE_PATH = "apps.configurations.selectors.Infra.get_storage_type"
_INFRA_PATH_PATH = "apps.configurations.selectors.Infra.get_storage_path"


def _mock_infra_type():
    m = MagicMock()
    m.value = "local"
    return m


class ProjectAttachmentServiceGetTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.service = ProjectAttachmentService(user=self.user)

    def test_get_returns_attachment(self):
        attachment = make_project_attachment()
        result = self.service.get(attachment.code)
        self.assertEqual(result.pk, attachment.pk)

    def test_get_raises_not_found_for_invalid_code(self):
        with self.assertRaises(NotFoundException):
            self.service.get("PROJAT-999999")


class ProjectAttachmentServiceListTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.service = ProjectAttachmentService(user=self.user)
        self.project = make_project("ListProject")

    def test_list_returns_all_attachments_for_project(self):
        make_project_attachment(project=self.project, file_name="a.pdf")
        make_project_attachment(project=self.project, file_name="b.pdf")
        result = self.service.list(self.project.code)
        self.assertEqual(len(result), 2)

    def test_list_raises_not_found_for_invalid_project(self):
        with self.assertRaises(NotFoundException):
            self.service.list("PROJ-999999")

    def test_list_excludes_attachments_from_other_projects(self):
        other = make_project("Other")
        make_project_attachment(project=self.project, file_name="mine.pdf")
        make_project_attachment(project=other, file_name="theirs.pdf")
        result = self.service.list(self.project.code)
        self.assertEqual(len(result), 1)

    def test_list_default_ordering_latest_first(self):
        a1 = make_project_attachment(project=self.project, file_name="first.pdf")
        a2 = make_project_attachment(project=self.project, file_name="second.pdf")
        result = self.service.list(self.project.code)
        self.assertEqual(result[0].pk, a2.pk)
        self.assertEqual(result[1].pk, a1.pk)

    def test_list_sorts_by_file_name_ascending_when_params_provided(self):
        make_project_attachment(project=self.project, file_name="zebra.pdf")
        make_project_attachment(project=self.project, file_name="apple.pdf")
        params = MagicMock()
        sort = MagicMock()
        sort.sort_by = "file_name"
        sort.direction = "asc"
        params.sorts = [sort]
        result = self.service.list(self.project.code, params=params)
        self.assertEqual(result[0].file_name, "apple.pdf")
        self.assertEqual(result[1].file_name, "zebra.pdf")

    def test_list_sorts_by_file_name_descending_when_params_provided(self):
        make_project_attachment(project=self.project, file_name="apple.pdf")
        make_project_attachment(project=self.project, file_name="zebra.pdf")
        params = MagicMock()
        sort = MagicMock()
        sort.sort_by = "file_name"
        sort.direction = "desc"
        params.sorts = [sort]
        result = self.service.list(self.project.code, params=params)
        self.assertEqual(result[0].file_name, "zebra.pdf")
        self.assertEqual(result[1].file_name, "apple.pdf")

    def test_list_ignores_unsortable_sort_fields(self):
        make_project_attachment(project=self.project, file_name="a.pdf")
        params = MagicMock()
        sort = MagicMock()
        sort.sort_by = "invalid_field"
        sort.direction = "asc"
        params.sorts = [sort]
        result = self.service.list(self.project.code, params=params)
        self.assertEqual(len(result), 1)


class ProjectAttachmentServiceUploadTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.service = ProjectAttachmentService(user=self.user)
        self.project = make_project("UploadProject")

    @patch(_STORE_PATH, return_value="file:///tmp/PROJAT-1_test.pdf")
    @patch(_INFRA_PATH_PATH, return_value="")
    @patch(_INFRA_TYPE_PATH)
    def test_upload_creates_attachment(self, mock_type, mock_path, mock_store):
        mock_type.return_value = _mock_infra_type()
        obj = self.service.upload(
            project_code=self.project.code,
            file_data=b"PDF content",
            file_name="test.pdf",
            content_type="application/pdf",
            file_size=len(b"PDF content"),
        )
        self.assertIsInstance(obj, ProjectAttachment)
        self.assertTrue(obj.code.startswith("PROJAT-"))

    @patch(_STORE_PATH, return_value="file:///tmp/PROJAT-1_test.pdf")
    @patch(_INFRA_PATH_PATH, return_value="")
    @patch(_INFRA_TYPE_PATH)
    def test_upload_sets_project(self, mock_type, mock_path, mock_store):
        mock_type.return_value = _mock_infra_type()
        obj = self.service.upload(
            project_code=self.project.code,
            file_data=b"data",
            file_name="doc.pdf",
            content_type="application/pdf",
            file_size=4,
        )
        self.assertEqual(obj.project_id, self.project.pk)

    @patch(_STORE_PATH, return_value="file:///tmp/PROJAT-1_test.pdf")
    @patch(_INFRA_PATH_PATH, return_value="")
    @patch(_INFRA_TYPE_PATH)
    def test_upload_sets_audit_fields(self, mock_type, mock_path, mock_store):
        mock_type.return_value = _mock_infra_type()
        obj = self.service.upload(
            project_code=self.project.code,
            file_data=b"data",
            file_name="audit.pdf",
            content_type="application/pdf",
            file_size=4,
        )
        self.assertEqual(obj.created_by, self.user)
        self.assertEqual(obj.updated_by, self.user)

    @patch(_STORE_PATH, return_value="file:///tmp/PROJAT-1_test.pdf")
    @patch(_INFRA_PATH_PATH, return_value="")
    @patch(_INFRA_TYPE_PATH)
    def test_upload_persists_file_path(self, mock_type, mock_path, mock_store):
        mock_type.return_value = _mock_infra_type()
        obj = self.service.upload(
            project_code=self.project.code,
            file_data=b"data",
            file_name="stored.pdf",
            content_type="application/pdf",
            file_size=4,
        )
        self.assertEqual(obj.file_path, "file:///tmp/PROJAT-1_test.pdf")

    @patch(_STORE_PATH, return_value="file:///tmp/test.pdf")
    @patch(_INFRA_PATH_PATH, return_value="")
    @patch(_INFRA_TYPE_PATH)
    def test_upload_persists_to_db(self, mock_type, mock_path, mock_store):
        mock_type.return_value = _mock_infra_type()
        self.service.upload(
            project_code=self.project.code,
            file_data=b"data",
            file_name="persisted.pdf",
            content_type="application/pdf",
            file_size=4,
        )
        self.assertEqual(
            ProjectAttachment.objects.filter(project=self.project).count(), 1
        )

    def test_upload_raises_validation_exception_when_file_too_large(self):
        oversized = 26 * 1024 * 1024  # 26 MB > 25 MB limit
        with self.assertRaises(ValidationException):
            self.service.upload(
                project_code=self.project.code,
                file_data=b"x",
                file_name="big.pdf",
                content_type="application/pdf",
                file_size=oversized,
            )

    @patch(_STORE_PATH, return_value="file:///tmp/test.pdf")
    @patch(_INFRA_PATH_PATH, return_value="")
    @patch(_INFRA_TYPE_PATH)
    def test_upload_raises_already_exists_on_duplicate_filename(
        self, mock_type, mock_path, mock_store
    ):
        mock_type.return_value = _mock_infra_type()
        self.service.upload(
            project_code=self.project.code,
            file_data=b"data",
            file_name="dup.pdf",
            content_type="application/pdf",
            file_size=4,
        )
        with self.assertRaises(AlreadyExistsException):
            self.service.upload(
                project_code=self.project.code,
                file_data=b"data",
                file_name="dup.pdf",
                content_type="application/pdf",
                file_size=4,
            )

    def test_upload_raises_not_found_for_invalid_project(self):
        with self.assertRaises(NotFoundException):
            self.service.upload(
                project_code="PROJ-999999",
                file_data=b"data",
                file_name="doc.pdf",
                content_type="application/pdf",
                file_size=4,
            )

    @patch(_STORE_PATH, return_value="file:///tmp/test.pdf")
    @patch(_INFRA_PATH_PATH, return_value="")
    @patch(_INFRA_TYPE_PATH)
    def test_upload_resolves_content_type_from_filename_when_not_supplied(
        self, mock_type, mock_path, mock_store
    ):
        mock_type.return_value = _mock_infra_type()
        obj = self.service.upload(
            project_code=self.project.code,
            file_data=b"data",
            file_name="report.pdf",
            content_type="",
            file_size=4,
        )
        self.assertEqual(obj.content_type, "application/pdf")


class ProjectAttachmentServiceDownloadTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.service = ProjectAttachmentService(user=self.user)

    @patch(_RETRIEVE_PATH, return_value=b"file content bytes")
    def test_download_returns_content_and_metadata(self, mock_retrieve):
        attachment = make_project_attachment(
            file_name="report.pdf",
            content_type="application/pdf",
            file_path="file:///tmp/report.pdf",
        )
        content, ct, name = self.service.download(code=attachment.code)
        self.assertEqual(content, b"file content bytes")
        self.assertEqual(ct, "application/pdf")
        self.assertEqual(name, "report.pdf")

    @patch(_RETRIEVE_PATH, return_value=b"data")
    def test_download_uses_octet_stream_when_content_type_blank(self, mock_retrieve):
        attachment = make_project_attachment(
            file_name="blob.bin",
            content_type="",
            file_path="file:///tmp/blob.bin",
        )
        _, ct, _ = self.service.download(code=attachment.code)
        self.assertEqual(ct, "application/octet-stream")

    def test_download_raises_not_found_for_invalid_code(self):
        with self.assertRaises(NotFoundException):
            self.service.download(code="PROJAT-999999")


class ProjectAttachmentServiceDeleteTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.service = ProjectAttachmentService(user=self.user)

    @patch(_DELETE_PATH)
    def test_delete_removes_attachment_from_db(self, mock_delete):
        attachment = make_project_attachment()
        code = attachment.code
        self.service.delete(code=code)
        self.assertFalse(ProjectAttachment.objects.filter(code=code).exists())

    @patch(_DELETE_PATH)
    def test_delete_calls_storagecore_delete(self, mock_delete):
        attachment = make_project_attachment(file_path="file:///tmp/doc.pdf")
        self.service.delete(code=attachment.code)
        mock_delete.assert_called_once()

    @patch(_DELETE_PATH, side_effect=Exception("storage error"))
    def test_delete_continues_gracefully_when_storagecore_fails(self, mock_delete):
        attachment = make_project_attachment()
        code = attachment.code
        self.service.delete(code=code)
        self.assertFalse(ProjectAttachment.objects.filter(code=code).exists())

    def test_delete_raises_not_found_for_invalid_code(self):
        with self.assertRaises(NotFoundException):
            self.service.delete(code="PROJAT-999999")
