from django.test import TestCase

from apps.projects import selectors
from apps.projects.tests.factories import make_programme


class GetAllProgrammesTest(TestCase):
    def test_returns_all_records(self):
        make_programme("Alpha", is_active=True)
        make_programme("Beta", is_active=False)
        # +1 for the seeded "Others" protected programme
        self.assertEqual(selectors.get_all_programmes().count(), 3)

    def test_includes_inactive(self):
        make_programme("Inactive", is_active=False)
        qs = selectors.get_all_programmes()
        self.assertEqual(qs.filter(is_active=False).count(), 1)


class GetActiveProgrammesTest(TestCase):
    def test_returns_only_active(self):
        make_programme("Active", is_active=True)
        make_programme("Inactive", is_active=False)
        qs = selectors.get_active_programmes()
        names = list(qs.values_list("name", flat=True))
        self.assertIn("Active", names)
        self.assertNotIn("Inactive", names)


class GetProgrammeByCodeTest(TestCase):
    def test_returns_matching_programme(self):
        p = make_programme("Alpha")
        result = selectors.get_programme_by_code(p.code)
        self.assertEqual(result, p)

    def test_returns_none_for_unknown_code(self):
        result = selectors.get_programme_by_code("PROG-99999")
        self.assertIsNone(result)


class ProgrammeExistsTest(TestCase):
    def test_returns_true_for_existing_name(self):
        make_programme("Alpha")
        self.assertTrue(selectors.programme_exists("Alpha"))

    def test_case_insensitive_check(self):
        make_programme("Alpha")
        self.assertTrue(selectors.programme_exists("alpha"))

    def test_returns_false_for_unknown_name(self):
        self.assertFalse(selectors.programme_exists("Unknown"))

    def test_exclude_pk_skips_own_record(self):
        p = make_programme("Alpha")
        self.assertFalse(selectors.programme_exists("Alpha", exclude_pk=p.pk))


class GetProgrammeOptionsTest(TestCase):
    def test_returns_only_active(self):
        make_programme("Active", is_active=True)
        make_programme("Inactive", is_active=False)
        qs = selectors.get_programme_options()
        names = list(qs.values_list("name", flat=True))
        self.assertIn("Active", names)
        self.assertNotIn("Inactive", names)

    def test_ordered_by_name(self):
        make_programme("Zeta")
        make_programme("Alpha")
        names = list(selectors.get_programme_options().values_list("name", flat=True))
        self.assertEqual(names, sorted(names))


class GetProgrammeStatsTest(TestCase):
    def test_counts_total_active_inactive(self):
        make_programme("A", is_active=True)
        make_programme("B", is_active=True)
        make_programme("C", is_active=False)
        stats = selectors.get_programme_stats()
        # +1 total and +1 active for the seeded "Others" protected programme
        self.assertEqual(stats["total"], 4)
        self.assertEqual(stats["active"], 3)
        self.assertEqual(stats["inactive"], 1)
