from django.test import SimpleTestCase

from apps.reports.reports.monthly_finance_report import _month_label


class MonthLabelTest(SimpleTestCase):
    def test_formats_month_as_short_name_and_year(self):
        self.assertEqual(_month_label("2025-04"), "Apr 2025")

    def test_formats_december(self):
        self.assertEqual(_month_label("2024-12"), "Dec 2024")
