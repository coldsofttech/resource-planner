from django.test import TestCase

from apps.projects.tests.factories import make_project_type
from apps.recharges import selectors
from apps.recharges.tests.factories import make_project_type_mapping, make_recharge_type

# ── get_all_recharge_types ────────────────────────────────────────────────────


class GetAllRechargeTypesTest(TestCase):
    def test_returns_all_records(self):
        make_recharge_type("BAU")
        make_recharge_type("PROJECT")
        self.assertEqual(selectors.get_all_recharge_types().count(), 2)

    def test_includes_inactive(self):
        make_recharge_type("BAU", is_active=False)
        self.assertEqual(selectors.get_all_recharge_types().count(), 1)

    def test_ordered_by_name(self):
        make_recharge_type("PROJECT")
        make_recharge_type("BAU")
        names = list(selectors.get_all_recharge_types().values_list("name", flat=True))
        self.assertEqual(names, sorted(names))

    def test_select_related_available(self):
        make_recharge_type("BAU")
        obj = selectors.get_all_recharge_types().first()
        self.assertIsNotNone(obj)


# ── get_active_recharge_types ─────────────────────────────────────────────────


class GetActiveRechargeTypesTest(TestCase):
    def test_returns_only_active(self):
        make_recharge_type("BAU", is_active=True)
        make_recharge_type("PROJECT", is_active=False)
        qs = selectors.get_active_recharge_types()
        names = list(qs.values_list("name", flat=True))
        self.assertIn("BAU", names)
        self.assertNotIn("PROJECT", names)

    def test_returns_empty_when_none_active(self):
        make_recharge_type("BAU", is_active=False)
        self.assertEqual(selectors.get_active_recharge_types().count(), 0)


# ── get_recharge_type_by_code ─────────────────────────────────────────────────


class GetRechargeTypeByCodeTest(TestCase):
    def test_returns_object_for_valid_code(self):
        rt = make_recharge_type("BAU")
        result = selectors.get_recharge_type_by_code(rt.code)
        self.assertIsNotNone(result)
        self.assertEqual(result.pk, rt.pk)

    def test_returns_none_for_unknown_code(self):
        result = selectors.get_recharge_type_by_code("RECHTY-999999")
        self.assertIsNone(result)

    def test_select_related_available(self):
        rt = make_recharge_type("BAU")
        result = selectors.get_recharge_type_by_code(rt.code)
        self.assertIsNotNone(result)


# ── recharge_type_exists ──────────────────────────────────────────────────────


class RechargeTypeExistsTest(TestCase):
    def test_returns_true_for_existing_name(self):
        make_recharge_type("BAU")
        self.assertTrue(selectors.recharge_type_exists("BAU"))

    def test_returns_false_for_unknown_name(self):
        self.assertFalse(selectors.recharge_type_exists("NONEXISTENT"))

    def test_case_insensitive_match(self):
        make_recharge_type("BAU")
        self.assertTrue(selectors.recharge_type_exists("bau"))

    def test_exclude_pk_skips_own_record(self):
        rt = make_recharge_type("BAU")
        self.assertFalse(selectors.recharge_type_exists("BAU", exclude_pk=rt.pk))

    def test_exclude_pk_still_finds_other_record(self):
        make_recharge_type("BAU")
        other = make_recharge_type("PROJECT")
        self.assertTrue(selectors.recharge_type_exists("BAU", exclude_pk=other.pk))


# ── get_recharge_type_options ─────────────────────────────────────────────────


class GetRechargeTypeOptionsTest(TestCase):
    def test_returns_only_active(self):
        make_recharge_type("BAU", is_active=True)
        make_recharge_type("PROJECT", is_active=False)
        names = list(
            selectors.get_recharge_type_options().values_list("name", flat=True)
        )
        self.assertIn("BAU", names)
        self.assertNotIn("PROJECT", names)

    def test_ordered_by_name(self):
        make_recharge_type("PROJECT")
        make_recharge_type("BAU")
        names = list(
            selectors.get_recharge_type_options().values_list("name", flat=True)
        )
        self.assertEqual(names, sorted(names))


# ── get_recharge_type_stats ───────────────────────────────────────────────────


class GetRechargeTypeStatsTest(TestCase):
    def test_returns_correct_totals(self):
        make_recharge_type("BAU", is_active=True)
        make_recharge_type("PROJECT", is_active=True)
        make_recharge_type("HOLIDAY", is_active=False)
        stats = selectors.get_recharge_type_stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["active"], 2)
        self.assertEqual(stats["inactive"], 1)

    def test_returns_zero_when_empty(self):
        stats = selectors.get_recharge_type_stats()
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["active"], 0)
        self.assertEqual(stats["inactive"], 0)


# ── get_all_project_type_mappings ─────────────────────────────────────────────


class GetAllProjectTypeMappingsTest(TestCase):
    def test_returns_mappings_for_recharge_type(self):
        rt = make_recharge_type("BAU")
        pt1 = make_project_type("Internal")
        pt2 = make_project_type("External")
        make_project_type_mapping(rt, pt1)
        make_project_type_mapping(rt, pt2)
        qs = selectors.get_all_project_type_mappings(rt.code)
        self.assertEqual(qs.count(), 2)

    def test_excludes_mappings_for_other_recharge_types(self):
        rt1 = make_recharge_type("BAU")
        rt2 = make_recharge_type("PROJECT")
        pt = make_project_type("Shared")
        make_project_type_mapping(rt1, pt)
        qs = selectors.get_all_project_type_mappings(rt2.code)
        self.assertEqual(qs.count(), 0)

    def test_ordered_by_project_type_name(self):
        rt = make_recharge_type("BAU")
        pt_z = make_project_type("Zzz")
        pt_a = make_project_type("Aaa")
        make_project_type_mapping(rt, pt_z)
        make_project_type_mapping(rt, pt_a)
        qs = selectors.get_all_project_type_mappings(rt.code)
        names = list(qs.values_list("project_type__name", flat=True))
        self.assertEqual(names, sorted(names))

    def test_select_related_project_type_available(self):
        rt = make_recharge_type("BAU")
        pt = make_project_type("Internal")
        make_project_type_mapping(rt, pt)
        obj = selectors.get_all_project_type_mappings(rt.code).first()
        self.assertIsNotNone(obj.project_type)

    def test_returns_empty_for_unknown_recharge_type_code(self):
        qs = selectors.get_all_project_type_mappings("RECHTY-999999")
        self.assertEqual(qs.count(), 0)


# ── get_project_type_mapping_by_id ────────────────────────────────────────────


class GetProjectTypeMappingByIdTest(TestCase):
    def test_returns_object_for_valid_id(self):
        rt = make_recharge_type("BAU")
        pt = make_project_type("Internal")
        mapping = make_project_type_mapping(rt, pt)
        result = selectors.get_project_type_mapping_by_id(rt.code, mapping.pk)
        self.assertIsNotNone(result)
        self.assertEqual(result.pk, mapping.pk)

    def test_returns_none_for_unknown_id(self):
        rt = make_recharge_type("BAU")
        result = selectors.get_project_type_mapping_by_id(rt.code, 999999)
        self.assertIsNone(result)

    def test_returns_none_when_recharge_type_code_mismatch(self):
        rt1 = make_recharge_type("BAU")
        rt2 = make_recharge_type("PROJECT")
        pt = make_project_type("Internal")
        mapping = make_project_type_mapping(rt1, pt)
        result = selectors.get_project_type_mapping_by_id(rt2.code, mapping.pk)
        self.assertIsNone(result)

    def test_select_related_available(self):
        rt = make_recharge_type("BAU")
        pt = make_project_type("Internal")
        mapping = make_project_type_mapping(rt, pt)
        result = selectors.get_project_type_mapping_by_id(rt.code, mapping.pk)
        self.assertIsNotNone(result.project_type)
        self.assertIsNotNone(result.recharge_type)


# ── project_type_mapping_exists ───────────────────────────────────────────────


class ProjectTypeMappingExistsTest(TestCase):
    def test_returns_true_for_existing_mapping(self):
        rt = make_recharge_type("BAU")
        pt = make_project_type("Internal")
        make_project_type_mapping(rt, pt)
        self.assertTrue(selectors.project_type_mapping_exists(rt.pk, pt.pk))

    def test_returns_false_when_no_mapping(self):
        rt = make_recharge_type("BAU")
        pt = make_project_type("Internal")
        self.assertFalse(selectors.project_type_mapping_exists(rt.pk, pt.pk))

    def test_exclude_pk_skips_own_mapping(self):
        rt = make_recharge_type("BAU")
        pt = make_project_type("Internal")
        mapping = make_project_type_mapping(rt, pt)
        self.assertFalse(
            selectors.project_type_mapping_exists(rt.pk, pt.pk, exclude_pk=mapping.pk)
        )

    def test_exclude_pk_finds_other_mapping_for_same_pair(self):
        rt = make_recharge_type("BAU")
        pt = make_project_type("Internal")
        make_project_type_mapping(rt, pt)
        other_rt = make_recharge_type("PROJECT")
        other_mapping = make_project_type_mapping(other_rt, pt)
        self.assertTrue(
            selectors.project_type_mapping_exists(
                rt.pk, pt.pk, exclude_pk=other_mapping.pk
            )
        )
