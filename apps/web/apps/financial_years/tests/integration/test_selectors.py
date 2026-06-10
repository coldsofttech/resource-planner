from datetime import date

from django.test import TestCase

from apps.financial_years import selectors
from apps.financial_years.constants import FinancialYearStatus
from apps.financial_years.tests.factories import make_financial_year


class GetAllFinancialYearsTest(TestCase):
    def test_returns_all_records(self):
        make_financial_year(start_date=date(2024, 4, 1), end_date=date(2025, 3, 31))
        make_financial_year(
            start_date=date(2025, 4, 1), end_date=date(2026, 3, 31), is_active=False
        )
        qs = selectors.get_all_financial_years()
        self.assertEqual(qs.count(), 2)

    def test_returns_empty_when_none(self):
        self.assertEqual(selectors.get_all_financial_years().count(), 0)


class GetActiveFinancialYearsTest(TestCase):
    def test_excludes_inactive(self):
        make_financial_year(start_date=date(2024, 4, 1), end_date=date(2025, 3, 31))
        make_financial_year(
            start_date=date(2025, 4, 1), end_date=date(2026, 3, 31), is_active=False
        )
        qs = selectors.get_active_financial_years()
        self.assertEqual(qs.count(), 1)

    def test_returns_active_only(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        result = selectors.get_active_financial_years().first()
        self.assertEqual(result.pk, fy.pk)


class GetFinancialYearByCodeTest(TestCase):
    def test_returns_matching_record(self):
        fy = make_financial_year()
        result = selectors.get_financial_year_by_code(fy.code)
        self.assertIsNotNone(result)
        self.assertEqual(result.pk, fy.pk)

    def test_returns_none_for_unknown_code(self):
        result = selectors.get_financial_year_by_code("FY-9999")
        self.assertIsNone(result)


class GetInProgressFinancialYearTest(TestCase):
    def test_returns_in_progress_record(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            status=FinancialYearStatus.IN_PROGRESS,
        )
        result = selectors.get_in_progress_financial_year()
        self.assertIsNotNone(result)
        self.assertEqual(result.pk, fy.pk)

    def test_returns_none_when_no_in_progress(self):
        make_financial_year(status=FinancialYearStatus.FUTURE)
        result = selectors.get_in_progress_financial_year()
        self.assertIsNone(result)

    def test_excludes_inactive_even_if_in_progress(self):
        make_financial_year(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            status=FinancialYearStatus.IN_PROGRESS,
            is_active=False,
        )
        result = selectors.get_in_progress_financial_year()
        self.assertIsNone(result)


class HasOverlappingFinancialYearTest(TestCase):
    def test_detects_full_overlap(self):
        make_financial_year(start_date=date(2024, 4, 1), end_date=date(2025, 3, 31))
        self.assertTrue(
            selectors.has_overlapping_financial_year(
                date(2024, 4, 1), date(2025, 3, 31)
            )
        )

    def test_detects_partial_overlap_start(self):
        make_financial_year(start_date=date(2024, 4, 1), end_date=date(2025, 3, 31))
        self.assertTrue(
            selectors.has_overlapping_financial_year(
                date(2024, 1, 1), date(2024, 6, 30)
            )
        )

    def test_detects_partial_overlap_end(self):
        make_financial_year(start_date=date(2024, 4, 1), end_date=date(2025, 3, 31))
        self.assertTrue(
            selectors.has_overlapping_financial_year(
                date(2025, 1, 1), date(2025, 6, 30)
            )
        )

    def test_no_overlap_before(self):
        make_financial_year(start_date=date(2024, 4, 1), end_date=date(2025, 3, 31))
        self.assertFalse(
            selectors.has_overlapping_financial_year(
                date(2023, 4, 1), date(2024, 3, 31)
            )
        )

    def test_no_overlap_after(self):
        make_financial_year(start_date=date(2024, 4, 1), end_date=date(2025, 3, 31))
        self.assertFalse(
            selectors.has_overlapping_financial_year(
                date(2025, 4, 1), date(2026, 3, 31)
            )
        )

    def test_exclude_pk_allows_self_update(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        self.assertFalse(
            selectors.has_overlapping_financial_year(
                date(2024, 4, 1), date(2025, 3, 31), exclude_pk=fy.pk
            )
        )


class GetFinancialYearStatsTest(TestCase):
    def test_stats_keys_present(self):
        stats = selectors.get_financial_year_stats()
        self.assertIn("total", stats)
        self.assertIn("active", stats)
        self.assertIn("inactive", stats)
        self.assertIn("in_progress", stats)
        self.assertIn("future", stats)
        self.assertIn("completed", stats)
        self.assertIn("expired", stats)

    def test_counts_accurate(self):
        make_financial_year(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            status=FinancialYearStatus.IN_PROGRESS,
        )
        make_financial_year(
            start_date=date(2025, 4, 1),
            end_date=date(2026, 3, 31),
            status=FinancialYearStatus.FUTURE,
        )
        stats = selectors.get_financial_year_stats()
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["in_progress"], 1)
        self.assertEqual(stats["future"], 1)
