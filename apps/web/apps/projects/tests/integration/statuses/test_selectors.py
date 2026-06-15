from django.test import TestCase

from apps.projects import selectors
from apps.projects.tests.factories import make_project_status, make_project_substatus

# ── ProjectStatus selectors ───────────────────────────────────────────────────


class GetAllProjectStatusesTest(TestCase):
    def test_returns_all_records(self):
        baseline = selectors.get_all_project_statuses().count()
        make_project_status("Alpha", is_active=True)
        make_project_status("Beta", is_active=False)
        self.assertEqual(selectors.get_all_project_statuses().count(), baseline + 2)

    def test_includes_inactive(self):
        make_project_status("Inactive", is_active=False)
        qs = selectors.get_all_project_statuses()
        self.assertEqual(qs.filter(is_active=False).count(), 1)


class GetProjectStatusByCodeTest(TestCase):
    def test_returns_matching_status(self):
        s = make_project_status("Alpha")
        result = selectors.get_project_status_by_code(s.code)
        self.assertEqual(result, s)

    def test_returns_none_for_unknown_code(self):
        result = selectors.get_project_status_by_code("PROJSTAT-99999")
        self.assertIsNone(result)


class GetProjectStatusOptionsTest(TestCase):
    def test_returns_only_active(self):
        make_project_status("Active", is_active=True)
        make_project_status("Inactive", is_active=False)
        qs = selectors.get_project_status_options()
        names = list(qs.values_list("name", flat=True))
        self.assertIn("Active", names)
        self.assertNotIn("Inactive", names)

    def test_ordered_by_name(self):
        make_project_status("Zeta")
        make_project_status("Alpha")
        names = list(
            selectors.get_project_status_options().values_list("name", flat=True)
        )
        self.assertEqual(names, sorted(names))


class GetProjectStatusStatsTest(TestCase):
    def test_counts_total_active_inactive(self):
        baseline = selectors.get_project_status_stats()
        make_project_status("A", is_active=True)
        make_project_status("B", is_active=True)
        make_project_status("C", is_active=False)
        stats = selectors.get_project_status_stats()
        self.assertEqual(stats["total"], baseline["total"] + 3)
        self.assertEqual(stats["active"], baseline["active"] + 2)
        self.assertEqual(stats["inactive"], baseline["inactive"] + 1)

    def test_seeded_defaults_are_all_active(self):
        stats = selectors.get_project_status_stats()
        self.assertGreater(stats["total"], 0)
        self.assertEqual(stats["inactive"], 0)


# ── ProjectSubStatus selectors ────────────────────────────────────────────────


class GetAllProjectSubStatusesTest(TestCase):
    def test_returns_all_records(self):
        s = make_project_status("Active")
        make_project_substatus("Draft", status=s)
        make_project_substatus("Review", status=s)
        self.assertEqual(selectors.get_all_project_sub_statuses().count(), 2)

    def test_includes_inactive(self):
        s = make_project_status("Active")
        make_project_substatus("Draft", status=s, is_active=False)
        qs = selectors.get_all_project_sub_statuses()
        self.assertEqual(qs.filter(is_active=False).count(), 1)


class GetProjectSubStatusesByStatusTest(TestCase):
    def test_returns_only_matching_status(self):
        s1 = make_project_status("Alpha")
        s2 = make_project_status("Beta")
        make_project_substatus("Draft", status=s1)
        make_project_substatus("Review", status=s2)
        qs = selectors.get_project_sub_statuses_by_status(s1.code)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().name, "Draft")

    def test_returns_empty_for_unknown_status(self):
        qs = selectors.get_project_sub_statuses_by_status("PROJSTAT-99999")
        self.assertEqual(qs.count(), 0)

    def test_ordered_by_order_then_name(self):
        s = make_project_status("Active")
        make_project_substatus("Beta", status=s, order=2)
        make_project_substatus("Alpha", status=s, order=1)
        names = list(
            selectors.get_project_sub_statuses_by_status(s.code).values_list(
                "name", flat=True
            )
        )
        self.assertEqual(names, ["Alpha", "Beta"])


class GetProjectSubStatusByCodeTest(TestCase):
    def test_returns_matching_substatus(self):
        ss = make_project_substatus()
        result = selectors.get_project_sub_status_by_code(ss.code)
        self.assertEqual(result, ss)

    def test_returns_none_for_unknown_code(self):
        result = selectors.get_project_sub_status_by_code("PROJSUBSTAT-99999")
        self.assertIsNone(result)


class ProjectSubStatusExistsTest(TestCase):
    def test_returns_true_for_existing_name_and_status(self):
        s = make_project_status("Active")
        make_project_substatus("Draft", status=s)
        self.assertTrue(selectors.project_sub_status_exists("Draft", s))

    def test_case_insensitive_check(self):
        s = make_project_status("Active")
        make_project_substatus("Draft", status=s)
        self.assertTrue(selectors.project_sub_status_exists("draft", s))

    def test_returns_false_for_unknown_name(self):
        s = make_project_status("Active")
        self.assertFalse(selectors.project_sub_status_exists("Unknown", s))

    def test_returns_false_for_name_in_different_status(self):
        s1 = make_project_status("Alpha")
        s2 = make_project_status("Beta")
        make_project_substatus("Draft", status=s1)
        self.assertFalse(selectors.project_sub_status_exists("Draft", s2))

    def test_exclude_pk_skips_own_record(self):
        s = make_project_status("Active")
        ss = make_project_substatus("Draft", status=s)
        self.assertFalse(
            selectors.project_sub_status_exists("Draft", s, exclude_pk=ss.pk)
        )


class GetProjectSubStatusOptionsTest(TestCase):
    def test_returns_only_active(self):
        s = make_project_status("Active")
        make_project_substatus("Draft", status=s, is_active=True)
        make_project_substatus("Archived", status=s, is_active=False)
        qs = selectors.get_project_sub_status_options()
        names = list(qs.values_list("name", flat=True))
        self.assertIn("Draft", names)
        self.assertNotIn("Archived", names)

    def test_filtered_by_status_code(self):
        s1 = make_project_status("Alpha")
        s2 = make_project_status("Beta")
        make_project_substatus("Draft", status=s1)
        make_project_substatus("Review", status=s2)
        qs = selectors.get_project_sub_status_options(s1.code)
        names = list(qs.values_list("name", flat=True))
        self.assertIn("Draft", names)
        self.assertNotIn("Review", names)

    def test_returns_all_active_when_no_status_code(self):
        s1 = make_project_status("Alpha")
        s2 = make_project_status("Beta")
        make_project_substatus("Draft", status=s1)
        make_project_substatus("Review", status=s2)
        qs = selectors.get_project_sub_status_options()
        self.assertEqual(qs.count(), 2)


class GetProjectSubStatusMaxOrderTest(TestCase):
    def test_returns_max_order(self):
        s = make_project_status("Active")
        make_project_substatus("A", status=s, order=1)
        make_project_substatus("B", status=s, order=5)
        make_project_substatus("C", status=s, order=3)
        self.assertEqual(selectors.get_project_sub_status_max_order(s), 5)

    def test_returns_zero_when_no_substatuses(self):
        s = make_project_status("Empty")
        self.assertEqual(selectors.get_project_sub_status_max_order(s), 0)


class GetProjectSubStatusStatsTest(TestCase):
    def test_counts_total_active_inactive(self):
        s = make_project_status("Active")
        make_project_substatus("A", status=s, is_active=True)
        make_project_substatus("B", status=s, is_active=True)
        make_project_substatus("C", status=s, is_active=False)
        stats = selectors.get_project_sub_status_stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["active"], 2)
        self.assertEqual(stats["inactive"], 1)

    def test_filtered_by_status_code(self):
        s1 = make_project_status("Alpha")
        s2 = make_project_status("Beta")
        make_project_substatus("Draft", status=s1, is_active=True)
        make_project_substatus("Review", status=s2, is_active=False)
        stats = selectors.get_project_sub_status_stats(s1.code)
        self.assertEqual(stats["total"], 1)
        self.assertEqual(stats["active"], 1)
        self.assertEqual(stats["inactive"], 0)

    def test_empty_returns_zeros(self):
        stats = selectors.get_project_sub_status_stats()
        self.assertEqual(stats["total"], 0)
