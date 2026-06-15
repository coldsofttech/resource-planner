from django.test import TestCase

from apps.tags.models import Tag
from apps.tags.tests.factories import make_tag


class NormaliseTagNameSignalTest(TestCase):
    def test_name_lowercased_on_create(self):
        tag = make_tag("Backend")
        self.assertEqual(tag.name, "#backend")

    def test_hash_prefix_added_on_create(self):
        tag = make_tag("backend")
        self.assertEqual(tag.name, "#backend")

    def test_hash_prefix_not_duplicated_on_create(self):
        tag = make_tag("#backend")
        self.assertEqual(tag.name, "#backend")

    def test_whitespace_stripped_on_create(self):
        tag = make_tag("  backend  ")
        self.assertEqual(tag.name, "#backend")

    def test_normalised_on_update(self):
        tag = make_tag("backend")
        tag.name = "DevOps"
        tag.save(update_fields=["name"])
        tag.refresh_from_db()
        self.assertEqual(tag.name, "#devops")

    def test_empty_name_stays_empty_on_save(self):
        tag = Tag(name="")
        tag.save()
        self.assertEqual(tag.name, "")
