from django.test import SimpleTestCase

from apps.projects.serializers.attachment import ProjectAttachmentSerializer


class ProjectAttachmentSerializerFieldsTest(SimpleTestCase):
    def test_expected_fields_declared(self):
        expected = {
            "code",
            "project_code",
            "file_name",
            "content_type",
            "file_size",
            "created_at",
            "created_by",
        }
        actual = set(ProjectAttachmentSerializer.Meta.fields)
        self.assertEqual(actual, expected)

    def test_all_fields_are_read_only(self):
        serializer = ProjectAttachmentSerializer()
        for name, field in serializer.fields.items():
            self.assertTrue(
                field.read_only,
                f"Field '{name}' should be read_only but is not.",
            )
