from django.test import TestCase

from apps.core.exceptions import NotFoundException, ValidationException
from apps.core.types import ListParams
from apps.projects.constants import ProjectEstimateAction, ProjectEstimateStatus
from apps.projects.models import ProjectEstimate, ProjectEstimateStatusHistory
from apps.projects.services import ProjectEstimateService
from apps.projects.tests.factories import (
    make_estimate,
    make_estimate_history,
    make_project,
)
from apps.users.tests.factories import make_user, make_user_with_profile


def make_service(user=None):
    return ProjectEstimateService(user=user)


# ── list ──────────────────────────────────────────────────────────────────────


class ProjectEstimateServiceListTest(TestCase):
    def setUp(self):
        self.project = make_project("List Project")
        make_estimate(project=self.project, version=1)
        make_estimate(
            project=self.project,
            version=2,
            status=ProjectEstimateStatus.REVIEWED,
            is_active=False,
        )
        self.svc = make_service()

    def test_returns_all_estimates_for_project(self):
        result = self.svc.list(project_code=self.project.code, params=ListParams())
        self.assertEqual(result.pagination.total_count, 2)

    def test_filters_by_status(self):
        result = self.svc.list(
            project_code=self.project.code,
            params=ListParams(filters={"status": ProjectEstimateStatus.DRAFT}),
        )
        statuses = [e.status for e in result.results]
        self.assertIn(ProjectEstimateStatus.DRAFT, statuses)
        self.assertNotIn(ProjectEstimateStatus.REVIEWED, statuses)

    def test_raises_not_found_for_unknown_project(self):
        with self.assertRaises(NotFoundException):
            self.svc.list(project_code="PROJ-99999", params=ListParams())


# ── get ───────────────────────────────────────────────────────────────────────


class ProjectEstimateServiceGetTest(TestCase):
    def setUp(self):
        self.estimate = make_estimate()
        self.svc = make_service()

    def test_returns_estimate_by_code(self):
        result = self.svc.get(code=self.estimate.code)
        self.assertEqual(result.pk, self.estimate.pk)

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.get(code="PROJEST-99999")


# ── create ────────────────────────────────────────────────────────────────────


class ProjectEstimateServiceCreateTest(TestCase):
    def setUp(self):
        self.project = make_project("Create Project")
        self.actor = make_user(email="actor@example.com")
        self.svc = make_service(user=self.actor)

    def test_creates_estimate_with_defaults(self):
        _, shared_profile = make_user_with_profile(email="shared@example.com")
        obj = self.svc.create(
            project_code=self.project.code,
            shared_by_codes=[shared_profile.code],
        )
        self.assertIsNotNone(obj.pk)
        self.assertEqual(obj.project, self.project)
        self.assertEqual(obj.status, ProjectEstimateStatus.DRAFT)
        self.assertEqual(obj.version, 1)

    def test_version_increments_per_project(self):
        _, shared_profile = make_user_with_profile(email="shared@example.com")
        e1 = self.svc.create(
            project_code=self.project.code,
            shared_by_codes=[shared_profile.code],
        )
        e2 = self.svc.create(
            project_code=self.project.code,
            shared_by_codes=[shared_profile.code],
        )
        self.assertEqual(e1.version, 1)
        self.assertEqual(e2.version, 2)

    def test_sets_shared_by(self):
        shared_user, shared_profile = make_user_with_profile(email="shared@example.com")
        obj = self.svc.create(
            project_code=self.project.code,
            shared_by_codes=[shared_profile.code],
        )
        self.assertIn(shared_user, obj.shared_by.all())

    def test_sets_reviewed_by(self):
        _, shared_profile = make_user_with_profile(email="shared@example.com")
        reviewer, reviewer_profile = make_user_with_profile(
            email="reviewer@example.com"
        )
        obj = self.svc.create(
            project_code=self.project.code,
            shared_by_codes=[shared_profile.code],
            reviewed_by_codes=[reviewer_profile.code],
        )
        self.assertIn(reviewer, obj.reviewed_by.all())

    def test_records_created_history_entry(self):
        _, shared_profile = make_user_with_profile(email="shared@example.com")
        obj = self.svc.create(
            project_code=self.project.code,
            shared_by_codes=[shared_profile.code],
        )
        history = ProjectEstimateStatusHistory.objects.filter(estimate=obj)
        self.assertEqual(history.count(), 1)
        self.assertEqual(history.first().action, ProjectEstimateAction.CREATED)

    def test_history_entry_has_correct_new_status(self):
        _, shared_profile = make_user_with_profile(email="shared@example.com")
        obj = self.svc.create(
            project_code=self.project.code,
            shared_by_codes=[shared_profile.code],
            status=ProjectEstimateStatus.REVIEWED,
        )
        history = ProjectEstimateStatusHistory.objects.filter(estimate=obj).first()
        self.assertEqual(history.new_status, ProjectEstimateStatus.REVIEWED)

    def test_raises_not_found_for_unknown_project(self):
        with self.assertRaises(NotFoundException):
            self.svc.create(
                project_code="PROJ-99999",
                shared_by_codes=["USER-1"],
            )

    def test_raises_validation_error_for_invalid_user_codes(self):
        with self.assertRaises(ValidationException):
            self.svc.create(
                project_code=self.project.code,
                shared_by_codes=["NONEXISTENT-CODE"],
            )

    def test_raises_validation_error_for_invalid_reviewed_by_codes(self):
        _, shared_profile = make_user_with_profile(email="shared@example.com")
        with self.assertRaises(ValidationException):
            self.svc.create(
                project_code=self.project.code,
                shared_by_codes=[shared_profile.code],
                reviewed_by_codes=["NONEXISTENT-CODE"],
            )


# ── update ────────────────────────────────────────────────────────────────────


class ProjectEstimateServiceUpdateTest(TestCase):
    def setUp(self):
        self.project = make_project("Update Project")
        self.actor = make_user(email="actor@example.com")
        self.svc = make_service(user=self.actor)

    def test_updates_estimate_days(self):
        est = make_estimate(project=self.project)
        updated = self.svc.update(code=est.code, estimate_days=20)
        self.assertEqual(float(updated.estimate_days), 20.0)

    def test_updates_contingency_percentage(self):
        est = make_estimate(project=self.project)
        updated = self.svc.update(code=est.code, contingency_percentage=15)
        self.assertEqual(float(updated.contingency_percentage), 15.0)

    def test_updates_status_from_draft_to_reviewed(self):
        est = make_estimate(project=self.project, status=ProjectEstimateStatus.DRAFT)
        updated = self.svc.update(code=est.code, status=ProjectEstimateStatus.REVIEWED)
        self.assertEqual(updated.status, ProjectEstimateStatus.REVIEWED)

    def test_records_updated_history_entry(self):
        est = make_estimate(project=self.project)
        self.svc.update(code=est.code, estimate_days=5)
        history = ProjectEstimateStatusHistory.objects.filter(
            estimate=est, action=ProjectEstimateAction.UPDATED
        )
        self.assertTrue(history.exists())

    def test_raises_validation_error_when_editing_approved(self):
        est = make_estimate(project=self.project, status=ProjectEstimateStatus.APPROVED)
        with self.assertRaises(ValidationException):
            self.svc.update(code=est.code, estimate_days=99)

    def test_raises_validation_error_when_editing_superseded(self):
        est = make_estimate(
            project=self.project, status=ProjectEstimateStatus.SUPERSEDED
        )
        with self.assertRaises(ValidationException):
            self.svc.update(code=est.code, estimate_days=99)

    def test_approving_supersedes_previous_approved(self):
        prev = make_estimate(
            project=self.project,
            version=1,
            status=ProjectEstimateStatus.APPROVED,
        )
        new_est = make_estimate(
            project=self.project,
            version=2,
            status=ProjectEstimateStatus.REVIEWED,
        )
        self.svc.update(code=new_est.code, status=ProjectEstimateStatus.APPROVED)
        prev.refresh_from_db()
        new_est.refresh_from_db()
        self.assertEqual(prev.status, ProjectEstimateStatus.SUPERSEDED)
        self.assertEqual(new_est.status, ProjectEstimateStatus.APPROVED)

    def test_supersede_history_recorded_for_previous_approved(self):
        prev = make_estimate(
            project=self.project,
            version=1,
            status=ProjectEstimateStatus.APPROVED,
        )
        new_est = make_estimate(
            project=self.project,
            version=2,
            status=ProjectEstimateStatus.REVIEWED,
        )
        self.svc.update(code=new_est.code, status=ProjectEstimateStatus.APPROVED)
        supersede_entry = ProjectEstimateStatusHistory.objects.filter(
            estimate=prev,
            action=ProjectEstimateAction.SUPERSEDED,
        )
        self.assertTrue(supersede_entry.exists())

    def test_approve_action_history_recorded_for_new_estimate(self):
        est = make_estimate(
            project=self.project,
            status=ProjectEstimateStatus.REVIEWED,
        )
        self.svc.update(code=est.code, status=ProjectEstimateStatus.APPROVED)
        history = ProjectEstimateStatusHistory.objects.filter(
            estimate=est,
            action=ProjectEstimateAction.APPROVED,
        )
        self.assertTrue(history.exists())

    def test_only_same_project_estimates_are_superseded(self):
        other_project = make_project("Other Project")
        other_approved = make_estimate(
            project=other_project,
            version=1,
            status=ProjectEstimateStatus.APPROVED,
        )
        est = make_estimate(
            project=self.project,
            version=1,
            status=ProjectEstimateStatus.REVIEWED,
        )
        self.svc.update(code=est.code, status=ProjectEstimateStatus.APPROVED)
        other_approved.refresh_from_db()
        self.assertEqual(other_approved.status, ProjectEstimateStatus.APPROVED)

    def test_updates_shared_by(self):
        est = make_estimate(project=self.project)
        new_user, new_profile = make_user_with_profile(email="new@example.com")
        self.svc.update(code=est.code, shared_by_codes=[new_profile.code])
        self.assertIn(new_user, est.shared_by.all())

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.update(code="PROJEST-99999", estimate_days=10)


# ── activate / deactivate ─────────────────────────────────────────────────────


class ProjectEstimateServiceActivateTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_activates_inactive_estimate(self):
        est = make_estimate(is_active=False)
        result = self.svc.activate(code=est.code)
        self.assertTrue(result.is_active)

    def test_activate_is_idempotent(self):
        est = make_estimate(is_active=True)
        result = self.svc.activate(code=est.code)
        self.assertTrue(result.is_active)

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.activate(code="PROJEST-99999")


class ProjectEstimateServiceDeactivateTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_deactivates_active_estimate(self):
        est = make_estimate(is_active=True)
        result = self.svc.deactivate(code=est.code)
        self.assertFalse(result.is_active)

    def test_deactivate_is_idempotent(self):
        est = make_estimate(is_active=False)
        result = self.svc.deactivate(code=est.code)
        self.assertFalse(result.is_active)

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.deactivate(code="PROJEST-99999")


# ── delete ────────────────────────────────────────────────────────────────────


class ProjectEstimateServiceDeleteTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_deletes_draft_estimate(self):
        est = make_estimate(status=ProjectEstimateStatus.DRAFT)
        code = est.code
        self.svc.delete(code=code)
        self.assertFalse(ProjectEstimate.objects.filter(code=code).exists())

    def test_deletes_reviewed_estimate(self):
        est = make_estimate(status=ProjectEstimateStatus.REVIEWED)
        code = est.code
        self.svc.delete(code=code)
        self.assertFalse(ProjectEstimate.objects.filter(code=code).exists())

    def test_raises_validation_error_when_deleting_approved(self):
        est = make_estimate(status=ProjectEstimateStatus.APPROVED)
        with self.assertRaises(ValidationException):
            self.svc.delete(code=est.code)

    def test_raises_validation_error_when_deleting_superseded(self):
        est = make_estimate(status=ProjectEstimateStatus.SUPERSEDED)
        with self.assertRaises(ValidationException):
            self.svc.delete(code=est.code)

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.delete(code="PROJEST-99999")


# ── history ───────────────────────────────────────────────────────────────────


class ProjectEstimateServiceHistoryTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_returns_history_entries(self):
        est = make_estimate()
        make_estimate_history(estimate=est, action=ProjectEstimateAction.CREATED)
        make_estimate_history(estimate=est, action=ProjectEstimateAction.UPDATED)
        result = self.svc.history(code=est.code)
        self.assertEqual(len(result), 2)

    def test_returns_empty_when_no_history(self):
        est = make_estimate()
        result = self.svc.history(code=est.code)
        self.assertEqual(len(result), 0)

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.history(code="PROJEST-99999")
