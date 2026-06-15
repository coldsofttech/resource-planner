import datetime

from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.holidays.models import Holiday
from apps.holidays.tests.factories import make_holiday
from apps.locations.tests.factories import make_location
from apps.users.tests.factories import make_user

LIST_URL = "/api/v1/holidays/"
STATS_URL = "/api/v1/holidays/stats/"
OPTIONS_URL = "/api/v1/holidays/options/"
DETAIL_URL = "/api/v1/holidays/{}/"


# ── GET /holidays/ ────────────────────────────────────────────────────────────


class HolidayListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.location = make_location()
        make_holiday(location=self.location, date=datetime.date(2025, 12, 25))

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

    def test_page_size_limits_results(self):
        loc2 = make_location(city="Paris")
        make_holiday(location=loc2, date=datetime.date(2025, 12, 25))
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"page_size": 1})
        self.assertEqual(len(response.data["data"]["results"]), 1)


# ── GET /holidays/<code>/ ─────────────────────────────────────────────────────


class HolidayRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.holiday = make_holiday()

    def test_unauthenticated_returns_401(self):
        response = self.client.get(DETAIL_URL.format(self.holiday.code))
        self.assertEqual(response.status_code, 401)

    def test_authenticated_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.holiday.code))
        self.assertEqual(response.status_code, 200)

    def test_unknown_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format("HOL-99999"))
        self.assertEqual(response.status_code, 404)

    def test_response_contains_code(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.holiday.code))
        self.assertEqual(response.data["data"]["code"], self.holiday.code)


# ── POST /holidays/ ───────────────────────────────────────────────────────────


class HolidayCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.location = make_location()

    def _payload(self, **overrides):
        data = {
            "name": "Christmas Day",
            "date": "2025-12-25",
            "location_code": self.location.code,
        }
        data.update(overrides)
        return data

    def test_unauthenticated_returns_401(self):
        response = self.client.post(LIST_URL, self._payload(), format="json")
        self.assertEqual(response.status_code, 401)

    def test_valid_create_returns_201(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, self._payload(), format="json")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Holiday.objects.count(), 1)

    def test_missing_name_returns_400(self):
        self.client.force_authenticate(user=self.user)
        payload = self._payload()
        del payload["name"]
        response = self.client.post(LIST_URL, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_missing_date_returns_400(self):
        self.client.force_authenticate(user=self.user)
        payload = self._payload()
        del payload["date"]
        response = self.client.post(LIST_URL, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_missing_location_code_returns_400(self):
        self.client.force_authenticate(user=self.user)
        payload = self._payload()
        del payload["location_code"]
        response = self.client.post(LIST_URL, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_duplicate_location_date_returns_409(self):
        make_holiday(location=self.location, date=datetime.date(2025, 12, 25))
        self.client.force_authenticate(user=self.user)
        response = self.client.post(LIST_URL, self._payload(), format="json")
        self.assertEqual(response.status_code, 409)

    def test_unknown_location_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            LIST_URL, self._payload(location_code="LOC-99999"), format="json"
        )
        self.assertEqual(response.status_code, 404)


# ── PATCH /holidays/<code>/ ───────────────────────────────────────────────────


class HolidayUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.location = make_location()
        self.holiday = make_holiday(
            location=self.location, date=datetime.date(2025, 12, 25)
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.patch(
            DETAIL_URL.format(self.holiday.code), {}, format="json"
        )
        self.assertEqual(response.status_code, 401)

    def test_update_name_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.holiday.code),
            {"name": "Updated Name"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.holiday.refresh_from_db()
        self.assertEqual(self.holiday.name, "Updated Name")

    def test_unknown_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(DETAIL_URL.format("HOL-99999"), {}, format="json")
        self.assertEqual(response.status_code, 404)

    def test_conflict_location_date_returns_409(self):
        other_loc = make_location(city="Paris")
        make_holiday(location=other_loc, date=datetime.date(2025, 12, 26))
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(
            DETAIL_URL.format(self.holiday.code),
            {"location_code": other_loc.code, "date": "2025-12-26"},
            format="json",
        )
        self.assertEqual(response.status_code, 409)


# ── DELETE /holidays/<code>/ ──────────────────────────────────────────────────


class HolidayDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.holiday = make_holiday()

    def test_unauthenticated_returns_401(self):
        response = self.client.delete(DETAIL_URL.format(self.holiday.code))
        self.assertEqual(response.status_code, 401)

    def test_authenticated_returns_204(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format(self.holiday.code))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Holiday.objects.filter(pk=self.holiday.pk).exists())

    def test_unknown_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(DETAIL_URL.format("HOL-99999"))
        self.assertEqual(response.status_code, 404)


# ── GET /holidays/options/ ────────────────────────────────────────────────────


class HolidayOptionsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.status_code, 401)

    def test_authenticated_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.status_code, 200)

    def test_response_contains_items(self):
        make_holiday()
        self.client.force_authenticate(user=self.user)
        response = self.client.get(OPTIONS_URL)
        self.assertIn("items", response.data["data"])


# ── GET /holidays/stats/ ──────────────────────────────────────────────────────


class HolidayStatsAPITest(TestCase):
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

    def test_response_contains_total(self):
        make_holiday()
        self.client.force_authenticate(user=self.user)
        response = self.client.get(STATS_URL)
        self.assertIn("total", response.data["data"])
