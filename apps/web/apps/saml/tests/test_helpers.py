from django.test import SimpleTestCase

from apps.saml.helpers import first_match


class FirstMatchTest(SimpleTestCase):
    def test_returns_first_matching_string_value(self):
        attrs = {"first_name": "Alice", "givenName": "Bob"}
        result = first_match(attrs, ("first_name", "givenName"))
        self.assertEqual(result, "Alice")

    def test_skips_missing_keys_and_returns_next_match(self):
        attrs = {"givenName": "Bob"}
        result = first_match(attrs, ("first_name", "givenName"))
        self.assertEqual(result, "Bob")

    def test_returns_empty_string_when_no_key_matches(self):
        attrs = {"other_attr": "value"}
        result = first_match(attrs, ("first_name", "givenName"))
        self.assertEqual(result, "")

    def test_returns_empty_string_for_empty_attrs(self):
        result = first_match({}, ("first_name", "givenName"))
        self.assertEqual(result, "")

    def test_returns_empty_string_for_empty_keys(self):
        result = first_match({"first_name": "Alice"}, ())
        self.assertEqual(result, "")

    def test_returns_first_element_when_value_is_a_list(self):
        attrs = {"email": ["user@example.com", "other@example.com"]}
        result = first_match(attrs, ("email",))
        self.assertEqual(result, "user@example.com")

    def test_skips_falsy_string_values(self):
        attrs = {"first_name": "", "givenName": "Alice"}
        result = first_match(attrs, ("first_name", "givenName"))
        self.assertEqual(result, "Alice")

    def test_skips_falsy_list_values(self):
        attrs = {"first_name": [], "givenName": "Alice"}
        result = first_match(attrs, ("first_name", "givenName"))
        self.assertEqual(result, "Alice")

    def test_handles_urn_style_attribute_keys(self):
        urn = "http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname"
        attrs = {urn: "Charlie"}
        result = first_match(attrs, (urn,))
        self.assertEqual(result, "Charlie")
