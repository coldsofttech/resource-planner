from django.test import TestCase

from apps.audit import selectors
from apps.audit.constants import Action
from apps.audit.models import Audit
from apps.audit.tests.factories import make_audit
from apps.users.tests.factories import make_user

# ── get_audit_entries — no filters ────────────────────────────────────────────


class GetAuditEntriesAllTest(TestCase):
    def test_returns_empty_queryset_when_no_entries(self):
        self.assertEqual(selectors.get_audit_entries().count(), 0)

    def test_returns_all_entries_without_filters(self):
        make_audit(module="projects")
        make_audit(module="teams")
        make_audit(module="sprints")
        self.assertEqual(selectors.get_audit_entries().count(), 3)

    def test_returns_queryset_type(self):
        from django.db.models import QuerySet

        self.assertIsInstance(selectors.get_audit_entries(), QuerySet)


# ── get_audit_entries — module filter ────────────────────────────────────────


class GetAuditEntriesModuleFilterTest(TestCase):
    def setUp(self):
        make_audit(module="projects")
        make_audit(module="projects")
        make_audit(module="teams")

    def test_filters_by_module(self):
        result = selectors.get_audit_entries(module="projects")
        self.assertEqual(result.count(), 2)

    def test_excludes_other_modules(self):
        result = selectors.get_audit_entries(module="projects")
        modules = list(result.values_list("module", flat=True))
        self.assertNotIn("teams", modules)

    def test_empty_string_module_returns_all(self):
        result = selectors.get_audit_entries(module="")
        self.assertEqual(result.count(), 3)

    def test_none_module_returns_all(self):
        result = selectors.get_audit_entries(module=None)
        self.assertEqual(result.count(), 3)

    def test_unknown_module_returns_empty(self):
        result = selectors.get_audit_entries(module="nonexistent")
        self.assertEqual(result.count(), 0)


# ── get_audit_entries — resource_type filter ──────────────────────────────────


class GetAuditEntriesResourceTypeFilterTest(TestCase):
    def setUp(self):
        make_audit(resource_type="project")
        make_audit(resource_type="project")
        make_audit(resource_type="team")

    def test_filters_by_resource_type(self):
        result = selectors.get_audit_entries(resource_type="project")
        self.assertEqual(result.count(), 2)

    def test_excludes_other_resource_types(self):
        result = selectors.get_audit_entries(resource_type="team")
        types = list(result.values_list("resource_type", flat=True))
        self.assertNotIn("project", types)

    def test_none_resource_type_returns_all(self):
        result = selectors.get_audit_entries(resource_type=None)
        self.assertEqual(result.count(), 3)


# ── get_audit_entries — resource_code filter ──────────────────────────────────


class GetAuditEntriesResourceCodeFilterTest(TestCase):
    def setUp(self):
        make_audit(resource_code="PROJ-1")
        make_audit(resource_code="PROJ-1")
        make_audit(resource_code="PROJ-2")

    def test_filters_by_resource_code(self):
        result = selectors.get_audit_entries(resource_code="PROJ-1")
        self.assertEqual(result.count(), 2)

    def test_excludes_other_codes(self):
        result = selectors.get_audit_entries(resource_code="PROJ-2")
        self.assertEqual(result.count(), 1)

    def test_none_resource_code_returns_all(self):
        result = selectors.get_audit_entries(resource_code=None)
        self.assertEqual(result.count(), 3)

    def test_unknown_code_returns_empty(self):
        result = selectors.get_audit_entries(resource_code="PROJ-999")
        self.assertEqual(result.count(), 0)


# ── get_audit_entries — action filter ────────────────────────────────────────


class GetAuditEntriesActionFilterTest(TestCase):
    def setUp(self):
        make_audit(action=Action.CREATE)
        make_audit(action=Action.CREATE)
        make_audit(action=Action.UPDATE)
        make_audit(action=Action.DELETE)

    def test_filters_by_create_action(self):
        result = selectors.get_audit_entries(action=Action.CREATE)
        self.assertEqual(result.count(), 2)

    def test_filters_by_update_action(self):
        result = selectors.get_audit_entries(action=Action.UPDATE)
        self.assertEqual(result.count(), 1)

    def test_filters_by_delete_action(self):
        result = selectors.get_audit_entries(action=Action.DELETE)
        self.assertEqual(result.count(), 1)

    def test_none_action_returns_all(self):
        result = selectors.get_audit_entries(action=None)
        self.assertEqual(result.count(), 4)

    def test_empty_string_action_returns_all(self):
        result = selectors.get_audit_entries(action="")
        self.assertEqual(result.count(), 4)

    def test_unknown_action_returns_empty(self):
        result = selectors.get_audit_entries(action="import")
        self.assertEqual(result.count(), 0)


# ── get_audit_entries — stacked filters ───────────────────────────────────────


class GetAuditEntriesStackedFiltersTest(TestCase):
    def setUp(self):
        make_audit(module="projects", resource_type="project", action=Action.CREATE)
        make_audit(module="projects", resource_type="project", action=Action.UPDATE)
        make_audit(module="projects", resource_type="team", action=Action.CREATE)
        make_audit(module="teams", resource_type="team", action=Action.CREATE)

    def test_filters_by_module_and_resource_type(self):
        result = selectors.get_audit_entries(module="projects", resource_type="project")
        self.assertEqual(result.count(), 2)

    def test_filters_by_module_and_action(self):
        result = selectors.get_audit_entries(module="projects", action=Action.CREATE)
        self.assertEqual(result.count(), 2)

    def test_filters_by_all_three(self):
        result = selectors.get_audit_entries(
            module="projects", resource_type="project", action=Action.CREATE
        )
        self.assertEqual(result.count(), 1)

    def test_no_match_returns_empty(self):
        result = selectors.get_audit_entries(module="sprints", resource_type="project")
        self.assertEqual(result.count(), 0)


class GetAuditEntriesAllFourFiltersTest(TestCase):
    def setUp(self):
        make_audit(
            module="projects",
            resource_type="project",
            resource_code="PROJ-1",
            action=Action.CREATE,
        )
        make_audit(
            module="projects",
            resource_type="project",
            resource_code="PROJ-2",
            action=Action.CREATE,
        )
        make_audit(
            module="projects",
            resource_type="project",
            resource_code="PROJ-1",
            action=Action.UPDATE,
        )

    def test_all_four_filters_combined(self):
        result = selectors.get_audit_entries(
            module="projects",
            resource_type="project",
            resource_code="PROJ-1",
            action=Action.CREATE,
        )
        self.assertEqual(result.count(), 1)

    def test_all_four_filters_no_match(self):
        result = selectors.get_audit_entries(
            module="projects",
            resource_type="project",
            resource_code="PROJ-1",
            action=Action.DELETE,
        )
        self.assertEqual(result.count(), 0)


# ── get_audit_entries — select_related ───────────────────────────────────────


class GetAuditEntriesSelectRelatedTest(TestCase):
    def test_actor_is_preloaded(self):
        user = make_user()
        make_audit(actor=user)
        with self.assertNumQueries(1):
            entries = list(selectors.get_audit_entries())
            for entry in entries:
                _ = entry.actor_id


# ── get_audit_entries_for_resource ───────────────────────────────────────────


class GetAuditEntriesForResourceTest(TestCase):
    def setUp(self):
        make_audit(resource_code="PROJ-1")
        make_audit(resource_code="PROJ-1")
        make_audit(resource_code="PROJ-2")

    def test_returns_only_matching_resource(self):
        result = selectors.get_audit_entries_for_resource(resource_code="PROJ-1")
        self.assertEqual(result.count(), 2)

    def test_excludes_other_resources(self):
        result = selectors.get_audit_entries_for_resource(resource_code="PROJ-1")
        codes = list(result.values_list("resource_code", flat=True))
        self.assertNotIn("PROJ-2", codes)

    def test_returns_empty_for_unknown_code(self):
        result = selectors.get_audit_entries_for_resource(resource_code="PROJ-999")
        self.assertEqual(result.count(), 0)

    def test_returns_empty_when_no_entries(self):
        Audit.objects.all().delete()
        result = selectors.get_audit_entries_for_resource(resource_code="PROJ-1")
        self.assertEqual(result.count(), 0)

    def test_does_not_return_null_code_entries(self):
        Audit.objects.create(
            module="projects",
            resource_type="project",
            action=Action.CREATE,
            resource_code=None,
        )
        result = selectors.get_audit_entries_for_resource(resource_code="PROJ-1")
        codes = list(result.values_list("resource_code", flat=True))
        self.assertNotIn(None, codes)

    def test_actor_is_preloaded(self):
        user = make_user()
        make_audit(resource_code="PROJ-3", actor=user)
        with self.assertNumQueries(1):
            entries = list(
                selectors.get_audit_entries_for_resource(resource_code="PROJ-3")
            )
            for entry in entries:
                _ = entry.actor_id

    def test_ordered_by_timestamp_descending(self):
        e1 = make_audit(resource_code="PROJ-5", module="a")
        make_audit(resource_code="PROJ-5", module="b")
        e3 = make_audit(resource_code="PROJ-5", module="c")
        entries = list(selectors.get_audit_entries_for_resource(resource_code="PROJ-5"))
        self.assertEqual(entries[0].pk, e3.pk)
        self.assertEqual(entries[2].pk, e1.pk)


# ── get_audit_entries_for_module ─────────────────────────────────────────────


class GetAuditEntriesForModuleTest(TestCase):
    def setUp(self):
        make_audit(module="projects")
        make_audit(module="projects")
        make_audit(module="teams")

    def test_returns_only_matching_module(self):
        result = selectors.get_audit_entries_for_module(module="projects")
        self.assertEqual(result.count(), 2)

    def test_excludes_other_modules(self):
        result = selectors.get_audit_entries_for_module(module="projects")
        modules = list(result.values_list("module", flat=True))
        self.assertNotIn("teams", modules)

    def test_returns_empty_for_unknown_module(self):
        result = selectors.get_audit_entries_for_module(module="sprints")
        self.assertEqual(result.count(), 0)

    def test_returns_empty_when_no_entries(self):
        Audit.objects.all().delete()
        result = selectors.get_audit_entries_for_module(module="projects")
        self.assertEqual(result.count(), 0)

    def test_actor_is_preloaded(self):
        user = make_user()
        make_audit(module="finance", actor=user)
        with self.assertNumQueries(1):
            entries = list(selectors.get_audit_entries_for_module(module="finance"))
            for entry in entries:
                _ = entry.actor_id

    def test_ordered_by_timestamp_descending(self):
        e1 = make_audit(module="reports", resource_code="R1")
        make_audit(module="reports", resource_code="R2")
        e3 = make_audit(module="reports", resource_code="R3")
        entries = list(selectors.get_audit_entries_for_module(module="reports"))
        self.assertEqual(entries[0].pk, e3.pk)
        self.assertEqual(entries[2].pk, e1.pk)


# ── get_audit_entries_for_actor ──────────────────────────────────────────────


class GetAuditEntriesForActorTest(TestCase):
    def setUp(self):
        self.user_a = make_user("a@example.com")
        self.user_b = make_user("b@example.com")
        make_audit(actor=self.user_a)
        make_audit(actor=self.user_a)
        make_audit(actor=self.user_b)
        make_audit(actor=None)

    def test_returns_entries_for_specific_actor(self):
        result = selectors.get_audit_entries_for_actor(actor=self.user_a)
        self.assertEqual(result.count(), 2)

    def test_excludes_other_actor_entries(self):
        result = selectors.get_audit_entries_for_actor(actor=self.user_a)
        actors = list(result.values_list("actor_id", flat=True))
        self.assertNotIn(self.user_b.pk, actors)

    def test_excludes_anonymous_entries(self):
        result = selectors.get_audit_entries_for_actor(actor=self.user_a)
        self.assertFalse(result.filter(actor__isnull=True).exists())

    def test_returns_empty_when_actor_has_no_entries(self):
        new_user = make_user("c@example.com")
        result = selectors.get_audit_entries_for_actor(actor=new_user)
        self.assertEqual(result.count(), 0)

    def test_returns_anonymous_entries_when_actor_is_none(self):
        result = selectors.get_audit_entries_for_actor(actor=None)
        self.assertEqual(result.count(), 1)
        self.assertTrue(result.filter(actor__isnull=True).exists())
