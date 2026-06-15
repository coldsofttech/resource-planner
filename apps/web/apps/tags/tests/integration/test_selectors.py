from django.test import TestCase

from apps.tags import selectors
from apps.tags.tests.factories import make_tag


class GetAllTagsTest(TestCase):
    def test_returns_all_tags(self):
        make_tag("backend")
        make_tag("frontend")
        qs = selectors.get_all_tags()
        self.assertEqual(qs.count(), 2)

    def test_returns_empty_queryset_when_no_tags(self):
        qs = selectors.get_all_tags()
        self.assertEqual(qs.count(), 0)

    def test_ordered_by_name(self):
        make_tag("zzz")
        make_tag("aaa")
        names = list(selectors.get_all_tags().values_list("name", flat=True))
        self.assertEqual(names, sorted(names))


class GetTagByCodeTest(TestCase):
    def test_returns_tag_for_valid_code(self):
        tag = make_tag("backend")
        result = selectors.get_tag_by_code(tag.code)
        self.assertEqual(result, tag)

    def test_returns_none_for_unknown_code(self):
        result = selectors.get_tag_by_code("TAG-9999")
        self.assertIsNone(result)


class GetTagByNameTest(TestCase):
    def test_returns_tag_for_exact_name(self):
        tag = make_tag("backend")
        result = selectors.get_tag_by_name(tag.name)
        self.assertEqual(result, tag)

    def test_returns_none_for_unknown_name(self):
        result = selectors.get_tag_by_name("#nonexistent")
        self.assertIsNone(result)

    def test_case_insensitive_match(self):
        tag = make_tag("backend")
        result = selectors.get_tag_by_name("#BACKEND")
        self.assertEqual(result, tag)


class TagExistsTest(TestCase):
    def test_returns_true_when_tag_exists(self):
        make_tag("backend")
        self.assertTrue(selectors.tag_exists("backend"))

    def test_returns_false_when_tag_absent(self):
        self.assertFalse(selectors.tag_exists("nonexistent"))

    def test_exclude_pk_allows_same_name_on_update(self):
        tag = make_tag("backend")
        self.assertFalse(selectors.tag_exists("backend", exclude_pk=tag.pk))

    def test_exclude_pk_still_detects_other_duplicate(self):
        make_tag("backend")
        other = make_tag("frontend")
        self.assertTrue(selectors.tag_exists("backend", exclude_pk=other.pk))


class GetTagStatsTest(TestCase):
    def test_returns_total_count(self):
        make_tag("backend")
        make_tag("frontend")
        stats = selectors.get_tag_stats()
        self.assertEqual(stats["total"], 2)

    def test_returns_zero_when_no_tags(self):
        stats = selectors.get_tag_stats()
        self.assertEqual(stats["total"], 0)
