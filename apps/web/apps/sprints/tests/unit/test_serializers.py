from datetime import date

from django.test import SimpleTestCase

from apps.sprints.serializers import (
    SprintCloseSerializer,
    SprintCreateSerializer,
    SprintGenerateSerializer,
    SprintUpdateSerializer,
)


class SprintCreateSerializerValidationTest(SimpleTestCase):
    def _valid(self, **kwargs):
        data = {
            "fy_code": "FY-1",
            "sprint_number": 1,
            "start_date": date(2024, 4, 1),
            "end_date": date(2024, 4, 14),
            **kwargs,
        }
        s = SprintCreateSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)
        return s.validated_data

    def test_valid_payload_passes(self):
        data = self._valid()
        self.assertEqual(data["fy_code"], "FY-1")
        self.assertEqual(data["sprint_number"], 1)

    def test_fy_code_required(self):
        s = SprintCreateSerializer(
            data={
                "sprint_number": 1,
                "start_date": date(2024, 4, 1),
                "end_date": date(2024, 4, 14),
            }
        )
        self.assertFalse(s.is_valid())
        self.assertIn("fy_code", s.errors)

    def test_sprint_number_required(self):
        s = SprintCreateSerializer(
            data={
                "fy_code": "FY-1",
                "start_date": date(2024, 4, 1),
                "end_date": date(2024, 4, 14),
            }
        )
        self.assertFalse(s.is_valid())
        self.assertIn("sprint_number", s.errors)

    def test_start_date_required(self):
        s = SprintCreateSerializer(
            data={
                "fy_code": "FY-1",
                "sprint_number": 1,
                "end_date": date(2024, 4, 14),
            }
        )
        self.assertFalse(s.is_valid())
        self.assertIn("start_date", s.errors)

    def test_end_date_required(self):
        s = SprintCreateSerializer(
            data={
                "fy_code": "FY-1",
                "sprint_number": 1,
                "start_date": date(2024, 4, 1),
            }
        )
        self.assertFalse(s.is_valid())
        self.assertIn("end_date", s.errors)

    def test_sprint_number_must_be_positive(self):
        s = SprintCreateSerializer(
            data={
                "fy_code": "FY-1",
                "sprint_number": 0,
                "start_date": date(2024, 4, 1),
                "end_date": date(2024, 4, 14),
            }
        )
        self.assertFalse(s.is_valid())
        self.assertIn("sprint_number", s.errors)

    def test_end_date_must_be_after_start_date(self):
        s = SprintCreateSerializer(
            data={
                "fy_code": "FY-1",
                "sprint_number": 1,
                "start_date": date(2024, 4, 14),
                "end_date": date(2024, 4, 1),
            }
        )
        self.assertFalse(s.is_valid())
        self.assertIn("end_date", s.errors)

    def test_equal_dates_invalid(self):
        s = SprintCreateSerializer(
            data={
                "fy_code": "FY-1",
                "sprint_number": 1,
                "start_date": date(2024, 4, 1),
                "end_date": date(2024, 4, 1),
            }
        )
        self.assertFalse(s.is_valid())

    def test_status_defaults_to_future(self):
        data = self._valid()
        self.assertEqual(data["status"], "future")

    def test_invalid_status_rejected(self):
        s = SprintCreateSerializer(
            data={
                "fy_code": "FY-1",
                "sprint_number": 1,
                "start_date": date(2024, 4, 1),
                "end_date": date(2024, 4, 14),
                "status": "not_a_valid_status",
            }
        )
        self.assertFalse(s.is_valid())
        self.assertIn("status", s.errors)

    def test_name_optional_and_blank_allowed(self):
        data = self._valid(name="")
        self.assertEqual(data["name"], "")

    def test_note_optional_defaults_to_empty(self):
        data = self._valid()
        self.assertEqual(data["note"], "")

    def test_is_active_defaults_to_true(self):
        data = self._valid()
        self.assertTrue(data["is_active"])


class SprintUpdateSerializerValidationTest(SimpleTestCase):
    def test_all_fields_optional(self):
        s = SprintUpdateSerializer(data={})
        self.assertTrue(s.is_valid(), s.errors)

    def test_end_before_start_invalid(self):
        s = SprintUpdateSerializer(
            data={
                "start_date": date(2024, 4, 14),
                "end_date": date(2024, 4, 1),
            }
        )
        self.assertFalse(s.is_valid())
        self.assertIn("end_date", s.errors)

    def test_valid_partial_status_update(self):
        s = SprintUpdateSerializer(data={"status": "in_progress"}, partial=True)
        self.assertTrue(s.is_valid(), s.errors)

    def test_valid_partial_name_update(self):
        s = SprintUpdateSerializer(data={"name": "Renamed Sprint"}, partial=True)
        self.assertTrue(s.is_valid(), s.errors)

    def test_invalid_status_rejected(self):
        s = SprintUpdateSerializer(data={"status": "unknown"}, partial=True)
        self.assertFalse(s.is_valid())
        self.assertIn("status", s.errors)


class SprintGenerateSerializerValidationTest(SimpleTestCase):
    def test_fy_code_required(self):
        s = SprintGenerateSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn("fy_code", s.errors)

    def test_valid_fy_code_passes(self):
        s = SprintGenerateSerializer(data={"fy_code": "FY-1"})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["fy_code"], "FY-1")


class SprintCloseSerializerValidationTest(SimpleTestCase):
    def test_lock_defaults_to_true(self):
        s = SprintCloseSerializer(data={})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertTrue(s.validated_data["lock"])

    def test_lock_false_accepted(self):
        s = SprintCloseSerializer(data={"lock": False})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertFalse(s.validated_data["lock"])
