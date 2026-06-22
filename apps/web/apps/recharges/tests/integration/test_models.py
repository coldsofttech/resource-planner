from django.db import IntegrityError
from django.test import TestCase

from apps.projects.tests.factories import make_project_type
from apps.recharges.models import ProjectTypeMapping, RechargeType
from apps.recharges.tests.factories import make_project_type_mapping, make_recharge_type
from apps.users.tests.factories import make_user

# ── RechargeType ──────────────────────────────────────────────────────────────


class RechargeTypeCodeTest(TestCase):
    def test_code_assigned_on_save(self):
        rt = make_recharge_type()
        self.assertTrue(rt.code.startswith("RECHTY-"))

    def test_code_contains_pk(self):
        rt = make_recharge_type()
        self.assertEqual(rt.code, f"RECHTY-{rt.pk}")

    def test_codes_are_unique_across_records(self):
        rt1 = make_recharge_type("BAU")
        rt2 = make_recharge_type("PROJECT")
        self.assertNotEqual(rt1.code, rt2.code)

    def test_code_not_editable_directly(self):
        self.assertFalse(RechargeType._meta.get_field("code").editable)


class RechargeTypeStrTest(TestCase):
    def test_str_returns_name(self):
        rt = make_recharge_type("HOLIDAY")
        self.assertEqual(str(rt), "HOLIDAY")


class RechargeTypeFieldDefaultsTest(TestCase):
    def setUp(self):
        self.rt = make_recharge_type()

    def test_is_active_defaults_to_true(self):
        self.assertTrue(self.rt.is_active)

    def test_description_defaults_to_empty(self):
        self.assertEqual(self.rt.description, "")

    def test_created_at_is_set(self):
        self.assertIsNotNone(self.rt.created_at)

    def test_updated_at_is_set(self):
        self.assertIsNotNone(self.rt.updated_at)

    def test_created_by_defaults_to_none(self):
        self.assertIsNone(self.rt.created_by)

    def test_updated_by_defaults_to_none(self):
        self.assertIsNone(self.rt.updated_by)

    def test_created_by_stores_user(self):
        user = make_user()
        rt = make_recharge_type("CAPEX", created_by=user, updated_by=user)
        self.assertEqual(rt.created_by, user)


class RechargeTypeConstraintTest(TestCase):
    def test_duplicate_name_raises_integrity_error(self):
        make_recharge_type("BAU")
        with self.assertRaises(IntegrityError):
            make_recharge_type("BAU")

    def test_different_names_are_allowed(self):
        rt1 = make_recharge_type("BAU")
        rt2 = make_recharge_type("PROJECT")
        self.assertNotEqual(rt1.pk, rt2.pk)


class RechargeTypeOrderingTest(TestCase):
    def test_ordered_by_name(self):
        make_recharge_type("PROJECT")
        make_recharge_type("BAU")
        make_recharge_type("HOLIDAY")
        names = list(RechargeType.objects.values_list("name", flat=True))
        self.assertEqual(names, sorted(names))


# ── ProjectTypeMapping ────────────────────────────────────────────────────────


class ProjectTypeMappingStrTest(TestCase):
    def test_str_contains_project_type_and_recharge_type(self):
        rt = make_recharge_type("BAU")
        pt = make_project_type("Internal")
        mapping = make_project_type_mapping(rt, pt)
        result = str(mapping)
        self.assertIn(str(pt), result)
        self.assertIn(str(rt), result)


class ProjectTypeMappingFieldDefaultsTest(TestCase):
    def setUp(self):
        self.rt = make_recharge_type("BAU")
        self.pt = make_project_type("Internal")
        self.mapping = make_project_type_mapping(self.rt, self.pt)

    def test_created_at_is_set(self):
        self.assertIsNotNone(self.mapping.created_at)

    def test_updated_at_is_set(self):
        self.assertIsNotNone(self.mapping.updated_at)

    def test_created_by_defaults_to_none(self):
        self.assertIsNone(self.mapping.created_by)

    def test_updated_by_defaults_to_none(self):
        self.assertIsNone(self.mapping.updated_by)


class ProjectTypeMappingForeignKeyTest(TestCase):
    def test_project_type_linked(self):
        rt = make_recharge_type("BAU")
        pt = make_project_type("External")
        mapping = make_project_type_mapping(rt, pt)
        self.assertEqual(mapping.project_type, pt)

    def test_recharge_type_linked(self):
        rt = make_recharge_type("BAU")
        pt = make_project_type("External")
        mapping = make_project_type_mapping(rt, pt)
        self.assertEqual(mapping.recharge_type, rt)


class ProjectTypeMappingConstraintTest(TestCase):
    def test_duplicate_mapping_raises_integrity_error(self):
        rt = make_recharge_type("BAU")
        pt = make_project_type("Duplicate")
        make_project_type_mapping(rt, pt)
        with self.assertRaises(IntegrityError):
            make_project_type_mapping(rt, pt)

    def test_same_project_type_on_different_recharge_types_allowed(self):
        rt1 = make_recharge_type("BAU")
        rt2 = make_recharge_type("PROJECT")
        pt = make_project_type("Shared Type")
        m1 = make_project_type_mapping(rt1, pt)
        m2 = make_project_type_mapping(rt2, pt)
        self.assertNotEqual(m1.pk, m2.pk)

    def test_different_project_types_on_same_recharge_type_allowed(self):
        rt = make_recharge_type("BAU")
        pt1 = make_project_type("Type A")
        pt2 = make_project_type("Type B")
        m1 = make_project_type_mapping(rt, pt1)
        m2 = make_project_type_mapping(rt, pt2)
        self.assertNotEqual(m1.pk, m2.pk)


class ProjectTypeMappingCascadeTest(TestCase):
    def test_cascade_delete_when_recharge_type_deleted(self):
        rt = make_recharge_type("BAU")
        pt = make_project_type("Internal")
        mapping = make_project_type_mapping(rt, pt)
        pk = mapping.pk
        rt.delete()
        self.assertFalse(ProjectTypeMapping.objects.filter(pk=pk).exists())

    def test_cascade_delete_when_project_type_deleted(self):
        rt = make_recharge_type("BAU")
        pt = make_project_type("Internal")
        mapping = make_project_type_mapping(rt, pt)
        pk = mapping.pk
        pt.delete()
        self.assertFalse(ProjectTypeMapping.objects.filter(pk=pk).exists())


class ProjectTypeMappingOrderingTest(TestCase):
    def test_ordered_by_project_type_name(self):
        rt = make_recharge_type("BAU")
        pt_z = make_project_type("Zzz Type")
        pt_a = make_project_type("Aaa Type")
        make_project_type_mapping(rt, pt_z)
        make_project_type_mapping(rt, pt_a)
        names = list(
            ProjectTypeMapping.objects.filter(recharge_type=rt).values_list(
                "project_type__name", flat=True
            )
        )
        self.assertEqual(names, sorted(names))
