from django.test import SimpleTestCase

from apps.projects.serializers import (
    ProjectCollaboratorSerializer,
    ProjectCreateSerializer,
    ProjectUpdateSerializer,
)


class ProjectCreateSerializerTest(SimpleTestCase):
    def test_valid_minimal_payload_is_valid(self):
        s = ProjectCreateSerializer(
            data={
                "name": "My Project",
                "project_type_code": "PROJTYPE-1",
                "status_code": "PROJSTAT-1",
            }
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_missing_name_is_invalid(self):
        s = ProjectCreateSerializer(
            data={"project_type_code": "PROJTYPE-1", "status_code": "PROJSTAT-1"}
        )
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_missing_project_type_code_is_invalid(self):
        s = ProjectCreateSerializer(
            data={"name": "My Project", "status_code": "PROJSTAT-1"}
        )
        self.assertFalse(s.is_valid())
        self.assertIn("project_type_code", s.errors)

    def test_missing_status_code_is_invalid(self):
        s = ProjectCreateSerializer(
            data={"name": "My Project", "project_type_code": "PROJTYPE-1"}
        )
        self.assertFalse(s.is_valid())
        self.assertIn("status_code", s.errors)

    def test_optional_fields_accepted(self):
        s = ProjectCreateSerializer(
            data={
                "name": "Full Project",
                "project_type_code": "PROJTYPE-1",
                "status_code": "PROJSTAT-1",
                "programme_code": "PROG-1",
                "sub_status_code": "PROJSUBSTAT-1",
                "assigned_team_code": "TEAM-1",
                "description": "A description",
                "confidence": "high",
                "priority": "medium",
                "efforts_issued": True,
                "run_cost_applies": False,
            }
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_name_exceeding_max_length_is_invalid(self):
        s = ProjectCreateSerializer(
            data={
                "name": "x" * 256,
                "project_type_code": "PROJTYPE-1",
                "status_code": "PROJSTAT-1",
            }
        )
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_is_active_defaults_to_true(self):
        s = ProjectCreateSerializer(
            data={
                "name": "Defaults",
                "project_type_code": "PROJTYPE-1",
                "status_code": "PROJSTAT-1",
            }
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertTrue(s.validated_data["is_active"])

    def test_efforts_issued_defaults_to_false(self):
        s = ProjectCreateSerializer(
            data={
                "name": "Defaults 2",
                "project_type_code": "PROJTYPE-1",
                "status_code": "PROJSTAT-1",
            }
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertFalse(s.validated_data["efforts_issued"])

    def test_programme_code_blank_is_accepted(self):
        s = ProjectCreateSerializer(
            data={
                "name": "Blank Prog",
                "project_type_code": "PROJTYPE-1",
                "status_code": "PROJSTAT-1",
                "programme_code": "",
            }
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_sprint_started_in_code_defaults_to_none(self):
        s = ProjectCreateSerializer(
            data={
                "name": "Sprint Default",
                "project_type_code": "PROJTYPE-1",
                "status_code": "PROJSTAT-1",
            }
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertIsNone(s.validated_data["sprint_started_in_code"])

    def test_sprint_completed_in_code_defaults_to_none(self):
        s = ProjectCreateSerializer(
            data={
                "name": "Sprint Default 2",
                "project_type_code": "PROJTYPE-1",
                "status_code": "PROJSTAT-1",
            }
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertIsNone(s.validated_data["sprint_completed_in_code"])

    def test_sprint_started_in_code_accepted(self):
        s = ProjectCreateSerializer(
            data={
                "name": "Sprint Start",
                "project_type_code": "PROJTYPE-1",
                "status_code": "PROJSTAT-1",
                "sprint_started_in_code": "SPRINT-1",
            }
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["sprint_started_in_code"], "SPRINT-1")

    def test_sprint_completed_in_code_accepted(self):
        s = ProjectCreateSerializer(
            data={
                "name": "Sprint Complete",
                "project_type_code": "PROJTYPE-1",
                "status_code": "PROJSTAT-1",
                "sprint_completed_in_code": "SPRINT-2",
            }
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["sprint_completed_in_code"], "SPRINT-2")

    def test_sprint_codes_blank_accepted(self):
        s = ProjectCreateSerializer(
            data={
                "name": "Blank Sprints",
                "project_type_code": "PROJTYPE-1",
                "status_code": "PROJSTAT-1",
                "sprint_started_in_code": "",
                "sprint_completed_in_code": "",
            }
        )
        self.assertTrue(s.is_valid(), s.errors)


class ProjectUpdateSerializerTest(SimpleTestCase):
    def test_empty_payload_is_valid(self):
        s = ProjectUpdateSerializer(data={})
        self.assertTrue(s.is_valid(), s.errors)

    def test_partial_name_only_is_valid(self):
        s = ProjectUpdateSerializer(data={"name": "Renamed"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_partial_status_only_is_valid(self):
        s = ProjectUpdateSerializer(data={"status_code": "PROJSTAT-2"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_name_exceeding_max_length_is_invalid(self):
        s = ProjectUpdateSerializer(data={"name": "x" * 256})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_all_optional_fields_accepted(self):
        s = ProjectUpdateSerializer(
            data={
                "name": "Updated",
                "project_type_code": "PROJTYPE-2",
                "status_code": "PROJSTAT-2",
                "programme_code": "PROG-2",
                "confidence": "low",
                "priority": "high",
                "is_active": False,
            }
        )
        self.assertTrue(s.is_valid(), s.errors)

    def test_sprint_started_in_code_accepted(self):
        s = ProjectUpdateSerializer(data={"sprint_started_in_code": "SPRINT-1"})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["sprint_started_in_code"], "SPRINT-1")

    def test_sprint_completed_in_code_accepted(self):
        s = ProjectUpdateSerializer(data={"sprint_completed_in_code": "SPRINT-2"})
        self.assertTrue(s.is_valid(), s.errors)
        self.assertEqual(s.validated_data["sprint_completed_in_code"], "SPRINT-2")

    def test_sprint_codes_can_be_null(self):
        s = ProjectUpdateSerializer(
            data={"sprint_started_in_code": None, "sprint_completed_in_code": None}
        )
        self.assertTrue(s.is_valid(), s.errors)
        self.assertIsNone(s.validated_data["sprint_started_in_code"])
        self.assertIsNone(s.validated_data["sprint_completed_in_code"])

    def test_sprint_codes_can_be_blank(self):
        s = ProjectUpdateSerializer(
            data={"sprint_started_in_code": "", "sprint_completed_in_code": ""}
        )
        self.assertTrue(s.is_valid(), s.errors)


class ProjectCollaboratorSerializerTest(SimpleTestCase):
    def test_valid_team_code_is_valid(self):
        s = ProjectCollaboratorSerializer(data={"team_code": "TEAM-1"})
        self.assertTrue(s.is_valid(), s.errors)

    def test_missing_team_code_is_invalid(self):
        s = ProjectCollaboratorSerializer(data={})
        self.assertFalse(s.is_valid())
        self.assertIn("team_code", s.errors)

    def test_empty_team_code_is_invalid(self):
        s = ProjectCollaboratorSerializer(data={"team_code": ""})
        self.assertFalse(s.is_valid())
        self.assertIn("team_code", s.errors)
