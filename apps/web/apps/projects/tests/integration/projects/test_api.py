from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.projects.models import Project, ProjectCollaborator
from apps.projects.tests.factories import (
    make_programme,
    make_project,
    make_project_collaborator,
    make_project_status,
    make_project_type,
)
from apps.teams.tests.factories import make_team
from apps.users.tests.factories import make_user

LIST_URL = "/api/v1/projects/"
STATS_URL = "/api/v1/projects/stats/"
OPTIONS_URL = "/api/v1/projects/options/"
DETAIL_URL = "/api/v1/projects/{}/"
ACTIVATE_URL = "/api/v1/projects/{}/activate/"
DEACTIVATE_URL = "/api/v1/projects/{}/deactivate/"
COLLABORATORS_URL = "/api/v1/projects/{}/collaborators/"
COLLABORATOR_DETAIL_URL = "/api/v1/projects/{}/collaborators/{}/"
IMPORT_URL = "/api/v1/projects/import/"
IMPORT_SPECS_URL = "/api/v1/projects/import/specs/"
IMPORT_SAMPLE_URL = "/api/v1/projects/import/sample/"
EXPORT_URL = "/api/v1/projects/export/"
EXPORT_SPECS_URL = "/api/v1/projects/export/specs/"


# ── GET /projects/ ────────────────────────────────────────────────────────────


class ProjectListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        make_project("Alpha", is_active=True)
        make_project("Inactive", is_active=False)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 401)

    def test_defaults_to_active_only(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertEqual(response.status_code, 200)
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("Alpha", names)
        self.assertNotIn("Inactive", names)

    def test_is_active_false_returns_inactive(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"is_active": "false"})
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("Inactive", names)
        self.assertNotIn("Alpha", names)

    def test_response_has_pagination(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertIn("pagination", response.data["data"])

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL)
        self.assertTrue(response.data["success"])

    def test_search_filters_by_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL, {"search": "Alpha"})
        names = [r["name"] for r in response.data["data"]["results"]]
        self.assertIn("Alpha", names)
        self.assertEqual(len(names), 1)


# ── POST /projects/ ───────────────────────────────────────────────────────────


class ProjectCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.pt = make_project_type("Standard")
        self.st = make_project_status("Active")

    def test_creates_project(self):
        response = self.client.post(
            LIST_URL,
            {
                "name": "New Project",
                "project_type_code": self.pt.code,
                "status_code": self.st.code,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(Project.objects.filter(name="New Project").exists())

    def test_returns_201_on_success(self):
        response = self.client.post(
            LIST_URL,
            {
                "name": "Created",
                "project_type_code": self.pt.code,
                "status_code": self.st.code,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.post(LIST_URL, {}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_duplicate_name_returns_409(self):
        make_project("Duplicate")
        response = self.client.post(
            LIST_URL,
            {
                "name": "Duplicate",
                "project_type_code": self.pt.code,
                "status_code": self.st.code,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_missing_name_returns_400(self):
        response = self.client.post(
            LIST_URL,
            {"project_type_code": self.pt.code, "status_code": self.st.code},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_missing_project_type_returns_400(self):
        response = self.client.post(
            LIST_URL,
            {"name": "No Type", "status_code": self.st.code},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_missing_status_returns_400(self):
        response = self.client.post(
            LIST_URL,
            {"name": "No Status", "project_type_code": self.pt.code},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_response_includes_code(self):
        response = self.client.post(
            LIST_URL,
            {
                "name": "Code Check",
                "project_type_code": self.pt.code,
                "status_code": self.st.code,
            },
            format="json",
        )
        self.assertIn("code", response.data["data"])

    def test_display_name_returned_in_response(self):
        prog = make_programme("Core")
        response = self.client.post(
            LIST_URL,
            {
                "name": "Display Test",
                "project_type_code": self.pt.code,
                "status_code": self.st.code,
                "programme_code": prog.code,
            },
            format="json",
        )
        self.assertEqual(response.data["data"]["display_name"], "Core: Display Test")


# ── GET /projects/<code>/ ─────────────────────────────────────────────────────


class ProjectRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("Known Project")

    def test_returns_200_for_known_code(self):
        response = self.client.get(DETAIL_URL.format(self.project.code))
        self.assertEqual(response.status_code, 200)

    def test_returns_404_for_unknown_code(self):
        response = self.client.get(DETAIL_URL.format("PROJ-99999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.get(DETAIL_URL.format(self.project.code))
        self.assertEqual(response.status_code, 401)

    def test_response_includes_collaborators(self):
        response = self.client.get(DETAIL_URL.format(self.project.code))
        self.assertIn("collaborators", response.data["data"])

    def test_response_includes_display_name(self):
        response = self.client.get(DETAIL_URL.format(self.project.code))
        self.assertIn("display_name", response.data["data"])


# ── PATCH /projects/<code>/ ───────────────────────────────────────────────────


class ProjectUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("Original")

    def test_updates_name(self):
        response = self.client.patch(
            DETAIL_URL.format(self.project.code),
            {"name": "Updated"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, "Updated")

    def test_returns_404_for_unknown_code(self):
        response = self.client.patch(
            DETAIL_URL.format("PROJ-99999"),
            {"name": "Ghost"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_duplicate_name_returns_409(self):
        make_project("Taken")
        response = self.client.patch(
            DETAIL_URL.format(self.project.code),
            {"name": "Taken"},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.patch(DETAIL_URL.format(self.project.code), {}, format="json")
        self.assertEqual(response.status_code, 401)


# ── DELETE /projects/<code>/ ──────────────────────────────────────────────────


class ProjectDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("To Delete")

    def test_deletes_project(self):
        response = self.client.delete(DETAIL_URL.format(self.project.code))
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Project.objects.filter(code=self.project.code).exists())

    def test_returns_404_for_unknown_code(self):
        response = self.client.delete(DETAIL_URL.format("PROJ-99999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.delete(DETAIL_URL.format(self.project.code))
        self.assertEqual(response.status_code, 401)


# ── POST /projects/<code>/activate/ ──────────────────────────────────────────


class ProjectActivateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("Dormant", is_active=False)

    def test_activates_project(self):
        response = self.client.post(ACTIVATE_URL.format(self.project.code))
        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        self.assertTrue(self.project.is_active)

    def test_returns_404_for_unknown_code(self):
        response = self.client.post(ACTIVATE_URL.format("PROJ-99999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.post(ACTIVATE_URL.format(self.project.code))
        self.assertEqual(response.status_code, 401)


# ── POST /projects/<code>/deactivate/ ────────────────────────────────────────


class ProjectDeactivateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("Running")

    def test_deactivates_project(self):
        response = self.client.post(DEACTIVATE_URL.format(self.project.code))
        self.assertEqual(response.status_code, 200)
        self.project.refresh_from_db()
        self.assertFalse(self.project.is_active)

    def test_returns_404_for_unknown_code(self):
        response = self.client.post(DEACTIVATE_URL.format("PROJ-99999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.post(DEACTIVATE_URL.format(self.project.code))
        self.assertEqual(response.status_code, 401)


# ── GET /projects/stats/ ─────────────────────────────────────────────────────


class ProjectStatsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        make_project("Active One")
        make_project("Inactive One", is_active=False)

    def test_returns_200(self):
        response = self.client.get(STATS_URL)
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.get(STATS_URL)
        self.assertEqual(response.status_code, 401)

    def test_response_has_total(self):
        response = self.client.get(STATS_URL)
        self.assertIn("total", response.data["data"])


# ── GET /projects/options/ ────────────────────────────────────────────────────


class ProjectOptionsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        make_project("Active Option")
        make_project("Hidden", is_active=False)

    def test_returns_200(self):
        response = self.client.get(OPTIONS_URL)
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.get(OPTIONS_URL)
        self.assertEqual(response.status_code, 401)

    def test_only_returns_active_projects(self):
        response = self.client.get(OPTIONS_URL)
        names = [p["name"] for p in response.data["data"]]
        self.assertIn("Active Option", names)
        self.assertNotIn("Hidden", names)


# ── GET /projects/<code>/collaborators/ ───────────────────────────────────────


class ProjectCollaboratorsListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("Collab Project")
        self.team = make_team("Collab Team")
        make_project_collaborator(self.project, self.team)

    def test_returns_200_with_collaborators(self):
        response = self.client.get(COLLABORATORS_URL.format(self.project.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 1)

    def test_returns_team_code(self):
        response = self.client.get(COLLABORATORS_URL.format(self.project.code))
        self.assertEqual(response.data["data"][0]["team_code"], self.team.code)

    def test_returns_404_for_unknown_project(self):
        response = self.client.get(COLLABORATORS_URL.format("PROJ-99999"))
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.get(COLLABORATORS_URL.format(self.project.code))
        self.assertEqual(response.status_code, 401)


# ── POST /projects/<code>/collaborators/ ──────────────────────────────────────


class ProjectAddCollaboratorAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("Add Collab Project")
        self.team = make_team("New Collaborator")

    def test_adds_collaborator(self):
        response = self.client.post(
            COLLABORATORS_URL.format(self.project.code),
            {"team_code": self.team.code},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            ProjectCollaborator.objects.filter(
                project=self.project, team=self.team
            ).exists()
        )

    def test_duplicate_returns_409(self):
        make_project_collaborator(self.project, self.team)
        response = self.client.post(
            COLLABORATORS_URL.format(self.project.code),
            {"team_code": self.team.code},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_assigned_team_as_collaborator_returns_422(self):
        pt = make_project_type("T")
        st = make_project_status("S")
        p = Project.objects.create(
            name="Assigned Conflict",
            project_type=pt,
            status=st,
            assigned_team=self.team,
        )
        response = self.client.post(
            COLLABORATORS_URL.format(p.code),
            {"team_code": self.team.code},
            format="json",
        )
        self.assertEqual(response.status_code, 422)

    def test_unknown_team_code_returns_404(self):
        response = self.client.post(
            COLLABORATORS_URL.format(self.project.code),
            {"team_code": "TEAM-99999"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_returns_404_for_unknown_project(self):
        response = self.client.post(
            COLLABORATORS_URL.format("PROJ-99999"),
            {"team_code": self.team.code},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.post(
            COLLABORATORS_URL.format(self.project.code),
            {"team_code": self.team.code},
            format="json",
        )
        self.assertEqual(response.status_code, 401)


# ── DELETE /projects/<code>/collaborators/<team_code>/ ────────────────────────


class ProjectRemoveCollaboratorAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("Remove Collab Project")
        self.team = make_team("To Remove")
        make_project_collaborator(self.project, self.team)

    def test_removes_collaborator(self):
        response = self.client.delete(
            COLLABORATOR_DETAIL_URL.format(self.project.code, self.team.code)
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(
            ProjectCollaborator.objects.filter(
                project=self.project, team=self.team
            ).exists()
        )

    def test_returns_404_for_unknown_team(self):
        other_team = make_team("Not A Collaborator")
        response = self.client.delete(
            COLLABORATOR_DETAIL_URL.format(self.project.code, other_team.code)
        )
        self.assertEqual(response.status_code, 404)

    def test_returns_404_for_unknown_project(self):
        response = self.client.delete(
            COLLABORATOR_DETAIL_URL.format("PROJ-99999", self.team.code)
        )
        self.assertEqual(response.status_code, 404)

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.delete(
            COLLABORATOR_DETAIL_URL.format(self.project.code, self.team.code)
        )
        self.assertEqual(response.status_code, 401)


# ── GET /projects/import/specs/ ───────────────────────────────────────────────


class ProjectImportSpecsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_returns_200(self):
        response = self.client.get(IMPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.get(IMPORT_SPECS_URL)
        self.assertEqual(response.status_code, 401)


# ── GET /projects/export/specs/ ───────────────────────────────────────────────


class ProjectExportSpecsAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)

    def test_returns_200(self):
        response = self.client.get(EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.get(EXPORT_SPECS_URL)
        self.assertEqual(response.status_code, 401)


# ── GET /projects/export/ ─────────────────────────────────────────────────────


class ProjectExportAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        make_project("Exportable")

    def test_returns_200_csv(self):
        response = self.client.get(EXPORT_URL, {"type": "csv"})
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_returns_401(self):
        client = APIClient()
        response = client.get(EXPORT_URL)
        self.assertEqual(response.status_code, 401)
