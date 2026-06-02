from django.test import SimpleTestCase

from apps.configurations.converters import get_bool, get_float, get_int


class GetBoolTest(SimpleTestCase):
    def test_returns_true_for_one(self):
        self.assertTrue(get_bool("1"))

    def test_returns_true_for_true(self):
        self.assertTrue(get_bool("true"))

    def test_returns_true_for_yes(self):
        self.assertTrue(get_bool("yes"))

    def test_returns_true_for_on(self):
        self.assertTrue(get_bool("on"))

    def test_is_case_insensitive_for_true(self):
        self.assertTrue(get_bool("True"))
        self.assertTrue(get_bool("YES"))
        self.assertTrue(get_bool("ON"))

    def test_strips_surrounding_whitespace(self):
        self.assertTrue(get_bool(" true "))

    def test_returns_false_for_false(self):
        self.assertFalse(get_bool("false"))

    def test_returns_false_for_zero(self):
        self.assertFalse(get_bool("0"))

    def test_returns_false_for_no(self):
        self.assertFalse(get_bool("no"))

    def test_returns_false_for_off(self):
        self.assertFalse(get_bool("off"))

    def test_returns_false_for_empty_string(self):
        self.assertFalse(get_bool(""))

    def test_returns_default_fallback_for_none(self):
        self.assertFalse(get_bool(None))

    def test_returns_default_fallback_for_integer(self):
        self.assertFalse(get_bool(1))

    def test_returns_custom_fallback_when_type_error(self):
        self.assertTrue(get_bool(None, fallback=True))


class GetFloatTest(SimpleTestCase):
    def test_converts_float_string(self):
        self.assertAlmostEqual(get_float("3.14"), 3.14)

    def test_converts_integer_string(self):
        self.assertAlmostEqual(get_float("5"), 5.0)

    def test_converts_negative_float(self):
        self.assertAlmostEqual(get_float("-1.5"), -1.5)

    def test_converts_zero(self):
        self.assertAlmostEqual(get_float("0"), 0.0)

    def test_returns_default_for_invalid_string(self):
        self.assertAlmostEqual(get_float("bad"), 0.0)

    def test_returns_default_for_none(self):
        self.assertAlmostEqual(get_float(None), 0.0)

    def test_returns_default_for_empty_string(self):
        self.assertAlmostEqual(get_float(""), 0.0)

    def test_returns_custom_fallback_for_invalid(self):
        self.assertAlmostEqual(get_float("bad", fallback=99.9), 99.9)


class GetIntTest(SimpleTestCase):
    def test_converts_integer_string(self):
        self.assertEqual(get_int("5"), 5)

    def test_converts_negative_integer_string(self):
        self.assertEqual(get_int("-3"), -3)

    def test_converts_zero_string(self):
        self.assertEqual(get_int("0"), 0)

    def test_returns_default_for_invalid_string(self):
        self.assertEqual(get_int("bad"), 0)

    def test_returns_default_for_none(self):
        self.assertEqual(get_int(None), 0)

    def test_returns_default_for_empty_string(self):
        self.assertEqual(get_int(""), 0)

    def test_returns_default_for_float_string(self):
        self.assertEqual(get_int("3.14"), 0)

    def test_returns_custom_fallback_for_invalid(self):
        self.assertEqual(get_int("bad", fallback=10), 10)
