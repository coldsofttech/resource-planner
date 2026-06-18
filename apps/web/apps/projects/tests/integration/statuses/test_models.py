from django.db import IntegrityError
from django.test import TestCase

from apps.projects.models import ProjectStatus, ProjectStatusHistory, ProjectSubStatus
from apps.projects.tests.factories import (
    make_project,
    make_project_status,
    make_project_status_history,
    make_project_substatus,
)
from apps.users.tests.factories import make_user

# ── ProjectStatus ─────────────────────────────────────────────────────────────


class ProjectStatusCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        s = make_project_status()
        self.assertTrue(s.code.startswith("PROJSTAT-"))

    def test_code_contains_pk(self):
        s = make_project_status()
        self.assertEqual(s.code, f"PROJSTAT-{s.pk}")

    def test_codes_are_unique(self):
        s1 = make_project_status("Alpha")
        s2 = make_project_status("Beta")
        self.assertNotEqual(s1.code, s2.code)


class ProjectStatusFieldTest(TestCase):
    def test_is_active_defaults_to_true(self):
        s = make_project_status()
        self.assertTrue(s.is_active)

    def test_str_returns_name(self):
        s = make_project_status("Being Reviewed")
        self.assertEqual(str(s), "Being Reviewed")

    def test_name_stores_value(self):
        s = make_project_status("Pending Approval")
        self.assertEqual(s.name, "Pending Approval")

    def test_is_active_can_be_false(self):
        s = make_project_status(is_active=False)
        self.assertFalse(s.is_active)


class ProjectStatusConstraintTest(TestCase):
    def test_duplicate_name_raises_integrity_error(self):
        make_project_status("Alpha")
        with self.assertRaises(IntegrityError):
            make_project_status("Alpha")

    def test_different_names_are_allowed(self):
        make_project_status("Alpha")
        s2 = make_project_status("Beta")
        self.assertIsNotNone(s2.pk)


class ProjectStatusOrderingTest(TestCase):
    def test_ordered_by_name(self):
        make_project_status("Zeta")
        make_project_status("Alpha")
        make_project_status("Mu")
        names = list(ProjectStatus.objects.values_list("name", flat=True))
        self.assertEqual(names, sorted(names))


class ProjectStatusAuditableTest(TestCase):
    def test_created_at_is_set(self):
        s = make_project_status()
        self.assertIsNotNone(s.created_at)

    def test_updated_at_is_set(self):
        s = make_project_status()
        self.assertIsNotNone(s.updated_at)

    def test_created_by_nullable(self):
        s = make_project_status()
        self.assertIsNone(s.created_by)

    def test_created_by_stores_user(self):
        user = make_user()
        s = ProjectStatus.objects.create(
            name="Managed", created_by=user, updated_by=user
        )
        self.assertEqual(s.created_by, user)


# ── ProjectSubStatus ──────────────────────────────────────────────────────────


class ProjectSubStatusCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        ss = make_project_substatus()
        self.assertTrue(ss.code.startswith("PROJSUBSTAT-"))

    def test_code_contains_pk(self):
        ss = make_project_substatus()
        self.assertEqual(ss.code, f"PROJSUBSTAT-{ss.pk}")

    def test_codes_are_unique(self):
        status = make_project_status("Alpha")
        ss1 = make_project_substatus("Draft", status=status)
        ss2 = make_project_substatus("Review", status=status)
        self.assertNotEqual(ss1.code, ss2.code)


class ProjectSubStatusFieldTest(TestCase):
    def test_is_active_defaults_to_true(self):
        ss = make_project_substatus()
        self.assertTrue(ss.is_active)

    def test_str_returns_name(self):
        ss = make_project_substatus("Draft")
        self.assertEqual(str(ss), "Draft")

    def test_main_status_fk_set(self):
        status = make_project_status("In Review")
        ss = make_project_substatus("Draft", status=status)
        self.assertEqual(ss.main_status, status)

    def test_order_stores_value(self):
        status = make_project_status("Active")
        ss = make_project_substatus("Draft", status=status, order=5)
        self.assertEqual(ss.order, 5)

    def test_is_active_can_be_false(self):
        ss = make_project_substatus(is_active=False)
        self.assertFalse(ss.is_active)


class ProjectSubStatusConstraintTest(TestCase):
    def test_duplicate_name_within_same_status_raises_integrity_error(self):
        status = make_project_status("Active")
        make_project_substatus("Draft", status=status, order=1)
        with self.assertRaises(IntegrityError):
            make_project_substatus("Draft", status=status, order=2)

    def test_duplicate_order_within_same_status_raises_integrity_error(self):
        status = make_project_status("Active")
        make_project_substatus("Draft", status=status, order=1)
        with self.assertRaises(IntegrityError):
            make_project_substatus("Review", status=status, order=1)

    def test_same_name_different_status_is_allowed(self):
        s1 = make_project_status("Alpha")
        s2 = make_project_status("Beta")
        ss1 = make_project_substatus("Draft", status=s1, order=1)
        ss2 = make_project_substatus("Draft", status=s2, order=1)
        self.assertIsNotNone(ss1.pk)
        self.assertIsNotNone(ss2.pk)

    def test_different_name_same_status_is_allowed(self):
        status = make_project_status("Active")
        ss1 = make_project_substatus("Draft", status=status, order=1)
        ss2 = make_project_substatus("Review", status=status, order=2)
        self.assertIsNotNone(ss1.pk)
        self.assertIsNotNone(ss2.pk)


class ProjectSubStatusCascadeTest(TestCase):
    def test_deleting_status_cascades_to_substatus(self):
        status = make_project_status("Cascade")
        ss = make_project_substatus("Draft", status=status)
        ss_code = ss.code
        status.delete()
        self.assertFalse(ProjectSubStatus.objects.filter(code=ss_code).exists())


class ProjectSubStatusOrderingTest(TestCase):
    def test_ordered_by_main_status_then_order_then_name(self):
        s = make_project_status("Active")
        ss3 = make_project_substatus("Zeta", status=s, order=3)
        ss1 = make_project_substatus("Alpha", status=s, order=1)
        ss2 = make_project_substatus("Mu", status=s, order=2)
        qs = list(
            ProjectSubStatus.objects.filter(main_status=s).values_list(
                "order", flat=True
            )
        )
        self.assertEqual(qs, [1, 2, 3])
        _ = ss1, ss2, ss3  # suppress unused warning


class ProjectSubStatusAuditableTest(TestCase):
    def test_created_at_is_set(self):
        ss = make_project_substatus()
        self.assertIsNotNone(ss.created_at)

    def test_updated_at_is_set(self):
        ss = make_project_substatus()
        self.assertIsNotNone(ss.updated_at)

    def test_created_by_nullable(self):
        ss = make_project_substatus()
        self.assertIsNone(ss.created_by)

    def test_created_by_stores_user(self):
        user = make_user()
        status = make_project_status("Audit")
        ss = ProjectSubStatus.objects.create(
            name="Managed",
            main_status=status,
            order=1,
            created_by=user,
            updated_by=user,
        )
        self.assertEqual(ss.created_by, user)


# ── ProjectStatusHistory ──────────────────────────────────────────────────────


class ProjectStatusHistoryFieldTest(TestCase):
    def test_project_linked(self):
        project = make_project()
        status = make_project_status("Linked Status")
        history = make_project_status_history(project=project, new_status=status)
        self.assertEqual(history.project, project)

    def test_new_status_linked(self):
        status = make_project_status("New State")
        history = make_project_status_history(new_status=status)
        self.assertEqual(history.new_status, status)

    def test_previous_status_defaults_to_none(self):
        history = make_project_status_history()
        self.assertIsNone(history.previous_status)

    def test_previous_status_stores_value(self):
        prev = make_project_status("Prev Status")
        new = make_project_status("Next Status")
        history = make_project_status_history(previous_status=prev, new_status=new)
        self.assertEqual(history.previous_status, prev)

    def test_previous_sub_status_defaults_to_none(self):
        history = make_project_status_history()
        self.assertIsNone(history.previous_sub_status)

    def test_new_sub_status_defaults_to_none(self):
        history = make_project_status_history()
        self.assertIsNone(history.new_sub_status)

    def test_note_defaults_to_empty(self):
        history = make_project_status_history()
        self.assertEqual(history.note, "")

    def test_note_stores_value(self):
        history = make_project_status_history(note="Moved to review")
        self.assertEqual(history.note, "Moved to review")

    def test_changed_on_auto_set(self):
        history = make_project_status_history()
        self.assertIsNotNone(history.changed_on)

    def test_changed_by_defaults_to_none(self):
        history = make_project_status_history()
        self.assertIsNone(history.changed_by)

    def test_changed_by_stores_user(self):
        user = make_user()
        history = make_project_status_history(changed_by=user)
        self.assertEqual(history.changed_by, user)


class ProjectStatusHistoryOrderingTest(TestCase):
    def test_ordered_by_changed_on_descending(self):
        project = make_project()
        s1 = make_project_status("Alpha Hist")
        s2 = make_project_status("Beta Hist")
        h1 = make_project_status_history(project=project, new_status=s1)
        h2 = make_project_status_history(project=project, new_status=s2)
        pks = list(
            ProjectStatusHistory.objects.filter(project=project).values_list(
                "pk", flat=True
            )
        )
        self.assertEqual(pks, [h2.pk, h1.pk])


class ProjectStatusHistoryCascadeTest(TestCase):
    def test_cascade_delete_with_project(self):
        project = make_project()
        history = make_project_status_history(project=project)
        history_pk = history.pk
        project.delete()
        self.assertFalse(ProjectStatusHistory.objects.filter(pk=history_pk).exists())

    def test_previous_status_set_null_on_status_delete(self):
        prev = make_project_status("Prev Cascade")
        new = make_project_status("New Cascade")
        history = make_project_status_history(previous_status=prev, new_status=new)
        prev.delete()
        history.refresh_from_db()
        self.assertIsNone(history.previous_status)
