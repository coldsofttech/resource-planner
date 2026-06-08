import logging

from django.test import TestCase

from apps.locations.tests.factories import make_location


class LocationSignalTest(TestCase):
    def test_save_signal_does_not_raise(self):
        with self.assertLogs("apps.locations.signals", level=logging.DEBUG):
            make_location("London", "United Kingdom")

    def test_delete_signal_does_not_raise(self):
        loc = make_location("London", "United Kingdom")
        with self.assertLogs("apps.locations.signals", level=logging.DEBUG):
            loc.delete()

    def test_update_signal_logs_updated(self):
        loc = make_location("London", "United Kingdom")
        with self.assertLogs("apps.locations.signals", level=logging.DEBUG) as cm:
            loc.city = "Manchester"
            loc.save(update_fields=["city"])
        self.assertTrue(any("Updated" in line for line in cm.output))
