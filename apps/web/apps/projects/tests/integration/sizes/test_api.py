from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.users.tests.factories import make_user

GET_URL = "/api/v1/projects/sizes/"
PATCH_URL = "/api/v1/projects/sizes/"

_VALID_PAYLOAD = {
    "xs_max_amount": 15000,
    "s_max_amount": 50000,
    "m_max_amount": 150000,
    "l_max_amount": 400000,
}

_VALID_BUDGET_PAYLOAD = {
    "budget_risk_threshold": 10.0,
    "xs_budget_variance": 0.5,
    "s_budget_variance": 0.5,
    "m_budget_variance": 0.5,
    "l_budget_variance": 1.0,
    "xl_budget_variance": 1.0,
}


# ── GET /api/v1/projects/sizes/ ───────────────────────────────────────────────


class ProjectSizeConfigGetAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(GET_URL)
        self.assertEqual(response.status_code, 401)

    def test_authenticated_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GET_URL)
        self.assertEqual(response.status_code, 200)

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GET_URL)
        self.assertTrue(response.data["success"])

    def test_response_contains_all_size_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GET_URL)
        data = response.data["data"]
        for field in ("xs_max_amount", "s_max_amount", "m_max_amount", "l_max_amount"):
            self.assertIn(field, data)

    def test_response_contains_budget_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GET_URL)
        data = response.data["data"]
        for field in (
            "budget_risk_threshold",
            "xs_budget_variance",
            "s_budget_variance",
            "m_budget_variance",
            "l_budget_variance",
            "xl_budget_variance",
        ):
            self.assertIn(field, data)

    def test_default_size_values_are_positive_integers(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GET_URL)
        data = response.data["data"]
        for field in ("xs_max_amount", "s_max_amount", "m_max_amount", "l_max_amount"):
            self.assertIsInstance(data[field], int)
            self.assertGreater(data[field], 0)

    def test_default_budget_values_are_non_negative_floats(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GET_URL)
        data = response.data["data"]
        for field in (
            "budget_risk_threshold",
            "xs_budget_variance",
            "s_budget_variance",
            "m_budget_variance",
            "l_budget_variance",
            "xl_budget_variance",
        ):
            self.assertIsInstance(data[field], float)
            self.assertGreaterEqual(data[field], 0)

    def test_default_values_are_in_ascending_order(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(GET_URL)
        data = response.data["data"]
        self.assertLess(data["xs_max_amount"], data["s_max_amount"])
        self.assertLess(data["s_max_amount"], data["m_max_amount"])
        self.assertLess(data["m_max_amount"], data["l_max_amount"])


# ── PATCH /api/v1/projects/sizes/ ─────────────────────────────────────────────


class ProjectSizeConfigPatchAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)

    def test_unauthenticated_returns_401(self):
        response = self.client.patch(PATCH_URL, _VALID_PAYLOAD, format="json")
        self.assertEqual(response.status_code, 401)

    def test_valid_size_payload_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(PATCH_URL, _VALID_PAYLOAD, format="json")
        self.assertEqual(response.status_code, 200)

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(PATCH_URL, _VALID_PAYLOAD, format="json")
        self.assertTrue(response.data["success"])

    def test_updated_size_values_reflected_in_response(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(PATCH_URL, _VALID_PAYLOAD, format="json")
        data = response.data["data"]
        self.assertEqual(data["xs_max_amount"], 15000)
        self.assertEqual(data["s_max_amount"], 50000)
        self.assertEqual(data["m_max_amount"], 150000)
        self.assertEqual(data["l_max_amount"], 400000)

    def test_updated_size_values_persist_on_subsequent_get(self):
        self.client.force_authenticate(user=self.user)
        self.client.patch(PATCH_URL, _VALID_PAYLOAD, format="json")
        response = self.client.get(GET_URL)
        data = response.data["data"]
        self.assertEqual(data["xs_max_amount"], 15000)
        self.assertEqual(data["l_max_amount"], 400000)

    def test_response_contains_message(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(PATCH_URL, _VALID_PAYLOAD, format="json")
        self.assertIn("message", response.data)
        self.assertIsNotNone(response.data["message"])

    def test_xs_greater_than_s_returns_400(self):
        self.client.force_authenticate(user=self.user)
        payload = {**_VALID_PAYLOAD, "xs_max_amount": 60000, "s_max_amount": 50000}
        response = self.client.patch(PATCH_URL, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_xs_equal_to_s_returns_400(self):
        self.client.force_authenticate(user=self.user)
        payload = {**_VALID_PAYLOAD, "xs_max_amount": 50000, "s_max_amount": 50000}
        response = self.client.patch(PATCH_URL, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_s_equal_to_m_returns_400(self):
        self.client.force_authenticate(user=self.user)
        payload = {**_VALID_PAYLOAD, "s_max_amount": 150000, "m_max_amount": 150000}
        response = self.client.patch(PATCH_URL, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_m_greater_than_l_returns_400(self):
        self.client.force_authenticate(user=self.user)
        payload = {**_VALID_PAYLOAD, "m_max_amount": 500000, "l_max_amount": 400000}
        response = self.client.patch(PATCH_URL, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_partial_size_payload_returns_200(self):
        self.client.force_authenticate(user=self.user)
        payload = {k: v for k, v in _VALID_PAYLOAD.items() if k != "xs_max_amount"}
        response = self.client.patch(PATCH_URL, payload, format="json")
        self.assertEqual(response.status_code, 200)

    def test_zero_value_returns_400(self):
        self.client.force_authenticate(user=self.user)
        payload = {**_VALID_PAYLOAD, "xs_max_amount": 0}
        response = self.client.patch(PATCH_URL, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_negative_value_returns_400(self):
        self.client.force_authenticate(user=self.user)
        payload = {**_VALID_PAYLOAD, "l_max_amount": -1}
        response = self.client.patch(PATCH_URL, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_valid_budget_payload_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(PATCH_URL, _VALID_BUDGET_PAYLOAD, format="json")
        self.assertEqual(response.status_code, 200)

    def test_updated_budget_values_reflected_in_response(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(PATCH_URL, _VALID_BUDGET_PAYLOAD, format="json")
        data = response.data["data"]
        self.assertEqual(data["budget_risk_threshold"], 10.0)
        self.assertEqual(data["xs_budget_variance"], 0.5)
        self.assertEqual(data["xl_budget_variance"], 1.0)

    def test_updated_budget_values_persist_on_subsequent_get(self):
        self.client.force_authenticate(user=self.user)
        self.client.patch(PATCH_URL, _VALID_BUDGET_PAYLOAD, format="json")
        response = self.client.get(GET_URL)
        data = response.data["data"]
        self.assertEqual(data["budget_risk_threshold"], 10.0)
        self.assertEqual(data["xl_budget_variance"], 1.0)

    def test_negative_budget_risk_threshold_returns_400(self):
        self.client.force_authenticate(user=self.user)
        payload = {**_VALID_BUDGET_PAYLOAD, "budget_risk_threshold": -1.0}
        response = self.client.patch(PATCH_URL, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_negative_budget_variance_returns_400(self):
        self.client.force_authenticate(user=self.user)
        payload = {**_VALID_BUDGET_PAYLOAD, "xs_budget_variance": -0.1}
        response = self.client.patch(PATCH_URL, payload, format="json")
        self.assertEqual(response.status_code, 400)

    def test_combined_size_and_budget_payload_returns_200(self):
        self.client.force_authenticate(user=self.user)
        payload = {**_VALID_PAYLOAD, **_VALID_BUDGET_PAYLOAD}
        response = self.client.patch(PATCH_URL, payload, format="json")
        self.assertEqual(response.status_code, 200)

    def test_response_always_contains_budget_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.patch(PATCH_URL, _VALID_PAYLOAD, format="json")
        data = response.data["data"]
        for field in (
            "budget_risk_threshold",
            "xs_budget_variance",
            "s_budget_variance",
            "m_budget_variance",
            "l_budget_variance",
            "xl_budget_variance",
        ):
            self.assertIn(field, data)
