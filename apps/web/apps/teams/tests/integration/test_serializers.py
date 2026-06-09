from django.test import TestCase

from apps.teams.serializers import TeamDetailSerializer, TeamListSerializer
from apps.teams.tests.factories import make_team
from apps.users.tests.factories import make_user

# ── TeamListSerializer ────────────────────────────────────────────────────────


class TeamListSerializerOutputTest(TestCase):
    _EXPECTED_FIELDS = frozenset(
        [
            "code",
            "name",
            "description",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]
    )

    def test_all_expected_fields_present(self):
        team = make_team("Alpha")
        data = TeamListSerializer(team).data
        self.assertEqual(set(data.keys()), self._EXPECTED_FIELDS)

    def test_name_matches_team(self):
        team = make_team("Alpha")
        self.assertEqual(TeamListSerializer(team).data["name"], "Alpha")

    def test_code_matches_team(self):
        team = make_team("Alpha")
        self.assertEqual(TeamListSerializer(team).data["code"], team.code)

    def test_is_active_reflects_team_value(self):
        team = make_team("Alpha", is_active=False)
        self.assertFalse(TeamListSerializer(team).data["is_active"])

    def test_description_matches_team(self):
        team = make_team("Alpha", description="Core squad")
        self.assertEqual(TeamListSerializer(team).data["description"], "Core squad")

    def test_created_by_is_null_when_not_set(self):
        team = make_team("Alpha")
        self.assertIsNone(TeamListSerializer(team).data["created_by"])

    def test_created_by_is_populated_when_set(self):
        user = make_user()
        team = make_team("Alpha")
        team.created_by = user
        team.save(update_fields=["created_by"])
        self.assertIsNotNone(TeamListSerializer(team).data["created_by"])


# ── TeamDetailSerializer ──────────────────────────────────────────────────────


class TeamDetailSerializerOutputTest(TestCase):
    _EXPECTED_FIELDS = frozenset(
        [
            "code",
            "name",
            "description",
            "is_active",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]
    )

    def test_all_expected_fields_present(self):
        team = make_team("Alpha")
        data = TeamDetailSerializer(team).data
        self.assertEqual(set(data.keys()), self._EXPECTED_FIELDS)

    def test_name_matches_team(self):
        team = make_team("Alpha")
        self.assertEqual(TeamDetailSerializer(team).data["name"], "Alpha")

    def test_is_active_matches_team(self):
        team = make_team("Alpha", is_active=True)
        self.assertTrue(TeamDetailSerializer(team).data["is_active"])

    def test_description_matches_team(self):
        team = make_team("Alpha", description="Squad")
        self.assertEqual(TeamDetailSerializer(team).data["description"], "Squad")

    def test_created_by_is_null_when_not_set(self):
        team = make_team("Alpha")
        self.assertIsNone(TeamDetailSerializer(team).data["created_by"])
