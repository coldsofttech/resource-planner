from django.test import TestCase

from apps.projects.selectors.comment import (
    get_all_project_comments,
    get_pinned_project_comments_count,
    get_project_comment_by_code,
)
from apps.projects.tests.factories import make_project, make_project_comment


class GetAllProjectCommentsTest(TestCase):
    def test_returns_comments_for_project(self):
        project = make_project()
        make_project_comment(project=project, comment_text="Alpha")
        make_project_comment(project=project, comment_text="Beta")
        qs = get_all_project_comments(project)
        self.assertEqual(qs.count(), 2)

    def test_excludes_comments_from_other_projects(self):
        project_a = make_project("Project A")
        project_b = make_project("Project B")
        make_project_comment(project=project_a)
        make_project_comment(project=project_b)
        qs = get_all_project_comments(project_a)
        self.assertEqual(qs.count(), 1)

    def test_returns_empty_queryset_when_no_comments(self):
        project = make_project()
        qs = get_all_project_comments(project)
        self.assertEqual(qs.count(), 0)

    def test_ordering_pinned_before_unpinned(self):
        project = make_project()
        unpinned = make_project_comment(project=project, comment_text="Unpinned")
        pinned = make_project_comment(
            project=project,
            comment_text="Pinned",
        )
        pinned.comment.is_pinned = True
        pinned.comment.save(update_fields=["is_pinned"])

        results = list(get_all_project_comments(project))
        self.assertEqual(results[0].pk, pinned.pk)
        self.assertEqual(results[1].pk, unpinned.pk)

    def test_select_related_comment_is_available(self):
        project = make_project()
        make_project_comment(project=project)
        qs = get_all_project_comments(project)
        obj = qs.first()
        self.assertIsNotNone(obj.comment)


class GetPinnedProjectCommentsCountTest(TestCase):
    def test_returns_zero_when_no_pinned_comments(self):
        project = make_project()
        make_project_comment(project=project)
        self.assertEqual(get_pinned_project_comments_count(project), 0)

    def test_counts_only_pinned_comments(self):
        project = make_project()
        pc = make_project_comment(project=project, comment_text="Will pin")
        pc.comment.is_pinned = True
        pc.comment.save(update_fields=["is_pinned"])
        make_project_comment(project=project, comment_text="Not pinned")
        self.assertEqual(get_pinned_project_comments_count(project), 1)

    def test_excludes_pinned_comments_from_other_projects(self):
        project_a = make_project("A")
        project_b = make_project("B")
        pc = make_project_comment(project=project_b, comment_text="Pinned in B")
        pc.comment.is_pinned = True
        pc.comment.save(update_fields=["is_pinned"])
        self.assertEqual(get_pinned_project_comments_count(project_a), 0)

    def test_counts_all_pinned_when_multiple(self):
        project = make_project()
        for i in range(3):
            pc = make_project_comment(project=project, comment_text=f"Comment {i}")
            pc.comment.is_pinned = True
            pc.comment.save(update_fields=["is_pinned"])
        self.assertEqual(get_pinned_project_comments_count(project), 3)


class GetProjectCommentByCodeTest(TestCase):
    def test_returns_project_comment_for_valid_code(self):
        pc = make_project_comment()
        result = get_project_comment_by_code(pc.code)
        self.assertIsNotNone(result)
        self.assertEqual(result.pk, pc.pk)

    def test_returns_none_for_unknown_code(self):
        result = get_project_comment_by_code("PROJCOMMENT-999999")
        self.assertIsNone(result)

    def test_select_related_project_available(self):
        pc = make_project_comment()
        result = get_project_comment_by_code(pc.code)
        self.assertIsNotNone(result.project)

    def test_select_related_comment_available(self):
        pc = make_project_comment()
        result = get_project_comment_by_code(pc.code)
        self.assertIsNotNone(result.comment)
