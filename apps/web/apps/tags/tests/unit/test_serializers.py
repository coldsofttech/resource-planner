from django.test import SimpleTestCase

from apps.tags.serializers import TagCreateSerializer


class TagCreateSerializerValidTest(SimpleTestCase):
    def test_valid_name_is_accepted(self):
        s = TagCreateSerializer(data={"name": "backend"})
        self.assertTrue(s.is_valid())

    def test_name_with_hash_prefix_is_accepted(self):
        s = TagCreateSerializer(data={"name": "#backend"})
        self.assertTrue(s.is_valid())

    def test_validated_data_contains_name(self):
        s = TagCreateSerializer(data={"name": "backend"})
        s.is_valid()
        self.assertIn("name", s.validated_data)


class TagCreateSerializerInvalidTest(SimpleTestCase):
    def test_missing_name_is_invalid(self):
        s = TagCreateSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_empty_name_is_invalid(self):
        s = TagCreateSerializer(data={"name": ""})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_name_exceeding_max_length_is_invalid(self):
        s = TagCreateSerializer(data={"name": "a" * 51})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_name_at_max_length_is_valid(self):
        s = TagCreateSerializer(data={"name": "a" * 50})
        self.assertTrue(s.is_valid())
