from django.test import TestCase

from apps.business_units.serializers import (
    BusinessUnitDetailSerializer,
    BusinessUnitListSerializer,
)
from apps.business_units.tests.factories import make_business_unit
from apps.users.tests.factories import make_user

# ── BusinessUnitListSerializer ────────────────────────────────────────────────


class BusinessUnitListSerializerOutputTest(TestCase):
    _EXPECTED_FIELDS = frozenset(
        [
            "code",
            "name",
            "short_name",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]
    )

    def test_all_expected_fields_present(self):
        bu = make_business_unit("Finance", "FIN")
        data = BusinessUnitListSerializer(bu).data
        self.assertEqual(set(data.keys()), self._EXPECTED_FIELDS)

    def test_name_matches_instance(self):
        bu = make_business_unit("Finance", "FIN")
        self.assertEqual(BusinessUnitListSerializer(bu).data["name"], "Finance")

    def test_short_name_matches_instance(self):
        bu = make_business_unit("Finance", "FIN")
        self.assertEqual(BusinessUnitListSerializer(bu).data["short_name"], "FIN")

    def test_code_matches_instance(self):
        bu = make_business_unit("Finance", "FIN")
        self.assertEqual(BusinessUnitListSerializer(bu).data["code"], bu.code)

    def test_is_active_reflects_value(self):
        bu = make_business_unit("Finance", "FIN", is_active=False)
        self.assertFalse(BusinessUnitListSerializer(bu).data["is_active"])

    def test_created_by_is_null_when_not_set(self):
        bu = make_business_unit("Finance", "FIN")
        self.assertIsNone(BusinessUnitListSerializer(bu).data["created_by"])

    def test_created_by_populated_when_set(self):
        user = make_user()
        bu = make_business_unit("Finance", "FIN")
        bu.created_by = user
        bu.save(update_fields=["created_by"])
        self.assertIsNotNone(BusinessUnitListSerializer(bu).data["created_by"])


# ── BusinessUnitDetailSerializer ──────────────────────────────────────────────


class BusinessUnitDetailSerializerOutputTest(TestCase):
    _EXPECTED_FIELDS = frozenset(
        [
            "code",
            "name",
            "short_name",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]
    )

    def test_all_expected_fields_present(self):
        bu = make_business_unit("Finance", "FIN")
        data = BusinessUnitDetailSerializer(bu).data
        self.assertEqual(set(data.keys()), self._EXPECTED_FIELDS)

    def test_name_matches_instance(self):
        bu = make_business_unit("Finance", "FIN")
        self.assertEqual(BusinessUnitDetailSerializer(bu).data["name"], "Finance")

    def test_short_name_matches_instance(self):
        bu = make_business_unit("Finance", "FIN")
        self.assertEqual(BusinessUnitDetailSerializer(bu).data["short_name"], "FIN")

    def test_is_active_matches_instance(self):
        bu = make_business_unit("Finance", "FIN", is_active=True)
        self.assertTrue(BusinessUnitDetailSerializer(bu).data["is_active"])

    def test_created_by_is_null_when_not_set(self):
        bu = make_business_unit("Finance", "FIN")
        self.assertIsNone(BusinessUnitDetailSerializer(bu).data["created_by"])
