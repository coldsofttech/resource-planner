import json

from django.test import TestCase

from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.core.types import ListParams
from apps.tags.models import Tag
from apps.tags.services import TagExportService, TagService
from apps.tags.tests.factories import make_tag
from apps.users.tests.factories import make_user


def make_service(user=None):
    return TagService(user=user)


# ── list ──────────────────────────────────────────────────────────────────────


class TagServiceListTest(TestCase):
    def setUp(self):
        self.svc = make_service()
        make_tag("backend")
        make_tag("frontend")
        make_tag("ops")

    def test_returns_all_tags(self):
        result = self.svc.list(ListParams())
        self.assertEqual(len(result.results), 3)

    def test_returns_paginated_result(self):
        result = self.svc.list(ListParams())
        self.assertIsNotNone(result.pagination)

    def test_search_by_name(self):
        result = self.svc.list(ListParams(search="back"))
        names = [t.name for t in result.results]
        self.assertTrue(any("back" in n for n in names))

    def test_search_returns_empty_for_no_match(self):
        result = self.svc.list(ListParams(search="zzznomatch"))
        self.assertEqual(len(result.results), 0)

    def test_page_size_limits_results(self):
        result = self.svc.list(ListParams(page_size=2))
        self.assertLessEqual(len(result.results), 2)


# ── get ───────────────────────────────────────────────────────────────────────


class TagServiceGetTest(TestCase):
    def setUp(self):
        self.svc = make_service()
        self.tag = make_tag("backend")

    def test_returns_tag_by_code(self):
        result = self.svc.get(self.tag.code)
        self.assertEqual(result, self.tag)

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.get("TAG-9999")


# ── create ────────────────────────────────────────────────────────────────────


class TagServiceCreateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)

    def test_creates_tag(self):
        tag = self.svc.create(name="backend")
        self.assertIsNotNone(tag.pk)

    def test_name_is_normalised_to_hash_lowercase(self):
        tag = self.svc.create(name="Backend")
        self.assertEqual(tag.name, "#backend")

    def test_sets_created_by(self):
        tag = self.svc.create(name="backend")
        self.assertEqual(tag.created_by, self.user)

    def test_code_is_assigned(self):
        tag = self.svc.create(name="backend")
        self.assertTrue(tag.code.startswith("TAG-"))

    def test_raises_conflict_on_duplicate_name(self):
        self.svc.create(name="backend")
        with self.assertRaises(AlreadyExistsException):
            self.svc.create(name="backend")

    def test_raises_conflict_case_insensitive(self):
        self.svc.create(name="backend")
        with self.assertRaises(AlreadyExistsException):
            self.svc.create(name="BACKEND")


# ── update ────────────────────────────────────────────────────────────────────


class TagServiceUpdateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = make_service(user=self.user)
        self.tag = make_tag("backend")

    def test_updates_name(self):
        updated = self.svc.update(self.tag.code, name="devops")
        self.assertEqual(updated.name, "#devops")

    def test_sets_updated_by(self):
        updated = self.svc.update(self.tag.code, name="devops")
        self.assertEqual(updated.updated_by, self.user)

    def test_raises_conflict_on_duplicate_name(self):
        make_tag("frontend")
        with self.assertRaises(AlreadyExistsException):
            self.svc.update(self.tag.code, name="frontend")

    def test_same_name_no_conflict(self):
        updated = self.svc.update(self.tag.code, name=self.tag.name)
        self.assertIsNotNone(updated.pk)

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.update("TAG-9999", name="x")

    def test_no_change_when_name_is_none(self):
        before_name = self.tag.name
        updated = self.svc.update(self.tag.code)
        self.assertEqual(updated.name, before_name)


# ── delete ────────────────────────────────────────────────────────────────────


class TagServiceDeleteTest(TestCase):
    def setUp(self):
        self.svc = make_service()

    def test_deletes_tag(self):
        tag = make_tag("backend")
        self.svc.delete(tag.code)
        self.assertFalse(Tag.objects.filter(pk=tag.pk).exists())

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.delete("TAG-9999")


# ── TagExportService ──────────────────────────────────────────────────────────


class TagExportServiceTest(TestCase):
    def setUp(self):
        make_tag("backend")
        make_tag("frontend")
        self.svc = TagExportService()

    def test_csv_export_contains_tag_names(self):
        response = self.svc.export(fields=["name"], export_format="csv")
        content = response.content.decode()
        self.assertIn("backend", content)
        self.assertIn("frontend", content)

    def test_json_export_returns_list(self):
        response = self.svc.export(fields=["name"], export_format="json")
        data = json.loads(response.content.decode())
        self.assertIsInstance(data, list)

    def test_search_filter_includes_matching_tag(self):
        response = self.svc.export(
            fields=["name"], export_format="csv", filters={"search": "back"}
        )
        content = response.content.decode()
        self.assertIn("backend", content)
        self.assertNotIn("frontend", content)

    def test_search_filter_case_insensitive(self):
        response = self.svc.export(
            fields=["name"], export_format="csv", filters={"search": "BACK"}
        )
        content = response.content.decode()
        self.assertIn("backend", content)

    def test_empty_search_returns_all(self):
        response = self.svc.export(
            fields=["name"], export_format="csv", filters={"search": ""}
        )
        content = response.content.decode()
        self.assertIn("backend", content)
        self.assertIn("frontend", content)

    def test_unsupported_format_raises_validation_exception(self):
        with self.assertRaises(ValidationException):
            self.svc.export(fields=["name"], export_format="xml")
