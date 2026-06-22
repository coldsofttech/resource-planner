from unittest.mock import MagicMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.projects.models import ProjectAttachment
from apps.projects.tests.factories import make_project, make_project_attachment
from apps.users.tests.factories import make_user

LIST_URL = "/api/v1/projects/{}/attachments/"
DETAIL_URL = "/api/v1/projects/{}/attachments/{}/"
DOWNLOAD_URL = "/api/v1/projects/{}/attachments/{}/download/"

_STORE_PATH = "storagecore.store"
_RETRIEVE_PATH = "storagecore.retrieve"
_DELETE_PATH = "storagecore.delete"
_INFRA_TYPE_PATH = "apps.configurations.selectors.Infra.get_storage_type"
_INFRA_PATH_PATH = "apps.configurations.selectors.Infra.get_storage_path"


def _mock_infra_type():
    m = MagicMock()
    m.value = "local"
    return m


class ProjectAttachmentListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.project = make_project("ListProject")
        make_project_attachment(project=self.project, file_name="alpha.pdf")
        make_project_attachment(project=self.project, file_name="beta.pdf")

    def test_unauthenticated_returns_401(self):
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_200_with_attachments(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 2)

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertTrue(response.data["success"])

    def test_returns_404_for_unknown_project(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format("PROJ-999999"))
        self.assertEqual(response.status_code, 404)

    def test_response_includes_expected_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        first = response.data["data"][0]
        for field in (
            "code",
            "project_code",
            "file_name",
            "content_type",
            "file_size",
            "created_at",
        ):
            self.assertIn(field, first)

    def test_excludes_attachments_from_other_projects(self):
        other = make_project("Other")
        make_project_attachment(project=other, file_name="theirs.pdf")
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertEqual(len(response.data["data"]), 2)

    def test_sort_by_file_name_ascending(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            LIST_URL.format(self.project.code) + "?sort=file_name&order_by=ASC"
        )
        self.assertEqual(response.status_code, 200)
        names = [item["file_name"] for item in response.data["data"]]
        self.assertEqual(names, sorted(names))

    def test_sort_by_file_name_descending(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            LIST_URL.format(self.project.code) + "?sort=file_name&order_by=DESC"
        )
        self.assertEqual(response.status_code, 200)
        names = [item["file_name"] for item in response.data["data"]]
        self.assertEqual(names, sorted(names, reverse=True))


class ProjectAttachmentUploadAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.project = make_project("UploadProject")

    def test_unauthenticated_returns_401(self):
        file_data = SimpleUploadedFile(
            "test.pdf", b"content", content_type="application/pdf"
        )
        response = self.client.post(
            LIST_URL.format(self.project.code), {"file": file_data}, format="multipart"
        )
        self.assertEqual(response.status_code, 401)

    @patch(_STORE_PATH, return_value="file:///tmp/test.pdf")
    @patch(_INFRA_PATH_PATH, return_value="")
    @patch(_INFRA_TYPE_PATH)
    def test_upload_returns_201_with_attachment_data(
        self, mock_type, mock_path, mock_store
    ):
        mock_type.return_value = _mock_infra_type()
        self.client.force_authenticate(user=self.user)
        file_data = SimpleUploadedFile(
            "upload.pdf", b"PDF data", content_type="application/pdf"
        )
        response = self.client.post(
            LIST_URL.format(self.project.code), {"file": file_data}, format="multipart"
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("code", response.data["data"])
        self.assertTrue(response.data["data"]["code"].startswith("PROJAT-"))

    @patch(_STORE_PATH, return_value="file:///tmp/test.pdf")
    @patch(_INFRA_PATH_PATH, return_value="")
    @patch(_INFRA_TYPE_PATH)
    def test_upload_response_includes_file_name(self, mock_type, mock_path, mock_store):
        mock_type.return_value = _mock_infra_type()
        self.client.force_authenticate(user=self.user)
        file_data = SimpleUploadedFile(
            "named.pdf", b"data", content_type="application/pdf"
        )
        response = self.client.post(
            LIST_URL.format(self.project.code), {"file": file_data}, format="multipart"
        )
        self.assertEqual(response.data["data"]["file_name"], "named.pdf")

    def test_upload_without_file_returns_422(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL.format(self.project.code), {}, format="multipart"
        )
        self.assertEqual(response.status_code, 422)

    @patch(_STORE_PATH, return_value="file:///tmp/dup.pdf")
    @patch(_INFRA_PATH_PATH, return_value="")
    @patch(_INFRA_TYPE_PATH)
    def test_duplicate_filename_returns_409(self, mock_type, mock_path, mock_store):
        mock_type.return_value = _mock_infra_type()
        make_project_attachment(project=self.project, file_name="dup.pdf")
        self.client.force_authenticate(user=self.user)
        file_data = SimpleUploadedFile(
            "dup.pdf", b"data", content_type="application/pdf"
        )
        response = self.client.post(
            LIST_URL.format(self.project.code), {"file": file_data}, format="multipart"
        )
        self.assertEqual(response.status_code, 409)

    def test_oversized_file_returns_422(self):
        self.client.force_authenticate(user=self.user)
        oversized_content = b"x" * (26 * 1024 * 1024)  # 26 MB
        file_data = SimpleUploadedFile(
            "huge.bin", oversized_content, content_type="application/octet-stream"
        )
        response = self.client.post(
            LIST_URL.format(self.project.code), {"file": file_data}, format="multipart"
        )
        self.assertEqual(response.status_code, 422)

    def test_upload_to_unknown_project_returns_404(self):
        self.client.force_authenticate(user=self.user)
        file_data = SimpleUploadedFile(
            "test.pdf", b"data", content_type="application/pdf"
        )
        response = self.client.post(
            LIST_URL.format("PROJ-999999"), {"file": file_data}, format="multipart"
        )
        self.assertEqual(response.status_code, 404)

    @patch(_STORE_PATH, return_value="file:///tmp/test.pdf")
    @patch(_INFRA_PATH_PATH, return_value="")
    @patch(_INFRA_TYPE_PATH)
    def test_upload_persists_attachment_to_db(self, mock_type, mock_path, mock_store):
        mock_type.return_value = _mock_infra_type()
        self.client.force_authenticate(user=self.user)
        file_data = SimpleUploadedFile(
            "persist.pdf", b"data", content_type="application/pdf"
        )
        self.client.post(
            LIST_URL.format(self.project.code), {"file": file_data}, format="multipart"
        )
        self.assertEqual(
            ProjectAttachment.objects.filter(project=self.project).count(), 1
        )


class ProjectAttachmentDownloadAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.project = make_project("DownloadProject")
        self.attachment = make_project_attachment(
            project=self.project,
            file_name="download.pdf",
            content_type="application/pdf",
            file_path="file:///tmp/download.pdf",
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.get(
            DOWNLOAD_URL.format(self.project.code, self.attachment.code)
        )
        self.assertEqual(response.status_code, 401)

    @patch(_RETRIEVE_PATH, return_value=b"PDF binary content")
    def test_download_returns_200_with_binary_content(self, mock_retrieve):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            DOWNLOAD_URL.format(self.project.code, self.attachment.code)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"PDF binary content")

    @patch(_RETRIEVE_PATH, return_value=b"data")
    def test_download_sets_content_disposition_header(self, mock_retrieve):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            DOWNLOAD_URL.format(self.project.code, self.attachment.code)
        )
        self.assertIn("Content-Disposition", response)
        self.assertIn("download.pdf", response["Content-Disposition"])

    @patch(_RETRIEVE_PATH, return_value=b"data")
    def test_download_sets_correct_content_type(self, mock_retrieve):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            DOWNLOAD_URL.format(self.project.code, self.attachment.code)
        )
        self.assertEqual(response["Content-Type"], "application/pdf")

    def test_download_unknown_attachment_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            DOWNLOAD_URL.format(self.project.code, "PROJAT-999999")
        )
        self.assertEqual(response.status_code, 404)


class ProjectAttachmentDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.project = make_project("DeleteProject")
        self.attachment = make_project_attachment(
            project=self.project, file_name="delete_me.pdf"
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.delete(
            DETAIL_URL.format(self.project.code, self.attachment.code)
        )
        self.assertEqual(response.status_code, 401)

    @patch(_DELETE_PATH)
    def test_delete_returns_204(self, mock_delete):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            DETAIL_URL.format(self.project.code, self.attachment.code)
        )
        self.assertEqual(response.status_code, 204)

    @patch(_DELETE_PATH)
    def test_delete_removes_attachment_from_db(self, mock_delete):
        self.client.force_authenticate(user=self.user)
        pk = self.attachment.pk
        self.client.delete(DETAIL_URL.format(self.project.code, self.attachment.code))
        self.assertFalse(ProjectAttachment.objects.filter(pk=pk).exists())

    def test_delete_unknown_attachment_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            DETAIL_URL.format(self.project.code, "PROJAT-999999")
        )
        self.assertEqual(response.status_code, 404)
