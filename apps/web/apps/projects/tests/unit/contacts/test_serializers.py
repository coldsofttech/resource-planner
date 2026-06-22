from django.test import SimpleTestCase

from apps.projects.serializers import ProjectContactCreateSerializer


class ProjectContactCreateSerializerTest(SimpleTestCase):
    def test_valid_with_all_fields(self):
        s = ProjectContactCreateSerializer(
            data={"name": "Alice", "email": "alice@example.com", "role": "project"}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_valid_without_email(self):
        s = ProjectContactCreateSerializer(data={"name": "Alice", "role": "project"})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["email"], "")

    def test_valid_with_blank_email(self):
        s = ProjectContactCreateSerializer(
            data={"name": "Alice", "email": "", "role": "project"}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_valid_role_finance(self):
        s = ProjectContactCreateSerializer(
            data={"name": "Bob", "email": "", "role": "finance"}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_invalid_without_name(self):
        s = ProjectContactCreateSerializer(
            data={"email": "alice@example.com", "role": "project"}
        )
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_invalid_without_role(self):
        s = ProjectContactCreateSerializer(
            data={"name": "Alice", "email": "alice@example.com"}
        )
        self.assertFalse(s.is_valid())
        self.assertIn("role", s.errors)

    def test_invalid_role_value(self):
        s = ProjectContactCreateSerializer(
            data={"name": "Alice", "email": "", "role": "unknown"}
        )
        self.assertFalse(s.is_valid())
        self.assertIn("role", s.errors)

    def test_invalid_email_format(self):
        s = ProjectContactCreateSerializer(
            data={"name": "Alice", "email": "not-an-email", "role": "project"}
        )
        self.assertFalse(s.is_valid())
        self.assertIn("email", s.errors)

    def test_name_max_length_255_enforced(self):
        s = ProjectContactCreateSerializer(
            data={"name": "x" * 256, "email": "", "role": "project"}
        )
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_name_at_max_length_255_accepted(self):
        s = ProjectContactCreateSerializer(
            data={"name": "x" * 255, "email": "", "role": "project"}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_empty_payload_invalid(self):
        s = ProjectContactCreateSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)
        self.assertIn("role", s.errors)

    def test_validated_data_contains_all_fields(self):
        s = ProjectContactCreateSerializer(
            data={"name": "Alice", "email": "alice@example.com", "role": "finance"}
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["name"], "Alice")
        self.assertEqual(s.validated_data["email"], "alice@example.com")
        self.assertEqual(s.validated_data["role"], "finance")
