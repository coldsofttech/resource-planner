from django.test import TestCase

from apps.core.exceptions import AlreadyExistsException, NotFoundException
from apps.projects.models import ProjectLink
from apps.projects.services import ProjectLinkService
from apps.projects.tests.factories import make_project, make_project_link
from apps.users.tests.factories import make_user


class ProjectLinkServiceGetTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.service = ProjectLinkService(user=self.user)
        self.link = make_project_link()

    def test_get_returns_link(self):
        result = self.service.get(self.link.code)
        self.assertEqual(result.pk, self.link.pk)

    def test_get_raises_not_found_for_invalid_code(self):
        with self.assertRaises(NotFoundException):
            self.service.get("PROJLNK-999999")


class ProjectLinkServiceListTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.service = ProjectLinkService(user=self.user)
        self.project = make_project("ListProject")
        make_project_link(project=self.project, title="Link A")
        make_project_link(project=self.project, title="Link B")

    def test_list_returns_all_links_for_project(self):
        result = self.service.list(self.project.code)
        self.assertEqual(len(result), 2)

    def test_list_raises_not_found_for_invalid_project(self):
        with self.assertRaises(NotFoundException):
            self.service.list("PROJ-999999")

    def test_list_excludes_links_from_other_projects(self):
        other = make_project("Other")
        make_project_link(project=other, title="Unrelated")
        result = self.service.list(self.project.code)
        self.assertEqual(len(result), 2)


class ProjectLinkServiceCreateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.service = ProjectLinkService(user=self.user)
        self.project = make_project("CreateProject")

    def test_create_returns_project_link(self):
        obj = self.service.create(
            project_code=self.project.code,
            title="My Link",
            url="https://example.com",
        )
        self.assertIsInstance(obj, ProjectLink)

    def test_create_assigns_code(self):
        obj = self.service.create(
            project_code=self.project.code,
            title="My Link",
            url="https://example.com",
        )
        self.assertTrue(obj.code.startswith("PROJLNK-"))

    def test_create_sets_project(self):
        obj = self.service.create(
            project_code=self.project.code,
            title="My Link",
            url="https://example.com",
        )
        self.assertEqual(obj.project_id, self.project.pk)

    def test_create_sets_title_and_url(self):
        obj = self.service.create(
            project_code=self.project.code,
            title="Wiki",
            url="https://wiki.example.com",
        )
        self.assertEqual(obj.title, "Wiki")
        self.assertEqual(obj.url, "https://wiki.example.com")

    def test_create_sets_audit_fields(self):
        obj = self.service.create(
            project_code=self.project.code,
            title="Audit Link",
            url="https://example.com",
        )
        self.assertEqual(obj.created_by, self.user)
        self.assertEqual(obj.updated_by, self.user)

    def test_create_persists_to_db(self):
        self.service.create(
            project_code=self.project.code,
            title="Persisted",
            url="https://example.com",
        )
        self.assertEqual(ProjectLink.objects.filter(project=self.project).count(), 1)

    def test_create_raises_already_exists_on_duplicate_title(self):
        self.service.create(
            project_code=self.project.code,
            title="Duplicate",
            url="https://example.com",
        )
        with self.assertRaises(AlreadyExistsException):
            self.service.create(
                project_code=self.project.code,
                title="Duplicate",
                url="https://other.com",
            )

    def test_create_raises_not_found_for_invalid_project(self):
        with self.assertRaises(NotFoundException):
            self.service.create(
                project_code="PROJ-999999",
                title="Link",
                url="https://example.com",
            )

    def test_same_title_on_different_projects_is_allowed(self):
        other = make_project("Other")
        obj1 = self.service.create(
            project_code=self.project.code,
            title="Shared Title",
            url="https://example.com",
        )
        obj2 = self.service.create(
            project_code=other.code,
            title="Shared Title",
            url="https://example.com",
        )
        self.assertNotEqual(obj1.pk, obj2.pk)


class ProjectLinkServiceUpdateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.service = ProjectLinkService(user=self.user)
        self.project = make_project("UpdateProject")
        self.link = make_project_link(
            project=self.project,
            title="Original",
            url="https://original.com",
        )

    def test_update_changes_title(self):
        obj = self.service.update(self.link.code, title="Updated")
        self.assertEqual(obj.title, "Updated")

    def test_update_changes_url(self):
        obj = self.service.update(self.link.code, url="https://updated.com")
        self.assertEqual(obj.url, "https://updated.com")

    def test_update_sets_updated_by(self):
        obj = self.service.update(self.link.code, title="Changed")
        self.assertEqual(obj.updated_by, self.user)

    def test_update_with_no_fields_is_a_noop(self):
        obj = self.service.update(self.link.code)
        self.assertEqual(obj.title, "Original")
        self.assertEqual(obj.url, "https://original.com")

    def test_update_same_title_on_same_record_does_not_raise(self):
        obj = self.service.update(self.link.code, title="Original")
        self.assertEqual(obj.title, "Original")

    def test_update_raises_not_found_for_invalid_code(self):
        with self.assertRaises(NotFoundException):
            self.service.update("PROJLNK-999999", title="X")

    def test_update_raises_already_exists_when_title_conflicts(self):
        make_project_link(project=self.project, title="Other Link")
        with self.assertRaises(AlreadyExistsException):
            self.service.update(self.link.code, title="Other Link")

    def test_update_title_conflict_only_within_same_project(self):
        other = make_project("Other")
        make_project_link(project=other, title="Conflict Title")
        obj = self.service.update(self.link.code, title="Conflict Title")
        self.assertEqual(obj.title, "Conflict Title")


class ProjectLinkServiceDeleteTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.service = ProjectLinkService(user=self.user)
        self.link = make_project_link()

    def test_delete_removes_link(self):
        code = self.link.code
        self.service.delete(code)
        self.assertFalse(ProjectLink.objects.filter(code=code).exists())

    def test_delete_raises_not_found_for_invalid_code(self):
        with self.assertRaises(NotFoundException):
            self.service.delete("PROJLNK-999999")
