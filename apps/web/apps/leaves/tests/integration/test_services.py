import datetime
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase

from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.leaves.engine import LeaveEngine
from apps.leaves.models import Leave, LeaveDayEntry
from apps.leaves.services import LeaveImportService, LeaveService
from apps.leaves.tests.factories import make_csv_file, make_leave
from apps.users.models import UserProfile
from apps.users.tests.factories import make_user


def _make_service(user=None):
    if user is None:
        user = make_user(email="actor@example.com")
    return LeaveService(user=user)


def _make_member_with_profile(email="member@example.com"):
    user = make_user(email=email)
    UserProfile.objects.create(user=user)
    return user


# ── LeaveService.create ───────────────────────────────────────────────────────


class LeaveServiceCreateTest(TestCase):
    def test_creates_leave_with_valid_data(self):
        member = _make_member_with_profile()
        svc = _make_service()
        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days", return_value=Decimal("5")
        ):
            leave = svc.create(
                member_code=member.profile.code,
                start_date=datetime.date(2025, 1, 6),
                end_date=datetime.date(2025, 1, 10),
            )
        self.assertEqual(leave.member, member)
        self.assertEqual(leave.days, Decimal("5"))
        self.assertFalse(leave.is_half_day)

    def test_creates_half_day_leave(self):
        member = _make_member_with_profile(email="half@example.com")
        svc = _make_service()
        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days", return_value=Decimal("0.5")
        ):
            leave = svc.create(
                member_code=member.profile.code,
                start_date=datetime.date(2025, 1, 6),
                end_date=datetime.date(2025, 1, 6),
                is_half_day=True,
                half_day_period="AM",
            )
        self.assertTrue(leave.is_half_day)
        self.assertEqual(leave.half_day_period, "AM")
        self.assertEqual(leave.days, Decimal("0.5"))

    def test_unknown_member_code_raises_not_found(self):
        svc = _make_service()
        with self.assertRaises(NotFoundException):
            svc.create(
                member_code="UNKNOWN-999",
                start_date=datetime.date(2025, 1, 6),
                end_date=datetime.date(2025, 1, 10),
            )

    def test_overlapping_leave_raises_already_exists(self):
        member = _make_member_with_profile(email="overlap@example.com")
        make_leave(
            member=member,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 10),
        )
        svc = _make_service()
        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days", return_value=Decimal("1")
        ):
            with self.assertRaises(AlreadyExistsException):
                svc.create(
                    member_code=member.profile.code,
                    start_date=datetime.date(2025, 1, 8),
                    end_date=datetime.date(2025, 1, 12),
                )

    def test_end_before_start_raises_validation(self):
        member = _make_member_with_profile(email="early@example.com")
        svc = _make_service()
        with self.assertRaises(ValidationException):
            svc.create(
                member_code=member.profile.code,
                start_date=datetime.date(2025, 1, 10),
                end_date=datetime.date(2025, 1, 6),
            )

    def test_half_day_different_dates_raises_validation(self):
        member = _make_member_with_profile(email="halfd@example.com")
        svc = _make_service()
        with self.assertRaises(ValidationException):
            svc.create(
                member_code=member.profile.code,
                start_date=datetime.date(2025, 1, 6),
                end_date=datetime.date(2025, 1, 7),
                is_half_day=True,
            )

    def test_half_day_period_cleared_when_not_half_day(self):
        member = _make_member_with_profile(email="clearperiod@example.com")
        svc = _make_service()
        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days", return_value=Decimal("5")
        ):
            leave = svc.create(
                member_code=member.profile.code,
                start_date=datetime.date(2025, 1, 6),
                end_date=datetime.date(2025, 1, 10),
                is_half_day=False,
                half_day_period="AM",
            )
        self.assertIsNone(leave.half_day_period)


# ── LeaveService.update ───────────────────────────────────────────────────────


class LeaveServiceUpdateTest(TestCase):
    def setUp(self):
        self.member = _make_member_with_profile(email="updmember@example.com")
        self.svc = _make_service()
        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days", return_value=Decimal("5")
        ):
            self.leave = self.svc.create(
                member_code=self.member.profile.code,
                start_date=datetime.date(2025, 1, 6),
                end_date=datetime.date(2025, 1, 10),
            )

    def test_update_note(self):
        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days", return_value=Decimal("5")
        ):
            leave = self.svc.update(code=self.leave.code, note="Updated note")
        self.assertEqual(leave.note, "Updated note")

    def test_update_end_date_recalculates_days(self):
        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days", return_value=Decimal("3")
        ):
            leave = self.svc.update(
                code=self.leave.code,
                end_date=datetime.date(2025, 1, 8),
            )
        self.assertEqual(leave.days, Decimal("3"))

    def test_update_unknown_code_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            self.svc.update(code="LEAVE-99999", note="x")

    def test_update_to_overlapping_raises_already_exists(self):
        member = self.member
        make_leave(
            member=member,
            start_date=datetime.date(2025, 2, 3),
            end_date=datetime.date(2025, 2, 7),
        )
        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days", return_value=Decimal("3")
        ):
            with self.assertRaises(AlreadyExistsException):
                self.svc.update(
                    code=self.leave.code,
                    start_date=datetime.date(2025, 2, 3),
                    end_date=datetime.date(2025, 2, 7),
                )


# ── LeaveService.delete ───────────────────────────────────────────────────────


class LeaveServiceDeleteTest(TestCase):
    def test_delete_removes_leave(self):
        leave = make_leave()
        svc = _make_service()
        svc.delete(code=leave.code)
        self.assertFalse(Leave.objects.filter(pk=leave.pk).exists())

    def test_delete_unknown_code_raises_not_found(self):
        svc = _make_service()
        with self.assertRaises(NotFoundException):
            svc.delete(code="LEAVE-99999")


# ── LeaveImportService ────────────────────────────────────────────────────────


class LeaveImportServiceTest(TestCase):
    def setUp(self):
        self.member = _make_member_with_profile(email="import@example.com")
        self.member_code = self.member.profile.code

    def _make_svc(self):
        actor = make_user(email="importactor@example.com")
        return LeaveImportService(user=actor)

    def test_dry_run_does_not_create_leave(self):
        csv_content = (
            "member_code,start_date,end_date\n"
            f"{self.member_code},2025-05-01,2025-05-02\n"
        )
        svc = self._make_svc()
        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days", return_value=Decimal("2")
        ):
            result = svc.bulk_import(make_csv_file(csv_content), dry_run=True)
        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["errors"]), 0)
        self.assertFalse(Leave.objects.exists())

    def test_valid_import_creates_leave(self):
        csv_content = (
            "member_code,start_date,end_date\n"
            f"{self.member_code},2025-05-01,2025-05-02\n"
        )
        svc = self._make_svc()
        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days", return_value=Decimal("2")
        ):
            result = svc.bulk_import(make_csv_file(csv_content), dry_run=False)
        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["errors"]), 0)
        self.assertEqual(Leave.objects.count(), 1)

    def test_missing_required_column_raises_validation(self):
        from apps.core.exceptions import ValidationException

        csv_content = "member_code,start_date\nMBR-1,2025-01-06\n"
        svc = self._make_svc()
        with self.assertRaises(ValidationException):
            svc.bulk_import(make_csv_file(csv_content))

    def test_unknown_member_code_produces_error(self):
        csv_content = (
            "member_code,start_date,end_date\nUNKNOWN-999,2025-05-01,2025-05-02\n"
        )
        svc = self._make_svc()
        result = svc.bulk_import(make_csv_file(csv_content), dry_run=False)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(Leave.objects.count(), 0)

    def test_invalid_date_format_produces_error(self):
        csv_content = (
            "member_code,start_date,end_date\n"
            f"{self.member_code},01-05-2025,02-05-2025\n"
        )
        svc = self._make_svc()
        result = svc.bulk_import(make_csv_file(csv_content), dry_run=False)
        self.assertGreater(len(result["errors"]), 0)


# ── sync_leave_day_entries ────────────────────────────────────────────────────


class SyncLeaveDayEntriesTest(TestCase):
    def setUp(self):
        self.member = _make_member_with_profile(email="sync@example.com")

    def test_full_day_leave_creates_entries_for_working_dates(self):
        leave = make_leave(
            member=self.member,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 10),
        )
        with patch(
            "apps.leaves.engine.LeaveEngine.get_working_dates",
            return_value=[
                datetime.date(2025, 1, 6),
                datetime.date(2025, 1, 7),
                datetime.date(2025, 1, 8),
                datetime.date(2025, 1, 9),
                datetime.date(2025, 1, 10),
            ],
        ):
            LeaveEngine.sync_day_entries(leave)

        entries = LeaveDayEntry.objects.filter(leave=leave).order_by("date")
        self.assertEqual(entries.count(), 5)
        self.assertFalse(entries.first().is_half_day)

    def test_half_day_leave_creates_single_entry_with_flag(self):
        leave = make_leave(
            member=self.member,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 6),
            is_half_day=True,
            half_day_period="AM",
            days="0.5",
        )
        LeaveEngine.sync_day_entries(leave)

        entries = LeaveDayEntry.objects.filter(leave=leave)
        self.assertEqual(entries.count(), 1)
        self.assertTrue(entries.first().is_half_day)
        self.assertEqual(entries.first().date, datetime.date(2025, 1, 6))

    def test_sync_deletes_existing_entries_before_recreating(self):
        leave = make_leave(
            member=self.member,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 8),
        )
        LeaveDayEntry.objects.create(leave=leave, date=datetime.date(2025, 1, 6))
        LeaveDayEntry.objects.create(leave=leave, date=datetime.date(2025, 1, 7))

        with patch(
            "apps.leaves.engine.LeaveEngine.get_working_dates",
            return_value=[datetime.date(2025, 1, 6)],
        ):
            LeaveEngine.sync_day_entries(leave)

        entries = LeaveDayEntry.objects.filter(leave=leave)
        self.assertEqual(entries.count(), 1)

    def test_no_working_dates_leaves_no_entries(self):
        leave = make_leave(
            member=self.member,
            start_date=datetime.date(2025, 1, 4),
            end_date=datetime.date(2025, 1, 5),
        )
        with patch(
            "apps.leaves.engine.LeaveEngine.get_working_dates",
            return_value=[],
        ):
            LeaveEngine.sync_day_entries(leave)

        self.assertEqual(LeaveDayEntry.objects.filter(leave=leave).count(), 0)

    def test_service_create_syncs_day_entries(self):
        svc = _make_service()
        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days", return_value=Decimal("3")
        ):
            with patch(
                "apps.leaves.engine.LeaveEngine.get_working_dates",
                return_value=[
                    datetime.date(2025, 1, 6),
                    datetime.date(2025, 1, 7),
                    datetime.date(2025, 1, 8),
                ],
            ):
                leave = svc.create(
                    member_code=self.member.profile.code,
                    start_date=datetime.date(2025, 1, 6),
                    end_date=datetime.date(2025, 1, 8),
                )

        self.assertEqual(LeaveDayEntry.objects.filter(leave=leave).count(), 3)

    def test_service_update_resyncs_day_entries(self):
        svc = _make_service()
        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days", return_value=Decimal("3")
        ):
            with patch(
                "apps.leaves.engine.LeaveEngine.get_working_dates",
                return_value=[
                    datetime.date(2025, 1, 6),
                    datetime.date(2025, 1, 7),
                    datetime.date(2025, 1, 8),
                ],
            ):
                leave = svc.create(
                    member_code=self.member.profile.code,
                    start_date=datetime.date(2025, 1, 6),
                    end_date=datetime.date(2025, 1, 8),
                )

        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days", return_value=Decimal("1")
        ):
            with patch(
                "apps.leaves.engine.LeaveEngine.get_working_dates",
                return_value=[datetime.date(2025, 1, 6)],
            ):
                svc.update(code=leave.code, end_date=datetime.date(2025, 1, 6))

        self.assertEqual(LeaveDayEntry.objects.filter(leave=leave).count(), 1)

    def test_service_delete_removes_day_entries(self):
        leave = make_leave(member=self.member)
        LeaveDayEntry.objects.create(leave=leave, date=datetime.date(2025, 1, 6))
        svc = _make_service()
        svc.delete(code=leave.code)
        self.assertEqual(LeaveDayEntry.objects.filter(leave=leave).count(), 0)
