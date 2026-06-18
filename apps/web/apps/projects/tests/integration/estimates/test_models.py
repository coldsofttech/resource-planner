from unittest.mock import patch

from django.db import IntegrityError
from django.test import TestCase

from apps.projects.constants import (
    ProjectEstimateAction,
    ProjectEstimateStatus,
    ProjectSize,
)
from apps.projects.models import ProjectEstimate, ProjectEstimateStatusHistory
from apps.projects.tests.factories import (
    make_estimate,
    make_estimate_history,
    make_project,
)
from apps.users.tests.factories import make_user

_XS_PATH = "apps.configurations.selectors.Project.get_size_xs_max_amount"
_S_PATH = "apps.configurations.selectors.Project.get_size_s_max_amount"
_M_PATH = "apps.configurations.selectors.Project.get_size_m_max_amount"
_L_PATH = "apps.configurations.selectors.Project.get_size_l_max_amount"

# ── ProjectEstimate field defaults ────────────────────────────────────────────


class ProjectEstimateCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        est = make_estimate()
        self.assertTrue(est.code.startswith("PROJEST-"))

    def test_code_contains_pk(self):
        est = make_estimate()
        self.assertEqual(est.code, f"PROJEST-{est.pk}")

    def test_codes_are_unique(self):
        p1 = make_project("Est Code P1")
        p2 = make_project("Est Code P2")
        e1 = make_estimate(project=p1)
        e2 = make_estimate(project=p2)
        self.assertNotEqual(e1.code, e2.code)


class ProjectEstimateFieldDefaultsTest(TestCase):
    def setUp(self):
        self.est = make_estimate()

    def test_is_active_defaults_to_true(self):
        self.assertTrue(self.est.is_active)

    def test_status_defaults_to_draft(self):
        project = make_project("Default Status Project")
        est = ProjectEstimate.objects.create(
            project=project, version=1, estimate_days=0, day_rate=0
        )
        self.assertEqual(est.status, ProjectEstimateStatus.DRAFT)

    def test_estimate_link_defaults_to_empty(self):
        project = make_project("Link Default Project")
        est = ProjectEstimate.objects.create(
            project=project, version=1, estimate_days=0, day_rate=0
        )
        self.assertEqual(est.estimate_link, "")

    def test_approval_email_sent_defaults_to_false(self):
        project = make_project("Email Default Project")
        est = ProjectEstimate.objects.create(
            project=project, version=1, estimate_days=0, day_rate=0
        )
        self.assertFalse(est.approval_email_sent)

    def test_created_by_defaults_to_none(self):
        self.assertIsNone(self.est.created_by)

    def test_updated_by_defaults_to_none(self):
        self.assertIsNone(self.est.updated_by)

    def test_created_at_is_set(self):
        self.assertIsNotNone(self.est.created_at)

    def test_updated_at_is_set(self):
        self.assertIsNotNone(self.est.updated_at)

    def test_version_stores_value(self):
        project = make_project("Version Project")
        est = make_estimate(project=project, version=3)
        self.assertEqual(est.version, 3)

    def test_version_display(self):
        project = make_project("Version Display Project")
        est = make_estimate(project=project, version=2)
        self.assertEqual(est.version_display, "v2")


class ProjectEstimateConstraintTest(TestCase):
    def test_duplicate_project_version_raises_integrity_error(self):
        project = make_project("Duplicate Est Project")
        make_estimate(project=project, version=1)
        with self.assertRaises(IntegrityError):
            make_estimate(project=project, version=1)

    def test_different_versions_on_same_project_allowed(self):
        project = make_project("Multi Version Project")
        e1 = make_estimate(project=project, version=1)
        e2 = make_estimate(project=project, version=2)
        self.assertNotEqual(e1.pk, e2.pk)

    def test_same_version_on_different_projects_allowed(self):
        p1 = make_project("Est Constraint P1")
        p2 = make_project("Est Constraint P2")
        e1 = make_estimate(project=p1, version=1)
        e2 = make_estimate(project=p2, version=1)
        self.assertNotEqual(e1.pk, e2.pk)


class ProjectEstimateCascadeTest(TestCase):
    def test_cascade_delete_with_project(self):
        project = make_project("Cascade Est Project")
        est = make_estimate(project=project)
        est_pk = est.pk
        project.delete()
        self.assertFalse(ProjectEstimate.objects.filter(pk=est_pk).exists())


# ── ProjectEstimate.total_cost ────────────────────────────────────────────────


class ProjectEstimateTotalCostTest(TestCase):
    def test_total_cost_zero_when_days_zero(self):
        est = make_estimate(estimate_days=0, day_rate=500)
        self.assertEqual(est.total_cost, 0.0)

    def test_total_cost_zero_when_rate_zero(self):
        est = make_estimate(estimate_days=10, day_rate=0)
        self.assertEqual(est.total_cost, 0.0)

    def test_total_cost_days_times_rate(self):
        p = make_project("Cost Calc Project")
        est = make_estimate(
            project=p, estimate_days=10, day_rate=1000, contingency_percentage=0
        )
        self.assertEqual(est.total_cost, 10000.0)

    def test_total_cost_includes_contingency(self):
        p = make_project("Contingency Project")
        est = make_estimate(
            project=p, estimate_days=10, day_rate=1000, contingency_percentage=10
        )
        self.assertAlmostEqual(est.total_cost, 11000.0, places=2)

    def test_total_cost_rounded_to_two_decimal_places(self):
        p = make_project("Rounding Project")
        est = make_estimate(
            project=p, estimate_days=3, day_rate=1000, contingency_percentage=10
        )
        self.assertAlmostEqual(est.total_cost, 3300.0, places=2)


# ── ProjectEstimate.size ──────────────────────────────────────────────────────


@patch(_L_PATH, return_value=500000)
@patch(_M_PATH, return_value=200000)
@patch(_S_PATH, return_value=60000)
@patch(_XS_PATH, return_value=20000)
class ProjectEstimateSizeTest(TestCase):
    def test_size_xs_below_threshold(self, mock_xs, mock_s, mock_m, mock_l):
        p = make_project("Size XS Project")
        est = make_estimate(project=p, estimate_days=10, day_rate=1000)  # 10,000
        self.assertEqual(est.size, ProjectSize.XS)

    def test_size_xs_at_boundary(self, mock_xs, mock_s, mock_m, mock_l):
        p = make_project("Size XS Boundary Project")
        est = make_estimate(
            project=p, estimate_days=20, day_rate=1000
        )  # exactly 20,000
        self.assertEqual(est.size, ProjectSize.XS)

    def test_size_s_above_xs_threshold(self, mock_xs, mock_s, mock_m, mock_l):
        p = make_project("Size S Project")
        est = make_estimate(project=p, estimate_days=30, day_rate=1000)  # 30,000
        self.assertEqual(est.size, ProjectSize.S)

    def test_size_s_at_boundary(self, mock_xs, mock_s, mock_m, mock_l):
        p = make_project("Size S Boundary Project")
        est = make_estimate(
            project=p, estimate_days=60, day_rate=1000
        )  # exactly 60,000
        self.assertEqual(est.size, ProjectSize.S)

    def test_size_m_above_s_threshold(self, mock_xs, mock_s, mock_m, mock_l):
        p = make_project("Size M Project")
        est = make_estimate(project=p, estimate_days=100, day_rate=1000)  # 100,000
        self.assertEqual(est.size, ProjectSize.M)

    def test_size_m_at_boundary(self, mock_xs, mock_s, mock_m, mock_l):
        p = make_project("Size M Boundary Project")
        est = make_estimate(
            project=p, estimate_days=200, day_rate=1000
        )  # exactly 200,000
        self.assertEqual(est.size, ProjectSize.M)

    def test_size_l_above_m_threshold(self, mock_xs, mock_s, mock_m, mock_l):
        p = make_project("Size L Project")
        est = make_estimate(project=p, estimate_days=300, day_rate=1000)  # 300,000
        self.assertEqual(est.size, ProjectSize.L)

    def test_size_l_at_boundary(self, mock_xs, mock_s, mock_m, mock_l):
        p = make_project("Size L Boundary Project")
        est = make_estimate(
            project=p, estimate_days=500, day_rate=1000
        )  # exactly 500,000
        self.assertEqual(est.size, ProjectSize.L)

    def test_size_xl_above_l_threshold(self, mock_xs, mock_s, mock_m, mock_l):
        p = make_project("Size XL Project")
        est = make_estimate(project=p, estimate_days=600, day_rate=1000)  # 600,000
        self.assertEqual(est.size, ProjectSize.XL)

    def test_size_label_xs(self, mock_xs, mock_s, mock_m, mock_l):
        p = make_project("Label XS Project")
        est = make_estimate(project=p, estimate_days=1, day_rate=100)
        self.assertEqual(est.size.label, "X-Small")

    def test_size_label_xl(self, mock_xs, mock_s, mock_m, mock_l):
        p = make_project("Label XL Project")
        est = make_estimate(project=p, estimate_days=600, day_rate=1000)
        self.assertEqual(est.size.label, "X-Large")


# ── ProjectEstimateStatusHistory ──────────────────────────────────────────────


class ProjectEstimateStatusHistoryFieldDefaultsTest(TestCase):
    def test_changed_on_auto_set(self):
        history = make_estimate_history()
        self.assertIsNotNone(history.changed_on)

    def test_note_defaults_to_empty(self):
        history = make_estimate_history()
        self.assertEqual(history.note, "")

    def test_note_stores_value(self):
        history = make_estimate_history(note="Status updated by PM")
        self.assertEqual(history.note, "Status updated by PM")

    def test_action_stores_value(self):
        history = make_estimate_history(action=ProjectEstimateAction.CREATED)
        self.assertEqual(history.action, ProjectEstimateAction.CREATED)

    def test_previous_status_can_be_null(self):
        history = make_estimate_history(previous_status=None)
        self.assertIsNone(history.previous_status)

    def test_previous_status_stores_value(self):
        history = make_estimate_history(
            previous_status=ProjectEstimateStatus.DRAFT,
            new_status=ProjectEstimateStatus.REVIEWED,
        )
        self.assertEqual(history.previous_status, ProjectEstimateStatus.DRAFT)

    def test_new_status_stores_value(self):
        history = make_estimate_history(new_status=ProjectEstimateStatus.APPROVED)
        self.assertEqual(history.new_status, ProjectEstimateStatus.APPROVED)

    def test_changed_by_defaults_to_none(self):
        history = make_estimate_history()
        self.assertIsNone(history.changed_by)

    def test_changed_by_stores_user(self):
        user = make_user()
        history = make_estimate_history(changed_by=user)
        self.assertEqual(history.changed_by, user)

    def test_estimate_linked(self):
        p = make_project("Hist Linked Est Project")
        est = make_estimate(project=p)
        history = make_estimate_history(estimate=est)
        self.assertEqual(history.estimate, est)


class ProjectEstimateStatusHistoryOrderingTest(TestCase):
    def test_ordered_by_changed_on_descending(self):
        est = make_estimate()
        h1 = make_estimate_history(estimate=est, new_status=ProjectEstimateStatus.DRAFT)
        h2 = make_estimate_history(
            estimate=est, new_status=ProjectEstimateStatus.REVIEWED
        )
        pks = list(
            ProjectEstimateStatusHistory.objects.filter(estimate=est).values_list(
                "pk", flat=True
            )
        )
        self.assertEqual(pks, [h2.pk, h1.pk])


class ProjectEstimateStatusHistoryCascadeTest(TestCase):
    def test_cascade_delete_with_estimate(self):
        est = make_estimate()
        history = make_estimate_history(estimate=est)
        history_pk = history.pk
        est.delete()
        self.assertFalse(
            ProjectEstimateStatusHistory.objects.filter(pk=history_pk).exists()
        )
