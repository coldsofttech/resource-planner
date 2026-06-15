from django.test import SimpleTestCase

from apps.users.serializers import (
    GroupAssignMemberSerializer,
    GroupCreateSerializer,
    GroupUpdateSerializer,
)

# ---------------------------------------------------------------------------
# GroupCreateSerializer — input validation
# ---------------------------------------------------------------------------


class GroupCreateSerializerTest(SimpleTestCase):
    def test_valid_name_only_is_valid(self):
        s = GroupCreateSerializer(data={"name": "Test Group"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_valid_name_and_description_is_valid(self):
        s = GroupCreateSerializer(data={"name": "Test Group", "description": "Desc"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_name_required(self):
        s = GroupCreateSerializer(data={"description": "No name"})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_empty_name_is_invalid(self):
        s = GroupCreateSerializer(data={"name": ""})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_blank_description_is_valid(self):
        s = GroupCreateSerializer(data={"name": "Group", "description": ""})
        self.assertTrue(s.is_valid(), s.errors)

    def test_description_defaults_to_empty_string(self):
        s = GroupCreateSerializer(data={"name": "Group"})
        s.is_valid()
        self.assertEqual(s.validated_data.get("description", ""), "")

    def test_name_max_length_150_accepted(self):
        s = GroupCreateSerializer(data={"name": "A" * 150})
        self.assertTrue(s.is_valid(), s.errors)

    def test_name_exceeding_150_chars_is_invalid(self):
        s = GroupCreateSerializer(data={"name": "A" * 151})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)


# ---------------------------------------------------------------------------
# GroupUpdateSerializer — input validation
# ---------------------------------------------------------------------------


class GroupUpdateSerializerTest(SimpleTestCase):
    def test_empty_payload_is_valid(self):
        s = GroupUpdateSerializer(data={})
        self.assertTrue(s.is_valid(), s.errors)

    def test_name_only_is_valid(self):
        s = GroupUpdateSerializer(data={"name": "Updated Name"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_description_only_is_valid(self):
        s = GroupUpdateSerializer(data={"description": "Updated description"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_both_fields_is_valid(self):
        s = GroupUpdateSerializer(data={"name": "Name", "description": "Desc"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_empty_name_is_invalid(self):
        s = GroupUpdateSerializer(data={"name": ""})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_blank_description_is_valid(self):
        s = GroupUpdateSerializer(data={"description": ""})
        self.assertTrue(s.is_valid(), s.errors)

    def test_name_exceeding_150_chars_is_invalid(self):
        s = GroupUpdateSerializer(data={"name": "A" * 151})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)


# ---------------------------------------------------------------------------
# GroupAssignMemberSerializer — input validation
# ---------------------------------------------------------------------------


class GroupAssignMemberSerializerTest(SimpleTestCase):
    def test_valid_member_code_is_valid(self):
        s = GroupAssignMemberSerializer(data={"member_code": "USER-123"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_member_code_required(self):
        s = GroupAssignMemberSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn("member_code", s.errors)

    def test_empty_member_code_is_invalid(self):
        s = GroupAssignMemberSerializer(data={"member_code": ""})
        self.assertFalse(s.is_valid())
        self.assertIn("member_code", s.errors)
