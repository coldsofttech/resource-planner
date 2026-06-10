import datetime

from django.test import TestCase

from apps.leaves.serializers import LeaveDetailSerializer, LeaveListSerializer
from apps.leaves.tests.factories import make_leave
from apps.users.tests.factories import make_user


class LeaveListSerializerOutputTest(TestCase):
    def test_contains_expected_fields(self):
        leave = make_leave()
        s = LeaveListSerializer(leave)
        self.assertIn("code", s.data)
        self.assertIn("member", s.data)
        self.assertIn("start_date", s.data)
        self.assertIn("end_date", s.data)
        self.assertIn("is_half_day", s.data)
        self.assertIn("half_day_period", s.data)
        self.assertIn("half_day_period_display", s.data)
        self.assertIn("days", s.data)

    def test_member_brief_serializer_contains_email(self):
        user = make_user(email="member@example.com")
        leave = make_leave(member=user)
        s = LeaveListSerializer(leave)
        self.assertEqual(s.data["member"]["email"], "member@example.com")

    def test_half_day_period_display_none_when_not_half_day(self):
        leave = make_leave()
        s = LeaveListSerializer(leave)
        self.assertIsNone(s.data["half_day_period_display"])

    def test_half_day_period_display_when_half_day(self):
        leave = make_leave(
            is_half_day=True,
            half_day_period="AM",
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 6),
            days="0.5",
        )
        s = LeaveListSerializer(leave)
        self.assertIsNotNone(s.data["half_day_period_display"])


class LeaveDetailSerializerOutputTest(TestCase):
    def test_contains_audit_fields(self):
        leave = make_leave()
        s = LeaveDetailSerializer(leave)
        self.assertIn("created_at", s.data)
        self.assertIn("updated_at", s.data)

    def test_code_matches_leave_code(self):
        leave = make_leave()
        s = LeaveDetailSerializer(leave)
        self.assertEqual(s.data["code"], leave.code)
