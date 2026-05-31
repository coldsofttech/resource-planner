from django.test import TestCase

from apps.meta.serializers import MetaSerializer, MetaUserSerializer

META_USER_DATA = {
    "name": "Jane Doe",
    "email": "jane@example.com",
    "is_superuser": False,
}

META_DATA = {
    "setup_complete": True,
    "app_name": "Resource Planner",
    "auth_mode": "classic",
    "allow_registration": True,
}

META_DATA_WITH_USER = {
    **META_DATA,
    "user": META_USER_DATA,
}


# ---------------------------------------------------------------------------
# MetaUserSerializer
# ---------------------------------------------------------------------------


class MetaUserSerializerTest(TestCase):
    def test_serializes_name_field(self):
        MetaUserSerializer(data=META_USER_DATA)
        self.assertIn("name", MetaUserSerializer(META_USER_DATA).data)

    def test_serializes_email_field(self):
        data = MetaUserSerializer(META_USER_DATA).data
        self.assertIn("email", data)

    def test_serializes_is_superuser_field(self):
        data = MetaUserSerializer(META_USER_DATA).data
        self.assertIn("is_superuser", data)

    def test_name_value_is_correct(self):
        data = MetaUserSerializer(META_USER_DATA).data
        self.assertEqual(data["name"], "Jane Doe")

    def test_email_value_is_correct(self):
        data = MetaUserSerializer(META_USER_DATA).data
        self.assertEqual(data["email"], "jane@example.com")

    def test_is_superuser_false_for_regular_user(self):
        data = MetaUserSerializer(META_USER_DATA).data
        self.assertFalse(data["is_superuser"])

    def test_is_superuser_true_for_admin(self):
        data = MetaUserSerializer({**META_USER_DATA, "is_superuser": True}).data
        self.assertTrue(data["is_superuser"])


# ---------------------------------------------------------------------------
# MetaSerializer — without user (unauthenticated)
# ---------------------------------------------------------------------------


class MetaSerializerPublicTest(TestCase):
    def test_serializes_setup_complete_field(self):
        data = MetaSerializer(META_DATA).data
        self.assertIn("setup_complete", data)

    def test_serializes_app_name_field(self):
        data = MetaSerializer(META_DATA).data
        self.assertIn("app_name", data)

    def test_serializes_auth_mode_field(self):
        data = MetaSerializer(META_DATA).data
        self.assertIn("auth_mode", data)

    def test_serializes_allow_registration_field(self):
        data = MetaSerializer(META_DATA).data
        self.assertIn("allow_registration", data)

    def test_setup_complete_value_is_correct(self):
        data = MetaSerializer(META_DATA).data
        self.assertTrue(data["setup_complete"])

    def test_app_name_value_is_correct(self):
        data = MetaSerializer(META_DATA).data
        self.assertEqual(data["app_name"], "Resource Planner")

    def test_auth_mode_value_is_correct(self):
        data = MetaSerializer(META_DATA).data
        self.assertEqual(data["auth_mode"], "classic")

    def test_allow_registration_value_is_correct(self):
        data = MetaSerializer(META_DATA).data
        self.assertTrue(data["allow_registration"])

    def test_user_is_absent_when_not_provided(self):
        data = MetaSerializer(META_DATA).data
        self.assertNotIn("user", data)


# ---------------------------------------------------------------------------
# MetaSerializer — with user (authenticated)
# ---------------------------------------------------------------------------


class MetaSerializerAuthenticatedTest(TestCase):
    def test_user_is_present_when_provided(self):
        data = MetaSerializer(META_DATA_WITH_USER).data
        self.assertIn("user", data)

    def test_user_name_is_correct(self):
        data = MetaSerializer(META_DATA_WITH_USER).data
        self.assertEqual(data["user"]["name"], "Jane Doe")

    def test_user_email_is_correct(self):
        data = MetaSerializer(META_DATA_WITH_USER).data
        self.assertEqual(data["user"]["email"], "jane@example.com")

    def test_user_is_superuser_is_correct(self):
        data = MetaSerializer(META_DATA_WITH_USER).data
        self.assertFalse(data["user"]["is_superuser"])
