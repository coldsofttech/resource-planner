from django.test import TestCase

from apps.employment_types import selectors
from apps.employment_types.tests.factories import make_employment_type


class GetAllEmploymentTypesTest(TestCase):
    def test_returns_all_employment_types(self):
        make_employment_type("Full-time")
        make_employment_type("Part-time", is_active=False)
        self.assertEqual(selectors.get_all_employment_types().count(), 2)

    def test_returns_empty_when_none(self):
        self.assertEqual(selectors.get_all_employment_types().count(), 0)


class GetActiveEmploymentTypesTest(TestCase):
    def test_returns_only_active_types(self):
        make_employment_type("Full-time", is_active=True)
        make_employment_type("Part-time", is_active=False)
        qs = selectors.get_active_employment_types()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().name, "Full-time")

    def test_returns_empty_when_no_active(self):
        make_employment_type("Full-time", is_active=False)
        self.assertEqual(selectors.get_active_employment_types().count(), 0)


class GetEmploymentTypeByCodeTest(TestCase):
    def test_returns_employment_type_by_code(self):
        et = make_employment_type("Full-time")
        result = selectors.get_employment_type_by_code(et.code)
        self.assertEqual(result, et)

    def test_returns_none_for_unknown_code(self):
        result = selectors.get_employment_type_by_code("EMPTYPE-9999")
        self.assertIsNone(result)


class EmploymentTypeExistsTest(TestCase):
    def test_returns_true_when_exists(self):
        make_employment_type("Full-time")
        self.assertTrue(selectors.employment_type_exists("Full-time"))

    def test_returns_false_when_missing(self):
        self.assertFalse(selectors.employment_type_exists("Full-time"))

    def test_excludes_own_pk(self):
        et = make_employment_type("Full-time")
        self.assertFalse(
            selectors.employment_type_exists("Full-time", exclude_pk=et.pk)
        )

    def test_detects_conflict_on_other_record(self):
        make_employment_type("Full-time")
        other = make_employment_type("Part-time")
        self.assertTrue(
            selectors.employment_type_exists("Full-time", exclude_pk=other.pk)
        )


class GetEmploymentTypeStatsTest(TestCase):
    def test_stats_counts_correctly(self):
        make_employment_type("Full-time", is_active=True)
        make_employment_type("Part-time", is_active=True)
        make_employment_type("Casual", is_active=False)
        stats = selectors.get_employment_type_stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["active"], 2)
        self.assertEqual(stats["inactive"], 1)

    def test_stats_with_no_records(self):
        stats = selectors.get_employment_type_stats()
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["active"], 0)
        self.assertEqual(stats["inactive"], 0)


class GetEmploymentTypeOptionsTest(TestCase):
    def test_returns_only_active_types(self):
        make_employment_type("Full-time", is_active=True)
        make_employment_type("Casual", is_active=False)
        qs = selectors.get_employment_type_options()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().name, "Full-time")

    def test_excludes_inactive_types(self):
        make_employment_type("Casual", is_active=False)
        self.assertEqual(selectors.get_employment_type_options().count(), 0)

    def test_returns_empty_when_no_types(self):
        self.assertEqual(selectors.get_employment_type_options().count(), 0)

    def test_ordered_alphabetically_by_name(self):
        make_employment_type("Part-time", is_active=True)
        make_employment_type("Casual", is_active=True)
        make_employment_type("Full-time", is_active=True)
        names = list(
            selectors.get_employment_type_options().values_list("name", flat=True)
        )
        self.assertEqual(names, sorted(names))

    def test_each_row_exposes_code_and_name(self):
        et = make_employment_type("Full-time", is_active=True)
        result = selectors.get_employment_type_options().first()
        self.assertEqual(result.code, et.code)
        self.assertEqual(result.name, et.name)

    def test_each_row_exposes_is_default(self):
        make_employment_type("Full-time", is_active=True, is_default=True)
        result = selectors.get_employment_type_options().first()
        self.assertTrue(result.is_default)
