from django.test import TestCase

from apps.core.exceptions import AlreadyExistsException, NotFoundException
from apps.projects.models import ProjectTag
from apps.projects.services import ProjectTagService
from apps.projects.tests.factories import make_project, make_project_tag, make_tag
from apps.users.tests.factories import make_user


class ProjectTagServiceGetTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.service = ProjectTagService(user=self.user)
        self.pt = make_project_tag()

    def test_get_returns_project_tag(self):
        result = self.service.get(self.pt.code)
        self.assertEqual(result.pk, self.pt.pk)

    def test_get_raises_not_found_for_invalid_code(self):
        with self.assertRaises(NotFoundException):
            self.service.get("PROJTAG-999999")


class ProjectTagServiceListTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.service = ProjectTagService(user=self.user)
        self.project = make_project("ListProject")
        self.tag1 = make_tag("#list-a")
        self.tag2 = make_tag("#list-b")
        make_project_tag(project=self.project, tag=self.tag1)
        make_project_tag(project=self.project, tag=self.tag2)

    def test_list_returns_all_tags_for_project(self):
        result = self.service.list(self.project.code)
        self.assertEqual(len(result), 2)

    def test_list_raises_not_found_for_invalid_project(self):
        with self.assertRaises(NotFoundException):
            self.service.list("PROJ-999999")

    def test_list_excludes_tags_from_other_projects(self):
        other_project = make_project("Other")
        make_project_tag(project=other_project, tag=make_tag("#other"))
        result = self.service.list(self.project.code)
        self.assertEqual(len(result), 2)


class ProjectTagServiceCreateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.service = ProjectTagService(user=self.user)
        self.project = make_project("CreateProject")
        self.tag = make_tag("#create")

    def test_create_adds_tag_to_project(self):
        obj = self.service.create(
            project_code=self.project.code, tag_code=self.tag.code
        )
        self.assertIsInstance(obj, ProjectTag)
        self.assertEqual(obj.project_id, self.project.pk)
        self.assertEqual(obj.tag_id, self.tag.pk)

    def test_create_sets_audit_fields(self):
        obj = self.service.create(
            project_code=self.project.code, tag_code=self.tag.code
        )
        self.assertEqual(obj.created_by, self.user)
        self.assertEqual(obj.updated_by, self.user)

    def test_create_assigns_code(self):
        obj = self.service.create(
            project_code=self.project.code, tag_code=self.tag.code
        )
        self.assertTrue(obj.code.startswith("PROJTAG-"))

    def test_create_raises_already_exists_on_duplicate(self):
        self.service.create(project_code=self.project.code, tag_code=self.tag.code)
        with self.assertRaises(AlreadyExistsException):
            self.service.create(project_code=self.project.code, tag_code=self.tag.code)

    def test_create_raises_not_found_for_invalid_project(self):
        with self.assertRaises(NotFoundException):
            self.service.create(project_code="PROJ-999999", tag_code=self.tag.code)

    def test_create_raises_not_found_for_invalid_tag(self):
        with self.assertRaises(NotFoundException):
            self.service.create(project_code=self.project.code, tag_code="TAG-999999")

    def test_same_tag_on_different_projects_is_allowed(self):
        other_project = make_project("Other")
        obj1 = self.service.create(
            project_code=self.project.code, tag_code=self.tag.code
        )
        obj2 = self.service.create(
            project_code=other_project.code, tag_code=self.tag.code
        )
        self.assertNotEqual(obj1.pk, obj2.pk)


class ProjectTagServiceUpdateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.service = ProjectTagService(user=self.user)
        self.project = make_project("UpdateProject")
        self.tag_a = make_tag("#update-a")
        self.tag_b = make_tag("#update-b")
        self.pt = make_project_tag(project=self.project, tag=self.tag_a)

    def test_update_changes_tag(self):
        obj = self.service.update(self.pt.code, tag_code=self.tag_b.code)
        self.assertEqual(obj.tag_id, self.tag_b.pk)

    def test_update_sets_updated_by(self):
        obj = self.service.update(self.pt.code, tag_code=self.tag_b.code)
        self.assertEqual(obj.updated_by, self.user)

    def test_update_raises_not_found_for_invalid_code(self):
        with self.assertRaises(NotFoundException):
            self.service.update("PROJTAG-999999", tag_code=self.tag_b.code)

    def test_update_raises_not_found_for_invalid_new_tag(self):
        with self.assertRaises(NotFoundException):
            self.service.update(self.pt.code, tag_code="TAG-999999")

    def test_update_raises_already_exists_when_new_tag_already_on_project(self):
        make_project_tag(project=self.project, tag=self.tag_b)
        with self.assertRaises(AlreadyExistsException):
            self.service.update(self.pt.code, tag_code=self.tag_b.code)

    def test_update_with_no_fields_is_a_noop(self):
        original_tag_id = self.pt.tag_id
        obj = self.service.update(self.pt.code)
        self.assertEqual(obj.tag_id, original_tag_id)


class ProjectTagServiceDeleteTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.service = ProjectTagService(user=self.user)
        self.pt = make_project_tag()

    def test_delete_removes_project_tag(self):
        code = self.pt.code
        self.service.delete(code)
        self.assertFalse(ProjectTag.objects.filter(code=code).exists())

    def test_delete_raises_not_found_for_invalid_code(self):
        with self.assertRaises(NotFoundException):
            self.service.delete("PROJTAG-999999")
