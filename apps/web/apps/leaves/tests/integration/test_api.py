import datetime
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.leaves.models import Leave
from apps.leaves.tests.factories import make_leave
from apps.users.models import UserProfile
from apps.users.tests.factories import make_user

LIST_URL = "/api/v1/leaves/"
STATS_URL = "/api/v1/leaves/stats/"
DETAIL_URL = "/api/v1/leaves/{}/"
IMPORT_URL = "/api/v1/leaves/import/"
IMPORT_SPECS_URL = "/api/v1/leaves/import/specs/"
IMPORT_SAMPLE_URL = "/api/v1/leaves/import/sample/"
EXPORT_URL = "/api/v1/leaves/export/"
EXPORT_SPECS_URL = "/api/v1/leaves/export/specs/"


def _make_member(email="member@example.com"):
    user = make_user(email=email)
    UserProfile.objects.create(user=user)
    return user


# ── GET /leaves/ ──────────────────────────────────────────────────────────────


class LeaveListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        member = _make_member()
        make_leave(
            member=member,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 10),
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 401)

    def test_authenticated_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 200)

    def test_response_has_pagination(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertIn("pagination", response.data["data"])

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertTrue(response.data["success"])

    def test_page_size_param_limits_results(self):
        member2 = _make_member(email="member2@example.com")
        make_leave(
            member=member2,
            start_date=datetime.date(2025, 2, 3),
            end_date=datetime.date(2025, 2, 7),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"page_size": 1})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]["results"]), 1)


# ── GET /leaves/<code>/ ───────────────────────────────────────────────────────


class LeaveRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        member = _make_member()
        self.leave = make_leave(member=member)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(DETAIL_URL.format(self.leave.code))
        self.assertEqual(response.status_code, 401)

    def test_authenticated_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.leave.code))
        self.assertEqual(response.status_code, 200)

    def test_unknown_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format("LEAVE-99999"))
        self.assertEqual(response.status_code, 404)

    def test_response_contains_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.leave.code))
        self.assertEqual(response.data["data"]["code"], self.leave.code)


# ── POST /leaves/ ─────────────────────────────────────────────────────────────


class LeaveCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.member = _make_member()

    def _payload(self, **overrides):
        data = {
            "member_code": self.member.profile.code,
            "start_date": "2025-03-03",
            "end_date": "2025-03-07",
        }
        data.update(overrides)
        return data

    def test_unauthenticated_returns_401(self):
        response = self.client.post(LIST_URL, self._payload(), format="json")
        self.assertEqual(response.status_code, 401)

    def test_valid_create_returns_201(self):
        self.client.force_authenticate(user=self.user)
        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days", return_value=Decimal("5")
        ):
            response = self.client.post(LIST_URL, self._payload(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Leave.objects.count(), 1)

    def test_missing_member_code_returns_400(self):
        self.client.force_authenticate(user=self.user)
        payload = self._payload()
        del payload["member_code"]
        response = self.client.post(LIST_URL, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_overlapping_leave_returns_409(self):
        make_leave(
            member=self.member,
            start_date=datetime.date(2025, 3, 3),
            end_date=datetime.date(2025, 3, 7),
        )
        self.client.force_authenticate(user=self.user)
        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days", return_value=Decimal("1")
        ):
            response = self.client.post(LIST_URL, self._payload(), format="json")
        self.assertEqual(response.status_code, 409)

    def test_invalid_date_order_returns_422(self):
        self.client.force_authenticate(user=self.user)
        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days", return_value=Decimal("1")
        ):
            response = self.client.post(
                LIST_URL,
                self._payload(start_date="2025-03-10", end_date="2025-03-05"),
                format="json",
            )
        self.assertEqual(response.status_code, 422)


# ── PATCH /leaves/<code>/ ─────────────────────────────────────────────────────


class LeaveUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.member = _make_member()
        self.leave = make_leave(
            member=self.member,
            start_date=datetime.date(2025, 1, 6),
            end_date=datetime.date(2025, 1, 10),
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.patch(
            DETAIL_URL.format(self.leave.code), {}, format="json"
        )
        self.assertEqual(response.status_code, 401)

    def test_update_note_returns_200(self):
        self.client.force_authenticate(user=self.user)
        with patch(
            "apps.leaves.engine.LeaveEngine.calculate_days", return_value=Decimal("5")
        ):
            response = self.client.patch(
                DETAIL_URL.format(self.leave.code),
                {"note": "Updated"},
                format="json",
            )
        self.assertEqual(response.status_code, 200)
        self.leave.refresh_from_db()
        self.assertEqual(self.leave.note, "Updated")

    def test_unknown_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format("LEAVE-99999"), {}, format="json"
        )
        self.assertEqual(response.status_code, 404)


# ── DELETE /leaves/<code>/ ────────────────────────────────────────────────────


class LeaveDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.member = _make_member()
        self.leave = make_leave(member=self.member)

    def test_unauthenticated_returns_401(self):
        response = self.client.delete(DETAIL_URL.format(self.leave.code))
        self.assertEqual(response.status_code, 401)

    def test_delete_returns_204(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format(self.leave.code))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Leave.objects.filter(pk=self.leave.pk).exists())

    def test_unknown_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format("LEAVE-99999"))
        self.assertEqual(response.status_code, 404)


# ── GET /leaves/stats/ ────────────────────────────────────────────────────────


class LeaveStatsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(STATS_URL)
        self.assertEqual(response.status_code, 401)

    def test_authenticated_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(STATS_URL)
        self.assertEqual(response.status_code, 200)


# ── GET /leaves/import/specs/ & /import/sample/ ───────────────────────────────


class LeaveImportSpecsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_import_specs_unauthenticated_returns_401(self):
        response = self.client.get(IMPORT_SPECS_URL)
        self.assertEqual(response.status_code, 401)

    def test_import_specs_authenticated_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(IMPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)

    def test_import_sample_returns_csv(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(IMPORT_SAMPLE_URL)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/csv", response.get("Content-Type", ""))


# ── GET /leaves/export/specs/ ─────────────────────────────────────────────────


class LeaveExportSpecsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_export_specs_unauthenticated_returns_401(self):
        response = self.client.get(EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 401)

    def test_export_specs_authenticated_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)
