from django.db import IntegrityError
from django.test import TestCase

from apps.tags.tests.factories import make_tag
from apps.users.tests.factories import make_user


class TagCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        tag = make_tag()
        self.assertTrue(tag.code.startswith("TAG-"))

    def test_code_contains_pk(self):
        tag = make_tag()
        self.assertEqual(tag.code, f"TAG-{tag.pk}")

    def test_codes_are_unique(self):
        t1 = make_tag("backend")
        t2 = make_tag("frontend")
        self.assertNotEqual(t1.code, t2.code)


class TagNameNormalisationTest(TestCase):
    def test_name_is_lowercased(self):
        tag = make_tag("Backend")
        self.assertEqual(tag.name, "#backend")

    def test_hash_prefix_added_when_missing(self):
        tag = make_tag("backend")
        self.assertEqual(tag.name, "#backend")

    def test_hash_prefix_not_duplicated(self):
        tag = make_tag("#backend")
        self.assertEqual(tag.name, "#backend")

    def test_whitespace_stripped(self):
        tag = make_tag("  backend  ")
        self.assertEqual(tag.name, "#backend")


class TagConstraintTest(TestCase):
    def test_duplicate_name_raises_integrity_error(self):
        make_tag("backend")
        with self.assertRaises(IntegrityError):
            make_tag("backend")

    def test_different_names_allowed(self):
        make_tag("backend")
        tag = make_tag("frontend")
        self.assertIsNotNone(tag.pk)


class TagOrderingTest(TestCase):
    def test_ordered_by_name(self):
        make_tag("zzz")
        make_tag("aaa")
        make_tag("mmm")
        from apps.tags.models import Tag

        names = list(Tag.objects.values_list("name", flat=True))
        self.assertEqual(names, sorted(names))


class TagAuditableTest(TestCase):
    def test_created_at_is_set(self):
        tag = make_tag()
        self.assertIsNotNone(tag.created_at)

    def test_updated_at_is_set(self):
        tag = make_tag()
        self.assertIsNotNone(tag.updated_at)

    def test_created_by_nullable_by_default(self):
        tag = make_tag()
        self.assertIsNone(tag.created_by)

    def test_created_by_stores_user(self):
        user = make_user()
        from apps.tags.models import Tag

        tag = Tag.objects.create(name="ops", created_by=user, updated_by=user)
        self.assertEqual(tag.created_by, user)
