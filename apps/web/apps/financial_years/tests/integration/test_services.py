from datetime import date

from django.test import TestCase

from apps.core.exceptions import NotFoundException, ValidationException
from apps.financial_years.constants import FinancialYearStatus
from apps.financial_years.models import FinancialYear
from apps.financial_years.services import (
    FinancialYearImportService,
    FinancialYearService,
)
from apps.financial_years.tests.factories import FakeCsvFile, make_financial_year
from apps.users.tests.factories import make_user


def _svc(user=None):
    return FinancialYearService(user=user or make_user())


class FinancialYearCreateTest(TestCase):
    def test_create_returns_instance(self):
        svc = _svc()
        fy = svc.create(start_date=date(2024, 4, 1), end_date=date(2025, 3, 31))
        self.assertIsNotNone(fy.pk)
        self.assertEqual(fy.long_fy, "FY2024-2025")

    def test_create_sets_derived_fields(self):
        svc = _svc()
        fy = svc.create(start_date=date(2024, 4, 1), end_date=date(2025, 3, 31))
        self.assertEqual(fy.short_fy, "FY24-25")
        expected_span = (date(2025, 3, 31) - date(2024, 4, 1)).days + 1
        self.assertEqual(fy.span_days, expected_span)

    def test_create_raises_on_end_before_start(self):
        svc = _svc()
        with self.assertRaises(ValidationException):
            svc.create(start_date=date(2025, 3, 31), end_date=date(2024, 4, 1))

    def test_create_raises_on_overlap(self):
        make_financial_year(start_date=date(2024, 4, 1), end_date=date(2025, 3, 31))
        svc = _svc()
        with self.assertRaises(ValidationException):
            svc.create(start_date=date(2024, 6, 1), end_date=date(2024, 12, 31))

    def test_create_with_note(self):
        svc = _svc()
        fy = svc.create(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            note="Test note",
        )
        self.assertEqual(fy.note, "Test note")

    def test_create_sets_created_by(self):
        user = make_user(email="creator@example.com")
        svc = FinancialYearService(user=user)
        fy = svc.create(start_date=date(2024, 4, 1), end_date=date(2025, 3, 31))
        self.assertEqual(fy.created_by, user)


class FinancialYearGetTest(TestCase):
    def test_get_by_code_returns_instance(self):
        fy = make_financial_year()
        result = _svc().get(code=fy.code)
        self.assertEqual(result.pk, fy.pk)

    def test_get_unknown_code_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            _svc().get(code="FY-9999")


class FinancialYearGetActiveTest(TestCase):
    def test_returns_in_progress_fy(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            status=FinancialYearStatus.IN_PROGRESS,
        )
        result = _svc().get_active()
        self.assertEqual(result.pk, fy.pk)

    def test_raises_when_no_active_fy(self):
        make_financial_year(status=FinancialYearStatus.FUTURE)
        with self.assertRaises(NotFoundException):
            _svc().get_active()


class FinancialYearUpdateTest(TestCase):
    def test_update_note(self):
        fy = make_financial_year()
        svc = _svc()
        updated = svc.update(code=fy.code, note="Updated note")
        self.assertEqual(updated.note, "Updated note")

    def test_update_status(self):
        fy = make_financial_year()
        svc = _svc()
        updated = svc.update(code=fy.code, status=FinancialYearStatus.IN_PROGRESS)
        self.assertEqual(updated.status, FinancialYearStatus.IN_PROGRESS)

    def test_update_recalculates_derived_on_date_change(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        svc = _svc()
        updated = svc.update(
            code=fy.code,
            start_date=date(2025, 4, 1),
            end_date=date(2026, 3, 31),
        )
        self.assertEqual(updated.long_fy, "FY2025-2026")
        self.assertEqual(updated.short_fy, "FY25-26")

    def test_update_raises_on_overlap(self):
        make_financial_year(start_date=date(2024, 4, 1), end_date=date(2025, 3, 31))
        fy2 = make_financial_year(
            start_date=date(2025, 4, 1), end_date=date(2026, 3, 31)
        )
        svc = _svc()
        with self.assertRaises(ValidationException):
            svc.update(
                code=fy2.code, start_date=date(2024, 6, 1), end_date=date(2025, 12, 31)
            )

    def test_update_unknown_code_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            _svc().update(code="FY-9999", note="x")


class FinancialYearActivateDeactivateTest(TestCase):
    def test_activate_sets_is_active_true(self):
        fy = make_financial_year(is_active=False)
        svc = _svc()
        result = svc.activate(code=fy.code)
        self.assertTrue(result.is_active)

    def test_deactivate_sets_is_active_false(self):
        fy = make_financial_year(is_active=True)
        svc = _svc()
        result = svc.deactivate(code=fy.code)
        self.assertFalse(result.is_active)

    def test_activate_idempotent(self):
        fy = make_financial_year(is_active=True)
        svc = _svc()
        result = svc.activate(code=fy.code)
        self.assertTrue(result.is_active)


class FinancialYearSetActiveTest(TestCase):
    def test_set_active_changes_status_to_in_progress(self):
        fy = make_financial_year(status=FinancialYearStatus.FUTURE)
        svc = _svc()
        result = svc.set_active(code=fy.code)
        self.assertEqual(result.status, FinancialYearStatus.IN_PROGRESS)

    def test_set_active_idempotent(self):
        fy = make_financial_year(status=FinancialYearStatus.IN_PROGRESS)
        svc = _svc()
        result = svc.set_active(code=fy.code)
        self.assertEqual(result.status, FinancialYearStatus.IN_PROGRESS)

    def test_set_active_unknown_code_raises(self):
        with self.assertRaises(NotFoundException):
            _svc().set_active(code="FY-9999")


class FinancialYearDeleteTest(TestCase):
    def test_delete_removes_record(self):
        fy = make_financial_year()
        code = fy.code
        _svc().delete(code=code)
        self.assertFalse(FinancialYear.objects.filter(code=code).exists())

    def test_delete_unknown_code_raises(self):
        with self.assertRaises(NotFoundException):
            _svc().delete(code="FY-9999")


class FinancialYearInProgressExclusivityTest(TestCase):
    """Only one financial year may be IN_PROGRESS at any time."""

    def test_set_active_retires_existing_in_progress(self):
        old = make_financial_year(
            start_date=date(2023, 4, 1),
            end_date=date(2024, 3, 31),
            status=FinancialYearStatus.IN_PROGRESS,
        )
        new = make_financial_year(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            status=FinancialYearStatus.FUTURE,
        )
        _svc().set_active(code=new.code)
        old.refresh_from_db()
        new.refresh_from_db()
        self.assertEqual(old.status, FinancialYearStatus.COMPLETED)
        self.assertEqual(new.status, FinancialYearStatus.IN_PROGRESS)

    def test_set_active_retires_multiple_in_progress(self):
        fy1 = make_financial_year(
            start_date=date(2022, 4, 1),
            end_date=date(2023, 3, 31),
            status=FinancialYearStatus.IN_PROGRESS,
        )
        fy2 = make_financial_year(
            start_date=date(2023, 4, 1),
            end_date=date(2024, 3, 31),
            status=FinancialYearStatus.IN_PROGRESS,
        )
        target = make_financial_year(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            status=FinancialYearStatus.FUTURE,
        )
        _svc().set_active(code=target.code)
        fy1.refresh_from_db()
        fy2.refresh_from_db()
        target.refresh_from_db()
        self.assertEqual(fy1.status, FinancialYearStatus.COMPLETED)
        self.assertEqual(fy2.status, FinancialYearStatus.COMPLETED)
        self.assertEqual(target.status, FinancialYearStatus.IN_PROGRESS)

    def test_set_active_idempotent_does_not_retire_itself(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            status=FinancialYearStatus.IN_PROGRESS,
        )
        _svc().set_active(code=fy.code)
        fy.refresh_from_db()
        self.assertEqual(fy.status, FinancialYearStatus.IN_PROGRESS)

    def test_update_status_to_in_progress_retires_existing(self):
        old = make_financial_year(
            start_date=date(2023, 4, 1),
            end_date=date(2024, 3, 31),
            status=FinancialYearStatus.IN_PROGRESS,
        )
        new = make_financial_year(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            status=FinancialYearStatus.FUTURE,
        )
        _svc().update(code=new.code, status=FinancialYearStatus.IN_PROGRESS)
        old.refresh_from_db()
        new.refresh_from_db()
        self.assertEqual(old.status, FinancialYearStatus.COMPLETED)
        self.assertEqual(new.status, FinancialYearStatus.IN_PROGRESS)

    def test_create_with_in_progress_status_retires_existing(self):
        old = make_financial_year(
            start_date=date(2023, 4, 1),
            end_date=date(2024, 3, 31),
            status=FinancialYearStatus.IN_PROGRESS,
        )
        svc = _svc()
        svc.create(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            status=FinancialYearStatus.IN_PROGRESS,
        )
        old.refresh_from_db()
        self.assertEqual(old.status, FinancialYearStatus.COMPLETED)
        self.assertEqual(
            FinancialYear.objects.filter(
                status=FinancialYearStatus.IN_PROGRESS
            ).count(),
            1,
        )

    def test_update_to_non_in_progress_does_not_retire_others(self):
        existing = make_financial_year(
            start_date=date(2023, 4, 1),
            end_date=date(2024, 3, 31),
            status=FinancialYearStatus.IN_PROGRESS,
        )
        other = make_financial_year(
            start_date=date(2024, 4, 1),
            end_date=date(2025, 3, 31),
            status=FinancialYearStatus.FUTURE,
        )
        _svc().update(code=other.code, status=FinancialYearStatus.COMPLETED)
        existing.refresh_from_db()
        self.assertEqual(existing.status, FinancialYearStatus.IN_PROGRESS)


class FinancialYearImportServiceTest(TestCase):
    def _import_svc(self):
        return FinancialYearImportService(user=make_user())

    def test_import_valid_rows(self):
        csv = "start_date,end_date\n2024-04-01,2025-03-31\n"
        svc = self._import_svc()
        result = svc.bulk_import(FakeCsvFile(csv))
        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(FinancialYear.objects.count(), 1)

    def test_dry_run_does_not_create(self):
        csv = "start_date,end_date\n2024-04-01,2025-03-31\n"
        svc = self._import_svc()
        result = svc.bulk_import(FakeCsvFile(csv), dry_run=True)
        self.assertTrue(result["dry_run"])
        self.assertEqual(FinancialYear.objects.count(), 0)

    def test_missing_required_columns_raises(self):
        from apps.core.exceptions import ValidationException

        csv = "note\nsome note\n"
        svc = self._import_svc()
        with self.assertRaises(ValidationException):
            svc.bulk_import(FakeCsvFile(csv))

    def test_overlapping_row_reported_as_error(self):
        make_financial_year(start_date=date(2024, 4, 1), end_date=date(2025, 3, 31))
        csv = "start_date,end_date\n2024-06-01,2024-12-31\n"
        svc = self._import_svc()
        result = svc.bulk_import(FakeCsvFile(csv))
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(FinancialYear.objects.count(), 1)

    def test_invalid_date_format_reported(self):
        csv = "start_date,end_date\n01/04/2024,31/03/2025\n"
        svc = self._import_svc()
        result = svc.bulk_import(FakeCsvFile(csv))
        self.assertEqual(len(result["errors"]), 1)
