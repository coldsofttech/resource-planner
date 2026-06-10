import datetime

from django.test import SimpleTestCase

from apps.core.exceptions import ValidationException
from apps.leaves.services import LeaveService


class LeaveServiceValidateDatesTest(SimpleTestCase):
    def test_full_day_valid_same_dates(self):
        LeaveService._validate_dates(
            datetime.date(2025, 1, 6),
            datetime.date(2025, 1, 6),
            is_half_day=False,
            half_day_period=None,
        )

    def test_full_day_end_before_start_raises(self):
        with self.assertRaises(ValidationException):
            LeaveService._validate_dates(
                datetime.date(2025, 1, 10),
                datetime.date(2025, 1, 6),
                is_half_day=False,
                half_day_period=None,
            )

    def test_full_day_multi_day_valid(self):
        LeaveService._validate_dates(
            datetime.date(2025, 1, 6),
            datetime.date(2025, 1, 10),
            is_half_day=False,
            half_day_period=None,
        )

    def test_half_day_same_date_valid(self):
        LeaveService._validate_dates(
            datetime.date(2025, 1, 6),
            datetime.date(2025, 1, 6),
            is_half_day=True,
            half_day_period="AM",
        )

    def test_half_day_different_dates_raises(self):
        with self.assertRaises(ValidationException):
            LeaveService._validate_dates(
                datetime.date(2025, 1, 6),
                datetime.date(2025, 1, 7),
                is_half_day=True,
                half_day_period="AM",
            )

    def test_half_day_invalid_period_raises(self):
        with self.assertRaises(ValidationException):
            LeaveService._validate_dates(
                datetime.date(2025, 1, 6),
                datetime.date(2025, 1, 6),
                is_half_day=True,
                half_day_period="NOON",
            )

    def test_half_day_no_period_is_valid(self):
        LeaveService._validate_dates(
            datetime.date(2025, 1, 6),
            datetime.date(2025, 1, 6),
            is_half_day=True,
            half_day_period=None,
        )
