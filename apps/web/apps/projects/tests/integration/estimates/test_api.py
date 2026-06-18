from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.projects.constants import ProjectEstimateAction, ProjectEstimateStatus
from apps.projects.models import ProjectEstimate
from apps.projects.tests.factories import (
    make_estimate,
    make_estimate_history,
    make_project,
)
from apps.users.tests.factories import make_user, make_user_with_profile

LIST_URL = "/api/v1/projects/{}/estimates/"
DETAIL_URL = "/api/v1/projects/{}/estimates/{}/"
ACTIVATE_URL = "/api/v1/projects/{}/estimates/{}/activate/"
DEACTIVATE_URL = "/api/v1/projects/{}/estimates/{}/deactivate/"
HISTORY_URL = "/api/v1/projects/{}/estimates/{}/history/"
EXPORT_SPECS_URL = "/api/v1/projects/{}/estimates/export/specs/"
EXPORT_URL = "/api/v1/projects/{}/estimates/export/"


# ── GET /projects/<code>/estimates/ ──────────────────────────────────────────


class ProjectEstimateListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.project = make_project("Estimate List Project")
        make_estimate(project=self.project, version=1)
        make_estimate(project=self.project, version=2)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_200_with_estimates(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertEqual(response.status_code, 200)

    def test_response_has_pagination(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertIn("pagination", response.data["data"])

    def test_returns_all_estimates_for_project(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertEqual(response.data["data"]["pagination"]["total_count"], 2)

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertTrue(response.data["success"])

    def test_returns_404_for_unknown_project(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format("PROJ-99999"))
        self.assertEqual(response.status_code, 404)


# ── POST /projects/<code>/estimates/ ─────────────────────────────────────────


class ProjectEstimateCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("Estimate Create Project")
        _, self.shared_profile = make_user_with_profile(email="shared@example.com")

    def test_creates_estimate(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"shared_by_codes": [self.shared_profile.code]},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(ProjectEstimate.objects.filter(project=self.project).exists())

    def test_returns_201_on_success(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"shared_by_codes": [self.shared_profile.code]},
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.post(
            LIST_URL.format(self.project.code),
            {"shared_by_codes": [self.shared_profile.code]},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_missing_shared_by_codes_returns_400(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_empty_shared_by_codes_returns_400(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"shared_by_codes": []},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_user_code_returns_422(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"shared_by_codes": ["NONEXISTENT-CODE"]},
            format="json",
        )
        self.assertEqual(response.status_code, 422)

    def test_invalid_estimate_link_returns_400(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {
                "shared_by_codes": [self.shared_profile.code],
                "estimate_link": "not-a-url",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_response_includes_code(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"shared_by_codes": [self.shared_profile.code]},
            format="json",
        )
        self.assertIn("code", response.data["data"])

    def test_response_includes_version(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"shared_by_codes": [self.shared_profile.code]},
            format="json",
        )
        self.assertIn("version", response.data["data"])

    def test_returns_404_for_unknown_project(self):
        response = self.client.post(
            LIST_URL.format("PROJ-99999"),
            {"shared_by_codes": [self.shared_profile.code]},
            format="json",
        )
        self.assertEqual(response.status_code, 404)


# ── GET /projects/<code>/estimates/<estimate_code>/ ───────────────────────────


class ProjectEstimateRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("Estimate Retrieve Project")
        self.estimate = make_estimate(project=self.project)

    def test_returns_200_for_known_code(self):
        response = self.client.get(
            DETAIL_URL.format(self.project.code, self.estimate.code)
        )
        self.assertEqual(response.status_code, 200)

    def test_returns_404_for_unknown_estimate_code(self):
        response = self.client.get(
            DETAIL_URL.format(self.project.code, "PROJEST-99999")
        )
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.get(DETAIL_URL.format(self.project.code, self.estimate.code))
        self.assertEqual(response.status_code, 401)

    def test_response_includes_status(self):
        response = self.client.get(
            DETAIL_URL.format(self.project.code, self.estimate.code)
        )
        self.assertIn("status", response.data["data"])

    def test_response_includes_version(self):
        response = self.client.get(
            DETAIL_URL.format(self.project.code, self.estimate.code)
        )
        self.assertIn("version", response.data["data"])

    def test_response_includes_total_cost(self):
        response = self.client.get(
            DETAIL_URL.format(self.project.code, self.estimate.code)
        )
        self.assertIn("total_cost", response.data["data"])


# ── PATCH /projects/<code>/estimates/<estimate_code>/ ────────────────────────


class ProjectEstimateUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("Estimate Update Project")

    def test_updates_estimate_days(self):
        est = make_estimate(project=self.project, status=ProjectEstimateStatus.DRAFT)
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, est.code),
            {"estimate_days": "25.0"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        est.refresh_from_db()
        self.assertEqual(float(est.estimate_days), 25.0)

    def test_updates_status_to_reviewed(self):
        est = make_estimate(project=self.project, status=ProjectEstimateStatus.DRAFT)
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, est.code),
            {"status": "REVIEWED"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        est.refresh_from_db()
        self.assertEqual(est.status, ProjectEstimateStatus.REVIEWED)

    def test_editing_approved_estimate_returns_422(self):
        est = make_estimate(project=self.project, status=ProjectEstimateStatus.APPROVED)
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, est.code),
            {"estimate_days": "30.0"},
            format="json",
        )
        self.assertEqual(response.status_code, 422)

    def test_editing_superseded_estimate_returns_422(self):
        est = make_estimate(
            project=self.project, status=ProjectEstimateStatus.SUPERSEDED
        )
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, est.code),
            {"estimate_days": "30.0"},
            format="json",
        )
        self.assertEqual(response.status_code, 422)

    def test_returns_404_for_unknown_estimate_code(self):
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, "PROJEST-99999"),
            {"estimate_days": "10.0"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        est = make_estimate(project=self.project)
        client = APIClient()
        response = client.patch(
            DETAIL_URL.format(self.project.code, est.code),
            {"estimate_days": "5.0"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_invalid_status_choice_returns_400(self):
        est = make_estimate(project=self.project)
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, est.code),
            {"status": "BOGUS"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)


# ── DELETE /projects/<code>/estimates/<estimate_code>/ ───────────────────────


class ProjectEstimateDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("Estimate Delete Project")

    def test_deletes_draft_estimate(self):
        est = make_estimate(project=self.project, status=ProjectEstimateStatus.DRAFT)
        response = self.client.delete(DETAIL_URL.format(self.project.code, est.code))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ProjectEstimate.objects.filter(code=est.code).exists())

    def test_deleting_approved_estimate_returns_422(self):
        est = make_estimate(project=self.project, status=ProjectEstimateStatus.APPROVED)
        response = self.client.delete(DETAIL_URL.format(self.project.code, est.code))
        self.assertEqual(response.status_code, 422)

    def test_deleting_superseded_estimate_returns_422(self):
        est = make_estimate(
            project=self.project, status=ProjectEstimateStatus.SUPERSEDED
        )
        response = self.client.delete(DETAIL_URL.format(self.project.code, est.code))
        self.assertEqual(response.status_code, 422)

    def test_returns_404_for_unknown_estimate_code(self):
        response = self.client.delete(
            DETAIL_URL.format(self.project.code, "PROJEST-99999")
        )
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        est = make_estimate(project=self.project)
        client = APIClient()
        response = client.delete(DETAIL_URL.format(self.project.code, est.code))
        self.assertEqual(response.status_code, 401)


# ── POST .../activate/ ────────────────────────────────────────────────────────


class ProjectEstimateActivateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("Estimate Activate Project")

    def test_activates_estimate(self):
        est = make_estimate(project=self.project, is_active=False)
        response = self.client.post(ACTIVATE_URL.format(self.project.code, est.code))
        self.assertEqual(response.status_code, 200)
        est.refresh_from_db()
        self.assertTrue(est.is_active)

    def test_returns_404_for_unknown_code(self):
        response = self.client.post(
            ACTIVATE_URL.format(self.project.code, "PROJEST-99999")
        )
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        est = make_estimate(project=self.project)
        client = APIClient()
        response = client.post(ACTIVATE_URL.format(self.project.code, est.code))
        self.assertEqual(response.status_code, 401)


# ── POST .../deactivate/ ─────────────────────────────────────────────────────


class ProjectEstimateDeactivateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("Estimate Deactivate Project")

    def test_deactivates_estimate(self):
        est = make_estimate(project=self.project, is_active=True)
        response = self.client.post(DEACTIVATE_URL.format(self.project.code, est.code))
        self.assertEqual(response.status_code, 200)
        est.refresh_from_db()
        self.assertFalse(est.is_active)

    def test_returns_404_for_unknown_code(self):
        response = self.client.post(
            DEACTIVATE_URL.format(self.project.code, "PROJEST-99999")
        )
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        est = make_estimate(project=self.project)
        client = APIClient()
        response = client.post(DEACTIVATE_URL.format(self.project.code, est.code))
        self.assertEqual(response.status_code, 401)


# ── GET .../history/ ─────────────────────────────────────────────────────────


class ProjectEstimateHistoryAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("Estimate History Project")

    def test_returns_history_entries(self):
        est = make_estimate(project=self.project)
        make_estimate_history(estimate=est, action=ProjectEstimateAction.CREATED)
        response = self.client.get(HISTORY_URL.format(self.project.code, est.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 1)

    def test_returns_empty_list_when_no_history(self):
        est = make_estimate(project=self.project)
        response = self.client.get(HISTORY_URL.format(self.project.code, est.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 0)

    def test_returns_404_for_unknown_estimate_code(self):
        response = self.client.get(
            HISTORY_URL.format(self.project.code, "PROJEST-99999")
        )
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        est = make_estimate(project=self.project)
        client = APIClient()
        response = client.get(HISTORY_URL.format(self.project.code, est.code))
        self.assertEqual(response.status_code, 401)

    def test_history_entry_includes_action(self):
        est = make_estimate(project=self.project)
        make_estimate_history(estimate=est, action=ProjectEstimateAction.CREATED)
        response = self.client.get(HISTORY_URL.format(self.project.code, est.code))
        self.assertIn("action", response.data["data"][0])


# ── GET .../export/specs/ ────────────────────────────────────────────────────


class ProjectEstimateExportSpecsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("Estimate Export Specs Project")

    def test_returns_200(self):
        response = self.client.get(EXPORT_SPECS_URL.format(self.project.code))
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.get(EXPORT_SPECS_URL.format(self.project.code))
        self.assertEqual(response.status_code, 401)


# ── GET .../export/ ──────────────────────────────────────────────────────────


class ProjectEstimateExportAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("Estimate Export CSV Project")
        make_estimate(project=self.project)

    def test_returns_200_csv(self):
        response = self.client.get(
            EXPORT_URL.format(self.project.code), {"type": "csv"}
        )
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.get(EXPORT_URL.format(self.project.code))
        self.assertEqual(response.status_code, 401)
