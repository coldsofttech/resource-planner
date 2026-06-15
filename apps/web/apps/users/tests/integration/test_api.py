from django.test import TestCase
from rest_framework.test import APIClient

from apps.auth.services import UserTokenService
from apps.configurations.tests.factories import mark_setup_complete
from apps.users.tests.factories import (
    make_group_with_profile,
    make_profile,
    make_user,
    make_user_with_profile,
)

USERS_ME_URL = "/api/v1/users/me/preferences/"
GROUPS_LIST_URL = "/api/v1/groups/"
GROUPS_STATS_URL = "/api/v1/groups/stats/"
GROUPS_DETAIL_URL = "/api/v1/groups/{}/"
GROUPS_ACTIVATE_URL = "/api/v1/groups/{}/activate/"
GROUPS_DEACTIVATE_URL = "/api/v1/groups/{}/deactivate/"
GROUPS_MEMBERS_URL = "/api/v1/groups/{}/members/"
GROUPS_MEMBER_DETAIL_URL = "/api/v1/groups/{}/members/{}/"
USERS_DETAIL_URL = "/api/v1/users/{}/"


# ---------------------------------------------------------------------------
# PATCH /api/v1/users/me/preferences/ — unauthenticated
# ---------------------------------------------------------------------------


class UsersMePatchUnauthenticatedTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()

    def test_unauthenticated_returns_401(self):
        response = self.client.patch(USERS_ME_URL, {"theme": "dark"}, format="json")
        self.assertEqual(response.status_code, 401)


# ---------------------------------------------------------------------------
# PATCH /api/v1/users/me/preferences/ — authenticated
# ---------------------------------------------------------------------------


class UsersMePatchAuthenticatedTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(email="prefs@example.com")
        make_profile(user=self.user, theme="light")
        token = UserTokenService(user=self.user, request=None).create_token(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")

    def test_valid_theme_returns_200(self):
        response = self.client.patch(USERS_ME_URL, {"theme": "dark"}, format="json")
        self.assertEqual(response.status_code, 200)

    def test_response_success_is_true(self):
        response = self.client.patch(USERS_ME_URL, {"theme": "dark"}, format="json")
        self.assertTrue(response.data["success"])

    def test_theme_persisted_to_database(self):
        self.client.patch(USERS_ME_URL, {"theme": "system"}, format="json")
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.theme, "system")

    def test_invalid_theme_returns_400(self):
        response = self.client.patch(USERS_ME_URL, {"theme": "purple"}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_missing_theme_returns_400(self):
        response = self.client.patch(USERS_ME_URL, {}, format="json")
        self.assertEqual(response.status_code, 400)


# ---------------------------------------------------------------------------
# GET /api/v1/groups/ — list
# ---------------------------------------------------------------------------


class GroupsListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_group_with_profile("Alpha Group")
        make_group_with_profile("Beta Group")

    def test_unauthenticated_returns_401(self):
        response = self.client.get(GROUPS_LIST_URL)
        self.assertEqual(response.status_code, 401)

    def test_authenticated_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GROUPS_LIST_URL)
        self.assertEqual(response.status_code, 200)

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GROUPS_LIST_URL)
        self.assertTrue(response.data["success"])

    def test_response_has_pagination(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GROUPS_LIST_URL)
        self.assertIn("pagination", response.data["data"])

    def test_response_has_results(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GROUPS_LIST_URL)
        self.assertIn("results", response.data["data"])

    def test_search_filters_by_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GROUPS_LIST_URL, {"search": "Alpha"})
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("Alpha Group", names)
        self.assertEqual(len(names), 1)

    def test_active_filter_returns_active_groups(self):
        from apps.users.models import GroupProfile

        _, gp = make_group_with_profile("Inactive Group")
        GroupProfile.objects.filter(pk=gp.pk).update(is_active=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GROUPS_LIST_URL, {"is_active": "true"})
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertNotIn("Inactive Group", names)


# ---------------------------------------------------------------------------
# GET /api/v1/groups/stats/
# ---------------------------------------------------------------------------


class GroupsStatsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_group_with_profile("G1")
        make_group_with_profile("G2")

    def test_unauthenticated_returns_401(self):
        response = self.client.get(GROUPS_STATS_URL)
        self.assertEqual(response.status_code, 401)

    def test_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GROUPS_STATS_URL)
        self.assertEqual(response.status_code, 200)

    def test_response_contains_total(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GROUPS_STATS_URL)
        self.assertIn("total", response.data["data"])

    def test_total_reflects_group_count(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GROUPS_STATS_URL)
        self.assertGreaterEqual(response.data["data"]["total"], 2)


# ---------------------------------------------------------------------------
# GET /api/v1/groups/<code>/ — retrieve
# ---------------------------------------------------------------------------


class GroupsRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.group, self.gp = make_group_with_profile("Detail Group")

    def test_unauthenticated_returns_401(self):
        response = self.client.get(GROUPS_DETAIL_URL.format(self.gp.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_200_for_known_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GROUPS_DETAIL_URL.format(self.gp.code))
        self.assertEqual(response.status_code, 200)

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GROUPS_DETAIL_URL.format("USRGRP-99999"))
        self.assertEqual(response.status_code, 404)

    def test_response_contains_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GROUPS_DETAIL_URL.format(self.gp.code))
        self.assertEqual(response.data["data"]["name"], "Detail Group")

    def test_response_contains_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GROUPS_DETAIL_URL.format(self.gp.code))
        self.assertEqual(response.data["data"]["code"], self.gp.code)


# ---------------------------------------------------------------------------
# POST /api/v1/groups/ — create
# ---------------------------------------------------------------------------


class GroupsCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.post(GROUPS_LIST_URL, {"name": "New"}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_valid_payload_returns_201(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            GROUPS_LIST_URL, {"name": "New Group"}, format="json"
        )
        self.assertEqual(response.status_code, 201)

    def test_missing_name_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(GROUPS_LIST_URL, {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_duplicate_name_returns_409(self):
        make_group_with_profile("Duplicate")
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            GROUPS_LIST_URL, {"name": "Duplicate"}, format="json"
        )
        self.assertEqual(response.status_code, 409)

    def test_response_contains_group_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            GROUPS_LIST_URL, {"name": "Coded Group"}, format="json"
        )
        self.assertIn("code", response.data["data"])


# ---------------------------------------------------------------------------
# PATCH /api/v1/groups/<code>/ — partial update
# ---------------------------------------------------------------------------


class GroupsUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.group, self.gp = make_group_with_profile("Update Group")

    def test_unauthenticated_returns_401(self):
        response = self.client.patch(
            GROUPS_DETAIL_URL.format(self.gp.code),
            {"description": "Updated"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_valid_payload_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            GROUPS_DETAIL_URL.format(self.gp.code),
            {"description": "Updated"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_description_updated_in_response(self):
        self.client.force_authenticate(user=self.user)
        self.client.patch(
            GROUPS_DETAIL_URL.format(self.gp.code),
            {"description": "New Desc"},
            format="json",
        )
        self.gp.refresh_from_db()
        self.assertEqual(self.gp.description, "New Desc")

    def test_duplicate_name_returns_409(self):
        make_group_with_profile("Taken Name")
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            GROUPS_DETAIL_URL.format(self.gp.code),
            {"name": "Taken Name"},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_unknown_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            GROUPS_DETAIL_URL.format("USRGRP-99999"),
            {"description": "x"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# DELETE /api/v1/groups/<code>/ — destroy
# ---------------------------------------------------------------------------


class GroupsDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        _, gp = make_group_with_profile("Delete Me")
        response = self.client.delete(GROUPS_DETAIL_URL.format(gp.code))
        self.assertEqual(response.status_code, 401)

    def test_deletes_group_returns_204(self):
        _, gp = make_group_with_profile("Deletable")
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(GROUPS_DETAIL_URL.format(gp.code))
        self.assertEqual(response.status_code, 204)

    def test_unknown_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(GROUPS_DETAIL_URL.format("USRGRP-99999"))
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# POST /api/v1/groups/<code>/activate|deactivate/
# ---------------------------------------------------------------------------


class GroupsActivateDeactivateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.group, self.gp = make_group_with_profile("Toggle")

    def test_activate_unauthenticated_returns_401(self):
        response = self.client.post(GROUPS_ACTIVATE_URL.format(self.gp.code))
        self.assertEqual(response.status_code, 401)

    def test_deactivate_unauthenticated_returns_401(self):
        response = self.client.post(GROUPS_DEACTIVATE_URL.format(self.gp.code))
        self.assertEqual(response.status_code, 401)

    def test_deactivate_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(GROUPS_DEACTIVATE_URL.format(self.gp.code))
        self.assertEqual(response.status_code, 200)

    def test_activate_returns_200(self):
        from apps.users.models import GroupProfile

        GroupProfile.objects.filter(pk=self.gp.pk).update(is_active=False)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(GROUPS_ACTIVATE_URL.format(self.gp.code))
        self.assertEqual(response.status_code, 200)

    def test_deactivate_sets_is_active_false(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(GROUPS_DEACTIVATE_URL.format(self.gp.code))
        self.gp.refresh_from_db()
        self.assertFalse(self.gp.is_active)

    def test_activate_unknown_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(GROUPS_ACTIVATE_URL.format("USRGRP-99999"))
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# GET /api/v1/groups/<code>/members/
# ---------------------------------------------------------------------------


class GroupsMembersListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.group, self.gp = make_group_with_profile("Members Group")

    def test_unauthenticated_returns_401(self):
        response = self.client.get(GROUPS_MEMBERS_URL.format(self.gp.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_200_for_empty_group(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GROUPS_MEMBERS_URL.format(self.gp.code))
        self.assertEqual(response.status_code, 200)

    def test_returns_404_for_unknown_group(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GROUPS_MEMBERS_URL.format("USRGRP-99999"))
        self.assertEqual(response.status_code, 404)

    def test_response_includes_assigned_member(self):
        member_user, member_profile = make_user_with_profile("listmember@example.com")
        self.group.user_set.add(member_user)
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GROUPS_MEMBERS_URL.format(self.gp.code))
        emails = [r["email"] for r in response.data["data"]["results"]]
        self.assertIn("listmember@example.com", emails)

    def test_response_has_pagination(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GROUPS_MEMBERS_URL.format(self.gp.code))
        self.assertIn("pagination", response.data["data"])


# ---------------------------------------------------------------------------
# POST /api/v1/groups/<code>/members/ — assign member
# ---------------------------------------------------------------------------


class GroupsAssignMemberAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.group, self.gp = make_group_with_profile("Assign Group")
        self.member_user, self.member_profile = make_user_with_profile(
            "newmember@example.com"
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.post(
            GROUPS_MEMBERS_URL.format(self.gp.code),
            {"member_code": self.member_profile.code},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_valid_assignment_returns_201(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            GROUPS_MEMBERS_URL.format(self.gp.code),
            {"member_code": self.member_profile.code},
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_member_added_to_group(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(
            GROUPS_MEMBERS_URL.format(self.gp.code),
            {"member_code": self.member_profile.code},
            format="json",
        )
        self.assertIn(self.group, self.member_user.groups.all())

    def test_duplicate_assignment_returns_409(self):
        self.group.user_set.add(self.member_user)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            GROUPS_MEMBERS_URL.format(self.gp.code),
            {"member_code": self.member_profile.code},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_unknown_member_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            GROUPS_MEMBERS_URL.format(self.gp.code),
            {"member_code": "USER-99999"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# DELETE /api/v1/groups/<code>/members/<member_code>/ — unassign member
# ---------------------------------------------------------------------------


class GroupsUnassignMemberAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.group, self.gp = make_group_with_profile("Unassign Group")
        self.member_user, self.member_profile = make_user_with_profile(
            "unassignee@example.com"
        )
        self.group.user_set.add(self.member_user)

    def test_unauthenticated_returns_401(self):
        response = self.client.delete(
            GROUPS_MEMBER_DETAIL_URL.format(self.gp.code, self.member_profile.code)
        )
        self.assertEqual(response.status_code, 401)

    def test_valid_unassignment_returns_204(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            GROUPS_MEMBER_DETAIL_URL.format(self.gp.code, self.member_profile.code)
        )
        self.assertEqual(response.status_code, 204)

    def test_member_removed_from_group(self):
        self.client.force_authenticate(user=self.user)
        self.client.delete(
            GROUPS_MEMBER_DETAIL_URL.format(self.gp.code, self.member_profile.code)
        )
        self.assertNotIn(self.group, self.member_user.groups.all())

    def test_unknown_member_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            GROUPS_MEMBER_DETAIL_URL.format(self.gp.code, "USER-99999")
        )
        self.assertEqual(response.status_code, 404)

    def test_unknown_group_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            GROUPS_MEMBER_DETAIL_URL.format("USRGRP-99999", self.member_profile.code)
        )
        self.assertEqual(response.status_code, 404)


# ---------------------------------------------------------------------------
# GET /api/v1/users/<code>/ — retrieve with extended detail serializer
# ---------------------------------------------------------------------------


class UsersAdminDetailAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.admin = make_user(is_superuser=True)
        self.target_user = make_user("target@example.com")
        self.target_profile = make_profile(user=self.target_user)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(USERS_DETAIL_URL.format(self.target_profile.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_200_for_known_user(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(USERS_DETAIL_URL.format(self.target_profile.code))
        self.assertEqual(response.status_code, 200)

    def test_returns_404_for_unknown_code(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(USERS_DETAIL_URL.format("USER-99999"))
        self.assertEqual(response.status_code, 404)

    def test_response_includes_groups_field(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(USERS_DETAIL_URL.format(self.target_profile.code))
        self.assertIn("groups", response.data["data"])

    def test_response_includes_avatar_url(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(USERS_DETAIL_URL.format(self.target_profile.code))
        self.assertIn("avatar_url", response.data["data"])

    def test_groups_is_list(self):
        self.client.force_authenticate(user=self.admin)
        response = self.client.get(USERS_DETAIL_URL.format(self.target_profile.code))
        self.assertIsInstance(response.data["data"]["groups"], list)
