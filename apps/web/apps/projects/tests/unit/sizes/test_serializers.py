from django.test import SimpleTestCase

from apps.projects.serializers.project_size_config import ProjectSizeConfigSerializer

_VALID = {
    "xs_max_amount": 10000,
    "s_max_amount": 50000,
    "m_max_amount": 150000,
    "l_max_amount": 400000,
}


class ProjectSizeConfigSerializerTest(SimpleTestCase):
    def test_valid_ascending_values(self):
        s = ProjectSizeConfigSerializer(data=_VALID)
        self.assertTrue(s.is_valid(), s.errors)

    def test_validated_data_contains_all_fields(self):
        s = ProjectSizeConfigSerializer(data=_VALID)
        self.assertTrue(s.is_valid(), s.errors)
        self.assertSetEqual(
            set(s.validated_data.keys()),
            {"xs_max_amount", "s_max_amount", "m_max_amount", "l_max_amount"},
        )

    def test_missing_xs_max_amount_invalid(self):
        data = {k: v for k, v in _VALID.items() if k != "xs_max_amount"}
        s = ProjectSizeConfigSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("xs_max_amount", s.errors)

    def test_missing_s_max_amount_invalid(self):
        data = {k: v for k, v in _VALID.items() if k != "s_max_amount"}
        s = ProjectSizeConfigSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("s_max_amount", s.errors)

    def test_missing_m_max_amount_invalid(self):
        data = {k: v for k, v in _VALID.items() if k != "m_max_amount"}
        s = ProjectSizeConfigSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("m_max_amount", s.errors)

    def test_missing_l_max_amount_invalid(self):
        data = {k: v for k, v in _VALID.items() if k != "l_max_amount"}
        s = ProjectSizeConfigSerializer(data=data)
        self.assertFalse(s.is_valid())
        self.assertIn("l_max_amount", s.errors)

    def test_zero_value_invalid(self):
        s = ProjectSizeConfigSerializer(data={**_VALID, "xs_max_amount": 0})
        self.assertFalse(s.is_valid())
        self.assertIn("xs_max_amount", s.errors)

    def test_negative_value_invalid(self):
        s = ProjectSizeConfigSerializer(data={**_VALID, "s_max_amount": -1})
        self.assertFalse(s.is_valid())
        self.assertIn("s_max_amount", s.errors)

    def test_xs_equal_to_s_invalid(self):
        s = ProjectSizeConfigSerializer(
            data={**_VALID, "xs_max_amount": 50000, "s_max_amount": 50000}
        )
        self.assertFalse(s.is_valid())
        self.assertIn("s_max_amount", s.errors)

    def test_xs_greater_than_s_invalid(self):
        s = ProjectSizeConfigSerializer(
            data={**_VALID, "xs_max_amount": 60000, "s_max_amount": 50000}
        )
        self.assertFalse(s.is_valid())
        self.assertIn("s_max_amount", s.errors)

    def test_s_equal_to_m_invalid(self):
        s = ProjectSizeConfigSerializer(
            data={**_VALID, "s_max_amount": 150000, "m_max_amount": 150000}
        )
        self.assertFalse(s.is_valid())
        self.assertIn("m_max_amount", s.errors)

    def test_m_equal_to_l_invalid(self):
        s = ProjectSizeConfigSerializer(
            data={**_VALID, "m_max_amount": 400000, "l_max_amount": 400000}
        )
        self.assertFalse(s.is_valid())
        self.assertIn("l_max_amount", s.errors)

    def test_non_integer_value_invalid(self):
        s = ProjectSizeConfigSerializer(
            data={**_VALID, "xs_max_amount": "not-a-number"}
        )
        self.assertFalse(s.is_valid())
        self.assertIn("xs_max_amount", s.errors)

    def test_minimum_valid_values(self):
        s = ProjectSizeConfigSerializer(
            data={
                "xs_max_amount": 1,
                "s_max_amount": 2,
                "m_max_amount": 3,
                "l_max_amount": 4,
            }
        )
        self.assertTrue(s.is_valid(), s.errors)
