from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.projects.models import ProjectLink
from apps.projects.tests.factories import make_project, make_project_link
from apps.users.tests.factories import make_user

LIST_URL = "/api/v1/projects/{}/links/"
DETAIL_URL = "/api/v1/projects/{}/links/{}/"


class ProjectLinkListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.project = make_project("ListAPIProject")
        make_project_link(project=self.project, title="Link A", url="https://a.com")
        make_project_link(project=self.project, title="Link B", url="https://b.com")

    def test_unauthenticated_returns_401(self):
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_links_for_project(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["data"]), 2)

    def test_response_has_success_flag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertTrue(response.data["success"])

    def test_returns_404_for_invalid_project(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format("PROJ-999999"))
        self.assertEqual(response.status_code, 404)

    def test_links_include_expected_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        first = response.data["data"][0]
        for field in ("code", "project_code", "title", "url"):
            self.assertIn(field, first)

    def test_links_ordered_by_title(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        titles = [item["title"] for item in response.data["data"]]
        self.assertEqual(titles, sorted(titles))

    def test_excludes_links_from_other_projects(self):
        other = make_project("Other")
        make_project_link(project=other, title="Other Link")
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertEqual(len(response.data["data"]), 2)


class ProjectLinkCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("CreateAPIProject")

    def test_creates_link(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"title": "New Link", "url": "https://new.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["title"], "New Link")
        self.assertEqual(response.data["data"]["url"], "https://new.com")

    def test_response_contains_code(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"title": "Coded", "url": "https://coded.com"},
            format="json",
        )
        self.assertTrue(response.data["data"]["code"].startswith("PROJLNK-"))

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"title": "X", "url": "https://x.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_duplicate_title_returns_409(self):
        make_project_link(project=self.project, title="Existing")
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"title": "Existing", "url": "https://new.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_invalid_project_returns_404(self):
        response = self.client.post(
            LIST_URL.format("PROJ-999999"),
            {"title": "X", "url": "https://x.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_missing_title_returns_400(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"url": "https://x.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_missing_url_returns_400(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"title": "No URL"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_url_format_returns_400(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"title": "Bad URL", "url": "not-a-url"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_same_title_on_different_project_is_allowed(self):
        other = make_project("Other")
        make_project_link(project=other, title="Shared")
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"title": "Shared", "url": "https://shared.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)


class ProjectLinkRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.project = make_project("RetrieveAPIProject")
        self.link = make_project_link(
            project=self.project,
            title="Retrieve Me",
            url="https://retrieve.com",
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.get(DETAIL_URL.format(self.project.code, self.link.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_link(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.project.code, self.link.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["code"], self.link.code)
        self.assertEqual(response.data["data"]["title"], "Retrieve Me")
        self.assertEqual(response.data["data"]["url"], "https://retrieve.com")

    def test_invalid_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            DETAIL_URL.format(self.project.code, "PROJLNK-999999")
        )
        self.assertEqual(response.status_code, 404)


class ProjectLinkUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("UpdateAPIProject")
        self.link = make_project_link(
            project=self.project,
            title="Old Title",
            url="https://old.com",
        )

    def test_updates_title(self):
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, self.link.code),
            {"title": "New Title"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["title"], "New Title")

    def test_updates_url(self):
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, self.link.code),
            {"url": "https://new.com"},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["url"], "https://new.com")

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, self.link.code),
            {"title": "X"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_duplicate_title_returns_409(self):
        make_project_link(project=self.project, title="Conflict")
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, self.link.code),
            {"title": "Conflict"},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_invalid_code_returns_404(self):
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, "PROJLNK-999999"),
            {"title": "X"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_invalid_url_format_returns_400(self):
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, self.link.code),
            {"url": "not-a-url"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_empty_patch_returns_200(self):
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, self.link.code),
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 200)


class ProjectLinkDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.project = make_project("DeleteAPIProject")
        self.link = make_project_link(project=self.project, title="Delete Me")

    def test_unauthenticated_returns_401(self):
        response = self.client.delete(
            DETAIL_URL.format(self.project.code, self.link.code)
        )
        self.assertEqual(response.status_code, 401)

    def test_removes_link(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            DETAIL_URL.format(self.project.code, self.link.code)
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ProjectLink.objects.filter(pk=self.link.pk).exists())

    def test_invalid_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            DETAIL_URL.format(self.project.code, "PROJLNK-999999")
        )
        self.assertEqual(response.status_code, 404)
