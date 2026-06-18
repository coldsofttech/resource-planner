from django.test import SimpleTestCase

from apps.projects.serializers import (
    ProjectEstimateCreateSerializer,
    ProjectEstimateUpdateSerializer,
)


class ProjectEstimateCreateSerializerTest(SimpleTestCase):
    def test_valid_with_required_fields_only(self):
        s = ProjectEstimateCreateSerializer(data={"shared_by_codes": ["USER-1"]})
        self.assertTrue(s.is_valid(), s.errors)

    def test_invalid_without_shared_by_codes(self):
        s = ProjectEstimateCreateSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn("shared_by_codes", s.errors)

    def test_invalid_with_empty_shared_by_codes(self):
        s = ProjectEstimateCreateSerializer(data={"shared_by_codes": []})
        self.assertFalse(s.is_valid())
        self.assertIn("shared_by_codes", s.errors)

    def test_estimate_link_defaults_to_empty_string(self):
        s = ProjectEstimateCreateSerializer(data={"shared_by_codes": ["USER-1"]})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["estimate_link"], "")

    def test_estimate_link_accepts_valid_url(self):
        s = ProjectEstimateCreateSerializer(
            data={
                "shared_by_codes": ["USER-1"],
                "estimate_link": "https://example.com/estimate",
            }
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_estimate_link_accepts_blank(self):
        s = ProjectEstimateCreateSerializer(
            data={"shared_by_codes": ["USER-1"], "estimate_link": ""}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_estimate_link_rejects_invalid_url(self):
        s = ProjectEstimateCreateSerializer(
            data={"shared_by_codes": ["USER-1"], "estimate_link": "not-a-url"}
        )
        self.assertFalse(s.is_valid())
        self.assertIn("estimate_link", s.errors)

    def test_status_defaults_to_draft(self):
        s = ProjectEstimateCreateSerializer(data={"shared_by_codes": ["USER-1"]})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["status"], "DRAFT")

    def test_status_accepts_valid_choice(self):
        s = ProjectEstimateCreateSerializer(
            data={"shared_by_codes": ["USER-1"], "status": "REVIEWED"}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_status_rejects_invalid_choice(self):
        s = ProjectEstimateCreateSerializer(
            data={"shared_by_codes": ["USER-1"], "status": "BOGUS"}
        )
        self.assertFalse(s.is_valid())
        self.assertIn("status", s.errors)

    def test_estimate_days_defaults_to_zero(self):
        s = ProjectEstimateCreateSerializer(data={"shared_by_codes": ["USER-1"]})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["estimate_days"], 0)

    def test_contingency_percentage_defaults_to_zero(self):
        s = ProjectEstimateCreateSerializer(data={"shared_by_codes": ["USER-1"]})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["contingency_percentage"], 0)

    def test_day_rate_defaults_to_none(self):
        s = ProjectEstimateCreateSerializer(data={"shared_by_codes": ["USER-1"]})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertIsNone(s.validated_data["day_rate"])

    def test_is_active_defaults_to_true(self):
        s = ProjectEstimateCreateSerializer(data={"shared_by_codes": ["USER-1"]})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertTrue(s.validated_data["is_active"])

    def test_reviewed_by_codes_defaults_to_empty_list(self):
        s = ProjectEstimateCreateSerializer(data={"shared_by_codes": ["USER-1"]})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["reviewed_by_codes"], [])

    def test_reviewed_by_codes_accepts_multiple(self):
        s = ProjectEstimateCreateSerializer(
            data={
                "shared_by_codes": ["USER-1"],
                "reviewed_by_codes": ["USER-2", "USER-3"],
            }
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["reviewed_by_codes"], ["USER-2", "USER-3"])

    def test_note_optional_defaults_to_empty(self):
        s = ProjectEstimateCreateSerializer(data={"shared_by_codes": ["USER-1"]})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["note"], "")

    def test_valid_with_all_fields(self):
        s = ProjectEstimateCreateSerializer(
            data={
                "shared_by_codes": ["USER-1"],
                "reviewed_by_codes": ["USER-2"],
                "estimate_link": "https://docs.example.com/v1",
                "status": "REVIEWED",
                "estimate_days": "15.5",
                "contingency_percentage": "10.0",
                "day_rate": 1200,
                "note": "First estimate version",
                "is_active": True,
            }
        )
        self.assertTrue(s.is_valid(), s.errors)


class ProjectEstimateUpdateSerializerTest(SimpleTestCase):
    def test_valid_with_no_fields(self):
        s = ProjectEstimateUpdateSerializer(data={})
        self.assertTrue(s.is_valid(), s.errors)

    def test_valid_with_status_only(self):
        s = ProjectEstimateUpdateSerializer(data={"status": "REVIEWED"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_status_rejects_invalid_choice(self):
        s = ProjectEstimateUpdateSerializer(data={"status": "UNKNOWN"})
        self.assertFalse(s.is_valid())
        self.assertIn("status", s.errors)

    def test_valid_with_estimate_link_url(self):
        s = ProjectEstimateUpdateSerializer(
            data={"estimate_link": "https://docs.example.com/est-v2"}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_estimate_link_accepts_blank(self):
        s = ProjectEstimateUpdateSerializer(data={"estimate_link": ""})
        self.assertTrue(s.is_valid(), s.errors)

    def test_estimate_link_rejects_non_url(self):
        s = ProjectEstimateUpdateSerializer(data={"estimate_link": "just-text"})
        self.assertFalse(s.is_valid())
        self.assertIn("estimate_link", s.errors)

    def test_valid_with_approval_email_sent(self):
        s = ProjectEstimateUpdateSerializer(data={"approval_email_sent": True})
        self.assertTrue(s.is_valid(), s.errors)

    def test_valid_with_is_active_false(self):
        s = ProjectEstimateUpdateSerializer(data={"is_active": False})
        self.assertTrue(s.is_valid(), s.errors)

    def test_valid_with_all_statuses(self):
        for st in ("DRAFT", "REVIEWED", "SHARED", "APPROVED", "SUPERSEDED"):
            with self.subTest(status=st):
                s = ProjectEstimateUpdateSerializer(data={"status": st})
                self.assertTrue(s.is_valid(), s.errors)

    def test_note_accepts_blank(self):
        s = ProjectEstimateUpdateSerializer(data={"note": ""})
        self.assertTrue(s.is_valid(), s.errors)

    def test_shared_by_codes_accepted_as_list(self):
        s = ProjectEstimateUpdateSerializer(data={"shared_by_codes": ["USER-1"]})
        self.assertTrue(s.is_valid(), s.errors)

    def test_reviewed_by_codes_accepted_as_list(self):
        s = ProjectEstimateUpdateSerializer(
            data={"reviewed_by_codes": ["USER-1", "USER-2"]}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_estimate_days_accepts_decimal(self):
        s = ProjectEstimateUpdateSerializer(data={"estimate_days": "12.50"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_contingency_percentage_accepts_decimal(self):
        s = ProjectEstimateUpdateSerializer(data={"contingency_percentage": "15.00"})
        self.assertTrue(s.is_valid(), s.errors)
