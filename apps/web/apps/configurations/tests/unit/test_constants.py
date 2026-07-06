from django.test import SimpleTestCase

from apps.configurations.constants import DataType, Module

# ── DataType values ────────────────────────────────────────────────────────────


class DataTypeValuesTest(SimpleTestCase):
    def test_string_value(self):
        self.assertEqual(DataType.STRING, "string")

    def test_integer_value(self):
        self.assertEqual(DataType.INTEGER, "integer")

    def test_float_value(self):
        self.assertEqual(DataType.FLOAT, "float")

    def test_boolean_value(self):
        self.assertEqual(DataType.BOOLEAN, "boolean")


# ── DataType labels ────────────────────────────────────────────────────────────


class DataTypeLabelsTest(SimpleTestCase):
    def test_string_label(self):
        self.assertEqual(DataType.STRING.label, "String")

    def test_integer_label(self):
        self.assertEqual(DataType.INTEGER.label, "Integer")

    def test_float_label(self):
        self.assertEqual(DataType.FLOAT.label, "Float")

    def test_boolean_label(self):
        self.assertEqual(DataType.BOOLEAN.label, "Boolean")


# ── DataType.choices ───────────────────────────────────────────────────────────


class DataTypeChoicesTest(SimpleTestCase):
    def test_choices_has_four_entries(self):
        self.assertEqual(len(DataType.choices), 4)

    def test_choices_contains_all_values(self):
        values = [v for v, _ in DataType.choices]
        self.assertIn("string", values)
        self.assertIn("integer", values)
        self.assertIn("float", values)
        self.assertIn("boolean", values)


# ── Module values ──────────────────────────────────────────────────────────────


class ModuleValuesTest(SimpleTestCase):
    def test_setup_value(self):
        self.assertEqual(Module.SETUP, "setup")

    def test_general_value(self):
        self.assertEqual(Module.GENERAL, "general")

    def test_authentication_value(self):
        self.assertEqual(Module.AUTHENTICATION, "auth")

    def test_infra_value(self):
        self.assertEqual(Module.INFRA, "infra")

    def test_email_value(self):
        self.assertEqual(Module.EMAIL, "email")

    def test_holidays_value(self):
        self.assertEqual(Module.HOLIDAYS, "holidays")

    def test_financial_year_value(self):
        self.assertEqual(Module.FINANCIAL_YEAR, "financial_year")

    def test_sprints_value(self):
        self.assertEqual(Module.SPRINTS, "sprints")

    def test_users_value(self):
        self.assertEqual(Module.USERS, "users")

    def test_projects_value(self):
        self.assertEqual(Module.PROJECTS, "projects")


# ── Module labels ──────────────────────────────────────────────────────────────


class ModuleLabelsTest(SimpleTestCase):
    def test_setup_label(self):
        self.assertEqual(Module.SETUP.label, "Setup")

    def test_general_label(self):
        self.assertEqual(Module.GENERAL.label, "General")

    def test_authentication_label(self):
        self.assertEqual(Module.AUTHENTICATION.label, "Authentication")

    def test_infra_label(self):
        self.assertEqual(Module.INFRA.label, "Infrastructure")

    def test_email_label(self):
        self.assertEqual(Module.EMAIL.label, "Email")

    def test_holidays_label(self):
        self.assertEqual(Module.HOLIDAYS.label, "Holidays")

    def test_financial_year_label(self):
        self.assertEqual(Module.FINANCIAL_YEAR.label, "Financial Year")

    def test_sprints_label(self):
        self.assertEqual(Module.SPRINTS.label, "Sprints")

    def test_users_label(self):
        self.assertEqual(Module.USERS.label, "Users")

    def test_projects_label(self):
        self.assertEqual(Module.PROJECTS.label, "Projects")


# ── Module.choices ─────────────────────────────────────────────────────────────


class ModuleChoicesTest(SimpleTestCase):
    def test_choices_has_fourteen_entries(self):
        self.assertEqual(len(Module.choices), 14)

    def test_choices_contains_all_values(self):
        values = [v for v, _ in Module.choices]
        self.assertIn("setup", values)
        self.assertIn("general", values)
        self.assertIn("auth", values)
        self.assertIn("infra", values)
        self.assertIn("email", values)
        self.assertIn("holidays", values)
        self.assertIn("financial_year", values)
        self.assertIn("sprints", values)
        self.assertIn("users", values)
        self.assertIn("projects", values)
        self.assertIn("ai", values)
        self.assertIn("wins", values)
        self.assertIn("security", values)
        self.assertIn("security_password", values)
