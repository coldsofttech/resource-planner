from django.test import SimpleTestCase

from apps.audit.constants import Action

# ── Action values ──────────────────────────────────────────────────────────────


class ActionValuesTest(SimpleTestCase):
    def test_create_value(self):
        self.assertEqual(Action.CREATE, "create")

    def test_update_value(self):
        self.assertEqual(Action.UPDATE, "update")

    def test_delete_value(self):
        self.assertEqual(Action.DELETE, "delete")

    def test_activate_value(self):
        self.assertEqual(Action.ACTIVATE, "activate")

    def test_deactivate_value(self):
        self.assertEqual(Action.DEACTIVATE, "deactivate")

    def test_restore_value(self):
        self.assertEqual(Action.RESTORE, "restore")

    def test_lock_value(self):
        self.assertEqual(Action.LOCK, "lock")


# ── Action labels ──────────────────────────────────────────────────────────────


class ActionLabelsTest(SimpleTestCase):
    def test_create_label(self):
        self.assertEqual(Action.CREATE.label, "Create")

    def test_update_label(self):
        self.assertEqual(Action.UPDATE.label, "Update")

    def test_delete_label(self):
        self.assertEqual(Action.DELETE.label, "Delete")

    def test_activate_label(self):
        self.assertEqual(Action.ACTIVATE.label, "Activate")

    def test_deactivate_label(self):
        self.assertEqual(Action.DEACTIVATE.label, "Deactivate")

    def test_restore_label(self):
        self.assertEqual(Action.RESTORE.label, "Restore")

    def test_lock_label(self):
        self.assertEqual(Action.LOCK.label, "Lock")


# ── Action.choices ─────────────────────────────────────────────────────────────


class ActionChoicesTest(SimpleTestCase):
    def test_choices_has_eight_entries(self):
        self.assertEqual(len(Action.choices), 8)

    def test_choices_contains_create(self):
        values = [v for v, _ in Action.choices]
        self.assertIn("create", values)

    def test_choices_contains_update(self):
        values = [v for v, _ in Action.choices]
        self.assertIn("update", values)

    def test_choices_contains_delete(self):
        values = [v for v, _ in Action.choices]
        self.assertIn("delete", values)

    def test_choices_contains_activate(self):
        values = [v for v, _ in Action.choices]
        self.assertIn("activate", values)

    def test_choices_contains_deactivate(self):
        values = [v for v, _ in Action.choices]
        self.assertIn("deactivate", values)

    def test_choices_contains_restore(self):
        values = [v for v, _ in Action.choices]
        self.assertIn("restore", values)

    def test_choices_contains_lock(self):
        values = [v for v, _ in Action.choices]
        self.assertIn("lock", values)
