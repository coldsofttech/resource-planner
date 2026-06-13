from django.test import TestCase

from apps.projects.models import Programme
from apps.projects.serializers import (
    ProgrammeDetailSerializer,
    ProgrammeListSerializer,
)
from apps.projects.tests.factories import make_programme


class ProgrammeListSerializerTest(TestCase):
    def test_output_fields_present(self):
        p = make_programme("Alpha", description="Desc")
        data = ProgrammeListSerializer(p).data
        for field in [
            "code",
            "name",
            "description",
            "is_active",
            "is_protected",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]:
            self.assertIn(field, data)

    def test_name_value_matches(self):
        p = make_programme("Beta")
        data = ProgrammeListSerializer(p).data
        self.assertEqual(data["name"], "Beta")

    def test_is_protected_included(self):
        p = Programme.objects.get(name="Others")
        data = ProgrammeListSerializer(p).data
        self.assertTrue(data["is_protected"])


class ProgrammeDetailSerializerTest(TestCase):
    def test_output_fields_present(self):
        p = make_programme("Alpha")
        data = ProgrammeDetailSerializer(p).data
        for field in [
            "code",
            "name",
            "description",
            "is_active",
            "is_protected",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
        ]:
            self.assertIn(field, data)

    def test_code_value_matches(self):
        p = make_programme("Alpha")
        data = ProgrammeDetailSerializer(p).data
        self.assertEqual(data["code"], p.code)
