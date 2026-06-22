from django.test import TestCase
from rest_framework.test import APIClient

from apps.configurations.tests.factories import mark_setup_complete
from apps.projects.models import ProjectContact
from apps.projects.tests.factories import (
    make_contact,
    make_project,
    make_project_contact,
)
from apps.users.tests.factories import make_user

LIST_URL = "/api/v1/projects/{}/contacts/"
DETAIL_URL = "/api/v1/projects/{}/contacts/{}/"


class ProjectContactListAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.project = make_project("List API Project")
        make_project_contact(
            project=self.project,
            contact=make_contact(name="Alice", email="alice@example.com"),
        )
        make_project_contact(
            project=self.project,
            contact=make_contact(name="Bob", email="bob@example.com"),
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertEqual(response.status_code, 401)

    def test_returns_contacts_for_project(self):
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

    def test_contacts_include_expected_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        first = response.data["data"][0]
        for field in (
            "code",
            "contact_code",
            "contact_name",
            "contact_email",
            "role",
            "role_display",
        ):
            self.assertIn(field, first)

    def test_contacts_ordered_by_contact_name(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        names = [item["contact_name"] for item in response.data["data"]]
        self.assertEqual(names, sorted(names))

    def test_excludes_contacts_from_other_projects(self):
        other = make_project("Other Project")
        make_project_contact(
            project=other,
            contact=make_contact(name="Zara", email="zara@example.com"),
        )
        self.client.force_authenticate(user=self.user)
        response = self.client.get(LIST_URL.format(self.project.code))
        self.assertEqual(len(response.data["data"]), 2)


class ProjectContactCreateAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.client.force_authenticate(user=self.user)
        self.project = make_project("Create API Project")

    def test_creates_project_contact(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"name": "Alice", "email": "alice@example.com", "role": "project"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_response_contains_code(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"name": "Alice", "email": "alice@example.com", "role": "project"},
            format="json",
        )
        self.assertTrue(response.data["data"]["code"].startswith("PROJCT-"))

    def test_response_contains_contact_fields(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"name": "Alice", "email": "alice@example.com", "role": "finance"},
            format="json",
        )
        data = response.data["data"]
        self.assertEqual(data["contact_name"], "Alice")
        self.assertEqual(data["contact_email"], "alice@example.com")
        self.assertEqual(data["role"], "finance")
        self.assertEqual(data["role_display"], "Finance")

    def test_creates_contact_if_not_existing(self):
        from apps.contacts.models import Contact

        self.assertEqual(Contact.objects.count(), 0)
        self.client.post(
            LIST_URL.format(self.project.code),
            {"name": "New Person", "email": "new@example.com", "role": "project"},
            format="json",
        )
        self.assertEqual(Contact.objects.filter(name="New Person").count(), 1)

    def test_reuses_existing_contact(self):
        from apps.contacts.models import Contact

        existing = make_contact(name="Existing", email="existing@example.com")
        self.client.post(
            LIST_URL.format(self.project.code),
            {"name": "Existing", "email": "existing@example.com", "role": "project"},
            format="json",
        )
        self.assertEqual(Contact.objects.filter(name="Existing").count(), 1)
        pc = ProjectContact.objects.get(project=self.project)
        self.assertEqual(pc.contact_id, existing.pk)

    def test_blank_email_accepted(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"name": "No Email", "email": "", "role": "project"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_omitted_email_accepted(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"name": "No Email Field", "role": "project"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)

    def test_unauthenticated_returns_401(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"name": "Alice", "email": "alice@example.com", "role": "project"},
            format="json",
        )
        self.assertEqual(response.status_code, 401)

    def test_duplicate_contact_returns_409(self):
        contact = make_contact(name="Alice", email="alice@example.com")
        make_project_contact(project=self.project, contact=contact)
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"name": "Alice", "email": "alice@example.com", "role": "finance"},
            format="json",
        )
        self.assertEqual(response.status_code, 409)

    def test_invalid_project_returns_404(self):
        response = self.client.post(
            LIST_URL.format("PROJ-999999"),
            {"name": "Alice", "email": "alice@example.com", "role": "project"},
            format="json",
        )
        self.assertEqual(response.status_code, 404)

    def test_missing_name_returns_400(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"email": "alice@example.com", "role": "project"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_role_returns_400(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"name": "Alice", "email": "alice@example.com", "role": "invalid"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_invalid_email_format_returns_400(self):
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"name": "Alice", "email": "not-an-email", "role": "project"},
            format="json",
        )
        self.assertEqual(response.status_code, 400)

    def test_same_contact_on_different_project_is_allowed(self):
        other = make_project("Other Project")
        make_project_contact(
            project=other,
            contact=make_contact(name="Shared", email="shared@example.com"),
        )
        response = self.client.post(
            LIST_URL.format(self.project.code),
            {"name": "Shared", "email": "shared@example.com", "role": "project"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)


class ProjectContactDestroyAPITest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.client = APIClient()
        self.user = make_user(is_superuser=True)
        self.project = make_project("Delete API Project")
        self.pc = make_project_contact(
            project=self.project,
            contact=make_contact(name="Delete Me", email="delete@example.com"),
        )

    def test_unauthenticated_returns_401(self):
        response = self.client.delete(
            DETAIL_URL.format(self.project.code, self.pc.code)
        )
        self.assertEqual(response.status_code, 401)

    def test_removes_project_contact(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            DETAIL_URL.format(self.project.code, self.pc.code)
        )
        self.assertEqual(response.status_code, 204)
        self.assertFalse(ProjectContact.objects.filter(pk=self.pc.pk).exists())

    def test_invalid_contact_code_returns_404(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.delete(
            DETAIL_URL.format(self.project.code, "PROJCT-999999")
        )
        self.assertEqual(response.status_code, 404)

    def test_does_not_delete_underlying_contact(self):
        from apps.contacts.models import Contact

        contact_pk = self.pc.contact_id
        self.client.force_authenticate(user=self.user)
        self.client.delete(DETAIL_URL.format(self.project.code, self.pc.code))
        self.assertTrue(Contact.objects.filter(pk=contact_pk).exists())
