from datetime import date

from django.test import TestCase

from apps.financial_years.tests.factories import make_financial_year
from apps.sprints import selectors
from apps.sprints.constants import (
    SprintDataImportStatus,
    SprintDataImportType,
    SprintStatus,
)
from apps.sprints.models import (
    SprintDataImport,
    SprintDataImportReview,
    SprintDataImportRow,
)
from apps.sprints.selectors.sprint_data_import import (
    get_has_review_for_import,
    get_import_by_code,
    get_imports_for_sprint_team,
    get_latest_active_import,
    get_rows_for_import,
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


class GetAllSprintsTest(TestCase):
    def test_returns_all_sprints(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
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
            is_active=False,
        )
        qs = selectors.get_all_sprints()
        self.assertEqual(qs.count(), 2)

    def test_returns_empty_when_none(self):
        self.assertEqual(selectors.get_all_sprints().count(), 0)

    def test_selects_related_financial_year(self):
        make_sprint()
        sprint = selectors.get_all_sprints().first()
        self.assertIsNotNone(sprint.financial_year)


class GetActiveSprintsTest(TestCase):
    def test_excludes_inactive_sprints(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        make_sprint(
            financial_year=fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
            is_active=True,
        )
        make_sprint(
            financial_year=fy,
            sprint_number=2,
            start_date=date(2024, 4, 15),
            end_date=date(2024, 4, 28),
            is_active=False,
        )
        qs = selectors.get_active_sprints()
        self.assertEqual(qs.count(), 1)


class GetSprintByCodeTest(TestCase):
    def test_returns_sprint_for_valid_code(self):
        sprint = make_sprint()
        result = selectors.get_sprint_by_code(sprint.code)
        self.assertIsNotNone(result)
        self.assertEqual(result.pk, sprint.pk)

    def test_returns_none_for_unknown_code(self):
        result = selectors.get_sprint_by_code("SPRINT-9999")
        self.assertIsNone(result)


class GetInProgressSprintTest(TestCase):
    def test_returns_in_progress_active_sprint(self):
        sprint = make_sprint(status=SprintStatus.IN_PROGRESS, is_active=True)
        result = selectors.get_in_progress_sprint()
        self.assertIsNotNone(result)
        self.assertEqual(result.pk, sprint.pk)

    def test_returns_none_when_no_in_progress(self):
        make_sprint(status=SprintStatus.FUTURE)
        result = selectors.get_in_progress_sprint()
        self.assertIsNone(result)

    def test_excludes_inactive_in_progress_sprint(self):
        make_sprint(status=SprintStatus.IN_PROGRESS, is_active=False)
        result = selectors.get_in_progress_sprint()
        self.assertIsNone(result)


class GetSprintsForFYTest(TestCase):
    def test_returns_sprints_for_correct_fy(self):
        fy1 = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        fy2 = make_financial_year(
            start_date=date(2025, 4, 1), end_date=date(2026, 3, 31)
        )
        make_sprint(
            financial_year=fy1,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        make_sprint(
            financial_year=fy2,
            sprint_number=2,
            start_date=date(2025, 4, 1),
            end_date=date(2025, 4, 14),
        )
        qs = selectors.get_sprints_for_fy(fy1.code)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().financial_year, fy1)

    def test_returns_empty_for_fy_with_no_sprints(self):
        fy = make_financial_year()
        qs = selectors.get_sprints_for_fy(fy.code)
        self.assertEqual(qs.count(), 0)


class GetSprintOptionsTest(TestCase):
    def test_returns_active_sprints_only(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        make_sprint(
            financial_year=fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
            is_active=True,
        )
        make_sprint(
            financial_year=fy,
            sprint_number=2,
            start_date=date(2024, 4, 15),
            end_date=date(2024, 4, 28),
            is_active=False,
        )
        qs = selectors.get_sprint_options()
        self.assertEqual(qs.count(), 1)

    def test_filters_by_fy_code(self):
        fy1 = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        fy2 = make_financial_year(
            start_date=date(2025, 4, 1), end_date=date(2026, 3, 31)
        )
        make_sprint(
            financial_year=fy1,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        make_sprint(
            financial_year=fy2,
            sprint_number=2,
            start_date=date(2025, 4, 1),
            end_date=date(2025, 4, 14),
        )
        qs = selectors.get_sprint_options(fy_code=fy1.code)
        self.assertEqual(qs.count(), 1)

    def test_ordered_by_sprint_number(self):
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
        numbers = list(
            selectors.get_sprint_options().values_list("sprint_number", flat=True)
        )
        self.assertEqual(numbers, sorted(numbers))


class GetDistinctMonthsForFYTest(TestCase):
    def test_returns_distinct_months_in_chronological_order(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        make_sprint(
            financial_year=fy,
            sprint_number=2,
            start_date=date(2024, 4, 15),
            end_date=date(2024, 4, 28),
        )
        make_sprint(
            financial_year=fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        make_sprint(
            financial_year=fy,
            sprint_number=3,
            start_date=date(2024, 4, 29),
            end_date=date(2024, 5, 12),
        )
        self.assertEqual(
            selectors.get_distinct_months_for_fy(fy.code), ["2024-04", "2024-05"]
        )

    def test_excludes_inactive_sprints(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        make_sprint(
            financial_year=fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
            is_active=False,
        )
        self.assertEqual(selectors.get_distinct_months_for_fy(fy.code), [])

    def test_scoped_to_fy(self):
        fy1 = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        fy2 = make_financial_year(
            start_date=date(2025, 4, 1), end_date=date(2026, 3, 31)
        )
        make_sprint(
            financial_year=fy1,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        make_sprint(
            financial_year=fy2,
            sprint_number=2,
            start_date=date(2025, 4, 1),
            end_date=date(2025, 4, 14),
        )
        self.assertEqual(selectors.get_distinct_months_for_fy(fy1.code), ["2024-04"])


class GetSprintStatsTest(TestCase):
    def test_all_expected_keys_present(self):
        stats = selectors.get_sprint_stats()
        for key in (
            "total",
            "active",
            "inactive",
            "in_progress",
            "future",
            "completed",
            "expired",
            "closed",
            "overridden",
        ):
            self.assertIn(key, stats)

    def test_stats_counts_are_accurate(self):
        make_sprint(status=SprintStatus.IN_PROGRESS, is_active=True)
        make_sprint(
            status=SprintStatus.FUTURE,
            is_active=True,
            sprint_number=2,
            start_date=date(2024, 4, 15),
            end_date=date(2024, 4, 28),
        )
        make_sprint(
            status=SprintStatus.COMPLETED,
            is_active=False,
            sprint_number=3,
            start_date=date(2024, 4, 29),
            end_date=date(2024, 5, 12),
        )
        stats = selectors.get_sprint_stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["active"], 2)
        self.assertEqual(stats["inactive"], 1)
        self.assertEqual(stats["in_progress"], 1)
        self.assertEqual(stats["future"], 1)
        self.assertEqual(stats["completed"], 1)

    def test_empty_returns_zeroes(self):
        stats = selectors.get_sprint_stats()
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["in_progress"], 0)


class HasOverlappingSprintTest(TestCase):
    def setUp(self):
        self.fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        self.sprint = make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )

    def test_detects_full_overlap(self):
        self.assertTrue(
            selectors.has_overlapping_sprint(
                date(2024, 4, 1), date(2024, 4, 14), fy_pk=self.fy.pk
            )
        )

    def test_detects_partial_overlap_at_start(self):
        self.assertTrue(
            selectors.has_overlapping_sprint(
                date(2024, 3, 28), date(2024, 4, 7), fy_pk=self.fy.pk
            )
        )

    def test_detects_partial_overlap_at_end(self):
        self.assertTrue(
            selectors.has_overlapping_sprint(
                date(2024, 4, 10), date(2024, 4, 20), fy_pk=self.fy.pk
            )
        )

    def test_no_overlap_before(self):
        self.assertFalse(
            selectors.has_overlapping_sprint(
                date(2024, 3, 1), date(2024, 3, 31), fy_pk=self.fy.pk
            )
        )

    def test_no_overlap_after(self):
        self.assertFalse(
            selectors.has_overlapping_sprint(
                date(2024, 4, 15), date(2024, 4, 28), fy_pk=self.fy.pk
            )
        )

    def test_exclude_pk_allows_self_update(self):
        self.assertFalse(
            selectors.has_overlapping_sprint(
                date(2024, 4, 1),
                date(2024, 4, 14),
                fy_pk=self.fy.pk,
                exclude_pk=self.sprint.pk,
            )
        )

    def test_different_fy_not_considered_overlap(self):
        fy2 = make_financial_year(
            start_date=date(2025, 4, 1), end_date=date(2026, 3, 31)
        )
        self.assertFalse(
            selectors.has_overlapping_sprint(
                date(2024, 4, 1), date(2024, 4, 14), fy_pk=fy2.pk
            )
        )


class GetMaxSprintNumberTest(TestCase):
    def test_returns_zero_when_no_sprints(self):
        self.assertEqual(selectors.get_max_sprint_number(), 0)

    def test_returns_highest_sprint_number(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        make_sprint(
            financial_year=fy,
            sprint_number=5,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        make_sprint(
            financial_year=fy,
            sprint_number=3,
            start_date=date(2024, 4, 15),
            end_date=date(2024, 4, 28),
        )
        self.assertEqual(selectors.get_max_sprint_number(), 5)


class GetCapacityForSprintTest(TestCase):
    def test_returns_capacity_rows_for_sprint(self):
        sprint = make_sprint()
        user = make_user()
        make_capacity(sprint=sprint, member=user)
        qs = selectors.get_capacity_for_sprint(sprint)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().member, user)

    def test_returns_empty_when_no_capacity(self):
        sprint = make_sprint()
        qs = selectors.get_capacity_for_sprint(sprint)
        self.assertEqual(qs.count(), 0)


class GetSprintsOverlappingDateTest(TestCase):
    def test_returns_sprint_containing_date(self):
        sprint = make_sprint(
            start_date=date(2024, 4, 1), end_date=date(2024, 4, 14), is_active=True
        )
        result = selectors.get_sprints_overlapping_date(date(2024, 4, 7))
        self.assertIn(sprint, result)

    def test_excludes_sprint_not_containing_date(self):
        make_sprint(
            start_date=date(2024, 4, 1), end_date=date(2024, 4, 14), is_active=True
        )
        result = selectors.get_sprints_overlapping_date(date(2024, 4, 20))
        self.assertEqual(result.count(), 0)

    def test_excludes_inactive_sprints(self):
        make_sprint(
            start_date=date(2024, 4, 1), end_date=date(2024, 4, 14), is_active=False
        )
        result = selectors.get_sprints_overlapping_date(date(2024, 4, 7))
        self.assertEqual(result.count(), 0)


class GetSprintsOverlappingRangeTest(TestCase):
    def test_returns_sprint_overlapping_range(self):
        sprint = make_sprint(
            start_date=date(2024, 4, 1), end_date=date(2024, 4, 14), is_active=True
        )
        result = selectors.get_sprints_overlapping_range(
            date(2024, 4, 7), date(2024, 4, 20)
        )
        self.assertIn(sprint, result)

    def test_excludes_non_overlapping_sprint(self):
        make_sprint(
            start_date=date(2024, 4, 1), end_date=date(2024, 4, 14), is_active=True
        )
        result = selectors.get_sprints_overlapping_range(
            date(2024, 4, 15), date(2024, 4, 28)
        )
        self.assertEqual(result.count(), 0)


class GetActiveAndFutureSprintsTest(TestCase):
    def test_returns_in_progress_and_future_only(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        make_sprint(
            financial_year=fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
            status=SprintStatus.IN_PROGRESS,
            is_active=True,
        )
        make_sprint(
            financial_year=fy,
            sprint_number=2,
            start_date=date(2024, 4, 15),
            end_date=date(2024, 4, 28),
            status=SprintStatus.FUTURE,
            is_active=True,
        )
        make_sprint(
            financial_year=fy,
            sprint_number=3,
            start_date=date(2024, 4, 29),
            end_date=date(2024, 5, 12),
            status=SprintStatus.COMPLETED,
            is_active=True,
        )
        qs = selectors.get_active_and_future_sprints()
        self.assertEqual(qs.count(), 2)

    def test_excludes_inactive_sprints(self):
        make_sprint(status=SprintStatus.FUTURE, is_active=False)
        qs = selectors.get_active_and_future_sprints()
        self.assertEqual(qs.count(), 0)


# ── SprintDataImport selectors ────────────────────────────────────────────────


class GetImportByCodeTest(TestCase):
    def test_returns_import_for_valid_code(self):
        sprint = make_sprint()
        team = make_team()
        record = _make_import(sprint, team)
        result = get_import_by_code(record.code)
        self.assertIsNotNone(result)
        self.assertEqual(result.pk, record.pk)

    def test_returns_none_for_unknown_code(self):
        result = get_import_by_code("SPTIMP-9999")
        self.assertIsNone(result)


class GetImportsForSprintTeamTest(TestCase):
    def setUp(self):
        self.sprint = make_sprint()
        self.team = make_team()
        self.user = make_user()

    def test_returns_all_imports_for_sprint_and_team(self):
        _make_import(self.sprint, self.team, user=self.user, version_number=1)
        _make_import(self.sprint, self.team, user=self.user, version_number=2)
        qs = get_imports_for_sprint_team(self.sprint.pk, self.team.pk)
        self.assertEqual(qs.count(), 2)

    def test_filters_by_import_type(self):
        _make_import(
            self.sprint,
            self.team,
            user=self.user,
            import_type=SprintDataImportType.FORECAST,
            version_number=1,
        )
        _make_import(
            self.sprint,
            self.team,
            user=self.user,
            import_type=SprintDataImportType.ACTUAL,
            version_number=1,
        )
        qs = get_imports_for_sprint_team(
            self.sprint.pk, self.team.pk, import_type=SprintDataImportType.FORECAST
        )
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().import_type, SprintDataImportType.FORECAST)

    def test_excludes_other_team(self):
        other_team = make_team(name="Other Team")
        _make_import(self.sprint, self.team, user=self.user)
        _make_import(self.sprint, other_team, user=self.user)
        qs = get_imports_for_sprint_team(self.sprint.pk, self.team.pk)
        self.assertEqual(qs.count(), 1)

    def test_returns_empty_when_none(self):
        qs = get_imports_for_sprint_team(self.sprint.pk, self.team.pk)
        self.assertEqual(qs.count(), 0)


class GetRowsForImportTest(TestCase):
    def setUp(self):
        self.sprint = make_sprint()
        self.team = make_team()
        self.record = _make_import(self.sprint, self.team)

    def test_returns_active_rows(self):
        SprintDataImportRow.objects.create(
            import_record=self.record, title="Row 1", is_deleted=False
        )
        SprintDataImportRow.objects.create(
            import_record=self.record, title="Row 2", is_deleted=False
        )
        qs = get_rows_for_import(self.record.pk)
        self.assertEqual(qs.count(), 2)

    def test_excludes_soft_deleted_rows(self):
        SprintDataImportRow.objects.create(
            import_record=self.record, title="Active", is_deleted=False
        )
        SprintDataImportRow.objects.create(
            import_record=self.record, title="Deleted", is_deleted=True
        )
        qs = get_rows_for_import(self.record.pk)
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().title, "Active")

    def test_returns_empty_when_no_rows(self):
        qs = get_rows_for_import(self.record.pk)
        self.assertEqual(qs.count(), 0)


class GetHasReviewForImportTest(TestCase):
    def setUp(self):
        self.sprint = make_sprint()
        self.team = make_team()
        self.user = make_user()
        self.record = _make_import(self.sprint, self.team, user=self.user)

    def test_returns_false_before_review(self):
        self.assertFalse(get_has_review_for_import(self.record.pk))

    def test_returns_true_after_review_created(self):
        SprintDataImportReview.objects.create(
            import_record=self.record,
            reviewed_by=self.user,
        )
        self.assertTrue(get_has_review_for_import(self.record.pk))

    def test_returns_false_for_nonexistent_import(self):
        self.assertFalse(get_has_review_for_import(99999))


class GetLatestActiveImportTest(TestCase):
    def setUp(self):
        self.sprint = make_sprint()
        self.team = make_team()
        self.user = make_user()

    def test_returns_none_when_no_active_import(self):
        result = get_latest_active_import(
            self.sprint.pk, self.team.pk, SprintDataImportType.FORECAST
        )
        self.assertIsNone(result)

    def test_returns_active_import(self):
        record = _make_import(
            self.sprint, self.team, user=self.user, status=SprintDataImportStatus.ACTIVE
        )
        result = get_latest_active_import(
            self.sprint.pk, self.team.pk, SprintDataImportType.FORECAST
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.pk, record.pk)

    def test_returns_none_when_only_superseded(self):
        _make_import(
            self.sprint,
            self.team,
            user=self.user,
            status=SprintDataImportStatus.SUPERSEDED,
        )
        result = get_latest_active_import(
            self.sprint.pk, self.team.pk, SprintDataImportType.FORECAST
        )
        self.assertIsNone(result)

    def test_filters_by_import_type(self):
        _make_import(
            self.sprint,
            self.team,
            user=self.user,
            import_type=SprintDataImportType.ACTUAL,
        )
        result = get_latest_active_import(
            self.sprint.pk, self.team.pk, SprintDataImportType.FORECAST
        )
        self.assertIsNone(result)
