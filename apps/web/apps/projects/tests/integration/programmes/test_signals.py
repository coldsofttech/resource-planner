import logging

from django.test import TestCase

from apps.projects.tests.factories import make_programme


class ProgrammeSignalTest(TestCase):
    def test_post_save_create_logged(self):
        with self.assertLogs("apps.projects.signals", level=logging.DEBUG):
            make_programme("Logged")

    def test_post_save_update_logged(self):
        p = make_programme("Alpha")
        with self.assertLogs("apps.projects.signals", level=logging.DEBUG):
            p.name = "Updated"
            p.save(update_fields=["name"])

    def test_post_delete_logged(self):
        p = make_programme("ToDelete")
        with self.assertLogs("apps.projects.signals", level=logging.DEBUG):
            p.delete()
