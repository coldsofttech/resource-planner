import datetime
from decimal import Decimal

from django.db import IntegrityError
from django.test import TestCase

from apps.leaves.models import Leave, LeaveDayEntry
from apps.leaves.tests.factories import make_leave
from apps.users.tests.factories import make_user


class LeaveCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        leave = make_leave()
        self.assertTrue(leave.code.startswith("LEAVE-"))

    def test_code_contains_pk(self):
        leave = make_leave()
        self.assertEqual(leave.code, f"LEAVE-{leave.pk}")

    def test_codes_are_unique(self):
        user = make_user()
        l1 = make_leave(
            member=user,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 6),
        )
        l2 = make_leave(
            member=user,
            start_date=datetime.date(2025, 2, 3),
            end_date=datetime.date(2025, 2, 3),
        )
        self.assertNotEqual(l1.code, l2.code)


class LeaveFieldDefaultsTest(TestCase):
    def test_is_half_day_defaults_false(self):
        leave = make_leave()
        self.assertFalse(leave.is_half_day)

    def test_half_day_period_nullable(self):
        leave = make_leave()
        self.assertIsNone(leave.half_day_period)

    def test_note_defaults_empty(self):
        leave = make_leave()
        self.assertEqual(leave.note, "")

    def test_days_stores_value(self):
        leave = make_leave(days="3")
        leave.refresh_from_db()
        self.assertEqual(leave.days, Decimal("3"))

    def test_half_day_stores_period(self):
        leave = make_leave(
            is_half_day=True,
            half_day_period="AM",
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 6),
            days="0.5",
        )
        self.assertEqual(leave.half_day_period, "AM")


class LeaveAuditableTest(TestCase):
    def test_created_at_is_set(self):
        leave = make_leave()
        self.assertIsNotNone(leave.created_at)

    def test_updated_at_is_set(self):
        leave = make_leave()
        self.assertIsNotNone(leave.updated_at)

    def test_created_by_nullable(self):
        leave = make_leave()
        self.assertIsNone(leave.created_by)

    def test_created_by_stores_user(self):
        actor = make_user(email="actor@example.com")
        member = make_user(email="member@example.com")
        leave = Leave.objects.create(
            member=member,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 10),
            days="5",
            created_by=actor,
            updated_by=actor,
        )
        self.assertEqual(leave.created_by, actor)


class LeaveOrderingTest(TestCase):
    def test_ordered_by_start_date_descending(self):
        user = make_user()
        make_leave(
            member=user,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 10),
        )
        make_leave(
            member=user,
            start_date=datetime.date(2025, 3, 3),
            end_date=datetime.date(2025, 3, 7),
        )
        leaves = list(Leave.objects.values_list("start_date", flat=True))
        self.assertEqual(leaves, sorted(leaves, reverse=True))


# ── LeaveDayEntry model ────────────────────────────────────────────────────────


class LeaveDayEntryFieldDefaultsTest(TestCase):
    def setUp(self):
        self.leave = make_leave()

    def test_is_half_day_defaults_false(self):
        entry = LeaveDayEntry.objects.create(
            leave=self.leave,
            date=datetime.date(2025, 1, 6),
        )
        self.assertFalse(entry.is_half_day)

    def test_created_at_is_set_automatically(self):
        entry = LeaveDayEntry.objects.create(
            leave=self.leave,
            date=datetime.date(2025, 1, 6),
        )
        self.assertIsNotNone(entry.created_at)

    def test_str_representation(self):
        entry = LeaveDayEntry.objects.create(
            leave=self.leave,
            date=datetime.date(2025, 1, 6),
        )
        self.assertEqual(str(entry), f"{self.leave.pk} — 2025-01-06")

    def test_half_day_flag_stored(self):
        entry = LeaveDayEntry.objects.create(
            leave=self.leave,
            date=datetime.date(2025, 1, 6),
            is_half_day=True,
        )
        self.assertTrue(entry.is_half_day)


class LeaveDayEntryConstraintTest(TestCase):
    def setUp(self):
        self.leave = make_leave()

    def test_duplicate_leave_and_date_raises_integrity_error(self):
        LeaveDayEntry.objects.create(
            leave=self.leave,
            date=datetime.date(2025, 1, 6),
        )
        with self.assertRaises(IntegrityError):
            LeaveDayEntry.objects.create(
                leave=self.leave,
                date=datetime.date(2025, 1, 6),
            )

    def test_same_date_different_leave_is_allowed(self):
        leave2 = make_leave(
            member=self.leave.member,
            start_date=datetime.date(2025, 2, 3),
            end_date=datetime.date(2025, 2, 3),
        )
        LeaveDayEntry.objects.create(leave=self.leave, date=datetime.date(2025, 1, 6))
        LeaveDayEntry.objects.create(leave=leave2, date=datetime.date(2025, 2, 3))
        self.assertEqual(LeaveDayEntry.objects.count(), 2)

    def test_same_leave_different_dates_allowed(self):
        LeaveDayEntry.objects.create(leave=self.leave, date=datetime.date(2025, 1, 6))
        LeaveDayEntry.objects.create(leave=self.leave, date=datetime.date(2025, 1, 7))
        self.assertEqual(LeaveDayEntry.objects.filter(leave=self.leave).count(), 2)


class LeaveDayEntryOrderingTest(TestCase):
    def test_ordered_by_date_ascending(self):
        leave = make_leave()
        LeaveDayEntry.objects.create(leave=leave, date=datetime.date(2025, 1, 10))
        LeaveDayEntry.objects.create(leave=leave, date=datetime.date(2025, 1, 6))
        LeaveDayEntry.objects.create(leave=leave, date=datetime.date(2025, 1, 8))
        dates = list(
            LeaveDayEntry.objects.filter(leave=leave).values_list("date", flat=True)
        )
        self.assertEqual(dates, sorted(dates))


class LeaveDayEntryCascadeDeleteTest(TestCase):
    def test_entries_deleted_when_leave_deleted(self):
        leave = make_leave()
        LeaveDayEntry.objects.create(leave=leave, date=datetime.date(2025, 1, 6))
        LeaveDayEntry.objects.create(leave=leave, date=datetime.date(2025, 1, 7))
        leave.delete()
        self.assertEqual(LeaveDayEntry.objects.count(), 0)
