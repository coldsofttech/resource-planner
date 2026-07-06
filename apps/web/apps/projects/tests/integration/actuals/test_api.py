from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.permissions.models import Permission
from apps.projects.models.project_actual_config import ProjectActualConfig
from apps.projects.tests.factories import make_project
from apps.users.tests.factories import make_user

CONFIG_URL = "/api/v1/projects/{}/actuals/config/"


def _grant(user, codename):
    """Assign a single Django permission to a user and clear the perm cache."""
    perm = Permission.objects.get(codename=codename, content_type__app_label="projects")
    user.user_permissions.add(perm)
    if hasattr(user, "_perm_cache"):
        del user._perm_cache
    if hasattr(user, "_user_perm_cache"):
        del user._user_perm_cache
    return user


class ProjectActualsConfigGetAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.project = make_project()

    def test_unauthenticated_returns_401(self):
        response = self.client.get(CONFIG_URL.format(self.project.code))
        self.assertEqual(response.status_code, 401)

    def test_authenticated_user_with_view_permission_returns_200(self):
        user = make_user(email="viewer@example.com")
        _grant(user, "view_project")
        self.client.force_authenticate(user=user)
        response = self.client.get(CONFIG_URL.format(self.project.code))
        self.assertEqual(response.status_code, 200)

    def test_response_contains_expected_fields(self):
        user = make_user(is_superuser=True)
        self.client.force_authenticate(user=user)
        response = self.client.get(CONFIG_URL.format(self.project.code))
        data = response.data["data"]
        self.assertIn("ignore_risk", data)
        self.assertIn("ignore_prev_fy_actuals", data)
        self.assertIn("notes", data)

    def test_returns_defaults_when_no_config_exists(self):
        user = make_user(is_superuser=True)
        self.client.force_authenticate(user=user)
        response = self.client.get(CONFIG_URL.format(self.project.code))
        data = response.data["data"]
        self.assertFalse(data["ignore_risk"])
        self.assertFalse(data["ignore_prev_fy_actuals"])
        self.assertEqual(data["notes"], "")

    def test_returns_persisted_config_values(self):
        ProjectActualConfig.objects.create(
            project=self.project,
            ignore_risk=True,
            ignore_prev_fy_actuals=True,
            notes="Test note.",
        )
        user = make_user(is_superuser=True)
        self.client.force_authenticate(user=user)
        response = self.client.get(CONFIG_URL.format(self.project.code))
        data = response.data["data"]
        self.assertTrue(data["ignore_risk"])
        self.assertTrue(data["ignore_prev_fy_actuals"])
        self.assertEqual(data["notes"], "Test note.")

    def test_returns_404_for_unknown_project_code(self):
        user = make_user(is_superuser=True)
        self.client.force_authenticate(user=user)
        response = self.client.get(CONFIG_URL.format("PROJ-NONE"))
        self.assertEqual(response.status_code, 404)


class ProjectActualsConfigPatchAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.project = make_project()

    def test_unauthenticated_returns_401(self):
        response = self.client.patch(
            CONFIG_URL.format(self.project.code),
            {"ignore_risk": True},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_user_without_change_permission_returns_403(self):
        user = make_user(email="readonly@example.com")
        _grant(user, "view_project")
        self.client.force_authenticate(user=user)
        response = self.client.patch(
            CONFIG_URL.format(self.project.code),
            {"ignore_risk": True},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_user_with_change_permission_returns_200(self):
        user = make_user(email="editor@example.com")
        _grant(user, "change_project")
        self.client.force_authenticate(user=user)
        response = self.client.patch(
            CONFIG_URL.format(self.project.code),
            {"ignore_risk": True},
            format="json",
        )
        self.assertEqual(response.status_code, 200)

    def test_patch_creates_config_record_when_none_exists(self):
        self.assertFalse(
            ProjectActualConfig.objects.filter(project=self.project).exists()
        )
        user = make_user(is_superuser=True)
        self.client.force_authenticate(user=user)
        self.client.patch(
            CONFIG_URL.format(self.project.code),
            {"ignore_risk": True},
            format="json",
        )
        self.assertTrue(
            ProjectActualConfig.objects.filter(project=self.project).exists()
        )

    def test_patch_persists_ignore_risk_to_db(self):
        user = make_user(is_superuser=True)
        self.client.force_authenticate(user=user)
        self.client.patch(
            CONFIG_URL.format(self.project.code),
            {"ignore_risk": True},
            format="json",
        )
        config = ProjectActualConfig.objects.get(project=self.project)
        self.assertTrue(config.ignore_risk)

    def test_partial_update_only_ignore_risk_leaves_notes_unchanged(self):
        ProjectActualConfig.objects.create(
            project=self.project,
            ignore_risk=False,
            ignore_prev_fy_actuals=False,
            notes="Existing note.",
        )
        user = make_user(is_superuser=True)
        self.client.force_authenticate(user=user)
        self.client.patch(
            CONFIG_URL.format(self.project.code),
            {"ignore_risk": True},
            format="json",
        )
        config = ProjectActualConfig.objects.get(project=self.project)
        self.assertTrue(config.ignore_risk)
        self.assertEqual(config.notes, "Existing note.")

    def test_response_contains_updated_values(self):
        user = make_user(is_superuser=True)
        self.client.force_authenticate(user=user)
        response = self.client.patch(
            CONFIG_URL.format(self.project.code),
            {"ignore_risk": True, "ignore_prev_fy_actuals": True, "notes": "Updated."},
            format="json",
        )
        data = response.data["data"]
        self.assertTrue(data["ignore_risk"])
        self.assertTrue(data["ignore_prev_fy_actuals"])
        self.assertEqual(data["notes"], "Updated.")

    def test_patch_with_notes_only_saves_correctly(self):
        user = make_user(is_superuser=True)
        self.client.force_authenticate(user=user)
        response = self.client.patch(
            CONFIG_URL.format(self.project.code),
            {"notes": "Notes only."},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        config = ProjectActualConfig.objects.get(project=self.project)
        self.assertEqual(config.notes, "Notes only.")

    def test_returns_404_for_unknown_project_code(self):
        user = make_user(is_superuser=True)
        self.client.force_authenticate(user=user)
        response = self.client.patch(
            CONFIG_URL.format("PROJ-NONE"),
            {"ignore_risk": True},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_subsequent_patch_updates_existing_record(self):
        user = make_user(is_superuser=True)
        self.client.force_authenticate(user=user)
        self.client.patch(
            CONFIG_URL.format(self.project.code),
            {"ignore_risk": True},
            format="json",
        )
        self.client.patch(
            CONFIG_URL.format(self.project.code),
            {"ignore_risk": False, "notes": "Second save."},
            format="json",
        )
        self.assertEqual(
            ProjectActualConfig.objects.filter(project=self.project).count(), 1
        )
        config = ProjectActualConfig.objects.get(project=self.project)
        self.assertFalse(config.ignore_risk)
        self.assertEqual(config.notes, "Second save.")
