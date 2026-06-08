from django.test import TestCase

from apps.teams.models import Team
from apps.teams.tests.factories import make_team


class TeamSignalLoggingTest(TestCase):
    def test_create_signal_fires_without_error(self):
        team = Team.objects.create(name="Alpha")
        self.assertIsNotNone(team.pk)

    def test_delete_signal_fires_without_error(self):
        team = Team.objects.create(name="Alpha")
        team.delete()
        self.assertFalse(Team.objects.filter(name="Alpha").exists())

    def test_create_logs_created_message(self):
        with self.assertLogs("apps.teams.signals", level="DEBUG") as cm:
            Team.objects.create(name="Alpha")
        self.assertTrue(any("Created" in msg and "Alpha" in msg for msg in cm.output))

    def test_update_logs_updated_message(self):
        team = make_team("Alpha")
        with self.assertLogs("apps.teams.signals", level="DEBUG") as cm:
            team.name = "AlphaRenamed"
            team.save()
        self.assertTrue(any("Updated" in msg for msg in cm.output))

    def test_delete_logs_deleted_message(self):
        team = make_team("Alpha")
        with self.assertLogs("apps.teams.signals", level="DEBUG") as cm:
            team.delete()
        self.assertTrue(any("Deleted" in msg and "Alpha" in msg for msg in cm.output))
