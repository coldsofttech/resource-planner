from django.test import TestCase

from apps.employment_types.serializers import (
    EmploymentTypeDetailSerializer,
    EmploymentTypeListSerializer,
)
from apps.employment_types.tests.factories import make_employment_type
from apps.users.tests.factories import make_user

# ── EmploymentTypeListSerializer ──────────────────────────────────────────────


class EmploymentTypeListSerializerOutputTest(TestCase):
    _EXPECTED_FIELDS = frozenset(
        [
            "code",
            "name",
            "is_active",
            "is_default",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]
    )

    def test_all_expected_fields_present(self):
        et = make_employment_type("Full-time")
        data = EmploymentTypeListSerializer(et).data
        self.assertEqual(set(data.keys()), self._EXPECTED_FIELDS)

    def test_name_matches_instance(self):
        et = make_employment_type("Full-time")
        self.assertEqual(EmploymentTypeListSerializer(et).data["name"], "Full-time")

    def test_code_matches_instance(self):
        et = make_employment_type("Full-time")
        self.assertEqual(EmploymentTypeListSerializer(et).data["code"], et.code)

    def test_is_active_reflects_instance_value(self):
        et = make_employment_type("Full-time", is_active=False)
        self.assertFalse(EmploymentTypeListSerializer(et).data["is_active"])

    def test_is_default_reflects_instance_value(self):
        et = make_employment_type("Full-time", is_default=True)
        self.assertTrue(EmploymentTypeListSerializer(et).data["is_default"])

    def test_created_by_is_null_when_not_set(self):
        et = make_employment_type("Full-time")
        self.assertIsNone(EmploymentTypeListSerializer(et).data["created_by"])

    def test_created_by_is_populated_when_set(self):
        user = make_user()
        et = make_employment_type("Full-time")
        et.created_by = user
        et.save(update_fields=["created_by"])
        self.assertIsNotNone(EmploymentTypeListSerializer(et).data["created_by"])


# ── EmploymentTypeDetailSerializer ────────────────────────────────────────────


class EmploymentTypeDetailSerializerOutputTest(TestCase):
    _EXPECTED_FIELDS = frozenset(
        [
            "code",
            "name",
            "is_active",
            "is_default",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]
    )

    def test_all_expected_fields_present(self):
        et = make_employment_type("Full-time")
        data = EmploymentTypeDetailSerializer(et).data
        self.assertEqual(set(data.keys()), self._EXPECTED_FIELDS)

    def test_name_matches_instance(self):
        et = make_employment_type("Full-time")
        self.assertEqual(EmploymentTypeDetailSerializer(et).data["name"], "Full-time")

    def test_is_active_matches_instance(self):
        et = make_employment_type("Full-time", is_active=True)
        self.assertTrue(EmploymentTypeDetailSerializer(et).data["is_active"])

    def test_is_default_matches_instance(self):
        et = make_employment_type("Full-time", is_default=True)
        self.assertTrue(EmploymentTypeDetailSerializer(et).data["is_default"])

    def test_created_by_is_null_when_not_set(self):
        et = make_employment_type("Full-time")
        self.assertIsNone(EmploymentTypeDetailSerializer(et).data["created_by"])
