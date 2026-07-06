from django.test import TestCase

from apps.projects.tests.factories import make_project
from apps.reports import selectors
from apps.reports.tests.factories import make_kpi_estimate_accuracy_config


class GetKPIEstimateAccuracyConfigsTest(TestCase):
    def test_returns_all_when_no_month_filter(self):
        make_kpi_estimate_accuracy_config(month="2025-04")
        make_kpi_estimate_accuracy_config(
            project=make_project(name="Second Project"), month="2025-05"
        )
        self.assertEqual(selectors.get_kpi_estimate_accuracy_configs().count(), 2)

    def test_filters_by_month(self):
        make_kpi_estimate_accuracy_config(month="2025-04")
        make_kpi_estimate_accuracy_config(
            project=make_project(name="Second Project"), month="2025-05"
        )
        qs = selectors.get_kpi_estimate_accuracy_configs(month="2025-04")
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().month, "2025-04")


class GetKPIEstimateAccuracyConfigByCodeTest(TestCase):
    def test_returns_matching_config(self):
        obj = make_kpi_estimate_accuracy_config()
        found = selectors.get_kpi_estimate_accuracy_config_by_code(obj.code)
        self.assertEqual(found, obj)

    def test_returns_none_for_unknown_code(self):
        self.assertIsNone(
            selectors.get_kpi_estimate_accuracy_config_by_code("KPICFG-999999")
        )


class KPIEstimateAccuracyConfigExistsTest(TestCase):
    def test_returns_true_when_exists(self):
        project = make_project()
        make_kpi_estimate_accuracy_config(project=project, month="2025-04")
        self.assertTrue(
            selectors.kpi_estimate_accuracy_config_exists(project.id, "2025-04")
        )

    def test_returns_false_when_not_exists(self):
        project = make_project()
        self.assertFalse(
            selectors.kpi_estimate_accuracy_config_exists(project.id, "2025-04")
        )

    def test_exclude_pk_ignores_own_record(self):
        project = make_project()
        obj = make_kpi_estimate_accuracy_config(project=project, month="2025-04")
        self.assertFalse(
            selectors.kpi_estimate_accuracy_config_exists(
                project.id, "2025-04", exclude_pk=obj.pk
            )
        )
