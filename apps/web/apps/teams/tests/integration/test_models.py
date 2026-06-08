from django.db import IntegrityError
from django.test import TestCase

from apps.teams.models import Team
from apps.teams.tests.factories import make_team
from apps.users.tests.factories import make_user

# ── Code assignment ───────────────────────────────────────────────────────────


class TeamCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        team = make_team()
        self.assertTrue(team.code.startswith("TEAM-"))

    def test_code_contains_pk(self):
        team = make_team()
        self.assertEqual(team.code, f"TEAM-{team.pk}")

    def test_codes_are_unique(self):
        t1 = make_team("Alpha")
        t2 = make_team("Beta")
        self.assertNotEqual(t1.code, t2.code)


# ── Field defaults ────────────────────────────────────────────────────────────


class TeamFieldTest(TestCase):
    def test_is_active_defaults_to_true(self):
        team = make_team()
        self.assertTrue(team.is_active)

    def test_description_defaults_to_empty(self):
        team = make_team()
        self.assertEqual(team.description, "")

    def test_str_returns_name(self):
        team = make_team("Alpha")
        self.assertEqual(str(team), "Alpha")

    def test_description_stores_value(self):
        team = make_team(description="Frontend squad")
        self.assertEqual(team.description, "Frontend squad")


# ── Constraints ───────────────────────────────────────────────────────────────


class TeamConstraintTest(TestCase):
    def test_duplicate_name_raises_integrity_error(self):
        make_team("Alpha")
        with self.assertRaises(IntegrityError):
            make_team("Alpha")

    def test_different_names_are_allowed(self):
        make_team("Alpha")
        team = make_team("Beta")
        self.assertIsNotNone(team.pk)


# ── Ordering ──────────────────────────────────────────────────────────────────


class TeamOrderingTest(TestCase):
    def test_ordered_by_name(self):
        make_team("Zeta")
        make_team("Alpha")
        make_team("Gamma")
        names = list(Team.objects.values_list("name", flat=True))
        self.assertEqual(names, sorted(names))


# ── Auditable fields ──────────────────────────────────────────────────────────


class TeamAuditableTest(TestCase):
    def test_created_at_is_set(self):
        team = make_team()
        self.assertIsNotNone(team.created_at)

    def test_updated_at_is_set(self):
        team = make_team()
        self.assertIsNotNone(team.updated_at)

    def test_created_by_nullable(self):
        team = make_team()
        self.assertIsNone(team.created_by)

    def test_created_by_stores_user(self):
        user = make_user()
        team = Team.objects.create(name="Alpha", created_by=user, updated_by=user)
        self.assertEqual(team.created_by, user)
