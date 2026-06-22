from django.test import SimpleTestCase

from apps.projects.serializers import (
    ProjectLinkCreateSerializer,
    ProjectLinkUpdateSerializer,
)


class ProjectLinkCreateSerializerTest(SimpleTestCase):
    def test_valid_with_required_fields(self):
        s = ProjectLinkCreateSerializer(
            data={"title": "My Link", "url": "https://example.com"}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_invalid_without_title(self):
        s = ProjectLinkCreateSerializer(data={"url": "https://example.com"})
        self.assertFalse(s.is_valid())
        self.assertIn("title", s.errors)

    def test_invalid_without_url(self):
        s = ProjectLinkCreateSerializer(data={"title": "My Link"})
        self.assertFalse(s.is_valid())
        self.assertIn("url", s.errors)

    def test_invalid_with_empty_payload(self):
        s = ProjectLinkCreateSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn("title", s.errors)
        self.assertIn("url", s.errors)

    def test_invalid_url_format_rejected(self):
        s = ProjectLinkCreateSerializer(data={"title": "Bad URL", "url": "not-a-url"})
        self.assertFalse(s.is_valid())
        self.assertIn("url", s.errors)

    def test_url_with_http_scheme_accepted(self):
        s = ProjectLinkCreateSerializer(
            data={"title": "HTTP Link", "url": "http://example.com"}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_url_with_https_scheme_accepted(self):
        s = ProjectLinkCreateSerializer(
            data={"title": "HTTPS Link", "url": "https://secure.example.com/path"}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_title_max_length_200_enforced(self):
        s = ProjectLinkCreateSerializer(
            data={"title": "x" * 201, "url": "https://example.com"}
        )
        self.assertFalse(s.is_valid())
        self.assertIn("title", s.errors)

    def test_title_at_max_length_200_accepted(self):
        s = ProjectLinkCreateSerializer(
            data={"title": "x" * 200, "url": "https://example.com"}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_url_max_length_500_enforced(self):
        long_url = "https://example.com/" + "a" * 490
        s = ProjectLinkCreateSerializer(data={"title": "Long URL", "url": long_url})
        self.assertFalse(s.is_valid())
        self.assertIn("url", s.errors)

    def test_validated_data_contains_title_and_url(self):
        s = ProjectLinkCreateSerializer(
            data={"title": "Validated", "url": "https://validated.com"}
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["title"], "Validated")
        self.assertEqual(s.validated_data["url"], "https://validated.com")


class ProjectLinkUpdateSerializerTest(SimpleTestCase):
    def test_valid_with_no_fields(self):
        s = ProjectLinkUpdateSerializer(data={})
        self.assertTrue(s.is_valid(), s.errors)

    def test_valid_with_title_only(self):
        s = ProjectLinkUpdateSerializer(data={"title": "Updated"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_valid_with_url_only(self):
        s = ProjectLinkUpdateSerializer(data={"url": "https://updated.com"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_valid_with_both_fields(self):
        s = ProjectLinkUpdateSerializer(
            data={"title": "New Title", "url": "https://new.com"}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_invalid_url_format_rejected(self):
        s = ProjectLinkUpdateSerializer(data={"url": "not-a-url"})
        self.assertFalse(s.is_valid())
        self.assertIn("url", s.errors)

    def test_title_max_length_200_enforced(self):
        s = ProjectLinkUpdateSerializer(data={"title": "x" * 201})
        self.assertFalse(s.is_valid())
        self.assertIn("title", s.errors)

    def test_url_max_length_500_enforced(self):
        long_url = "https://example.com/" + "a" * 490
        s = ProjectLinkUpdateSerializer(data={"url": long_url})
        self.assertFalse(s.is_valid())
        self.assertIn("url", s.errors)

    def test_validated_data_contains_only_provided_fields(self):
        s = ProjectLinkUpdateSerializer(data={"title": "Only Title"})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertIn("title", s.validated_data)
        self.assertNotIn("url", s.validated_data)
