from django.test import TestCase

from apps.business_units.models import BusinessUnit
from apps.business_units.tests.factories import make_business_unit


class BusinessUnitSignalLoggingTest(TestCase):
    def test_create_signal_fires_without_error(self):
        bu = BusinessUnit.objects.create(name="Finance", short_name="FIN")
        self.assertIsNotNone(bu.pk)

    def test_delete_signal_fires_without_error(self):
        bu = BusinessUnit.objects.create(name="Finance", short_name="FIN")
        bu.delete()
        self.assertFalse(BusinessUnit.objects.filter(name="Finance").exists())

    def test_create_logs_created_message(self):
        with self.assertLogs("apps.business_units.signals", level="DEBUG") as cm:
            BusinessUnit.objects.create(name="Finance", short_name="FIN")
        self.assertTrue(any("Created" in msg and "Finance" in msg for msg in cm.output))

    def test_update_logs_updated_message(self):
        bu = make_business_unit("Finance", "FIN")
        with self.assertLogs("apps.business_units.signals", level="DEBUG") as cm:
            bu.name = "Finance Renamed"
            bu.save()
        self.assertTrue(any("Updated" in msg for msg in cm.output))

    def test_delete_logs_deleted_message(self):
        bu = make_business_unit("Finance", "FIN")
        with self.assertLogs("apps.business_units.signals", level="DEBUG") as cm:
            bu.delete()
        self.assertTrue(any("Deleted" in msg and "Finance" in msg for msg in cm.output))
