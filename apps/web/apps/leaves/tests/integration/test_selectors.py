import datetime

from django.test import TestCase

from apps.leaves.models import LeaveDayEntry
from apps.leaves.selectors import (
    get_all_leaves,
    get_day_entries_for_leave,
    get_day_entries_for_member_in_range,
    get_leave_by_code,
    get_leaves_affected_by_location_date_range,
    leave_overlaps,
)
from apps.leaves.tests.factories import make_leave
from apps.locations.tests.factories import make_location
from apps.users.models import UserProfile
from apps.users.tests.factories import make_user


class GetAllLeavesTest(TestCase):
    def test_returns_all_leaves(self):
        user = make_user()
        make_leave(
            member=user,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 6),
        )
        make_leave(
            member=user,
            start_date=datetime.date(2025, 2, 3),
            end_date=datetime.date(2025, 2, 3),
        )
        self.assertEqual(get_all_leaves().count(), 2)

    def test_empty_returns_no_leaves(self):
        self.assertEqual(get_all_leaves().count(), 0)


class GetLeaveByCodeTest(TestCase):
    def test_returns_leave_for_valid_code(self):
        leave = make_leave()
        found = get_leave_by_code(leave.code)
        self.assertEqual(found, leave)

    def test_returns_none_for_unknown_code(self):
        result = get_leave_by_code("LEAVE-99999")
        self.assertIsNone(result)


class LeaveOverlapsTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.leave = make_leave(
            member=self.user,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 10),
        )

    def test_exact_overlap_returns_true(self):
        result = leave_overlaps(
            self.user.pk,
            datetime.date(2025, 1, 6),
            datetime.date(2025, 1, 10),
        )
        self.assertTrue(result)

    def test_partial_overlap_returns_true(self):
        result = leave_overlaps(
            self.user.pk,
            datetime.date(2025, 1, 8),
            datetime.date(2025, 1, 12),
        )
        self.assertTrue(result)

    def test_no_overlap_returns_false(self):
        result = leave_overlaps(
            self.user.pk,
            datetime.date(2025, 1, 13),
            datetime.date(2025, 1, 17),
        )
        self.assertFalse(result)

    def test_exclude_pk_allows_self_overlap(self):
        result = leave_overlaps(
            self.user.pk,
            datetime.date(2025, 1, 6),
            datetime.date(2025, 1, 10),
            exclude_pk=self.leave.pk,
        )
        self.assertFalse(result)

    def test_different_member_no_overlap(self):
        other = make_user(email="other@example.com")
        result = leave_overlaps(
            other.pk,
            datetime.date(2025, 1, 6),
            datetime.date(2025, 1, 10),
        )
        self.assertFalse(result)


class GetLeavesAffectedByLocationDateRangeTest(TestCase):
    def test_returns_leaves_for_matching_location(self):
        location = make_location()
        user = make_user(email="located@example.com")
        UserProfile.objects.create(user=user, location=location)
        leave = make_leave(
            member=user,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 10),
        )
        result = get_leaves_affected_by_location_date_range(
            location_id=location.pk,
            start_date=datetime.date(2025, 1, 8),
            end_date=datetime.date(2025, 1, 8),
        )
        self.assertIn(leave, result)

    def test_excludes_leaves_outside_date_range(self):
        location = make_location()
        user = make_user(email="located2@example.com")
        UserProfile.objects.create(user=user, location=location)
        make_leave(
            member=user,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 10),
        )
        result = get_leaves_affected_by_location_date_range(
            location_id=location.pk,
            start_date=datetime.date(2025, 2, 1),
            end_date=datetime.date(2025, 2, 1),
        )
        self.assertEqual(result.count(), 0)

    def test_excludes_different_location(self):
        loc1 = make_location(city="London")
        loc2 = make_location(city="Paris")
        user = make_user(email="paris@example.com")
        UserProfile.objects.create(user=user, location=loc1)
        make_leave(
            member=user,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 10),
        )
        result = get_leaves_affected_by_location_date_range(
            location_id=loc2.pk,
            start_date=datetime.date(2025, 1, 8),
            end_date=datetime.date(2025, 1, 8),
        )
        self.assertEqual(result.count(), 0)


# ── get_day_entries_for_leave ─────────────────────────────────────────────────


class GetDayEntriesForLeaveTest(TestCase):
    def setUp(self):
        self.leave = make_leave(
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 10),
        )

    def test_returns_entries_for_leave(self):
        e1 = LeaveDayEntry.objects.create(
            leave=self.leave, date=datetime.date(2025, 1, 6)
        )
        e2 = LeaveDayEntry.objects.create(
            leave=self.leave, date=datetime.date(2025, 1, 7)
        )
        qs = get_day_entries_for_leave(self.leave)
        self.assertIn(e1, qs)
        self.assertIn(e2, qs)

    def test_returns_empty_when_no_entries(self):
        qs = get_day_entries_for_leave(self.leave)
        self.assertEqual(qs.count(), 0)

    def test_ordered_by_date_ascending(self):
        LeaveDayEntry.objects.create(leave=self.leave, date=datetime.date(2025, 1, 10))
        LeaveDayEntry.objects.create(leave=self.leave, date=datetime.date(2025, 1, 6))
        dates = list(
            get_day_entries_for_leave(self.leave).values_list("date", flat=True)
        )
        self.assertEqual(dates, sorted(dates))

    def test_excludes_entries_for_other_leave(self):
        other_user = make_user(email="other@example.com")
        other_leave = make_leave(
            member=other_user,
            start_date=datetime.date(2025, 2, 3),
            end_date=datetime.date(2025, 2, 3),
        )
        LeaveDayEntry.objects.create(leave=other_leave, date=datetime.date(2025, 2, 3))
        LeaveDayEntry.objects.create(leave=self.leave, date=datetime.date(2025, 1, 6))
        qs = get_day_entries_for_leave(self.leave)
        self.assertEqual(qs.count(), 1)


# ── get_day_entries_for_member_in_range ──────────────────────────────────────


class GetDayEntriesForMemberInRangeTest(TestCase):
    def setUp(self):
        self.member = make_user(email="range@example.com")
        self.leave = make_leave(
            member=self.member,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 10),
        )
        LeaveDayEntry.objects.create(leave=self.leave, date=datetime.date(2025, 1, 6))
        LeaveDayEntry.objects.create(leave=self.leave, date=datetime.date(2025, 1, 7))
        LeaveDayEntry.objects.create(leave=self.leave, date=datetime.date(2025, 1, 8))

    def test_returns_entries_within_range(self):
        qs = get_day_entries_for_member_in_range(
            self.member.pk,
            datetime.date(2025, 1, 6),
            datetime.date(2025, 1, 8),
        )
        self.assertEqual(qs.count(), 3)

    def test_excludes_entries_outside_range(self):
        qs = get_day_entries_for_member_in_range(
            self.member.pk,
            datetime.date(2025, 1, 9),
            datetime.date(2025, 1, 10),
        )
        self.assertEqual(qs.count(), 0)

    def test_excludes_entries_for_different_member(self):
        other = make_user(email="other2@example.com")
        qs = get_day_entries_for_member_in_range(
            other.pk,
            datetime.date(2025, 1, 6),
            datetime.date(2025, 1, 8),
        )
        self.assertEqual(qs.count(), 0)

    def test_ordered_by_date_ascending(self):
        dates = list(
            get_day_entries_for_member_in_range(
                self.member.pk,
                datetime.date(2025, 1, 6),
                datetime.date(2025, 1, 8),
            ).values_list("date", flat=True)
        )
        self.assertEqual(dates, sorted(dates))

    def test_select_related_leave_avoids_extra_queries(self):
        entries = list(
            get_day_entries_for_member_in_range(
                self.member.pk,
                datetime.date(2025, 1, 6),
                datetime.date(2025, 1, 8),
            )
        )
        with self.assertNumQueries(0):
            for entry in entries:
                _ = entry.leave
