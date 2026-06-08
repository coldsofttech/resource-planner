from django.test import TestCase

from apps.teams import selectors
from apps.teams.tests.factories import make_team


class GetAllTeamsTest(TestCase):
    def test_returns_all_teams(self):
        make_team("Alpha")
        make_team("Beta", is_active=False)
        self.assertEqual(selectors.get_all_teams().count(), 2)

    def test_returns_empty_when_none(self):
        self.assertEqual(selectors.get_all_teams().count(), 0)


class GetActiveTeamsTest(TestCase):
    def test_returns_only_active_teams(self):
        make_team("Alpha", is_active=True)
        make_team("Beta", is_active=False)
        qs = selectors.get_active_teams()
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().name, "Alpha")

    def test_returns_empty_when_no_active(self):
        make_team("Alpha", is_active=False)
        self.assertEqual(selectors.get_active_teams().count(), 0)


class GetTeamByCodeTest(TestCase):
    def test_returns_team_by_code(self):
        team = make_team("Alpha")
        result = selectors.get_team_by_code(team.code)
        self.assertEqual(result, team)

    def test_returns_none_for_unknown_code(self):
        result = selectors.get_team_by_code("TEAM-9999")
        self.assertIsNone(result)


class TeamNameExistsTest(TestCase):
    def test_returns_true_when_name_exists(self):
        make_team("Alpha")
        self.assertTrue(selectors.team_name_exists("Alpha"))

    def test_returns_false_when_name_missing(self):
        self.assertFalse(selectors.team_name_exists("Alpha"))

    def test_excludes_own_pk(self):
        team = make_team("Alpha")
        self.assertFalse(selectors.team_name_exists("Alpha", exclude_pk=team.pk))

    def test_detects_conflict_on_other_team(self):
        make_team("Alpha")
        other = make_team("Beta")
        self.assertTrue(selectors.team_name_exists("Alpha", exclude_pk=other.pk))


class GetTeamStatsTest(TestCase):
    def test_stats_counts_correctly(self):
        make_team("Alpha", is_active=True)
        make_team("Beta", is_active=True)
        make_team("Gamma", is_active=False)
        stats = selectors.get_team_stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["active"], 2)
        self.assertEqual(stats["inactive"], 1)

    def test_stats_with_no_teams(self):
        stats = selectors.get_team_stats()
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["active"], 0)
        self.assertEqual(stats["inactive"], 0)
