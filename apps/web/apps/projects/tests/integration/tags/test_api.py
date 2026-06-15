from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.projects.models import ProjectTag
from apps.projects.tests.factories import make_project, make_project_tag, make_tag
from apps.users.tests.factories import make_user

LIST_URL = "/api/v1/projects/{}/tags/"
DETAIL_URL = "/api/v1/projects/{}/tags/{}/"


class ProjectTagListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.project = make_project("TagListProject")
        self.tag1 = make_tag("#api-a")
        self.tag2 = make_tag("#api-b")
        make_project_tag(project=self.project, tag=self.tag1)
        make_project_tag(project=self.project, tag=self.tag2)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_tags_for_project(self):
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

    def test_tags_include_expected_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        first = response.data["data"][0]
        self.assertIn("code", first)
        self.assertIn("tag_code", first)
        self.assertIn("tag_name", first)


class ProjectTagCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("TagCreateProject")
        self.tag = make_tag("#new")

    def test_adds_tag_to_project(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"tag_code": self.tag.code},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["data"]["tag_code"], self.tag.code)

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"tag_code": self.tag.code},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_duplicate_returns_409(self):
        make_project_tag(project=self.project, tag=self.tag)
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"tag_code": self.tag.code},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_invalid_project_returns_404(self):
        response = self.client.post(
            LIST_URL.format("PROJ-999999"),
            {"tag_code": self.tag.code},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_invalid_tag_returns_404(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"tag_code": "TAG-999999"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_missing_tag_code_returns_400(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {},
            format="json",
        )
        self.assertEqual(response.status_code, 400)


class ProjectTagRetrieveAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.project = make_project("TagRetrieveProject")
        self.tag = make_tag("#retrieve")
        self.pt = make_project_tag(project=self.project, tag=self.tag)

    def test_unauthenticated_returns_401(self):
        response = self.client.get(DETAIL_URL.format(self.project.code, self.pt.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_project_tag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(DETAIL_URL.format(self.project.code, self.pt.code))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["code"], self.pt.code)
        self.assertEqual(response.data["data"]["tag_code"], self.tag.code)

    def test_invalid_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            DETAIL_URL.format(self.project.code, "PROJTAG-999999")
        )
        self.assertEqual(response.status_code, 404)


class ProjectTagUpdateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("TagUpdateProject")
        self.tag_a = make_tag("#patch-a")
        self.tag_b = make_tag("#patch-b")
        self.pt = make_project_tag(project=self.project, tag=self.tag_a)

    def test_updates_tag(self):
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, self.pt.code),
            {"tag_code": self.tag_b.code},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["tag_code"], self.tag_b.code)

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, self.pt.code),
            {"tag_code": self.tag_b.code},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_conflict_returns_409(self):
        make_project_tag(project=self.project, tag=self.tag_b)
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, self.pt.code),
            {"tag_code": self.tag_b.code},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_invalid_code_returns_404(self):
        response = self.client.patch(
            DETAIL_URL.format(self.project.code, "PROJTAG-999999"),
            {"tag_code": self.tag_b.code},
            format="json",
        )
        self.assertEqual(response.status_code, 404)


class ProjectTagDeleteAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.project = make_project("TagDeleteProject")
        self.tag = make_tag("#delete")
        self.pt = make_project_tag(project=self.project, tag=self.tag)

    def test_unauthenticated_returns_401(self):
        response = self.client.delete(
            DETAIL_URL.format(self.project.code, self.pt.code)
        )
        self.assertEqual(response.status_code, 401)

    def test_removes_project_tag(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            DETAIL_URL.format(self.project.code, self.pt.code)
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ProjectTag.objects.filter(pk=self.pt.pk).exists())

    def test_invalid_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            DETAIL_URL.format(self.project.code, "PROJTAG-999999")
        )
        self.assertEqual(response.status_code, 404)
