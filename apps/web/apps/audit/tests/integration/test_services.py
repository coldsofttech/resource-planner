from django.test import TestCase

from apps.audit.constants import Action
from apps.audit.models import Audit
from apps.audit.services import AuditService
from apps.users.tests.factories import make_user

# ── AuditService.log ───────────────────────────────────────────────────────────


class AuditServiceLogTest(TestCase):
    def test_returns_audit_instance(self):
        entry = AuditService.log(
            module="projects",
            resource_type="project",
            action=Action.CREATE,
        )
        self.assertIsInstance(entry, Audit)

    def test_creates_db_record(self):
        AuditService.log(
            module="projects",
            resource_type="project",
            action=Action.UPDATE,
        )
        self.assertEqual(Audit.objects.count(), 1)

    def test_persists_module(self):
        entry = AuditService.log(
            module="teams",
            resource_type="team",
            action=Action.CREATE,
        )
        self.assertEqual(entry.module, "teams")

    def test_persists_resource_type(self):
        entry = AuditService.log(
            module="teams",
            resource_type="team",
            action=Action.CREATE,
        )
        self.assertEqual(entry.resource_type, "team")

    def test_persists_resource_code(self):
        entry = AuditService.log(
            module="teams",
            resource_type="team",
            resource_code="TEAM-5",
            action=Action.UPDATE,
        )
        self.assertEqual(entry.resource_code, "TEAM-5")

    def test_persists_action(self):
        entry = AuditService.log(
            module="projects",
            resource_type="project",
            action=Action.DELETE,
        )
        self.assertEqual(entry.action, Action.DELETE)

    def test_persists_before_snapshot(self):
        snapshot = {"name": "Old", "is_active": True}
        entry = AuditService.log(
            module="projects",
            resource_type="project",
            action=Action.UPDATE,
            before=snapshot,
        )
        self.assertEqual(entry.before, snapshot)

    def test_persists_after_snapshot(self):
        snapshot = {"name": "New", "is_active": False}
        entry = AuditService.log(
            module="projects",
            resource_type="project",
            action=Action.UPDATE,
            after=snapshot,
        )
        self.assertEqual(entry.after, snapshot)

    def test_persists_actor(self):
        user = make_user()
        entry = AuditService.log(
            module="projects",
            resource_type="project",
            action=Action.CREATE,
            actor=user,
        )
        self.assertEqual(entry.actor, user)

    def test_actor_defaults_to_none(self):
        entry = AuditService.log(
            module="projects",
            resource_type="project",
            action=Action.CREATE,
        )
        self.assertIsNone(entry.actor)

    def test_resource_code_defaults_to_none(self):
        entry = AuditService.log(
            module="projects",
            resource_type="project",
            action=Action.CREATE,
        )
        self.assertIsNone(entry.resource_code)

    def test_before_defaults_to_none(self):
        entry = AuditService.log(
            module="projects",
            resource_type="project",
            action=Action.CREATE,
        )
        self.assertIsNone(entry.before)

    def test_after_defaults_to_none(self):
        entry = AuditService.log(
            module="projects",
            resource_type="project",
            action=Action.CREATE,
        )
        self.assertIsNone(entry.after)


# ── AuditService.log_create ────────────────────────────────────────────────────


class AuditServiceLogCreateTest(TestCase):
    def test_sets_action_to_create(self):
        entry = AuditService.log_create(
            module="projects",
            resource_type="project",
            after={"name": "Alpha"},
        )
        self.assertEqual(entry.action, Action.CREATE)

    def test_stores_after_snapshot(self):
        snapshot = {"name": "Alpha", "is_active": True}
        entry = AuditService.log_create(
            module="projects",
            resource_type="project",
            after=snapshot,
        )
        self.assertEqual(entry.after, snapshot)

    def test_before_is_always_none(self):
        entry = AuditService.log_create(
            module="projects",
            resource_type="project",
            after={"name": "Alpha"},
        )
        self.assertIsNone(entry.before)

    def test_accepts_resource_code(self):
        entry = AuditService.log_create(
            module="projects",
            resource_type="project",
            resource_code="PROJ-10",
            after={"name": "Alpha"},
        )
        self.assertEqual(entry.resource_code, "PROJ-10")

    def test_accepts_actor(self):
        user = make_user()
        entry = AuditService.log_create(
            module="projects",
            resource_type="project",
            after={"name": "Alpha"},
            actor=user,
        )
        self.assertEqual(entry.actor, user)

    def test_returns_audit_instance(self):
        entry = AuditService.log_create(
            module="projects",
            resource_type="project",
            after={"name": "Alpha"},
        )
        self.assertIsInstance(entry, Audit)


# ── AuditService.log_update ────────────────────────────────────────────────────


class AuditServiceLogUpdateTest(TestCase):
    def test_sets_action_to_update(self):
        entry = AuditService.log_update(
            module="projects",
            resource_type="project",
            before={"name": "Old"},
            after={"name": "New"},
        )
        self.assertEqual(entry.action, Action.UPDATE)

    def test_stores_before_snapshot(self):
        before = {"name": "Old", "is_active": True}
        entry = AuditService.log_update(
            module="projects",
            resource_type="project",
            before=before,
            after={"name": "New"},
        )
        self.assertEqual(entry.before, before)

    def test_stores_after_snapshot(self):
        after = {"name": "New", "is_active": False}
        entry = AuditService.log_update(
            module="projects",
            resource_type="project",
            before={"name": "Old"},
            after=after,
        )
        self.assertEqual(entry.after, after)

    def test_accepts_resource_code(self):
        entry = AuditService.log_update(
            module="projects",
            resource_type="project",
            resource_code="PROJ-3",
            before={"name": "Old"},
            after={"name": "New"},
        )
        self.assertEqual(entry.resource_code, "PROJ-3")

    def test_accepts_actor(self):
        user = make_user()
        entry = AuditService.log_update(
            module="projects",
            resource_type="project",
            before={"name": "Old"},
            after={"name": "New"},
            actor=user,
        )
        self.assertEqual(entry.actor, user)

    def test_returns_audit_instance(self):
        entry = AuditService.log_update(
            module="projects",
            resource_type="project",
            before={"name": "Old"},
            after={"name": "New"},
        )
        self.assertIsInstance(entry, Audit)


# ── AuditService.log_delete ────────────────────────────────────────────────────


class AuditServiceLogDeleteTest(TestCase):
    def test_sets_action_to_delete(self):
        entry = AuditService.log_delete(
            module="projects",
            resource_type="project",
            before={"name": "Alpha"},
        )
        self.assertEqual(entry.action, Action.DELETE)

    def test_stores_before_snapshot(self):
        before = {"name": "Alpha", "is_active": True}
        entry = AuditService.log_delete(
            module="projects",
            resource_type="project",
            before=before,
        )
        self.assertEqual(entry.before, before)

    def test_after_is_always_none(self):
        entry = AuditService.log_delete(
            module="projects",
            resource_type="project",
            before={"name": "Alpha"},
        )
        self.assertIsNone(entry.after)

    def test_accepts_resource_code(self):
        entry = AuditService.log_delete(
            module="projects",
            resource_type="project",
            resource_code="PROJ-99",
            before={"name": "Alpha"},
        )
        self.assertEqual(entry.resource_code, "PROJ-99")

    def test_accepts_actor(self):
        user = make_user()
        entry = AuditService.log_delete(
            module="projects",
            resource_type="project",
            before={"name": "Alpha"},
            actor=user,
        )
        self.assertEqual(entry.actor, user)

    def test_returns_audit_instance(self):
        entry = AuditService.log_delete(
            module="projects",
            resource_type="project",
            before={"name": "Alpha"},
        )
        self.assertIsInstance(entry, Audit)


# ── AuditService.log_activate ─────────────────────────────────────────────────


class AuditServiceLogActivateTest(TestCase):
    def test_sets_action_to_activate(self):
        entry = AuditService.log_activate(
            module="teams",
            resource_type="team",
            after={"is_active": True},
        )
        self.assertEqual(entry.action, Action.ACTIVATE)

    def test_stores_after_snapshot(self):
        after = {"is_active": True, "name": "Alpha"}
        entry = AuditService.log_activate(
            module="teams",
            resource_type="team",
            after=after,
        )
        self.assertEqual(entry.after, after)

    def test_before_defaults_to_none(self):
        entry = AuditService.log_activate(
            module="teams",
            resource_type="team",
            after={"is_active": True},
        )
        self.assertIsNone(entry.before)

    def test_accepts_optional_before_snapshot(self):
        before = {"is_active": False}
        entry = AuditService.log_activate(
            module="teams",
            resource_type="team",
            before=before,
            after={"is_active": True},
        )
        self.assertEqual(entry.before, before)

    def test_accepts_resource_code(self):
        entry = AuditService.log_activate(
            module="teams",
            resource_type="team",
            resource_code="TEAM-5",
            after={"is_active": True},
        )
        self.assertEqual(entry.resource_code, "TEAM-5")

    def test_accepts_actor(self):
        user = make_user()
        entry = AuditService.log_activate(
            module="teams",
            resource_type="team",
            after={"is_active": True},
            actor=user,
        )
        self.assertEqual(entry.actor, user)

    def test_returns_audit_instance(self):
        entry = AuditService.log_activate(
            module="teams",
            resource_type="team",
            after={"is_active": True},
        )
        self.assertIsInstance(entry, Audit)


# ── AuditService.log_deactivate ───────────────────────────────────────────────


class AuditServiceLogDeactivateTest(TestCase):
    def test_sets_action_to_deactivate(self):
        entry = AuditService.log_deactivate(
            module="teams",
            resource_type="team",
            before={"is_active": True},
        )
        self.assertEqual(entry.action, Action.DEACTIVATE)

    def test_stores_before_snapshot(self):
        before = {"is_active": True, "name": "Alpha"}
        entry = AuditService.log_deactivate(
            module="teams",
            resource_type="team",
            before=before,
        )
        self.assertEqual(entry.before, before)

    def test_after_defaults_to_none(self):
        entry = AuditService.log_deactivate(
            module="teams",
            resource_type="team",
            before={"is_active": True},
        )
        self.assertIsNone(entry.after)

    def test_accepts_optional_after_snapshot(self):
        after = {"is_active": False}
        entry = AuditService.log_deactivate(
            module="teams",
            resource_type="team",
            before={"is_active": True},
            after=after,
        )
        self.assertEqual(entry.after, after)

    def test_accepts_resource_code(self):
        entry = AuditService.log_deactivate(
            module="teams",
            resource_type="team",
            resource_code="TEAM-9",
            before={"is_active": True},
        )
        self.assertEqual(entry.resource_code, "TEAM-9")

    def test_accepts_actor(self):
        user = make_user()
        entry = AuditService.log_deactivate(
            module="teams",
            resource_type="team",
            before={"is_active": True},
            actor=user,
        )
        self.assertEqual(entry.actor, user)

    def test_returns_audit_instance(self):
        entry = AuditService.log_deactivate(
            module="teams",
            resource_type="team",
            before={"is_active": True},
        )
        self.assertIsInstance(entry, Audit)


# ── Multiple entries ───────────────────────────────────────────────────────────


class AuditServiceMultipleEntriesTest(TestCase):
    def test_each_call_creates_a_separate_record(self):
        AuditService.log_create(
            module="projects", resource_type="project", after={"name": "A"}
        )
        AuditService.log_create(
            module="projects", resource_type="project", after={"name": "B"}
        )
        self.assertEqual(Audit.objects.count(), 2)

    def test_entries_for_different_modules_are_independent(self):
        AuditService.log_create(
            module="projects", resource_type="project", after={"name": "Alpha"}
        )
        AuditService.log_create(
            module="teams", resource_type="team", after={"name": "Beta"}
        )
        self.assertEqual(Audit.objects.filter(module="projects").count(), 1)
        self.assertEqual(Audit.objects.filter(module="teams").count(), 1)
