from django.test import TestCase

from apps.business_units import selectors
from apps.business_units.tests.factories import make_business_unit


class GetAllBusinessUnitsTest(TestCase):
    def test_returns_all_records(self):
        make_business_unit("Finance", "FIN", is_active=True)
        make_business_unit("Technology", "TECH", is_active=False)
        result = selectors.get_all_business_units()
        self.assertEqual(result.count(), 2)

    def test_returns_empty_when_none(self):
        result = selectors.get_all_business_units()
        self.assertEqual(result.count(), 0)


class GetActiveBusinessUnitsTest(TestCase):
    def test_returns_only_active(self):
        make_business_unit("Finance", "FIN", is_active=True)
        make_business_unit("Technology", "TECH", is_active=False)
        result = selectors.get_active_business_units()
        self.assertEqual(result.count(), 1)
        self.assertEqual(result.first().name, "Finance")

    def test_excludes_inactive(self):
        make_business_unit("Operations", "OPS", is_active=False)
        result = selectors.get_active_business_units()
        self.assertEqual(result.count(), 0)


class GetBusinessUnitByCodeTest(TestCase):
    def test_returns_matching_record(self):
        bu = make_business_unit("Finance", "FIN")
        result = selectors.get_business_unit_by_code(bu.code)
        self.assertEqual(result, bu)

    def test_returns_none_for_unknown_code(self):
        result = selectors.get_business_unit_by_code("BU-9999")
        self.assertIsNone(result)


class BusinessUnitNameExistsTest(TestCase):
    def test_returns_true_when_name_exists(self):
        make_business_unit("Finance", "FIN")
        self.assertTrue(selectors.business_unit_name_exists("Finance"))

    def test_returns_false_when_name_absent(self):
        self.assertFalse(selectors.business_unit_name_exists("Finance"))

    def test_excludes_given_pk(self):
        bu = make_business_unit("Finance", "FIN")
        self.assertFalse(
            selectors.business_unit_name_exists("Finance", exclude_pk=bu.pk)
        )

    def test_detects_duplicate_excluding_different_pk(self):
        make_business_unit("Finance", "FIN")
        bu2 = make_business_unit("Technology", "TECH")
        self.assertTrue(
            selectors.business_unit_name_exists("Finance", exclude_pk=bu2.pk)
        )


class GetBusinessUnitStatsTest(TestCase):
    def test_returns_correct_counts(self):
        make_business_unit("Finance", "FIN", is_active=True)
        make_business_unit("Technology", "TECH", is_active=True)
        make_business_unit("Operations", "OPS", is_active=False)
        stats = selectors.get_business_unit_stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["active"], 2)
        self.assertEqual(stats["inactive"], 1)

    def test_returns_zeros_when_empty(self):
        stats = selectors.get_business_unit_stats()
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["active"], 0)
        self.assertEqual(stats["inactive"], 0)
