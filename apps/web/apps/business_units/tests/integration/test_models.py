from django.db import IntegrityError
from django.test import TestCase

from apps.business_units.models import BusinessUnit
from apps.business_units.tests.factories import make_business_unit
from apps.users.tests.factories import make_user


class BusinessUnitCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        bu = make_business_unit()
        self.assertTrue(bu.code.startswith("BU-"))

    def test_code_contains_pk(self):
        bu = make_business_unit()
        self.assertEqual(bu.code, f"BU-{bu.pk}")

    def test_codes_are_unique(self):
        b1 = make_business_unit("Finance", "FIN")
        b2 = make_business_unit("Technology", "TECH")
        self.assertNotEqual(b1.code, b2.code)


class BusinessUnitFieldTest(TestCase):
    def test_is_active_defaults_to_true(self):
        bu = make_business_unit()
        self.assertTrue(bu.is_active)

    def test_short_name_stores_value(self):
        bu = make_business_unit(short_name="FIN")
        self.assertEqual(bu.short_name, "FIN")

    def test_str_returns_name(self):
        bu = make_business_unit("Finance")
        self.assertEqual(str(bu), "Finance")

    def test_name_stores_value(self):
        bu = make_business_unit("Technology")
        self.assertEqual(bu.name, "Technology")


class BusinessUnitConstraintTest(TestCase):
    def test_duplicate_name_raises_integrity_error(self):
        make_business_unit("Finance", "FIN")
        with self.assertRaises(IntegrityError):
            make_business_unit("Finance", "FIN2")

    def test_different_names_are_allowed(self):
        make_business_unit("Finance", "FIN")
        bu = make_business_unit("Technology", "TECH")
        self.assertIsNotNone(bu.pk)

    def test_short_name_max_length(self):
        bu = make_business_unit(short_name="A" * 10)
        self.assertEqual(len(bu.short_name), 10)


class BusinessUnitOrderingTest(TestCase):
    def test_ordered_by_name(self):
        make_business_unit("Zeta BU", "Z")
        make_business_unit("Alpha BU", "A")
        make_business_unit("Gamma BU", "G")
        names = list(BusinessUnit.objects.values_list("name", flat=True))
        self.assertEqual(names, sorted(names))


class BusinessUnitAuditableTest(TestCase):
    def test_created_at_is_set(self):
        bu = make_business_unit()
        self.assertIsNotNone(bu.created_at)

    def test_updated_at_is_set(self):
        bu = make_business_unit()
        self.assertIsNotNone(bu.updated_at)

    def test_created_by_nullable(self):
        bu = make_business_unit()
        self.assertIsNone(bu.created_by)

    def test_created_by_stores_user(self):
        user = make_user()
        bu = BusinessUnit.objects.create(
            name="HR", short_name="HR", created_by=user, updated_by=user
        )
        self.assertEqual(bu.created_by, user)
