from django.test import SimpleTestCase

from apps.roles.serializers import RoleCreateSerializer, RoleUpdateSerializer

# ── RoleCreateSerializer ──────────────────────────────────────────────────────


class RoleCreateSerializerValidTest(SimpleTestCase):
    def test_valid_with_role_only(self):
        s = RoleCreateSerializer(data={"role": "Developer"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_valid_with_all_fields(self):
        s = RoleCreateSerializer(
            data={
                "role": "Tech Lead",
                "is_active": True,
                "is_default": False,
                "is_assignable": True,
                "is_leadership": True,
            }
        )
        self.assertTrue(s.is_valid(), s.errors)


class RoleCreateSerializerRequiredTest(SimpleTestCase):
    def test_missing_role_is_invalid(self):
        s = RoleCreateSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn("role", s.errors)

    def test_blank_role_is_invalid(self):
        s = RoleCreateSerializer(data={"role": ""})
        self.assertFalse(s.is_valid())
        self.assertIn("role", s.errors)

    def test_whitespace_only_role_is_invalid(self):
        s = RoleCreateSerializer(data={"role": "   "})
        self.assertFalse(s.is_valid())
        self.assertIn("role", s.errors)


class RoleCreateSerializerLengthTest(SimpleTestCase):
    def test_role_at_max_length_is_valid(self):
        s = RoleCreateSerializer(data={"role": "A" * 100})
        self.assertTrue(s.is_valid(), s.errors)

    def test_role_exceeding_max_length_is_invalid(self):
        s = RoleCreateSerializer(data={"role": "A" * 101})
        self.assertFalse(s.is_valid())
        self.assertIn("role", s.errors)


class RoleCreateSerializerDefaultsTest(SimpleTestCase):
    def test_is_active_defaults_to_true(self):
        s = RoleCreateSerializer(data={"role": "Developer"})
        s.is_valid()
        self.assertTrue(s.validated_data["is_active"])

    def test_is_default_defaults_to_false(self):
        s = RoleCreateSerializer(data={"role": "Developer"})
        s.is_valid()
        self.assertFalse(s.validated_data["is_default"])

    def test_is_assignable_defaults_to_false(self):
        s = RoleCreateSerializer(data={"role": "Developer"})
        s.is_valid()
        self.assertFalse(s.validated_data["is_assignable"])

    def test_is_leadership_defaults_to_false(self):
        s = RoleCreateSerializer(data={"role": "Developer"})
        s.is_valid()
        self.assertFalse(s.validated_data["is_leadership"])

    def test_is_active_false_is_accepted(self):
        s = RoleCreateSerializer(data={"role": "Developer", "is_active": False})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertFalse(s.validated_data["is_active"])

    def test_boolean_fields_accept_true(self):
        s = RoleCreateSerializer(
            data={
                "role": "Developer",
                "is_assignable": True,
                "is_leadership": True,
                "is_default": True,
            }
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertTrue(s.validated_data["is_assignable"])
        self.assertTrue(s.validated_data["is_leadership"])
        self.assertTrue(s.validated_data["is_default"])


# ── RoleUpdateSerializer ──────────────────────────────────────────────────────


class RoleUpdateSerializerValidTest(SimpleTestCase):
    def test_empty_payload_is_valid(self):
        s = RoleUpdateSerializer(data={})
        self.assertTrue(s.is_valid(), s.errors)

    def test_partial_update_with_role_only(self):
        s = RoleUpdateSerializer(data={"role": "Senior Developer"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_partial_update_with_booleans_only(self):
        s = RoleUpdateSerializer(data={"is_assignable": True, "is_leadership": False})
        self.assertTrue(s.is_valid(), s.errors)

    def test_full_payload_is_valid(self):
        s = RoleUpdateSerializer(
            data={
                "role": "Tech Lead",
                "is_active": False,
                "is_default": True,
                "is_assignable": True,
                "is_leadership": True,
            }
        )
        self.assertTrue(s.is_valid(), s.errors)


class RoleUpdateSerializerLengthTest(SimpleTestCase):
    def test_role_at_max_length_is_valid(self):
        s = RoleUpdateSerializer(data={"role": "B" * 100})
        self.assertTrue(s.is_valid(), s.errors)

    def test_role_exceeding_max_length_is_invalid(self):
        s = RoleUpdateSerializer(data={"role": "B" * 101})
        self.assertFalse(s.is_valid())
        self.assertIn("role", s.errors)


class RoleUpdateSerializerOptionalTest(SimpleTestCase):
    def test_all_fields_are_optional(self):
        s = RoleUpdateSerializer(data={})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data, {})

    def test_role_not_required(self):
        s = RoleUpdateSerializer(data={"is_active": True})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertNotIn("role", s.validated_data)

    def test_boolean_fields_not_required(self):
        s = RoleUpdateSerializer(data={"role": "Analyst"})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertNotIn("is_active", s.validated_data)
        self.assertNotIn("is_default", s.validated_data)
