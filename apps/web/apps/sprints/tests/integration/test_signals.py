from datetime import date
from unittest.mock import patch

from django.test import TestCase

from apps.financial_years.tests.factories import make_financial_year
from apps.sprints.tests.factories import make_sprint


class OnSprintSaveCreatedSignalTest(TestCase):
    @patch("apps.sprints.signals._rebuild_sprint")
    def test_rebuild_triggered_on_sprint_creation(self, mock_rebuild):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        make_sprint(
            financial_year=fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        mock_rebuild.assert_called_once()


class OnSprintSaveUpdateCapacityFieldsSignalTest(TestCase):
    @patch("apps.sprints.signals._rebuild_sprint")
    def test_rebuild_triggered_when_start_date_updated(self, mock_rebuild):
        sprint = make_sprint()
        mock_rebuild.reset_mock()
        sprint.start_date = date(2024, 4, 2)
        sprint.save(update_fields=["start_date"])
        mock_rebuild.assert_called_once()

    @patch("apps.sprints.signals._rebuild_sprint")
    def test_rebuild_triggered_when_end_date_updated(self, mock_rebuild):
        sprint = make_sprint()
        mock_rebuild.reset_mock()
        sprint.end_date = date(2024, 4, 15)
        sprint.save(update_fields=["end_date"])
        mock_rebuild.assert_called_once()

    @patch("apps.sprints.signals._rebuild_sprint")
    def test_rebuild_triggered_when_status_updated(self, mock_rebuild):
        sprint = make_sprint()
        mock_rebuild.reset_mock()
        from apps.sprints.constants import SprintStatus

        sprint.status = SprintStatus.IN_PROGRESS
        sprint.save(update_fields=["status"])
        mock_rebuild.assert_called_once()

    @patch("apps.sprints.signals._rebuild_sprint")
    def test_rebuild_triggered_when_is_active_updated(self, mock_rebuild):
        sprint = make_sprint()
        mock_rebuild.reset_mock()
        sprint.is_active = False
        sprint.save(update_fields=["is_active"])
        mock_rebuild.assert_called_once()


class OnSprintSaveNonCapacityFieldsSignalTest(TestCase):
    @patch("apps.sprints.signals._rebuild_sprint")
    def test_rebuild_not_triggered_when_only_note_updated(self, mock_rebuild):
        sprint = make_sprint()
        mock_rebuild.reset_mock()
        sprint.note = "Updated note"
        sprint.save(update_fields=["note"])
        mock_rebuild.assert_not_called()

    @patch("apps.sprints.signals._rebuild_sprint")
    def test_rebuild_not_triggered_when_only_name_updated(self, mock_rebuild):
        sprint = make_sprint()
        mock_rebuild.reset_mock()
        sprint.name = "Renamed Sprint"
        sprint.save(update_fields=["name"])
        mock_rebuild.assert_not_called()


class OnSprintDeleteSignalTest(TestCase):
    def test_sprint_can_be_deleted_without_error(self):
        sprint = make_sprint()
        sprint_pk = sprint.pk
        sprint.delete()
        from apps.sprints.models import Sprint

        self.assertFalse(Sprint.objects.filter(pk=sprint_pk).exists())
