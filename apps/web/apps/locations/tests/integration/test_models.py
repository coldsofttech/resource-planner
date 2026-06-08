from django.db import IntegrityError
from django.test import TestCase

from apps.locations.models import Location
from apps.locations.tests.factories import make_location
from apps.users.tests.factories import make_user

# ── Code assignment ───────────────────────────────────────────────────────────


class LocationCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        loc = make_location()
        self.assertTrue(loc.code.startswith("LOC-"))

    def test_code_contains_pk(self):
        loc = make_location()
        self.assertEqual(loc.code, f"LOC-{loc.pk}")

    def test_codes_are_unique(self):
        loc1 = make_location("London", "United Kingdom")
        loc2 = make_location("Paris", "France")
        self.assertNotEqual(loc1.code, loc2.code)


# ── Field defaults ────────────────────────────────────────────────────────────


class LocationFieldTest(TestCase):
    def test_is_active_defaults_to_true(self):
        loc = make_location()
        self.assertTrue(loc.is_active)

    def test_is_default_defaults_to_false(self):
        loc = make_location()
        self.assertFalse(loc.is_default)

    def test_str_returns_city_country(self):
        loc = make_location("London", "United Kingdom")
        self.assertEqual(str(loc), "London, United Kingdom")

    def test_city_stores_value(self):
        loc = make_location(city="Dublin")
        self.assertEqual(loc.city, "Dublin")

    def test_country_stores_value(self):
        loc = make_location(country="Ireland")
        self.assertEqual(loc.country, "Ireland")


# ── Constraints ───────────────────────────────────────────────────────────────


class LocationConstraintTest(TestCase):
    def test_duplicate_city_country_raises_integrity_error(self):
        make_location("London", "United Kingdom")
        with self.assertRaises(IntegrityError):
            make_location("London", "United Kingdom")

    def test_same_city_different_country_is_allowed(self):
        make_location("London", "United Kingdom")
        loc = make_location("London", "Canada")
        self.assertIsNotNone(loc.pk)

    def test_same_country_different_city_is_allowed(self):
        make_location("London", "United Kingdom")
        loc = make_location("Manchester", "United Kingdom")
        self.assertIsNotNone(loc.pk)


# ── Ordering ──────────────────────────────────────────────────────────────────


class LocationOrderingTest(TestCase):
    def test_ordered_by_country_then_city(self):
        make_location("Paris", "France")
        make_location("London", "United Kingdom")
        make_location("Manchester", "United Kingdom")
        locs = list(Location.objects.values_list("city", flat=True))
        self.assertEqual(locs[0], "Paris")
        self.assertIn("London", locs[1:])
        self.assertIn("Manchester", locs[1:])


# ── Auditable fields ──────────────────────────────────────────────────────────


class LocationAuditableTest(TestCase):
    def test_created_at_is_set(self):
        loc = make_location()
        self.assertIsNotNone(loc.created_at)

    def test_updated_at_is_set(self):
        loc = make_location()
        self.assertIsNotNone(loc.updated_at)

    def test_created_by_nullable(self):
        loc = make_location()
        self.assertIsNone(loc.created_by)

    def test_created_by_stores_user(self):
        user = make_user()
        loc = Location.objects.create(
            city="Dublin", country="Ireland", created_by=user, updated_by=user
        )
        self.assertEqual(loc.created_by, user)
