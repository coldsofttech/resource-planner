from datetime import date
from unittest.mock import patch

from django.db import IntegrityError
from django.test import TestCase

from apps.financial_years.tests.factories import make_financial_year
from apps.sprints.constants import SprintStatus
from apps.sprints.models import Capacity, Sprint
from apps.sprints.tests.factories import make_capacity, make_sprint
from apps.users.tests.factories import make_user


class SprintCodeTest(TestCase):
    def test_code_starts_with_sprint_prefix(self):
        sprint = make_sprint()
        self.assertTrue(sprint.code.startswith("SPRINT-"))

    def test_code_contains_pk(self):
        sprint = make_sprint()
        self.assertEqual(sprint.code, f"SPRINT-{sprint.pk}")

    def test_codes_are_unique_across_sprints(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        s1 = make_sprint(
            financial_year=fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        s2 = make_sprint(
            financial_year=fy,
            sprint_number=2,
            start_date=date(2024, 4, 15),
            end_date=date(2024, 4, 28),
        )
        self.assertNotEqual(s1.code, s2.code)


class SprintFieldDefaultsTest(TestCase):
    def test_status_defaults_to_future(self):
        sprint = make_sprint()
        self.assertEqual(sprint.status, SprintStatus.FUTURE)

    def test_is_overridden_defaults_to_false(self):
        sprint = make_sprint()
        self.assertFalse(sprint.is_overridden)

    def test_is_closed_defaults_to_false(self):
        sprint = make_sprint()
        self.assertFalse(sprint.is_closed)

    def test_closed_on_defaults_to_null(self):
        sprint = make_sprint()
        self.assertIsNone(sprint.closed_on)

    def test_closed_by_defaults_to_null(self):
        sprint = make_sprint()
        self.assertIsNone(sprint.closed_by)

    def test_note_defaults_to_empty(self):
        sprint = make_sprint()
        self.assertEqual(sprint.note, "")

    def test_is_active_defaults_to_true(self):
        sprint = make_sprint()
        self.assertTrue(sprint.is_active)

    def test_created_at_set_on_create(self):
        sprint = make_sprint()
        self.assertIsNotNone(sprint.created_at)

    def test_updated_at_set_on_create(self):
        sprint = make_sprint()
        self.assertIsNotNone(sprint.updated_at)

    def test_created_by_nullable(self):
        sprint = make_sprint()
        self.assertIsNone(sprint.created_by)

    def test_updated_by_nullable(self):
        sprint = make_sprint()
        self.assertIsNone(sprint.updated_by)

    def test_created_by_stores_user(self):
        user = make_user()
        sprint = make_sprint(created_by=user, updated_by=user)
        self.assertEqual(sprint.created_by, user)


class SprintMonthFieldTest(TestCase):
    def test_month_auto_set_from_end_date_on_create(self):
        sprint = make_sprint(end_date=date(2024, 4, 14))
        self.assertEqual(sprint.month, "2024-04")

    def test_month_updates_when_end_date_changes(self):
        sprint = make_sprint(end_date=date(2024, 4, 14))
        sprint.end_date = date(2024, 5, 31)
        sprint.save(update_fields=["end_date", "month"])
        sprint.refresh_from_db()
        self.assertEqual(sprint.month, "2024-05")


class SprintStrTest(TestCase):
    def test_str_includes_name_and_code(self):
        sprint = make_sprint(name="Sprint 1")
        expected = f"Sprint 1 ({sprint.code})"
        self.assertEqual(str(sprint), expected)


class SprintOrderingTest(TestCase):
    def test_ordered_by_sprint_number_ascending(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        make_sprint(
            financial_year=fy,
            sprint_number=3,
            start_date=date(2024, 4, 29),
            end_date=date(2024, 5, 12),
        )
        make_sprint(
            financial_year=fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        make_sprint(
            financial_year=fy,
            sprint_number=2,
            start_date=date(2024, 4, 15),
            end_date=date(2024, 4, 28),
        )
        numbers = list(Sprint.objects.values_list("sprint_number", flat=True))
        self.assertEqual(numbers, [1, 2, 3])


class SprintSprintNumberUniqueTest(TestCase):
    def test_duplicate_sprint_number_raises_integrity_error(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        make_sprint(
            financial_year=fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        with self.assertRaises(IntegrityError):
            Sprint.objects.create(
                financial_year=fy,
                sprint_number=1,
                name="Duplicate",
                start_date=date(2024, 4, 15),
                end_date=date(2024, 4, 28),
            )


class SprintCustomPermissionsTest(TestCase):
    def test_custom_permissions_defined(self):
        perm_codenames = {p[0] for p in Sprint._meta.permissions}
        self.assertIn("import_sprint", perm_codenames)
        self.assertIn("export_sprint", perm_codenames)
        self.assertIn("generate_sprint", perm_codenames)
        self.assertIn("close_sprint", perm_codenames)


@patch("apps.sprints.signals._rebuild_sprint")
class CapacityFieldDefaultsTest(TestCase):
    def test_working_days_defaults_to_zero(self, _mock_rebuild):
        user = make_user()
        sprint = make_sprint()
        cap = Capacity.objects.create(sprint=sprint, member=user)
        self.assertEqual(cap.working_days, 0)

    def test_net_capacity_defaults_to_zero(self, _mock_rebuild):
        user = make_user()
        sprint = make_sprint()
        cap = Capacity.objects.create(sprint=sprint, member=user)
        self.assertEqual(cap.net_capacity, 0)

    def test_str_includes_member_and_sprint(self, _mock_rebuild):
        user = make_user(
            email="member@example.com", first_name="Alice", last_name="Smith"
        )
        sprint = make_sprint(name="Sprint 1")
        cap = make_capacity(sprint=sprint, member=user)
        self.assertIn(str(user), str(cap))
        self.assertIn(str(sprint), str(cap))


@patch("apps.sprints.signals._rebuild_sprint")
class CapacityUniqueConstraintTest(TestCase):
    def test_duplicate_sprint_member_raises_integrity_error(self, _mock_rebuild):
        user = make_user()
        sprint = make_sprint()
        make_capacity(sprint=sprint, member=user)
        with self.assertRaises(IntegrityError):
            Capacity.objects.create(sprint=sprint, member=user)
