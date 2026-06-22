from django.test import SimpleTestCase

from apps.projects.serializers import (
    ProjectCommentCreateSerializer,
    ProjectCommentUpdateSerializer,
)


class ProjectCommentCreateSerializerTest(SimpleTestCase):
    def _valid(self, data):
        s = ProjectCommentCreateSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        return s.validated_data

    def _invalid(self, data):
        s = ProjectCommentCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        return s.errors

    def test_valid_comment_only(self):
        data = self._valid({"comment": "Hello world."})
        self.assertEqual(data["comment"], "Hello world.")

    def test_mentions_defaults_to_empty_list(self):
        data = self._valid({"comment": "No mentions."})
        self.assertEqual(data["mentions"], [])

    def test_valid_comment_with_mentions(self):
        data = self._valid({"comment": "Hi @user.", "mentions": ["USR-1"]})
        self.assertEqual(data["mentions"], ["USR-1"])

    def test_multiple_mentions_accepted(self):
        data = self._valid({"comment": "Hi!", "mentions": ["USR-1", "USR-2", "USR-3"]})
        self.assertEqual(len(data["mentions"]), 3)

    def test_empty_mentions_list_accepted(self):
        data = self._valid({"comment": "No one.", "mentions": []})
        self.assertEqual(data["mentions"], [])

    def test_missing_comment_is_invalid(self):
        errors = self._invalid({})
        self.assertIn("comment", errors)

    def test_empty_string_comment_is_invalid(self):
        errors = self._invalid({"comment": ""})
        self.assertIn("comment", errors)

    def test_multiline_comment_accepted(self):
        data = self._valid({"comment": "Line 1.\nLine 2.\nLine 3."})
        self.assertIn("Line 2.", data["comment"])

    def test_long_comment_accepted(self):
        long_text = "x" * 5000
        data = self._valid({"comment": long_text})
        self.assertEqual(data["comment"], long_text)


class ProjectCommentUpdateSerializerTest(SimpleTestCase):
    def _valid(self, data):
        s = ProjectCommentUpdateSerializer(data=data, partial=True)
        self.assertTrue(s.is_valid(), s.errors)
        return s.validated_data

    def _invalid(self, data):
        s = ProjectCommentUpdateSerializer(data=data, partial=True)
        self.assertFalse(s.is_valid())
        return s.errors

    def test_update_comment_text_only(self):
        data = self._valid({"comment": "Updated comment."})
        self.assertEqual(data["comment"], "Updated comment.")

    def test_update_mentions_only(self):
        data = self._valid({"mentions": ["USR-1"]})
        self.assertEqual(data["mentions"], ["USR-1"])

    def test_update_both_fields(self):
        data = self._valid({"comment": "New text.", "mentions": ["USR-2"]})
        self.assertEqual(data["comment"], "New text.")
        self.assertEqual(data["mentions"], ["USR-2"])

    def test_empty_payload_accepted_for_partial(self):
        data = self._valid({})
        self.assertNotIn("comment", data)
        self.assertNotIn("mentions", data)

    def test_empty_mentions_list_clears_mentions(self):
        data = self._valid({"mentions": []})
        self.assertEqual(data["mentions"], [])

    def test_empty_comment_string_is_invalid(self):
        errors = self._invalid({"comment": ""})
        self.assertIn("comment", errors)
