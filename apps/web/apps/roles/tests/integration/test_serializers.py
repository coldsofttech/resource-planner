from django.test import TestCase

from apps.roles.serializers import RoleDetailSerializer, RoleListSerializer
from apps.roles.tests.factories import make_role
from apps.users.tests.factories import make_user

_LIST_FIELDS = frozenset(
    [
        "code",
        "role",
        "is_active",
        "is_default",
        "is_assignable",
        "is_leadership",
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
    ]
)

_DETAIL_FIELDS = frozenset(
    [
        "code",
        "role",
        "is_active",
        "is_default",
        "is_assignable",
        "is_leadership",
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
    ]
)


# ── RoleListSerializer ────────────────────────────────────────────────────────


class RoleListSerializerOutputTest(TestCase):
    def test_all_expected_fields_present(self):
        role = make_role("Developer")
        data = RoleListSerializer(role).data
        self.assertEqual(set(data.keys()), _LIST_FIELDS)

    def test_role_matches_instance(self):
        role = make_role("Developer")
        self.assertEqual(RoleListSerializer(role).data["role"], "Developer")

    def test_code_matches_instance(self):
        role = make_role("Developer")
        self.assertEqual(RoleListSerializer(role).data["code"], role.code)

    def test_is_active_reflects_instance_value(self):
        role = make_role("Developer", is_active=False)
        self.assertFalse(RoleListSerializer(role).data["is_active"])

    def test_is_default_reflects_instance_value(self):
        role = make_role("Developer", is_default=True)
        self.assertTrue(RoleListSerializer(role).data["is_default"])

    def test_is_assignable_reflects_instance_value(self):
        role = make_role("Developer", is_assignable=True)
        self.assertTrue(RoleListSerializer(role).data["is_assignable"])

    def test_is_leadership_reflects_instance_value(self):
        role = make_role("Tech Lead", is_leadership=True)
        self.assertTrue(RoleListSerializer(role).data["is_leadership"])

    def test_created_by_is_null_when_not_set(self):
        role = make_role("Developer")
        self.assertIsNone(RoleListSerializer(role).data["created_by"])

    def test_created_by_is_populated_when_set(self):
        user = make_user()
        role = make_role("Developer")
        role.created_by = user
        role.save(update_fields=["created_by"])
        self.assertIsNotNone(RoleListSerializer(role).data["created_by"])


# ── RoleDetailSerializer ──────────────────────────────────────────────────────


class RoleDetailSerializerOutputTest(TestCase):
    def test_all_expected_fields_present(self):
        role = make_role("Developer")
        data = RoleDetailSerializer(role).data
        self.assertEqual(set(data.keys()), _DETAIL_FIELDS)

    def test_role_matches_instance(self):
        role = make_role("Developer")
        self.assertEqual(RoleDetailSerializer(role).data["role"], "Developer")

    def test_is_active_matches_instance(self):
        role = make_role("Developer", is_active=True)
        self.assertTrue(RoleDetailSerializer(role).data["is_active"])

    def test_is_assignable_matches_instance(self):
        role = make_role("Developer", is_assignable=True)
        self.assertTrue(RoleDetailSerializer(role).data["is_assignable"])

    def test_is_leadership_matches_instance(self):
        role = make_role("Tech Lead", is_leadership=True)
        self.assertTrue(RoleDetailSerializer(role).data["is_leadership"])

    def test_created_by_is_null_when_not_set(self):
        role = make_role("Developer")
        self.assertIsNone(RoleDetailSerializer(role).data["created_by"])
