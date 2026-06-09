from django.test import TestCase

from apps.locations import selectors
from apps.locations.tests.factories import make_location


class GetAllLocationsTest(TestCase):
    def test_returns_all_locations(self):
        make_location("London", "United Kingdom")
        make_location("Paris", "France", is_active=False)
        self.assertEqual(selectors.get_all_locations().count(), 2)

    def test_returns_empty_when_none(self):
        self.assertEqual(selectors.get_all_locations().count(), 0)


class GetActiveLocationsTest(TestCase):
    def test_returns_only_active_locations(self):
        make_location("London", "United Kingdom", is_active=True)
        make_location("Paris", "France", is_active=False)
        qs = selectors.get_active_locations()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().city, "London")

    def test_returns_empty_when_no_active(self):
        make_location("London", "United Kingdom", is_active=False)
        self.assertEqual(selectors.get_active_locations().count(), 0)


class GetLocationByCodeTest(TestCase):
    def test_returns_location_by_code(self):
        loc = make_location()
        result = selectors.get_location_by_code(loc.code)
        self.assertEqual(result, loc)

    def test_returns_none_for_unknown_code(self):
        result = selectors.get_location_by_code("LOC-9999")
        self.assertIsNone(result)


class LocationExistsTest(TestCase):
    def test_returns_true_when_location_exists(self):
        make_location("London", "United Kingdom")
        self.assertTrue(selectors.location_exists("London", "United Kingdom"))

    def test_returns_false_when_location_missing(self):
        self.assertFalse(selectors.location_exists("London", "United Kingdom"))

    def test_same_city_different_country_not_found(self):
        make_location("London", "United Kingdom")
        self.assertFalse(selectors.location_exists("London", "Canada"))

    def test_excludes_own_pk(self):
        loc = make_location("London", "United Kingdom")
        self.assertFalse(
            selectors.location_exists("London", "United Kingdom", exclude_pk=loc.pk)
        )

    def test_detects_conflict_on_other_location(self):
        make_location("London", "United Kingdom")
        other = make_location("Paris", "France")
        self.assertTrue(
            selectors.location_exists("London", "United Kingdom", exclude_pk=other.pk)
        )


class GetLocationStatsTest(TestCase):
    def test_stats_counts_correctly(self):
        make_location("London", "United Kingdom", is_active=True)
        make_location("Paris", "France", is_active=True)
        make_location("Berlin", "Germany", is_active=False)
        stats = selectors.get_location_stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["active"], 2)
        self.assertEqual(stats["inactive"], 1)

    def test_stats_with_no_locations(self):
        stats = selectors.get_location_stats()
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["active"], 0)
        self.assertEqual(stats["inactive"], 0)


class GetLocationOptionsTest(TestCase):
    def test_returns_only_active_locations(self):
        make_location("London", "United Kingdom", is_active=True)
        make_location("Paris", "France", is_active=False)
        qs = selectors.get_location_options()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().city, "London")

    def test_excludes_inactive_locations(self):
        make_location("London", "United Kingdom", is_active=False)
        self.assertEqual(selectors.get_location_options().count(), 0)

    def test_returns_empty_when_no_locations(self):
        self.assertEqual(selectors.get_location_options().count(), 0)

    def test_ordered_by_country_then_city(self):
        make_location("Paris", "France", is_active=True)
        make_location("Manchester", "United Kingdom", is_active=True)
        make_location("London", "United Kingdom", is_active=True)
        locs = list(selectors.get_location_options().values_list("city", flat=True))
        self.assertEqual(locs[0], "Paris")

    def test_each_row_exposes_code_city_country(self):
        loc = make_location("London", "United Kingdom", is_active=True)
        result = selectors.get_location_options().first()
        self.assertEqual(result.code, loc.code)
        self.assertEqual(result.city, loc.city)
        self.assertEqual(result.country, loc.country)
