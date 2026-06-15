from django.test import TestCase

from apps.roles.models import Role
from apps.roles.tests.factories import make_role


class RoleSignalLoggingTest(TestCase):
    def test_create_signal_fires_without_error(self):
        role = Role.objects.create(role="Developer")
        self.assertIsNotNone(role.pk)

    def test_delete_signal_fires_without_error(self):
        role = Role.objects.create(role="Developer")
        role.delete()
        self.assertFalse(Role.objects.filter(role="Developer").exists())

    def test_create_logs_created_message(self):
        with self.assertLogs("apps.roles.signals", level="DEBUG") as cm:
            Role.objects.create(role="Developer")
        self.assertTrue(
            any("Created" in msg and "Developer" in msg for msg in cm.output)
        )

    def test_update_logs_updated_message(self):
        role = make_role("Developer")
        with self.assertLogs("apps.roles.signals", level="DEBUG") as cm:
            role.role = "Senior Developer"
            role.save()
        self.assertTrue(any("Updated" in msg for msg in cm.output))

    def test_delete_logs_deleted_message(self):
        role = make_role("Developer")
        with self.assertLogs("apps.roles.signals", level="DEBUG") as cm:
            role.delete()
        self.assertTrue(
            any("Deleted" in msg and "Developer" in msg for msg in cm.output)
        )
