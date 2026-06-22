from unittest.mock import patch

from django.test import TestCase

from apps.comments.models import Comment, CommentMention
from apps.core.exceptions import NotFoundException, ValidationException
from apps.projects.models import ProjectComment
from apps.projects.services import ProjectCommentService
from apps.projects.tests.factories import make_project, make_project_comment
from apps.users.tests.factories import make_profile, make_user


def _svc(user=None):
    if user is None:
        user = make_user()
    return ProjectCommentService(user=user)


class ProjectCommentServiceGetTest(TestCase):
    def test_get_returns_project_comment(self):
        pc = make_project_comment()
        result = _svc().get(code=pc.code)
        self.assertEqual(result.pk, pc.pk)

    def test_get_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            _svc().get(code="PROJCOMMENT-999999")


class ProjectCommentServiceListTest(TestCase):
    def test_list_returns_paginated_result(self):
        project = make_project()
        make_project_comment(project=project, comment_text="Alpha")
        make_project_comment(project=project, comment_text="Beta")
        result = _svc().list(project_code=project.code)
        self.assertEqual(result.pagination.total_count, 2)

    def test_list_raises_not_found_for_invalid_project(self):
        with self.assertRaises(NotFoundException):
            _svc().list(project_code="PROJ-999999")

    def test_list_excludes_comments_from_other_projects(self):
        project_a = make_project("A")
        project_b = make_project("B")
        make_project_comment(project=project_a)
        make_project_comment(project=project_b)
        result = _svc().list(project_code=project_a.code)
        self.assertEqual(result.pagination.total_count, 1)

    def test_list_respects_page_size(self):
        project = make_project()
        for i in range(5):
            make_project_comment(project=project, comment_text=f"Comment {i}")
        result = _svc().list(project_code=project.code, page=1, page_size=3)
        self.assertEqual(len(result.results), 3)
        self.assertEqual(result.pagination.total_count, 5)


class ProjectCommentServiceCreateTest(TestCase):
    @patch("apps.projects.services.comment.AuditService.log_create")
    def test_create_returns_project_comment(self, _mock):
        user = make_user()
        project = make_project()
        obj = _svc(user).create(project_code=project.code, comment="New comment.")
        self.assertIsInstance(obj, ProjectComment)

    @patch("apps.projects.services.comment.AuditService.log_create")
    def test_create_assigns_code(self, _mock):
        project = make_project()
        obj = _svc().create(project_code=project.code, comment="Hello.")
        self.assertTrue(obj.code.startswith("PROJCOMMENT-"))

    @patch("apps.projects.services.comment.AuditService.log_create")
    def test_create_sets_project(self, _mock):
        project = make_project()
        obj = _svc().create(project_code=project.code, comment="Hello.")
        self.assertEqual(obj.project_id, project.pk)

    @patch("apps.projects.services.comment.AuditService.log_create")
    def test_create_creates_underlying_comment(self, _mock):
        project = make_project()
        obj = _svc().create(project_code=project.code, comment="Test text.")
        self.assertEqual(obj.comment.comment, "Test text.")

    @patch("apps.projects.services.comment.AuditService.log_create")
    def test_create_sets_audit_user_on_comment(self, _mock):
        user = make_user()
        project = make_project()
        obj = _svc(user).create(project_code=project.code, comment="By user.")
        self.assertEqual(obj.comment.created_by, user)
        self.assertEqual(obj.comment.updated_by, user)

    @patch("apps.projects.services.comment.AuditService.log_create")
    def test_create_sets_audit_user_on_project_comment(self, _mock):
        user = make_user()
        project = make_project()
        obj = _svc(user).create(project_code=project.code, comment="By user.")
        self.assertEqual(obj.created_by, user)
        self.assertEqual(obj.updated_by, user)

    @patch("apps.projects.services.comment.AuditService.log_create")
    def test_create_persists_to_db(self, _mock):
        project = make_project()
        obj = _svc().create(project_code=project.code, comment="Persisted.")
        self.assertTrue(ProjectComment.objects.filter(pk=obj.pk).exists())

    @patch("apps.projects.services.comment.AuditService.log_create")
    def test_create_with_mentions_creates_comment_mentions(self, _mock):
        user = make_user(email="mentioned@example.com")
        profile = make_profile(user=user)
        project = make_project()
        svc = _svc()
        obj = svc.create(
            project_code=project.code,
            comment="Hey @user.",
            mentions=[profile.code],
        )
        self.assertEqual(obj.comment.mentions.count(), 1)
        self.assertEqual(obj.comment.mentions.first().user, user)

    @patch("apps.projects.services.comment.AuditService.log_create")
    def test_create_without_mentions_creates_no_mentions(self, _mock):
        project = make_project()
        obj = _svc().create(project_code=project.code, comment="No mentions.")
        self.assertEqual(obj.comment.mentions.count(), 0)

    @patch("apps.projects.services.comment.AuditService.log_create")
    def test_create_raises_not_found_for_invalid_project(self, _mock):
        with self.assertRaises(NotFoundException):
            _svc().create(project_code="PROJ-999999", comment="Hello.")


class ProjectCommentServiceUpdateTest(TestCase):
    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_update_changes_comment_text(self, _mock):
        pc = make_project_comment(comment_text="Original.")
        _svc().update(code=pc.code, comment="Updated.")
        pc.comment.refresh_from_db()
        self.assertEqual(pc.comment.comment, "Updated.")

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_update_marks_comment_as_edited(self, _mock):
        pc = make_project_comment(comment_text="Original.")
        self.assertFalse(pc.comment.is_edited)
        _svc().update(code=pc.code, comment="Updated.")
        pc.comment.refresh_from_db()
        self.assertTrue(pc.comment.is_edited)

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_update_sets_updated_by_on_comment(self, _mock):
        user = make_user()
        pc = make_project_comment()
        _svc(user).update(code=pc.code, comment="Updated.")
        pc.comment.refresh_from_db()
        self.assertEqual(pc.comment.updated_by, user)

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_update_replaces_mentions(self, _mock):
        actor = make_user(email="actor@example.com")
        user1 = make_user(email="u1@example.com")
        user2 = make_user(email="u2@example.com")
        profile2 = make_profile(user=user2)
        pc = make_project_comment()
        CommentMention.objects.create(comment=pc.comment, user=user1)
        _svc(actor).update(code=pc.code, mentions=[profile2.code])
        pks = list(pc.comment.mentions.values_list("user_id", flat=True))
        self.assertNotIn(user1.pk, pks)
        self.assertIn(user2.pk, pks)

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_update_with_empty_mentions_clears_all_mentions(self, _mock):
        actor = make_user(email="actor@example.com")
        other = make_user(email="other@example.com")
        pc = make_project_comment()
        CommentMention.objects.create(comment=pc.comment, user=other)
        _svc(actor).update(code=pc.code, mentions=[])
        self.assertEqual(pc.comment.mentions.count(), 0)

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_update_raises_not_found_for_unknown_code(self, _mock):
        with self.assertRaises(NotFoundException):
            _svc().update(code="PROJCOMMENT-999999", comment="Hello.")


class ProjectCommentServiceDeleteTest(TestCase):
    @patch("apps.projects.services.comment.AuditService.log_delete")
    def test_delete_removes_project_comment(self, _mock):
        pc = make_project_comment()
        pk = pc.pk
        _svc().delete(code=pc.code)
        self.assertFalse(ProjectComment.objects.filter(pk=pk).exists())

    @patch("apps.projects.services.comment.AuditService.log_delete")
    def test_delete_removes_underlying_comment(self, _mock):
        pc = make_project_comment()
        comment_pk = pc.comment_id
        _svc().delete(code=pc.code)
        self.assertFalse(Comment.objects.filter(pk=comment_pk).exists())

    @patch("apps.projects.services.comment.AuditService.log_delete")
    def test_delete_raises_not_found_for_unknown_code(self, _mock):
        with self.assertRaises(NotFoundException):
            _svc().delete(code="PROJCOMMENT-999999")


class ProjectCommentServicePinTest(TestCase):
    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_pin_sets_is_pinned_true(self, _mock):
        pc = make_project_comment()
        _svc().pin(code=pc.code)
        pc.comment.refresh_from_db()
        self.assertTrue(pc.comment.is_pinned)

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_pin_allows_up_to_three_pinned(self, _mock):
        user = make_user()
        project = make_project()
        codes = []
        for i in range(3):
            pc = make_project_comment(project=project, comment_text=f"Comment {i}")
            codes.append(pc.code)
        svc = _svc(user)
        for code in codes:
            svc.pin(code=code)
        for code in codes:
            pc = ProjectComment.objects.select_related("comment").get(code=code)
            self.assertTrue(pc.comment.is_pinned)

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_pin_raises_validation_error_when_three_already_pinned(self, _mock):
        project = make_project()
        for i in range(3):
            pc = make_project_comment(project=project, comment_text=f"Comment {i}")
            pc.comment.is_pinned = True
            pc.comment.save(update_fields=["is_pinned"])
        fourth = make_project_comment(project=project, comment_text="Fourth")
        with self.assertRaises(ValidationException):
            _svc().pin(code=fourth.code)

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_pin_already_pinned_comment_does_not_exceed_limit(self, _mock):
        project = make_project()
        for i in range(3):
            pc = make_project_comment(project=project, comment_text=f"Comment {i}")
            pc.comment.is_pinned = True
            pc.comment.save(update_fields=["is_pinned"])
        already_pinned = make_project_comment(project=project, comment_text="Already")
        already_pinned.comment.is_pinned = True
        already_pinned.comment.save(update_fields=["is_pinned"])
        result = _svc().pin(code=already_pinned.code)
        self.assertTrue(result.comment.is_pinned)

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_pin_raises_not_found_for_unknown_code(self, _mock):
        with self.assertRaises(NotFoundException):
            _svc().pin(code="PROJCOMMENT-999999")


class ProjectCommentServiceUnpinTest(TestCase):
    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_unpin_sets_is_pinned_false(self, _mock):
        pc = make_project_comment()
        pc.comment.is_pinned = True
        pc.comment.save(update_fields=["is_pinned"])
        _svc().unpin(code=pc.code)
        pc.comment.refresh_from_db()
        self.assertFalse(pc.comment.is_pinned)

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_unpin_already_unpinned_comment_is_idempotent(self, _mock):
        pc = make_project_comment()
        _svc().unpin(code=pc.code)
        pc.comment.refresh_from_db()
        self.assertFalse(pc.comment.is_pinned)

    @patch("apps.projects.services.comment.AuditService.log_update")
    def test_unpin_raises_not_found_for_unknown_code(self, _mock):
        with self.assertRaises(NotFoundException):
            _svc().unpin(code="PROJCOMMENT-999999")
