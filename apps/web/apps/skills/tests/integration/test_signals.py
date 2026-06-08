from django.test import TestCase

from apps.skills.models import Skill
from apps.skills.tests.factories import make_skill


class SkillSignalLoggingTest(TestCase):
    def test_create_signal_fires_without_error(self):
        skill = Skill.objects.create(skill="Python")
        self.assertIsNotNone(skill.pk)

    def test_delete_signal_fires_without_error(self):
        skill = Skill.objects.create(skill="Python")
        skill.delete()
        self.assertFalse(Skill.objects.filter(skill="Python").exists())

    def test_create_logs_created_message(self):
        with self.assertLogs("apps.skills.signals", level="DEBUG") as cm:
            Skill.objects.create(skill="Python")
        self.assertTrue(any("Created" in msg and "Python" in msg for msg in cm.output))

    def test_update_logs_updated_message(self):
        skill = make_skill("Python")
        with self.assertLogs("apps.skills.signals", level="DEBUG") as cm:
            skill.skill = "Rust"
            skill.save()
        self.assertTrue(any("Updated" in msg for msg in cm.output))

    def test_delete_logs_deleted_message(self):
        skill = make_skill("Python")
        with self.assertLogs("apps.skills.signals", level="DEBUG") as cm:
            skill.delete()
        self.assertTrue(any("Deleted" in msg and "Python" in msg for msg in cm.output))
