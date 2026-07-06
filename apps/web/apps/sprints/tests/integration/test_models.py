from datetime import date
from unittest.mock import patch

from django.db import IntegrityError
from django.test import TestCase

from apps.financial_years.tests.factories import make_financial_year
from apps.sprints.constants import (
    SprintDataImportStatus,
    SprintDataImportType,
    SprintStatus,
)
from apps.sprints.models import (
    Capacity,
    Sprint,
    SprintDataImport,
    SprintDataImportConfirmed,
    SprintDataImportRow,
)
from apps.sprints.tests.factories import make_capacity, make_sprint
from apps.teams.tests.factories import make_team
from apps.users.tests.factories import make_user


def _make_import(
    sprint,
    team,
    user=None,
    import_type=SprintDataImportType.FORECAST,
    version_number=1,
    status=SprintDataImportStatus.ACTIVE,
):
    if user is None:
        user = make_user()
    return SprintDataImport.objects.create(
        sprint=sprint,
        team=team,
        version_number=version_number,
        file_name="test.csv",
        status=status,
        import_type=import_type,
        created_by=user,
        updated_by=user,
    )


class SprintCodeTest(TestCase):
    def test_code_starts_with_sprint_prefix(self):
        sprint = make_sprint()
        self.assertTrue(sprint.code.startswith("SPRINT-"))

    def test_code_contains_pk(self):
        sprint = make_sprint()
        self.assertEqual(sprint.code, f"SPRINT-{sprint.pk}")

    def test_codes_are_unique_across_sprints(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        s1 = make_sprint(
            financial_year=fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        s2 = make_sprint(
            financial_year=fy,
            sprint_number=2,
            start_date=date(2024, 4, 15),
            end_date=date(2024, 4, 28),
        )
        self.assertNotEqual(s1.code, s2.code)


class SprintFieldDefaultsTest(TestCase):
    def test_status_defaults_to_future(self):
        sprint = make_sprint()
        self.assertEqual(sprint.status, SprintStatus.FUTURE)

    def test_is_overridden_defaults_to_false(self):
        sprint = make_sprint()
        self.assertFalse(sprint.is_overridden)

    def test_is_closed_defaults_to_false(self):
        sprint = make_sprint()
        self.assertFalse(sprint.is_closed)

    def test_closed_on_defaults_to_null(self):
        sprint = make_sprint()
        self.assertIsNone(sprint.closed_on)

    def test_closed_by_defaults_to_null(self):
        sprint = make_sprint()
        self.assertIsNone(sprint.closed_by)

    def test_note_defaults_to_empty(self):
        sprint = make_sprint()
        self.assertEqual(sprint.note, "")

    def test_is_active_defaults_to_true(self):
        sprint = make_sprint()
        self.assertTrue(sprint.is_active)

    def test_created_at_set_on_create(self):
        sprint = make_sprint()
        self.assertIsNotNone(sprint.created_at)

    def test_updated_at_set_on_create(self):
        sprint = make_sprint()
        self.assertIsNotNone(sprint.updated_at)

    def test_created_by_nullable(self):
        sprint = make_sprint()
        self.assertIsNone(sprint.created_by)

    def test_updated_by_nullable(self):
        sprint = make_sprint()
        self.assertIsNone(sprint.updated_by)

    def test_created_by_stores_user(self):
        user = make_user()
        sprint = make_sprint(created_by=user, updated_by=user)
        self.assertEqual(sprint.created_by, user)


class SprintMonthFieldTest(TestCase):
    def test_month_auto_set_from_end_date_on_create(self):
        sprint = make_sprint(end_date=date(2024, 4, 14))
        self.assertEqual(sprint.month, "2024-04")

    def test_month_updates_when_end_date_changes(self):
        sprint = make_sprint(end_date=date(2024, 4, 14))
        sprint.end_date = date(2024, 5, 31)
        sprint.save(update_fields=["end_date", "month"])
        sprint.refresh_from_db()
        self.assertEqual(sprint.month, "2024-05")


class SprintStrTest(TestCase):
    def test_str_includes_name_and_code(self):
        sprint = make_sprint(name="Sprint 1")
        expected = f"Sprint 1 ({sprint.code})"
        self.assertEqual(str(sprint), expected)


class SprintOrderingTest(TestCase):
    def test_ordered_by_sprint_number_ascending(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        make_sprint(
            financial_year=fy,
            sprint_number=3,
            start_date=date(2024, 4, 29),
            end_date=date(2024, 5, 12),
        )
        make_sprint(
            financial_year=fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        make_sprint(
            financial_year=fy,
            sprint_number=2,
            start_date=date(2024, 4, 15),
            end_date=date(2024, 4, 28),
        )
        numbers = list(Sprint.objects.values_list("sprint_number", flat=True))
        self.assertEqual(numbers, [1, 2, 3])


class SprintSprintNumberUniqueTest(TestCase):
    def test_duplicate_sprint_number_raises_integrity_error(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        make_sprint(
            financial_year=fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        with self.assertRaises(IntegrityError):
            Sprint.objects.create(
                financial_year=fy,
                sprint_number=1,
                name="Duplicate",
                start_date=date(2024, 4, 15),
                end_date=date(2024, 4, 28),
            )


class SprintCustomPermissionsTest(TestCase):
    def test_custom_permissions_defined(self):
        perm_codenames = {p[0] for p in Sprint._meta.permissions}
        self.assertIn("import_sprint", perm_codenames)
        self.assertIn("export_sprint", perm_codenames)
        self.assertIn("generate_sprint", perm_codenames)
        self.assertIn("close_sprint", perm_codenames)


@patch("apps.sprints.signals._rebuild_sprint")
class CapacityFieldDefaultsTest(TestCase):
    def test_working_days_defaults_to_zero(self, _mock_rebuild):
        user = make_user()
        sprint = make_sprint()
        cap = Capacity.objects.create(sprint=sprint, member=user)
        self.assertEqual(cap.working_days, 0)

    def test_net_capacity_defaults_to_zero(self, _mock_rebuild):
        user = make_user()
        sprint = make_sprint()
        cap = Capacity.objects.create(sprint=sprint, member=user)
        self.assertEqual(cap.net_capacity, 0)

    def test_str_includes_member_and_sprint(self, _mock_rebuild):
        user = make_user(
            email="member@example.com", first_name="Alice", last_name="Smith"
        )
        sprint = make_sprint(name="Sprint 1")
        cap = make_capacity(sprint=sprint, member=user)
        self.assertIn(str(user), str(cap))
        self.assertIn(str(sprint), str(cap))


@patch("apps.sprints.signals._rebuild_sprint")
class CapacityUniqueConstraintTest(TestCase):
    def test_duplicate_sprint_member_raises_integrity_error(self, _mock_rebuild):
        user = make_user()
        sprint = make_sprint()
        make_capacity(sprint=sprint, member=user)
        with self.assertRaises(IntegrityError):
            Capacity.objects.create(sprint=sprint, member=user)


# ── SprintDataImport ──────────────────────────────────────────────────────────


class SprintDataImportCodeTest(TestCase):
    def test_code_starts_with_sptimp_prefix(self):
        sprint = make_sprint()
        team = make_team()
        record = _make_import(sprint, team)
        self.assertTrue(record.code.startswith("SPTIMP-"))

    def test_code_contains_pk(self):
        sprint = make_sprint()
        team = make_team()
        record = _make_import(sprint, team)
        self.assertEqual(record.code, f"SPTIMP-{record.pk}")


class SprintDataImportFieldDefaultsTest(TestCase):
    def test_status_defaults_to_active(self):
        sprint = make_sprint()
        team = make_team()
        record = SprintDataImport.objects.create(
            sprint=sprint, team=team, version_number=1
        )
        self.assertEqual(record.status, SprintDataImportStatus.ACTIVE)

    def test_import_type_defaults_to_forecast(self):
        sprint = make_sprint()
        team = make_team()
        record = SprintDataImport.objects.create(
            sprint=sprint, team=team, version_number=1
        )
        self.assertEqual(record.import_type, SprintDataImportType.FORECAST)

    def test_file_name_defaults_to_empty(self):
        sprint = make_sprint()
        team = make_team()
        record = SprintDataImport.objects.create(
            sprint=sprint, team=team, version_number=1
        )
        self.assertEqual(record.file_name, "")

    def test_created_at_set_on_create(self):
        sprint = make_sprint()
        team = make_team()
        record = _make_import(sprint, team)
        self.assertIsNotNone(record.created_at)

    def test_created_by_nullable(self):
        sprint = make_sprint()
        team = make_team()
        record = SprintDataImport.objects.create(
            sprint=sprint, team=team, version_number=1
        )
        self.assertIsNone(record.created_by)

    def test_created_by_stores_user(self):
        user = make_user()
        sprint = make_sprint()
        team = make_team()
        record = _make_import(sprint, team, user=user)
        self.assertEqual(record.created_by, user)

    def test_version_number_stores_correctly(self):
        sprint = make_sprint()
        team = make_team()
        record = _make_import(sprint, team, version_number=3)
        self.assertEqual(record.version_number, 3)


class SprintDataImportStrTest(TestCase):
    def test_str_contains_import_type_and_version(self):
        sprint = make_sprint(name="Sprint 1")
        team = make_team(name="Team A")
        record = _make_import(sprint, team, import_type=SprintDataImportType.FORECAST)
        result = str(record)
        self.assertIn("FORECAST", result.upper())
        self.assertIn("1", result)


class SprintDataImportOrderingTest(TestCase):
    def test_ordered_by_version_number_descending(self):
        sprint = make_sprint()
        team = make_team()
        user = make_user()
        _make_import(sprint, team, user=user, version_number=1)
        _make_import(sprint, team, user=user, version_number=2)
        _make_import(sprint, team, user=user, version_number=3)
        version_numbers = list(
            SprintDataImport.objects.filter(sprint=sprint, team=team).values_list(
                "version_number", flat=True
            )
        )
        self.assertEqual(version_numbers, [3, 2, 1])


class SprintDataImportUniqueConstraintTest(TestCase):
    def test_duplicate_sprint_team_type_version_raises_integrity_error(self):
        sprint = make_sprint()
        team = make_team()
        _make_import(
            sprint, team, import_type=SprintDataImportType.FORECAST, version_number=1
        )
        with self.assertRaises(IntegrityError):
            SprintDataImport.objects.create(
                sprint=sprint,
                team=team,
                import_type=SprintDataImportType.FORECAST,
                version_number=1,
            )

    def test_same_sprint_team_different_import_type_allowed(self):
        sprint = make_sprint()
        team = make_team()
        _make_import(
            sprint, team, import_type=SprintDataImportType.FORECAST, version_number=1
        )
        record = SprintDataImport.objects.create(
            sprint=sprint,
            team=team,
            import_type=SprintDataImportType.ACTUAL,
            version_number=1,
        )
        self.assertIsNotNone(record.pk)


class SprintDataImportCustomPermissionsTest(TestCase):
    def test_custom_permissions_defined(self):
        perm_codenames = {p[0] for p in SprintDataImport._meta.permissions}
        self.assertIn("import_forecast", perm_codenames)
        self.assertIn("import_actuals", perm_codenames)
        self.assertIn("review_forecast", perm_codenames)
        self.assertIn("confirm_forecast", perm_codenames)
        self.assertIn("review_complete", perm_codenames)


# ── SprintDataImportRow ───────────────────────────────────────────────────────


class SprintDataImportRowCodeTest(TestCase):
    def test_code_starts_with_sptimprw_prefix(self):
        sprint = make_sprint()
        team = make_team()
        record = _make_import(sprint, team)
        row = SprintDataImportRow.objects.create(import_record=record, title="Test")
        self.assertTrue(row.code.startswith("SPTIMPRW-"))


class SprintDataImportRowFieldDefaultsTest(TestCase):
    def test_is_manually_added_defaults_to_false(self):
        sprint = make_sprint()
        team = make_team()
        record = _make_import(sprint, team)
        row = SprintDataImportRow.objects.create(import_record=record, title="Row")
        self.assertFalse(row.is_manually_added)

    def test_is_deleted_defaults_to_false(self):
        sprint = make_sprint()
        team = make_team()
        record = _make_import(sprint, team)
        row = SprintDataImportRow.objects.create(import_record=record, title="Row")
        self.assertFalse(row.is_deleted)

    def test_story_type_defaults_to_empty(self):
        sprint = make_sprint()
        team = make_team()
        record = _make_import(sprint, team)
        row = SprintDataImportRow.objects.create(import_record=record)
        self.assertEqual(row.story_type, "")

    def test_efforts_defaults_to_empty(self):
        sprint = make_sprint()
        team = make_team()
        record = _make_import(sprint, team)
        row = SprintDataImportRow.objects.create(import_record=record)
        self.assertEqual(row.efforts, "")


# ── SprintDataImportConfirmed ─────────────────────────────────────────────────


class SprintDataImportConfirmedFieldsTest(TestCase):
    def setUp(self):
        self.sprint = make_sprint()
        self.team = make_team()
        self.import_record = _make_import(self.sprint, self.team)

    def test_story_type_defaults_to_empty(self):
        confirmed = SprintDataImportConfirmed.objects.create(
            sprint=self.sprint,
            team=self.team,
            import_record=self.import_record,
            import_type=SprintDataImportType.FORECAST,
        )
        self.assertEqual(confirmed.story_type, "")

    def test_days_defaults_to_zero(self):
        from decimal import Decimal

        confirmed = SprintDataImportConfirmed.objects.create(
            sprint=self.sprint,
            team=self.team,
            import_record=self.import_record,
            import_type=SprintDataImportType.FORECAST,
        )
        self.assertEqual(confirmed.days, Decimal("0"))

    def test_jira_id_stores_correctly(self):
        confirmed = SprintDataImportConfirmed.objects.create(
            sprint=self.sprint,
            team=self.team,
            import_record=self.import_record,
            import_type=SprintDataImportType.FORECAST,
            jira_id="JIRA-42",
        )
        self.assertEqual(confirmed.jira_id, "JIRA-42")

    def test_import_type_stores_correctly(self):
        confirmed = SprintDataImportConfirmed.objects.create(
            sprint=self.sprint,
            team=self.team,
            import_record=self.import_record,
            import_type=SprintDataImportType.ACTUAL,
        )
        self.assertEqual(confirmed.import_type, SprintDataImportType.ACTUAL)

    def test_created_at_set_on_create(self):
        confirmed = SprintDataImportConfirmed.objects.create(
            sprint=self.sprint,
            team=self.team,
            import_record=self.import_record,
            import_type=SprintDataImportType.FORECAST,
        )
        self.assertIsNotNone(confirmed.created_at)
