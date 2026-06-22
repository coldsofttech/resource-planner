from django.test import TestCase

from apps.contacts.models import Contact
from apps.core.exceptions import AlreadyExistsException, NotFoundException
from apps.projects.models import ProjectContact
from apps.projects.services import ProjectContactService
from apps.projects.tests.factories import (
    make_contact,
    make_project,
    make_project_contact,
)
from apps.users.tests.factories import make_user


class ProjectContactServiceGetTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.service = ProjectContactService(user=self.user)
        self.pc = make_project_contact()

    def test_get_returns_project_contact(self):
        result = self.service.get(self.pc.code)
        self.assertEqual(result.pk, self.pc.pk)

    def test_get_raises_not_found_for_invalid_code(self):
        with self.assertRaises(NotFoundException):
            self.service.get("PROJCT-999999")


class ProjectContactServiceListTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.service = ProjectContactService(user=self.user)
        self.project = make_project("List Project")
        make_project_contact(
            project=self.project,
            contact=make_contact(name="Alice", email="alice@example.com"),
        )
        make_project_contact(
            project=self.project,
            contact=make_contact(name="Bob", email="bob@example.com"),
        )

    def test_list_returns_all_contacts_for_project(self):
        result = self.service.list(self.project.code)
        self.assertEqual(len(result), 2)

    def test_list_raises_not_found_for_invalid_project(self):
        with self.assertRaises(NotFoundException):
            self.service.list("PROJ-999999")

    def test_list_excludes_contacts_from_other_projects(self):
        other = make_project("Other Project")
        make_project_contact(
            project=other,
            contact=make_contact(name="Zara", email="zara@example.com"),
        )
        result = self.service.list(self.project.code)
        self.assertEqual(len(result), 2)


class ProjectContactServiceCreateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.service = ProjectContactService(user=self.user)
        self.project = make_project("Create Project")

    def test_create_returns_project_contact(self):
        obj = self.service.create(
            project_code=self.project.code,
            name="Alice",
            email="alice@example.com",
            role="project",
        )
        self.assertIsInstance(obj, ProjectContact)

    def test_create_assigns_code(self):
        obj = self.service.create(
            project_code=self.project.code,
            name="Alice",
            email="alice@example.com",
            role="project",
        )
        self.assertTrue(obj.code.startswith("PROJCT-"))

    def test_create_sets_project(self):
        obj = self.service.create(
            project_code=self.project.code,
            name="Alice",
            email="alice@example.com",
            role="project",
        )
        self.assertEqual(obj.project_id, self.project.pk)

    def test_create_sets_role(self):
        obj = self.service.create(
            project_code=self.project.code,
            name="Alice",
            email="alice@example.com",
            role="finance",
        )
        self.assertEqual(obj.role, "finance")

    def test_create_sets_audit_fields(self):
        obj = self.service.create(
            project_code=self.project.code,
            name="Alice",
            email="alice@example.com",
            role="project",
        )
        self.assertEqual(obj.created_by, self.user)
        self.assertEqual(obj.updated_by, self.user)

    def test_create_persists_to_db(self):
        self.service.create(
            project_code=self.project.code,
            name="Alice",
            email="alice@example.com",
            role="project",
        )
        self.assertEqual(ProjectContact.objects.filter(project=self.project).count(), 1)

    def test_create_finds_existing_contact(self):
        existing = make_contact(name="Alice", email="alice@example.com")
        obj = self.service.create(
            project_code=self.project.code,
            name="Alice",
            email="alice@example.com",
            role="project",
        )
        self.assertEqual(obj.contact_id, existing.pk)
        self.assertEqual(Contact.objects.filter(name="Alice").count(), 1)

    def test_create_creates_new_contact_if_not_found(self):
        self.assertEqual(Contact.objects.count(), 0)
        self.service.create(
            project_code=self.project.code,
            name="New Person",
            email="new@example.com",
            role="project",
        )
        self.assertEqual(Contact.objects.filter(name="New Person").count(), 1)

    def test_create_new_contact_has_audit_user(self):
        self.service.create(
            project_code=self.project.code,
            name="Created By",
            email="created@example.com",
            role="project",
        )
        contact = Contact.objects.get(name="Created By")
        self.assertEqual(contact.created_by, self.user)

    def test_create_raises_already_exists_for_duplicate_project_contact(self):
        contact = make_contact(name="Alice", email="alice@example.com")
        make_project_contact(project=self.project, contact=contact)
        with self.assertRaises(AlreadyExistsException):
            self.service.create(
                project_code=self.project.code,
                name="Alice",
                email="alice@example.com",
                role="finance",
            )

    def test_create_raises_not_found_for_invalid_project(self):
        with self.assertRaises(NotFoundException):
            self.service.create(
                project_code="PROJ-999999",
                name="Alice",
                email="alice@example.com",
                role="project",
            )

    def test_create_raises_value_error_for_invalid_role(self):
        with self.assertRaises(ValueError):
            self.service.create(
                project_code=self.project.code,
                name="Alice",
                email="alice@example.com",
                role="invalid_role",
            )

    def test_same_contact_on_different_projects_is_allowed(self):
        other = make_project("Other Project")
        obj1 = self.service.create(
            project_code=self.project.code,
            name="Shared",
            email="shared@example.com",
            role="project",
        )
        obj2 = self.service.create(
            project_code=other.code,
            name="Shared",
            email="shared@example.com",
            role="project",
        )
        self.assertNotEqual(obj1.pk, obj2.pk)
        self.assertEqual(obj1.contact_id, obj2.contact_id)


class ProjectContactServiceDeleteTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.service = ProjectContactService(user=self.user)
        self.pc = make_project_contact()

    def test_delete_removes_project_contact(self):
        code = self.pc.code
        self.service.delete(code=code)
        self.assertFalse(ProjectContact.objects.filter(code=code).exists())

    def test_delete_raises_not_found_for_invalid_code(self):
        with self.assertRaises(NotFoundException):
            self.service.delete(code="PROJCT-999999")

    def test_delete_does_not_remove_underlying_contact(self):
        contact_pk = self.pc.contact_id
        self.service.delete(code=self.pc.code)
        self.assertTrue(Contact.objects.filter(pk=contact_pk).exists())
