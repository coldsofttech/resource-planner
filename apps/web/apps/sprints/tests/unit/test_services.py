from datetime import date
from unittest.mock import MagicMock

from django.test import SimpleTestCase

from apps.core.exceptions import ValidationException
from apps.sprints.constants import SprintStatus
from apps.sprints.engine import SprintEngine, SprintGenerationEngine
from apps.sprints.services import SprintService


class ValidateDatesTest(SimpleTestCase):
    def test_raises_when_end_equals_start(self):
        with self.assertRaises(ValidationException):
            SprintService._validate_dates(date(2024, 4, 1), date(2024, 4, 1))

    def test_raises_when_end_before_start(self):
        with self.assertRaises(ValidationException):
            SprintService._validate_dates(date(2024, 4, 14), date(2024, 4, 1))

    def test_passes_when_end_after_start(self):
        SprintService._validate_dates(date(2024, 4, 1), date(2024, 4, 14))


class ValidateDatesWithinFYTest(SimpleTestCase):
    def _make_fy(self, start, end, code="FY-1"):
        fy = MagicMock()
        fy.code = code
        fy.start_date = start
        fy.end_date = end
        return fy

    def test_raises_when_start_before_fy(self):
        fy = self._make_fy(date(2024, 4, 1), date(2025, 3, 31))
        with self.assertRaises(ValidationException):
            SprintService._validate_dates_within_fy(
                date(2024, 3, 31), date(2024, 4, 14), fy
            )

    def test_raises_when_end_after_fy(self):
        fy = self._make_fy(date(2024, 4, 1), date(2025, 3, 31))
        with self.assertRaises(ValidationException):
            SprintService._validate_dates_within_fy(
                date(2025, 3, 1), date(2025, 4, 1), fy
            )

    def test_passes_for_dates_within_fy(self):
        fy = self._make_fy(date(2024, 4, 1), date(2025, 3, 31))
        SprintService._validate_dates_within_fy(date(2024, 4, 1), date(2024, 4, 14), fy)

    def test_passes_for_dates_on_fy_boundaries(self):
        fy = self._make_fy(date(2024, 4, 1), date(2025, 3, 31))
        SprintService._validate_dates_within_fy(date(2024, 4, 1), date(2025, 3, 31), fy)


class SprintEngineDaysRemainingTest(SimpleTestCase):
    def test_returns_zero_when_end_date_is_none(self):
        self.assertEqual(SprintEngine.days_remaining(None), 0)

    def test_returns_positive_for_future_end_date(self):
        future_end = date(2099, 12, 31)
        result = SprintEngine.days_remaining(future_end)
        self.assertGreater(result, 0)

    def test_returns_negative_for_past_end_date(self):
        past_end = date(2000, 1, 1)
        result = SprintEngine.days_remaining(past_end)
        self.assertLess(result, 0)


class SprintEngineComputeStatusTest(SimpleTestCase):
    def test_returns_future_when_start_in_future(self):
        status = SprintEngine.compute_status(date(2099, 1, 1), date(2099, 1, 14))
        self.assertEqual(status, SprintStatus.FUTURE)

    def test_returns_expired_when_end_in_past(self):
        status = SprintEngine.compute_status(date(2000, 1, 1), date(2000, 1, 14))
        self.assertEqual(status, SprintStatus.EXPIRED)


class SprintGenerationEngineWindowsTest(SimpleTestCase):
    def test_generates_single_window_for_exact_fit(self):
        windows = SprintGenerationEngine.generate_date_windows(
            date(2024, 4, 1), date(2024, 4, 14), duration_days=14
        )
        self.assertEqual(len(windows), 1)
        self.assertEqual(windows[0], (date(2024, 4, 1), date(2024, 4, 14)))

    def test_generates_two_windows(self):
        windows = SprintGenerationEngine.generate_date_windows(
            date(2024, 4, 1), date(2024, 4, 28), duration_days=14
        )
        self.assertEqual(len(windows), 2)
        self.assertEqual(windows[0][0], date(2024, 4, 1))
        self.assertEqual(windows[0][1], date(2024, 4, 14))
        self.assertEqual(windows[1][0], date(2024, 4, 15))
        self.assertEqual(windows[1][1], date(2024, 4, 28))

    def test_last_window_capped_at_fy_end(self):
        windows = SprintGenerationEngine.generate_date_windows(
            date(2024, 4, 1), date(2024, 4, 20), duration_days=14
        )
        self.assertEqual(windows[-1][1], date(2024, 4, 20))

    def test_windows_are_non_overlapping_and_contiguous(self):
        windows = SprintGenerationEngine.generate_date_windows(
            date(2024, 4, 1), date(2024, 5, 31), duration_days=14
        )
        for i in range(1, len(windows)):
            prev_end = windows[i - 1][1]
            curr_start = windows[i][0]
            from datetime import timedelta

            self.assertEqual(curr_start, prev_end + timedelta(days=1))

    def test_single_day_range_yields_one_window(self):
        windows = SprintGenerationEngine.generate_date_windows(
            date(2024, 4, 1), date(2024, 4, 1), duration_days=14
        )
        self.assertEqual(len(windows), 1)
        self.assertEqual(windows[0], (date(2024, 4, 1), date(2024, 4, 1)))
