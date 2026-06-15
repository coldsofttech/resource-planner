from django.test import TestCase

from apps.users.models import GroupProfile
from apps.users.serializers import (
    GroupAdminListSerializer,
    GroupMemberSerializer,
    UserAdminDetailSerializer,
)
from apps.users.tests.factories import (
    make_group_with_profile,
    make_profile,
    make_user,
    make_user_with_profile,
)

# ---------------------------------------------------------------------------
# GroupAdminListSerializer — output structure
# ---------------------------------------------------------------------------


class GroupAdminListSerializerTest(TestCase):
    def setUp(self):
        from django.db.models import Count

        self.group, self.gp = make_group_with_profile("Serialized Group")
        self.gp_annotated = (
            GroupProfile.objects.select_related("group", "created_by", "updated_by")
            .annotate(member_count=Count("group__user"))
            .get(pk=self.gp.pk)
        )

    def _serialize(self):
        return GroupAdminListSerializer(self.gp_annotated).data

    def test_code_present(self):
        data = self._serialize()
        self.assertIn("code", data)
        self.assertTrue(data["code"].startswith("USRGRP-"))

    def test_name_reflects_group_name(self):
        data = self._serialize()
        self.assertEqual(data["name"], "Serialized Group")

    def test_description_present(self):
        data = self._serialize()
        self.assertIn("description", data)

    def test_is_active_present(self):
        data = self._serialize()
        self.assertIn("is_active", data)
        self.assertTrue(data["is_active"])

    def test_is_admin_group_defaults_false(self):
        data = self._serialize()
        self.assertFalse(data["is_admin_group"])

    def test_is_system_defaults_false(self):
        data = self._serialize()
        self.assertFalse(data["is_system"])

    def test_member_count_present(self):
        data = self._serialize()
        self.assertIn("member_count", data)
        self.assertEqual(data["member_count"], 0)

    def test_created_at_present(self):
        data = self._serialize()
        self.assertIn("created_at", data)
        self.assertIsNotNone(data["created_at"])

    def test_created_by_null_by_default(self):
        data = self._serialize()
        self.assertIsNone(data["created_by"])

    def test_updated_at_present(self):
        data = self._serialize()
        self.assertIn("updated_at", data)

    def test_updated_by_null_by_default(self):
        data = self._serialize()
        self.assertIsNone(data["updated_by"])


# ---------------------------------------------------------------------------
# GroupMemberSerializer — output structure
# ---------------------------------------------------------------------------


class GroupMemberSerializerTest(TestCase):
    def setUp(self):
        self.user, self.profile = make_user_with_profile("groupmember@example.com")

    def _serialize(self):
        from apps.users.models import UserProfile

        profile = (
            UserProfile.objects.select_related("user")
            .prefetch_related("user__avatars")
            .get(pk=self.profile.pk)
        )
        return GroupMemberSerializer(profile).data

    def test_code_present(self):
        data = self._serialize()
        self.assertIn("code", data)
        self.assertTrue(data["code"].startswith("USER-"))

    def test_email_reflects_user_email(self):
        data = self._serialize()
        self.assertEqual(data["email"], "groupmember@example.com")

    def test_is_active_reflects_user_active_status(self):
        data = self._serialize()
        self.assertTrue(data["is_active"])

    def test_avatar_url_present(self):
        data = self._serialize()
        self.assertIn("avatar_url", data)
        self.assertIn(self.profile.code, data["avatar_url"])

    def test_display_name_present(self):
        data = self._serialize()
        self.assertIn("display_name", data)


# ---------------------------------------------------------------------------
# UserAdminDetailSerializer — output structure
# ---------------------------------------------------------------------------


class UserAdminDetailSerializerTest(TestCase):
    def setUp(self):
        self.user = make_user("detail@example.com")
        self.profile = make_profile(user=self.user)

    def _serialize(self):
        from apps.users.models import UserProfile

        profile = (
            UserProfile.objects.select_related(
                "user",
                "location",
                "employment_type",
                "role",
                "sso_provider_content_type",
                "created_by",
                "updated_by",
            )
            .prefetch_related("user__groups__profile")
            .get(pk=self.profile.pk)
        )
        return UserAdminDetailSerializer(profile).data

    def test_inherits_base_fields(self):
        data = self._serialize()
        self.assertIn("code", data)
        self.assertIn("email", data)
        self.assertIn("is_active", data)
        self.assertIn("auth_type", data)

    def test_groups_present_as_list(self):
        data = self._serialize()
        self.assertIn("groups", data)
        self.assertIsInstance(data["groups"], list)

    def test_groups_empty_when_no_groups_assigned(self):
        data = self._serialize()
        self.assertEqual(data["groups"], [])

    def test_groups_populated_when_group_assigned(self):

        group, gp = make_group_with_profile("Detail Test Group")
        self.user.groups.add(group)
        data = self._serialize()
        self.assertEqual(len(data["groups"]), 1)
        self.assertEqual(data["groups"][0]["name"], "Detail Test Group")
        self.assertEqual(data["groups"][0]["code"], gp.code)

    def test_location_is_none_when_not_set(self):
        data = self._serialize()
        self.assertIsNone(data["location"])

    def test_employment_type_is_none_when_not_set(self):
        data = self._serialize()
        self.assertIsNone(data["employment_type"])

    def test_role_is_none_when_not_set(self):
        data = self._serialize()
        self.assertIsNone(data["role"])

    def test_avatar_url_contains_profile_code(self):
        data = self._serialize()
        self.assertIn("avatar_url", data)
        self.assertIn(self.profile.code, data["avatar_url"])

    def test_avatar_url_follows_expected_pattern(self):
        data = self._serialize()
        self.assertEqual(
            data["avatar_url"], f"/api/v1/users/{self.profile.code}/avatar/"
        )

    def test_auth_type_defaults_to_classic(self):
        data = self._serialize()
        self.assertEqual(data["auth_type"], "classic")
