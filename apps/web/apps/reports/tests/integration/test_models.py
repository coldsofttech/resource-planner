from django.db import IntegrityError
from django.test import TestCase

from apps.projects.tests.factories import make_project
from apps.reports.models import KPIEstimateAccuracyConfig
from apps.reports.tests.factories import make_kpi_estimate_accuracy_config


class KPIEstimateAccuracyConfigModelTest(TestCase):
    def test_defaults(self):
        obj = make_kpi_estimate_accuracy_config()
        self.assertIsNotNone(obj.code)
        self.assertIsNone(obj.created_by)
        self.assertIsNone(obj.updated_by)
        self.assertIsNotNone(obj.created_at)
        self.assertIsNotNone(obj.updated_at)

    def test_str_representation(self):
        project = make_project(name="Migrate Billing")
        obj = make_kpi_estimate_accuracy_config(project=project, month="2025-04")
        self.assertIn("Migrate Billing", str(obj))
        self.assertIn("2025-04", str(obj))

    def test_duplicate_project_month_raises_integrity_error(self):
        project = make_project()
        make_kpi_estimate_accuracy_config(project=project, month="2025-04")
        with self.assertRaises(IntegrityError):
            make_kpi_estimate_accuracy_config(project=project, month="2025-04")

    def test_same_project_different_month_allowed(self):
        project = make_project()
        make_kpi_estimate_accuracy_config(project=project, month="2025-04")
        obj2 = make_kpi_estimate_accuracy_config(project=project, month="2025-05")
        self.assertIsNotNone(obj2.pk)

    def test_ordering_by_month_then_project_name(self):
        project_a = make_project(name="Alpha Project")
        project_b = make_project(name="Beta Project")
        make_kpi_estimate_accuracy_config(project=project_b, month="2025-04")
        make_kpi_estimate_accuracy_config(project=project_a, month="2025-04")
        names = list(
            KPIEstimateAccuracyConfig.objects.values_list("project__name", flat=True)
        )
        self.assertEqual(names, ["Alpha Project", "Beta Project"])
