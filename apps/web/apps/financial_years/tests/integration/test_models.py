from datetime import date

from django.test import TestCase

from apps.financial_years.constants import FinancialYearStatus
from apps.financial_years.models import FinancialYear
from apps.financial_years.tests.factories import make_financial_year
from apps.users.tests.factories import make_user


class FinancialYearCodeTest(TestCase):
    def test_code_starts_with_fy_prefix(self):
        fy = make_financial_year()
        self.assertTrue(fy.code.startswith("FY-"))

    def test_code_contains_pk(self):
        fy = make_financial_year()
        self.assertEqual(fy.code, f"FY-{fy.pk}")

    def test_codes_are_unique(self):
        fy1 = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        fy2 = make_financial_year(
            start_date=date(2025, 4, 1), end_date=date(2026, 3, 31)
        )
        self.assertNotEqual(fy1.code, fy2.code)


class FinancialYearDerivedFieldsTest(TestCase):
    def test_long_fy_auto_populated(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        self.assertEqual(fy.long_fy, "FY2024-2025")

    def test_short_fy_auto_populated(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        self.assertEqual(fy.short_fy, "FY24-25")

    def test_span_days_auto_calculated(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        # 366 days (2025 has Feb 29? No - 2024 is the leap year)
        # From 2024-04-01 to 2025-03-31 inclusive = 365 days
        expected = (date(2025, 3, 31) - date(2024, 4, 1)).days + 1
        self.assertEqual(fy.span_days, expected)

    def test_str_returns_long_fy(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        self.assertEqual(str(fy), "FY2024-2025")

    def test_derived_fields_update_on_date_change(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        fy.start_date = date(2025, 4, 1)
        fy.end_date = date(2026, 3, 31)
        fy.save(
            update_fields=["start_date", "end_date", "long_fy", "short_fy", "span_days"]
        )
        fy.refresh_from_db()
        self.assertEqual(fy.long_fy, "FY2025-2026")
        self.assertEqual(fy.short_fy, "FY25-26")


class FinancialYearFieldDefaultsTest(TestCase):
    def test_status_defaults_to_future(self):
        fy = make_financial_year()
        self.assertEqual(fy.status, FinancialYearStatus.FUTURE)

    def test_is_active_defaults_to_true(self):
        fy = make_financial_year()
        self.assertTrue(fy.is_active)

    def test_note_defaults_to_empty(self):
        fy = make_financial_year()
        self.assertEqual(fy.note, "")

    def test_created_at_set(self):
        fy = make_financial_year()
        self.assertIsNotNone(fy.created_at)

    def test_updated_at_set(self):
        fy = make_financial_year()
        self.assertIsNotNone(fy.updated_at)

    def test_created_by_nullable(self):
        fy = make_financial_year()
        self.assertIsNone(fy.created_by)

    def test_created_by_stores_user(self):
        user = make_user()
        fy = FinancialYear.objects.create(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            created_by=user,
            updated_by=user,
        )
        self.assertEqual(fy.created_by, user)


class FinancialYearOrderingTest(TestCase):
    def test_ordered_by_start_date_descending(self):
        make_financial_year(start_date=date(2023, 4, 1), end_date=date(2024, 3, 31))
        make_financial_year(start_date=date(2025, 4, 1), end_date=date(2026, 3, 31))
        make_financial_year(start_date=date(2024, 4, 1), end_date=date(2025, 3, 31))
        dates = list(FinancialYear.objects.values_list("start_date", flat=True))
        self.assertEqual(dates, sorted(dates, reverse=True))
