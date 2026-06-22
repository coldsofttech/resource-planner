import time

from django.db import IntegrityError
from django.test import TestCase

from apps.comments.models import Comment, CommentMention
from apps.comments.tests.factories import make_comment, make_comment_mention
from apps.users.tests.factories import make_user


class CommentCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        c = make_comment()
        self.assertTrue(c.code.startswith("COMMENT-"))

    def test_code_contains_pk(self):
        c = make_comment()
        self.assertEqual(c.code, f"COMMENT-{c.pk}")

    def test_codes_are_unique_across_comments(self):
        c1 = make_comment(comment="First")
        c2 = make_comment(comment="Second")
        self.assertNotEqual(c1.code, c2.code)

    def test_code_not_editable_directly(self):
        self.assertFalse(Comment._meta.get_field("code").editable)


class CommentStrTest(TestCase):
    def test_str_returns_comment_text(self):
        c = make_comment(comment="Short comment.")
        self.assertEqual(str(c), "Short comment.")

    def test_str_truncates_at_72_chars(self):
        long_text = "x" * 100
        c = make_comment(comment=long_text)
        self.assertEqual(str(c), long_text[:72])

    def test_str_returns_full_text_when_exactly_72_chars(self):
        text = "a" * 72
        c = make_comment(comment=text)
        self.assertEqual(str(c), text)

    def test_str_returns_full_text_when_under_72_chars(self):
        text = "Short."
        c = make_comment(comment=text)
        self.assertEqual(str(c), text)


class CommentFieldDefaultsTest(TestCase):
    def setUp(self):
        self.comment = make_comment()

    def test_is_edited_defaults_to_false(self):
        self.assertFalse(self.comment.is_edited)

    def test_is_pinned_defaults_to_false(self):
        self.assertFalse(self.comment.is_pinned)

    def test_created_at_is_set(self):
        self.assertIsNotNone(self.comment.created_at)

    def test_updated_at_is_set(self):
        self.assertIsNotNone(self.comment.updated_at)

    def test_created_by_defaults_to_none(self):
        self.assertIsNone(self.comment.created_by)

    def test_updated_by_defaults_to_none(self):
        self.assertIsNone(self.comment.updated_by)

    def test_comment_text_stored_correctly(self):
        self.assertEqual(self.comment.comment, "This is a test comment.")


class CommentFieldFlagsTest(TestCase):
    def test_is_edited_can_be_set_true(self):
        c = make_comment(is_edited=True)
        self.assertTrue(c.is_edited)

    def test_is_pinned_can_be_set_true(self):
        c = make_comment(is_pinned=True)
        self.assertTrue(c.is_pinned)

    def test_is_edited_can_be_updated(self):
        c = make_comment(is_edited=False)
        c.is_edited = True
        c.save(update_fields=["is_edited"])
        c.refresh_from_db()
        self.assertTrue(c.is_edited)

    def test_is_pinned_can_be_updated(self):
        c = make_comment(is_pinned=False)
        c.is_pinned = True
        c.save(update_fields=["is_pinned"])
        c.refresh_from_db()
        self.assertTrue(c.is_pinned)

    def test_comment_text_accepts_multiline(self):
        text = "Line one.\nLine two.\nLine three."
        c = make_comment(comment=text)
        c.refresh_from_db()
        self.assertEqual(c.comment, text)

    def test_comment_text_accepts_long_text(self):
        text = "w" * 5000
        c = make_comment(comment=text)
        c.refresh_from_db()
        self.assertEqual(c.comment, text)


class CommentAuditUserTest(TestCase):
    def test_created_by_stores_user(self):
        user = make_user()
        c = make_comment(created_by=user, updated_by=user)
        self.assertEqual(c.created_by, user)

    def test_updated_by_stores_user(self):
        user = make_user()
        c = make_comment(created_by=user, updated_by=user)
        self.assertEqual(c.updated_by, user)

    def test_created_by_set_null_when_user_deleted(self):
        user = make_user()
        c = make_comment(created_by=user, updated_by=user)
        user.delete()
        c.refresh_from_db()
        self.assertIsNone(c.created_by)

    def test_updated_by_set_null_when_user_deleted(self):
        user = make_user()
        c = make_comment(created_by=user, updated_by=user)
        user.delete()
        c.refresh_from_db()
        self.assertIsNone(c.updated_by)


class CommentOrderingTest(TestCase):
    def test_pinned_comments_appear_before_unpinned(self):
        unpinned = make_comment(comment="Unpinned", is_pinned=False)
        pinned = make_comment(comment="Pinned", is_pinned=True)
        comments = list(Comment.objects.all())
        self.assertEqual(comments[0].pk, pinned.pk)
        self.assertEqual(comments[1].pk, unpinned.pk)

    def test_newer_comments_appear_before_older_within_same_pin_state(self):
        older = make_comment(comment="Older comment")
        time.sleep(0.01)
        newer = make_comment(comment="Newer comment")
        unpinned = list(
            Comment.objects.filter(is_pinned=False).values_list("pk", flat=True)
        )
        self.assertEqual(unpinned[0], newer.pk)
        self.assertEqual(unpinned[1], older.pk)

    def test_pinned_comments_ordered_newest_first_among_themselves(self):
        pinned_old = make_comment(comment="Old pinned", is_pinned=True)
        time.sleep(0.01)
        pinned_new = make_comment(comment="New pinned", is_pinned=True)
        pinned = list(
            Comment.objects.filter(is_pinned=True).values_list("pk", flat=True)
        )
        self.assertEqual(pinned[0], pinned_new.pk)
        self.assertEqual(pinned[1], pinned_old.pk)

    def test_default_ordering_defined_on_model(self):
        self.assertEqual(Comment._meta.ordering, ["-is_pinned", "-created_at"])


class CommentPersistenceTest(TestCase):
    def test_comment_persists_to_db(self):
        make_comment(comment="Persisted comment.")
        self.assertTrue(Comment.objects.filter(comment="Persisted comment.").exists())

    def test_comment_text_can_be_updated(self):
        c = make_comment(comment="Original text.")
        c.comment = "Updated text."
        c.save(update_fields=["comment"])
        c.refresh_from_db()
        self.assertEqual(c.comment, "Updated text.")

    def test_delete_removes_comment(self):
        c = make_comment()
        pk = c.pk
        c.delete()
        self.assertFalse(Comment.objects.filter(pk=pk).exists())


class CommentMentionStrTest(TestCase):
    def test_str_contains_user_and_comment_id(self):
        user = make_user()
        c = make_comment()
        mention = make_comment_mention(comment=c, user=user)
        self.assertIn(str(user), str(mention))
        self.assertIn(str(c.pk), str(mention))


class CommentMentionFieldDefaultsTest(TestCase):
    def test_created_at_is_set(self):
        mention = make_comment_mention()
        self.assertIsNotNone(mention.created_at)


class CommentMentionRelationshipsTest(TestCase):
    def test_comment_fk_set(self):
        c = make_comment()
        mention = make_comment_mention(comment=c)
        self.assertEqual(mention.comment_id, c.pk)

    def test_user_fk_set(self):
        user = make_user()
        mention = make_comment_mention(user=user)
        self.assertEqual(mention.user_id, user.pk)

    def test_reverse_relation_from_comment(self):
        c = make_comment()
        user1 = make_user(email="u1@example.com")
        user2 = make_user(email="u2@example.com")
        make_comment_mention(comment=c, user=user1)
        make_comment_mention(comment=c, user=user2)
        self.assertEqual(c.mentions.count(), 2)

    def test_reverse_relation_from_user(self):
        user = make_user()
        c1 = make_comment(comment="First")
        c2 = make_comment(comment="Second")
        make_comment_mention(comment=c1, user=user)
        make_comment_mention(comment=c2, user=user)
        self.assertEqual(user.comment_mentions.count(), 2)

    def test_cascade_delete_when_comment_deleted(self):
        c = make_comment()
        mention = make_comment_mention(comment=c)
        pk = mention.pk
        c.delete()
        self.assertFalse(CommentMention.objects.filter(pk=pk).exists())

    def test_cascade_delete_when_user_deleted(self):
        user = make_user()
        mention = make_comment_mention(user=user)
        pk = mention.pk
        user.delete()
        self.assertFalse(CommentMention.objects.filter(pk=pk).exists())


class CommentMentionUniqueConstraintTest(TestCase):
    def test_duplicate_comment_user_pair_raises_integrity_error(self):
        c = make_comment()
        user = make_user()
        make_comment_mention(comment=c, user=user)
        with self.assertRaises(IntegrityError):
            make_comment_mention(comment=c, user=user)

    def test_same_user_on_different_comments_is_allowed(self):
        user = make_user()
        c1 = make_comment(comment="Comment 1")
        c2 = make_comment(comment="Comment 2")
        m1 = make_comment_mention(comment=c1, user=user)
        m2 = make_comment_mention(comment=c2, user=user)
        self.assertNotEqual(m1.pk, m2.pk)

    def test_same_comment_with_different_users_is_allowed(self):
        c = make_comment()
        user1 = make_user(email="u1@example.com")
        user2 = make_user(email="u2@example.com")
        m1 = make_comment_mention(comment=c, user=user1)
        m2 = make_comment_mention(comment=c, user=user2)
        self.assertNotEqual(m1.pk, m2.pk)

    def test_constraint_name_is_deterministic(self):
        names = [c.name for c in CommentMention._meta.constraints]
        self.assertIn("comments_commentmention_comment_user_uniq", names)
