from django.test import TestCase

from apps.employment_types.models import EmploymentType
from apps.employment_types.tests.factories import make_employment_type


class EmploymentTypeSignalLoggingTest(TestCase):
    def test_create_signal_fires_without_error(self):
        et = EmploymentType.objects.create(name="Full-time")
        self.assertIsNotNone(et.pk)

    def test_delete_signal_fires_without_error(self):
        et = EmploymentType.objects.create(name="Full-time")
        et.delete()
        self.assertFalse(EmploymentType.objects.filter(name="Full-time").exists())

    def test_create_logs_created_message(self):
        with self.assertLogs("apps.employment_types.signals", level="DEBUG") as cm:
            EmploymentType.objects.create(name="Full-time")
        self.assertTrue(
            any("Created" in msg and "Full-time" in msg for msg in cm.output)
        )

    def test_update_logs_updated_message(self):
        et = make_employment_type("Full-time")
        with self.assertLogs("apps.employment_types.signals", level="DEBUG") as cm:
            et.name = "Full Time"
            et.save()
        self.assertTrue(any("Updated" in msg for msg in cm.output))

    def test_delete_logs_deleted_message(self):
        et = make_employment_type("Full-time")
        with self.assertLogs("apps.employment_types.signals", level="DEBUG") as cm:
            et.delete()
        self.assertTrue(
            any("Deleted" in msg and "Full-time" in msg for msg in cm.output)
        )
