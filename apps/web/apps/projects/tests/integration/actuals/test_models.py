from django.db import IntegrityError
from django.test import TestCase

from apps.configurations.tests.factories import mark_setup_complete
from apps.projects.models.project_actual_config import ProjectActualConfig
from apps.projects.tests.factories import make_project


class ProjectActualConfigFieldDefaultsTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.project = make_project()

    def test_ignore_risk_defaults_to_false(self):
        config = ProjectActualConfig.objects.create(project=self.project)
        self.assertFalse(config.ignore_risk)

    def test_ignore_prev_fy_actuals_defaults_to_false(self):
        config = ProjectActualConfig.objects.create(project=self.project)
        self.assertFalse(config.ignore_prev_fy_actuals)

    def test_notes_defaults_to_empty_string(self):
        config = ProjectActualConfig.objects.create(project=self.project)
        self.assertEqual(config.notes, "")

    def test_created_at_is_auto_set(self):
        config = ProjectActualConfig.objects.create(project=self.project)
        self.assertIsNotNone(config.created_at)

    def test_updated_at_is_auto_set(self):
        config = ProjectActualConfig.objects.create(project=self.project)
        self.assertIsNotNone(config.updated_at)

    def test_created_by_defaults_to_none(self):
        config = ProjectActualConfig.objects.create(project=self.project)
        self.assertIsNone(config.created_by)

    def test_updated_by_defaults_to_none(self):
        config = ProjectActualConfig.objects.create(project=self.project)
        self.assertIsNone(config.updated_by)


class ProjectActualConfigOneToOneConstraintTest(TestCase):
    def setUp(self):
        mark_setup_complete()

    def test_duplicate_config_for_same_project_raises_integrity_error(self):
        project = make_project()
        ProjectActualConfig.objects.create(project=project)
        with self.assertRaises(IntegrityError):
            ProjectActualConfig.objects.create(project=project)

    def test_separate_projects_can_each_have_a_config(self):
        project_a = make_project(name="Project A")
        project_b = make_project(name="Project B")
        config_a = ProjectActualConfig.objects.create(project=project_a)
        config_b = ProjectActualConfig.objects.create(project=project_b)
        self.assertNotEqual(config_a.pk, config_b.pk)
