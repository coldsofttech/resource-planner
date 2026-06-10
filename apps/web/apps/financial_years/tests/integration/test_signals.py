from django.test import TestCase

from apps.financial_years.models import FinancialYear
from apps.financial_years.tests.factories import make_financial_year


class FinancialYearSignalLoggingTest(TestCase):
    def test_create_signal_fires_without_error(self):
        fy = make_financial_year()
        self.assertIsNotNone(fy.pk)

    def test_delete_signal_fires_without_error(self):
        fy = make_financial_year()
        fy.delete()
        self.assertFalse(FinancialYear.objects.filter(pk=fy.pk).exists())

    def test_create_logs_created_message(self):
        with self.assertLogs("apps.financial_years.signals", level="DEBUG") as cm:
            make_financial_year()
        self.assertTrue(any("Created" in msg for msg in cm.output))

    def test_update_logs_updated_message(self):
        fy = make_financial_year()
        with self.assertLogs("apps.financial_years.signals", level="DEBUG") as cm:
            fy.note = "Updated note"
            fy.save()
        self.assertTrue(any("Updated" in msg for msg in cm.output))

    def test_delete_logs_deleted_message(self):
        fy = make_financial_year()
        long_fy = fy.long_fy
        with self.assertLogs("apps.financial_years.signals", level="DEBUG") as cm:
            fy.delete()
        self.assertTrue(any("Deleted" in msg and long_fy in msg for msg in cm.output))

    def test_create_log_includes_code(self):
        with self.assertLogs("apps.financial_years.signals", level="DEBUG") as cm:
            fy = make_financial_year()
        self.assertTrue(any(fy.code in msg for msg in cm.output))
