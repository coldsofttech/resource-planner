from django.test import SimpleTestCase

from apps.leaves.serializers import LeaveCreateSerializer, LeaveUpdateSerializer


class LeaveCreateSerializerValidationTest(SimpleTestCase):
    def _make_valid(self, **overrides):
        data = {
            "member_code": "MBR-1",
            "start_date": "2025-01-06",
            "end_date": "2025-01-10",
        }
        data.update(overrides)
        return data

    def test_valid_payload_passes(self):
        s = LeaveCreateSerializer(data=self._make_valid())
        self.assertTrue(s.is_valid(), s.errors)

    def test_member_code_required(self):
        data = self._make_valid()
        del data["member_code"]
        s = LeaveCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("member_code", s.errors)

    def test_start_date_required(self):
        data = self._make_valid()
        del data["start_date"]
        s = LeaveCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("start_date", s.errors)

    def test_end_date_required(self):
        data = self._make_valid()
        del data["end_date"]
        s = LeaveCreateSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("end_date", s.errors)

    def test_is_half_day_defaults_false(self):
        s = LeaveCreateSerializer(data=self._make_valid())
        s.is_valid()
        self.assertFalse(s.validated_data["is_half_day"])

    def test_note_defaults_empty(self):
        s = LeaveCreateSerializer(data=self._make_valid())
        s.is_valid()
        self.assertEqual(s.validated_data["note"], "")

    def test_half_day_period_optional(self):
        data = self._make_valid(
            is_half_day=True, start_date="2025-01-06", end_date="2025-01-06"
        )
        s = LeaveCreateSerializer(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_invalid_date_format_fails(self):
        s = LeaveCreateSerializer(data=self._make_valid(start_date="06-01-2025"))
        self.assertFalse(s.is_valid())
        self.assertIn("start_date", s.errors)


class LeaveUpdateSerializerValidationTest(SimpleTestCase):
    def test_all_fields_optional(self):
        s = LeaveUpdateSerializer(data={})
        self.assertTrue(s.is_valid(), s.errors)

    def test_valid_date_passes(self):
        s = LeaveUpdateSerializer(
            data={"start_date": "2025-02-01", "end_date": "2025-02-05"}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_invalid_date_format_fails(self):
        s = LeaveUpdateSerializer(data={"start_date": "not-a-date"})
        self.assertFalse(s.is_valid())
        self.assertIn("start_date", s.errors)

    def test_half_day_period_allows_null(self):
        s = LeaveUpdateSerializer(data={"half_day_period": None})
        self.assertTrue(s.is_valid(), s.errors)
