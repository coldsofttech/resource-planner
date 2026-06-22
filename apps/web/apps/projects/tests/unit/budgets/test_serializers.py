from django.test import SimpleTestCase

from apps.projects.serializers import (
    ProjectBudgetCreateSerializer,
    ProjectBudgetUpdateSerializer,
)


class ProjectBudgetCreateSerializerTest(SimpleTestCase):
    def test_valid_with_required_fields_only(self):
        s = ProjectBudgetCreateSerializer(
            data={"financial_year_code": "FY-001", "allocated_budget": "100000.00"}
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_financial_year_code_required(self):
        s = ProjectBudgetCreateSerializer(data={"allocated_budget": "100000.00"})
        self.assertFalse(s.is_valid())
        self.assertIn("financial_year_code", s.errors)

    def test_allocated_budget_required(self):
        s = ProjectBudgetCreateSerializer(data={"financial_year_code": "FY-001"})
        self.assertFalse(s.is_valid())
        self.assertIn("allocated_budget", s.errors)

    def test_allocated_budget_must_be_decimal(self):
        s = ProjectBudgetCreateSerializer(
            data={"financial_year_code": "FY-001", "allocated_budget": "not-a-number"}
        )
        self.assertFalse(s.is_valid())
        self.assertIn("allocated_budget", s.errors)

    def test_refined_budget_optional_defaults_to_none(self):
        s = ProjectBudgetCreateSerializer(
            data={"financial_year_code": "FY-001", "allocated_budget": "100000.00"}
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertIsNone(s.validated_data["refined_budget"])

    def test_refined_budget_accepts_null(self):
        s = ProjectBudgetCreateSerializer(
            data={
                "financial_year_code": "FY-001",
                "allocated_budget": "100000.00",
                "refined_budget": None,
            }
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertIsNone(s.validated_data["refined_budget"])

    def test_refined_budget_accepts_decimal_value(self):
        s = ProjectBudgetCreateSerializer(
            data={
                "financial_year_code": "FY-001",
                "allocated_budget": "100000.00",
                "refined_budget": "95000.50",
            }
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_estimate_version_code_optional_defaults_to_none(self):
        s = ProjectBudgetCreateSerializer(
            data={"financial_year_code": "FY-001", "allocated_budget": "100000.00"}
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertIsNone(s.validated_data["estimate_version_code"])

    def test_estimate_version_code_accepts_null(self):
        s = ProjectBudgetCreateSerializer(
            data={
                "financial_year_code": "FY-001",
                "allocated_budget": "100000.00",
                "estimate_version_code": None,
            }
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_estimate_version_code_accepts_string(self):
        s = ProjectBudgetCreateSerializer(
            data={
                "financial_year_code": "FY-001",
                "allocated_budget": "100000.00",
                "estimate_version_code": "PROJEST-001",
            }
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_note_optional_defaults_to_empty_string(self):
        s = ProjectBudgetCreateSerializer(
            data={"financial_year_code": "FY-001", "allocated_budget": "100000.00"}
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["note"], "")

    def test_note_accepts_blank(self):
        s = ProjectBudgetCreateSerializer(
            data={
                "financial_year_code": "FY-001",
                "allocated_budget": "100000.00",
                "note": "",
            }
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_note_accepts_text(self):
        s = ProjectBudgetCreateSerializer(
            data={
                "financial_year_code": "FY-001",
                "allocated_budget": "100000.00",
                "note": "Initial budget allocation.",
            }
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_valid_with_all_fields(self):
        s = ProjectBudgetCreateSerializer(
            data={
                "financial_year_code": "FY-001",
                "allocated_budget": "250000.00",
                "refined_budget": "230000.00",
                "estimate_version_code": "PROJEST-042",
                "note": "Approved budget for FY2024-25.",
            }
        )
        self.assertTrue(s.is_valid(), s.errors)


class ProjectBudgetUpdateSerializerTest(SimpleTestCase):
    def test_valid_with_no_fields(self):
        s = ProjectBudgetUpdateSerializer(data={})
        self.assertTrue(s.is_valid(), s.errors)

    def test_valid_with_allocated_budget_only(self):
        s = ProjectBudgetUpdateSerializer(data={"allocated_budget": "120000.00"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_allocated_budget_must_be_decimal(self):
        s = ProjectBudgetUpdateSerializer(data={"allocated_budget": "abc"})
        self.assertFalse(s.is_valid())
        self.assertIn("allocated_budget", s.errors)

    def test_refined_budget_accepts_null(self):
        s = ProjectBudgetUpdateSerializer(data={"refined_budget": None})
        self.assertTrue(s.is_valid(), s.errors)

    def test_refined_budget_accepts_decimal(self):
        s = ProjectBudgetUpdateSerializer(data={"refined_budget": "95000.00"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_estimate_version_code_accepts_null(self):
        s = ProjectBudgetUpdateSerializer(data={"estimate_version_code": None})
        self.assertTrue(s.is_valid(), s.errors)

    def test_estimate_version_code_accepts_blank(self):
        s = ProjectBudgetUpdateSerializer(data={"estimate_version_code": ""})
        self.assertTrue(s.is_valid(), s.errors)

    def test_estimate_version_code_accepts_string(self):
        s = ProjectBudgetUpdateSerializer(data={"estimate_version_code": "PROJEST-005"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_note_accepts_blank(self):
        s = ProjectBudgetUpdateSerializer(data={"note": ""})
        self.assertTrue(s.is_valid(), s.errors)

    def test_note_accepts_text(self):
        s = ProjectBudgetUpdateSerializer(data={"note": "Revised after Q2 review."})
        self.assertTrue(s.is_valid(), s.errors)

    def test_valid_with_all_fields(self):
        s = ProjectBudgetUpdateSerializer(
            data={
                "allocated_budget": "300000.00",
                "refined_budget": "280000.00",
                "estimate_version_code": "PROJEST-010",
                "note": "Updated after board approval.",
            }
        )
        self.assertTrue(s.is_valid(), s.errors)
