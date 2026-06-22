from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.comments.models import Comment
from apps.configurations.tests.factories import mark_setup_complete
from apps.projects.models import ProjectComment
from apps.projects.tests.factories import make_project, make_project_comment
from apps.users.tests.factories import make_profile, make_user

LIST_URL = "/api/v1/projects/{}/comments/"
DETAIL_URL = "/api/v1/projects/{}/comments/{}/"
PIN_URL = "/api/v1/projects/{}/comments/{}/pin/"
UNPIN_URL = "/api/v1/projects/{}/comments/{}/unpin/"


class ProjectCommentListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.project = make_project("List API Project")
        make_project_comment(self.project, comment_text="First comment.")
        make_project_comment(self.project, comment_text="Second comment.")

    def test_unauthenticated_returns_401(self):
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_200_for_authenticated_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertEqual(response.status_code, 200)

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertTrue(response.data["success"])

    def test_returns_all_comments_for_project(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertEqual(len(response.data["data"]["results"]), 2)

    def test_returns_404_for_invalid_project(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format("PROJ-999999"))
        self.assertEqual(response.status_code, 404)

    def test_response_contains_expected_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        item = response.data["data"]["results"][0]
        for field in ("code", "comment", "is_edited", "is_pinned", "mentions"):
            self.assertIn(field, item)

    def test_excludes_comments_from_other_projects(self):
        other_project = make_project("Other Project")
        make_project_comment(other_project, comment_text="Other.")
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertEqual(len(response.data["data"]["results"]), 2)


class ProjectCommentCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.project = make_project("Create API Project")

    @patch("apps.projects.services.comment.AuditService.log_create")
    def test_unauthenticated_returns_401(self, _mock):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"comment": "Hello."},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    @patch("apps.projects.services.comment.AuditService.log_create")
    def test_create_returns_201(self, _mock):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"comment": "New comment."},
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    @patch("apps.projects.services.comment.AuditService.log_create")
    def test_create_persists_comment(self, _mock):
        self.client.force_authenticate(user=self.user)
        self.client.post(
            LIST_URL.format(self.project.code),
            {"comment": "Persisted comment."},
            format="json",
        )
        self.assertTrue(ProjectComment.objects.filter(project=self.project).exists())

    @patch("apps.projects.services.comment.AuditService.log_create")
    def test_create_response_has_correct_code_prefix(self, _mock):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"comment": "Code check."},
            format="json",
        )
        self.assertTrue(response.data["data"]["code"].startswith("PROJCOMMENT-"))

    @patch("apps.projects.services.comment.AuditService.log_create")
    def test_create_returns_comment_text_in_response(self, _mock):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"comment": "Check text."},
            format="json",
        )
        self.assertEqual(response.data["data"]["comment"], "Check text.")

    @patch("apps.projects.services.comment.AuditService.log_create")
    def test_create_returns_is_edited_false(self, _mock):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"comment": "Not edited."},
            format="json",
        )
        self.assertFalse(response.data["data"]["is_edited"])

    @patch("apps.projects.services.comment.AuditService.log_create")
    def test_create_returns_is_pinned_false(self, _mock):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"comment": "Not pinned."},
            format="json",
        )
        self.assertFalse(response.data["data"]["is_pinned"])

    @patch("apps.projects.services.comment.AuditService.log_create")
    def test_create_with_mentions_creates_mentions(self, _mock):
        mentioned_user = make_user(email="mentioned@example.com")
        profile = make_profile(user=mentioned_user)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {
                "comment": "Hey @user.",
                "mentions": [profile.code],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(len(response.data["data"]["mentions"]), 1)

    @patch("apps.projects.services.comment.AuditService.log_create")
    def test_create_returns_400_when_comment_missing(self, _mock):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    @patch("apps.projects.services.comment.AuditService.log_create")
    def test_create_returns_404_for_invalid_project(self, _mock):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL.format("PROJ-999999"),
            {"comment": "Hello."},
            format="json",
        )
        self.assertEqual(response.status_code, 404)


class ProjectCommentRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.project = make_project("Retrieve API Project")
        self.pc = make_project_comment(self.project, comment_text="Retrievable.")

    def test_unauthenticated_returns_401(self):
        response = self.client.get(DETAIL_URL.format(self.project.code, self.pc.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_200_for_authenticated_user(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.project.code, self.pc.code))
        self.assertEqual(response.status_code, 200)

    def test_returns_correct_comment_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.project.code, self.pc.code))
        self.assertEqual(response.data["data"]["code"], self.pc.code)

    def test_returns_404_for_unknown_comment_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            DETAIL_URL.format(self.project.code, "PROJCOMMENT-999999")
        )
        self.assertEqual(response.status_code, 404)


class ProjectCommentUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.project = make_project("Update API Project")
        self.pc = make_project_comment(self.project, comment_text="Original.")

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_unauthenticated_returns_401(self, _mock):
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, self.pc.code),
            {"comment": "Updated."},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_update_returns_200(self, _mock):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, self.pc.code),
            {"comment": "Updated."},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_update_persists_new_comment_text(self, _mock):
        self.client.force_authenticate(user=self.user)
        self.client.patch(
            DETAIL_URL.format(self.project.code, self.pc.code),
            {"comment": "New text."},
            format="json",
        )
        self.pc.comment.refresh_from_db()
        self.assertEqual(self.pc.comment.comment, "New text.")

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_update_marks_is_edited(self, _mock):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, self.pc.code),
            {"comment": "Edited."},
            format="json",
        )
        self.assertTrue(response.data["data"]["is_edited"])

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_update_returns_404_for_unknown_comment(self, _mock):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, "PROJCOMMENT-999999"),
            {"comment": "Hello."},
            format="json",
        )
        self.assertEqual(response.status_code, 404)


class ProjectCommentDestroyAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.project = make_project("Destroy API Project")

    @patch("apps.projects.services.comment.AuditService.log_delete")
    def test_unauthenticated_returns_401(self, _mock):
        pc = make_project_comment(self.project)
        response = self.client.delete(DETAIL_URL.format(self.project.code, pc.code))
        self.assertEqual(response.status_code, 401)

    @patch("apps.projects.services.comment.AuditService.log_delete")
    def test_delete_returns_204(self, _mock):
        pc = make_project_comment(self.project)
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format(self.project.code, pc.code))
        self.assertEqual(response.status_code, 204)

    @patch("apps.projects.services.comment.AuditService.log_delete")
    def test_delete_removes_project_comment(self, _mock):
        pc = make_project_comment(self.project)
        pk = pc.pk
        self.client.force_authenticate(user=self.user)
        self.client.delete(DETAIL_URL.format(self.project.code, pc.code))
        self.assertFalse(ProjectComment.objects.filter(pk=pk).exists())

    @patch("apps.projects.services.comment.AuditService.log_delete")
    def test_delete_removes_underlying_comment(self, _mock):
        pc = make_project_comment(self.project)
        comment_pk = pc.comment_id
        self.client.force_authenticate(user=self.user)
        self.client.delete(DETAIL_URL.format(self.project.code, pc.code))
        self.assertFalse(Comment.objects.filter(pk=comment_pk).exists())

    @patch("apps.projects.services.comment.AuditService.log_delete")
    def test_delete_returns_404_for_unknown_comment(self, _mock):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            DETAIL_URL.format(self.project.code, "PROJCOMMENT-999999")
        )
        self.assertEqual(response.status_code, 404)


class ProjectCommentPinAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.project = make_project("Pin API Project")

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_unauthenticated_returns_401(self, _mock):
        pc = make_project_comment(self.project)
        response = self.client.post(PIN_URL.format(self.project.code, pc.code))
        self.assertEqual(response.status_code, 401)

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_pin_returns_200(self, _mock):
        pc = make_project_comment(self.project)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(PIN_URL.format(self.project.code, pc.code))
        self.assertEqual(response.status_code, 200)

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_pin_sets_is_pinned_in_response(self, _mock):
        pc = make_project_comment(self.project)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(PIN_URL.format(self.project.code, pc.code))
        self.assertTrue(response.data["data"]["is_pinned"])

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_pin_returns_400_when_three_already_pinned(self, _mock):
        for i in range(3):
            pc = make_project_comment(self.project, comment_text=f"Pinned {i}")
            pc.comment.is_pinned = True
            pc.comment.save(update_fields=["is_pinned"])
        fourth = make_project_comment(self.project, comment_text="Fourth")
        self.client.force_authenticate(user=self.user)
        response = self.client.post(PIN_URL.format(self.project.code, fourth.code))
        self.assertEqual(response.status_code, 422)

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_pin_returns_404_for_unknown_comment(self, _mock):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            PIN_URL.format(self.project.code, "PROJCOMMENT-999999")
        )
        self.assertEqual(response.status_code, 404)


class ProjectCommentUnpinAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.project = make_project("Unpin API Project")

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_unauthenticated_returns_401(self, _mock):
        pc = make_project_comment(self.project)
        response = self.client.post(UNPIN_URL.format(self.project.code, pc.code))
        self.assertEqual(response.status_code, 401)

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_unpin_returns_200(self, _mock):
        pc = make_project_comment(self.project)
        pc.comment.is_pinned = True
        pc.comment.save(update_fields=["is_pinned"])
        self.client.force_authenticate(user=self.user)
        response = self.client.post(UNPIN_URL.format(self.project.code, pc.code))
        self.assertEqual(response.status_code, 200)

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_unpin_sets_is_pinned_false_in_response(self, _mock):
        pc = make_project_comment(self.project)
        pc.comment.is_pinned = True
        pc.comment.save(update_fields=["is_pinned"])
        self.client.force_authenticate(user=self.user)
        response = self.client.post(UNPIN_URL.format(self.project.code, pc.code))
        self.assertFalse(response.data["data"]["is_pinned"])

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_unpin_returns_404_for_unknown_comment(self, _mock):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            UNPIN_URL.format(self.project.code, "PROJCOMMENT-999999")
        )
        self.assertEqual(response.status_code, 404)
