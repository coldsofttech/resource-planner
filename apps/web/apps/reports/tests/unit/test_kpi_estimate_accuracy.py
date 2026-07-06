from decimal import Decimal

from django.test import SimpleTestCase

from apps.reports.reports.kpi_estimate_accuracy import _accuracy_band, _month_label


class MonthLabelTest(SimpleTestCase):
    def test_formats_month_as_short_name_and_year(self):
        self.assertEqual(_month_label("2025-04"), "Apr 2025")

    def test_formats_december(self):
        self.assertEqual(_month_label("2024-12"), "Dec 2024")


class AccuracyBandTest(SimpleTestCase):
    def test_comment_forces_exception_band(self):
        band_key, band_label = _accuracy_band(
            Decimal("100"), Decimal("100"), Decimal("110"), "Scope change."
        )
        self.assertEqual(band_key, "exception")
        self.assertEqual(band_label, "Exception")

    def test_blank_comment_does_not_force_exception(self):
        band_key, _ = _accuracy_band(
            Decimal("95"), Decimal("100"), Decimal("110"), "   "
        )
        self.assertNotEqual(band_key, "exception")

    def test_no_estimate_value_returns_no_estimate_band(self):
        band_key, band_label = _accuracy_band(
            Decimal("100"), Decimal("0"), Decimal("0"), ""
        )
        self.assertEqual(band_key, "no_estimate")
        self.assertEqual(band_label, "—")

    def test_over_estimate_within_contingency_is_in_range(self):
        band_key, band_label = _accuracy_band(
            Decimal("105"), Decimal("100"), Decimal("110"), ""
        )
        self.assertEqual(band_key, "in_range")
        self.assertEqual(band_label, "In Range")

    def test_exactly_at_estimate_is_in_range(self):
        band_key, _ = _accuracy_band(Decimal("100"), Decimal("100"), Decimal("110"), "")
        self.assertEqual(band_key, "in_range")

    def test_accuracy_gte_90_bands_gt90(self):
        band_key, band_label = _accuracy_band(
            Decimal("91"), Decimal("100"), Decimal("100"), ""
        )
        self.assertEqual(band_key, "gt90")
        self.assertEqual(band_label, "> 90%")

    def test_accuracy_gte_80_bands_gt80(self):
        band_key, _ = _accuracy_band(Decimal("81"), Decimal("100"), Decimal("100"), "")
        self.assertEqual(band_key, "gt80")

    def test_accuracy_gte_70_bands_gt70(self):
        band_key, _ = _accuracy_band(Decimal("71"), Decimal("100"), Decimal("100"), "")
        self.assertEqual(band_key, "gt70")

    def test_accuracy_gte_60_bands_gt60(self):
        band_key, _ = _accuracy_band(Decimal("61"), Decimal("100"), Decimal("100"), "")
        self.assertEqual(band_key, "gt60")

    def test_accuracy_gte_50_bands_gt50(self):
        band_key, _ = _accuracy_band(Decimal("51"), Decimal("100"), Decimal("100"), "")
        self.assertEqual(band_key, "gt50")

    def test_accuracy_below_50_bands_lt50(self):
        band_key, band_label = _accuracy_band(
            Decimal("10"), Decimal("100"), Decimal("100"), ""
        )
        self.assertEqual(band_key, "lt50")
        self.assertEqual(band_label, "< 50%")

    def test_boundary_at_exactly_50_bands_gt50(self):
        # Below the estimate but exactly at the 50% threshold.
        band_key, _ = _accuracy_band(Decimal("50"), Decimal("100"), Decimal("100"), "")
        self.assertEqual(band_key, "gt50")
