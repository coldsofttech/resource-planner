from django.test import TestCase

from apps.audit.constants import Action
from apps.audit.models import Audit
from apps.audit.tests.factories import make_audit
from apps.users.tests.factories import make_user

# ── Field defaults ─────────────────────────────────────────────────────────────


class AuditFieldDefaultsTest(TestCase):
    def test_timestamp_is_set_automatically(self):
        entry = make_audit()
        self.assertIsNotNone(entry.timestamp)

    def test_resource_code_is_nullable(self):
        entry = Audit.objects.create(
            module="projects",
            resource_type="project",
            action=Action.CREATE,
            resource_code=None,
        )
        self.assertIsNone(entry.resource_code)

    def test_before_defaults_to_none(self):
        entry = make_audit()
        self.assertIsNone(entry.before)

    def test_after_defaults_to_none(self):
        entry = make_audit()
        self.assertIsNone(entry.after)

    def test_actor_defaults_to_none(self):
        entry = make_audit()
        self.assertIsNone(entry.actor)


# ── Field storage ──────────────────────────────────────────────────────────────


class AuditFieldStorageTest(TestCase):
    def test_stores_module(self):
        entry = make_audit(module="teams")
        self.assertEqual(entry.module, "teams")

    def test_stores_resource_type(self):
        entry = make_audit(resource_type="team")
        self.assertEqual(entry.resource_type, "team")

    def test_stores_resource_code(self):
        entry = make_audit(resource_code="TEAM-42")
        self.assertEqual(entry.resource_code, "TEAM-42")

    def test_stores_action(self):
        entry = make_audit(action=Action.UPDATE)
        self.assertEqual(entry.action, Action.UPDATE)

    def test_stores_before_snapshot(self):
        snapshot = {"name": "Old Name", "is_active": True}
        entry = make_audit(before=snapshot)
        self.assertEqual(entry.before, snapshot)

    def test_stores_after_snapshot(self):
        snapshot = {"name": "New Name", "is_active": False}
        entry = make_audit(after=snapshot)
        self.assertEqual(entry.after, snapshot)

    def test_stores_actor(self):
        user = make_user()
        entry = make_audit(actor=user)
        self.assertEqual(entry.actor, user)

    def test_stores_nested_json_in_before(self):
        snapshot = {"meta": {"tags": ["a", "b"], "count": 2}, "active": True}
        entry = make_audit(before=snapshot)
        entry.refresh_from_db()
        self.assertEqual(entry.before, snapshot)

    def test_stores_nested_json_in_after(self):
        snapshot = {"resources": [{"id": 1, "name": "R1"}, {"id": 2, "name": "R2"}]}
        entry = make_audit(after=snapshot)
        entry.refresh_from_db()
        self.assertEqual(entry.after, snapshot)


# ── Actor nullability ──────────────────────────────────────────────────────────


class AuditActorNullabilityTest(TestCase):
    def test_actor_set_null_when_user_deleted(self):
        user = make_user()
        entry = make_audit(actor=user)
        user.delete()
        entry.refresh_from_db()
        self.assertIsNone(entry.actor)

    def test_audit_entry_survives_actor_deletion(self):
        user = make_user()
        entry = make_audit(actor=user)
        user.delete()
        self.assertTrue(Audit.objects.filter(pk=entry.pk).exists())


# ── Action choices ─────────────────────────────────────────────────────────────


class AuditActionChoicesTest(TestCase):
    def test_create_action_stored(self):
        entry = make_audit(action=Action.CREATE)
        self.assertEqual(entry.action, "create")

    def test_update_action_stored(self):
        entry = make_audit(action=Action.UPDATE)
        self.assertEqual(entry.action, "update")

    def test_delete_action_stored(self):
        entry = make_audit(action=Action.DELETE)
        self.assertEqual(entry.action, "delete")

    def test_activate_action_stored(self):
        entry = make_audit(action=Action.ACTIVATE)
        self.assertEqual(entry.action, "activate")

    def test_deactivate_action_stored(self):
        entry = make_audit(action=Action.DEACTIVATE)
        self.assertEqual(entry.action, "deactivate")


# ── __str__ (with DB-assigned timestamp) ──────────────────────────────────────


class AuditStrDbTest(TestCase):
    def test_str_includes_action(self):
        entry = make_audit(
            action=Action.CREATE, resource_type="project", resource_code="PROJ-1"
        )
        self.assertIn("create", str(entry))

    def test_str_includes_resource_type(self):
        entry = make_audit(resource_type="team")
        self.assertIn("team", str(entry))

    def test_str_includes_resource_code(self):
        entry = make_audit(resource_code="TEAM-7")
        self.assertIn("TEAM-7", str(entry))

    def test_str_includes_timestamp_separator(self):
        entry = make_audit()
        self.assertIn("@", str(entry))

    def test_str_with_none_resource_code(self):
        entry = Audit.objects.create(
            module="projects",
            resource_type="project",
            action=Action.DELETE,
            resource_code=None,
        )
        self.assertIn("None", str(entry))


# ── Ordering ───────────────────────────────────────────────────────────────────


class AuditOrderingTest(TestCase):
    def test_ordered_by_timestamp_descending(self):
        e1 = make_audit(module="m1")
        make_audit(module="m2")
        e3 = make_audit(module="m3")
        entries = list(Audit.objects.all())
        self.assertEqual(entries[0].pk, e3.pk)
        self.assertEqual(entries[2].pk, e1.pk)
