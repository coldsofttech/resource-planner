from django.test import TestCase

from apps.configurations.tests.factories import mark_setup_complete
from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.projects.tests.factories import make_project_type
from apps.recharges.constants import RechargeType as RechargeTypeChoice
from apps.recharges.models import (
    ProjectTypeMapping,
    Recharge,
    RechargeDetail,
    RechargeType,
)
from apps.recharges.services import (
    ProjectTypeMappingImportService,
    ProjectTypeMappingService,
    RechargeDetailService,
    RechargeTypeImportService,
    RechargeTypeService,
)
from apps.recharges.tests.factories import (
    FakeCsvFile,
    make_project_type_mapping,
    make_recharge_type,
)
from apps.sprints.constants import SprintDataImportStatus, SprintDataImportType
from apps.sprints.models import SprintDataImport
from apps.sprints.services.sprint_data_import import SprintDataImportForecastService
from apps.sprints.tests.factories import make_sprint
from apps.teams.tests.factories import make_team
from apps.users.tests.factories import make_user


def _make_import(sprint, team, user=None):
    if user is None:
        user = make_user()
    return SprintDataImport.objects.create(
        sprint=sprint,
        team=team,
        version_number=1,
        file_name="test.csv",
        status=SprintDataImportStatus.ACTIVE,
        import_type=SprintDataImportType.FORECAST,
        created_by=user,
        updated_by=user,
    )


CSV_HEADER = "Story Type,Jira ID,Title,Assignee,Efforts,Sprint,Label,Mapping\n"
CSV_ROW = (
    "Story,JIRA-1,Test Title,user@example.com,3600,Sprint 1,sample-label,PROJECT\n"
)


def _make_valid_csv(rows: int = 1) -> FakeCsvFile:
    content = CSV_HEADER + (CSV_ROW * rows)
    return FakeCsvFile(content, name="forecast.csv")


def _svc(user=None):
    if user is None:
        user = make_user()
    return RechargeTypeService(user=user)


def _mapping_svc(recharge_type_code: str, user=None):
    if user is None:
        user = make_user()
    return ProjectTypeMappingService(user=user, recharge_type_code=recharge_type_code)


# ── RechargeTypeService.get ───────────────────────────────────────────────────


class RechargeTypeServiceGetTest(TestCase):
    def test_returns_recharge_type_by_code(self):
        rt = make_recharge_type("BAU")
        result = _svc().get(code=rt.code)
        self.assertEqual(result.pk, rt.pk)

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            _svc().get(code="RECHTY-999999")


# ── RechargeTypeService.list ──────────────────────────────────────────────────


class RechargeTypeServiceListTest(TestCase):
    def setUp(self):
        make_recharge_type("BAU", is_active=True)
        make_recharge_type("PROJECT", is_active=True)
        make_recharge_type("HOLIDAY", is_active=False)

    def test_returns_paginated_result(self):
        result = _svc().list()
        self.assertIsNotNone(result.pagination)

    def test_defaults_to_active_only(self):
        result = _svc().list()
        names = [r.name for r in result.results]
        self.assertIn("BAU", names)
        self.assertNotIn("HOLIDAY", names)

    def test_is_active_false_returns_inactive(self):
        from apps.core.types import ListParams

        result = _svc().list(ListParams(filters={"is_active": "false"}))
        names = [r.name for r in result.results]
        self.assertIn("HOLIDAY", names)
        self.assertNotIn("BAU", names)

    def test_search_by_name(self):
        from apps.core.types import ListParams

        result = _svc().list(ListParams(search="BAU"))
        self.assertEqual(len(result.results), 1)
        self.assertEqual(result.results[0].name, "BAU")


# ── RechargeTypeService.create ────────────────────────────────────────────────


class RechargeTypeServiceCreateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = _svc(self.user)

    def test_creates_recharge_type(self):
        rt = self.svc.create(name="BAU")
        self.assertIsNotNone(rt.pk)
        self.assertEqual(rt.name, "BAU")

    def test_assigns_code(self):
        rt = self.svc.create(name="BAU")
        self.assertTrue(rt.code.startswith("RECHTY-"))

    def test_sets_created_by(self):
        rt = self.svc.create(name="BAU")
        self.assertEqual(rt.created_by, self.user)

    def test_description_defaults_to_empty(self):
        rt = self.svc.create(name="BAU")
        self.assertEqual(rt.description, "")

    def test_is_active_defaults_to_true(self):
        rt = self.svc.create(name="BAU")
        self.assertTrue(rt.is_active)

    def test_stores_description(self):
        rt = self.svc.create(name="BAU", description="Business as usual")
        self.assertEqual(rt.description, "Business as usual")

    def test_raises_already_exists_on_duplicate_name(self):
        make_recharge_type("BAU")
        with self.assertRaises(AlreadyExistsException):
            self.svc.create(name="BAU")


# ── RechargeTypeService.update ────────────────────────────────────────────────


class RechargeTypeServiceUpdateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = _svc(self.user)
        self.rt = make_recharge_type("BAU")

    def test_updates_name(self):
        updated = self.svc.update(code=self.rt.code, name="PROJECT")
        self.assertEqual(updated.name, "PROJECT")

    def test_updates_description(self):
        updated = self.svc.update(code=self.rt.code, description="Updated")
        self.assertEqual(updated.description, "Updated")

    def test_updates_is_active(self):
        updated = self.svc.update(code=self.rt.code, is_active=False)
        self.assertFalse(updated.is_active)

    def test_same_name_update_is_idempotent(self):
        updated = self.svc.update(code=self.rt.code, name="BAU")
        self.assertEqual(updated.name, "BAU")

    def test_raises_already_exists_on_name_conflict(self):
        make_recharge_type("PROJECT")
        with self.assertRaises(AlreadyExistsException):
            self.svc.update(code=self.rt.code, name="PROJECT")

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.update(code="RECHTY-999999", name="NEW")

    def test_sets_updated_by(self):
        updated = self.svc.update(code=self.rt.code, name="PROJECT")
        self.assertEqual(updated.updated_by, self.user)


# ── RechargeTypeService.activate / deactivate ────────────────────────────────


class RechargeTypeServiceActivateDeactivateTest(TestCase):
    def setUp(self):
        self.svc = _svc()

    def test_activate_sets_is_active(self):
        rt = make_recharge_type("BAU", is_active=False)
        result = self.svc.activate(code=rt.code)
        self.assertTrue(result.is_active)

    def test_deactivate_clears_is_active(self):
        rt = make_recharge_type("BAU", is_active=True)
        result = self.svc.deactivate(code=rt.code)
        self.assertFalse(result.is_active)

    def test_activate_already_active_is_noop(self):
        rt = make_recharge_type("BAU", is_active=True)
        result = self.svc.activate(code=rt.code)
        self.assertTrue(result.is_active)

    def test_deactivate_already_inactive_is_noop(self):
        rt = make_recharge_type("BAU", is_active=False)
        result = self.svc.deactivate(code=rt.code)
        self.assertFalse(result.is_active)

    def test_activate_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.activate(code="RECHTY-999999")

    def test_deactivate_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.deactivate(code="RECHTY-999999")


# ── RechargeTypeService.delete ────────────────────────────────────────────────


class RechargeTypeServiceDeleteTest(TestCase):
    def setUp(self):
        self.svc = _svc()

    def test_deletes_recharge_type(self):
        rt = make_recharge_type("BAU")
        code = rt.code
        self.svc.delete(code=code)
        self.assertFalse(RechargeType.objects.filter(code=code).exists())

    def test_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            self.svc.delete(code="RECHTY-999999")


# ── RechargeTypeService.options ───────────────────────────────────────────────


class RechargeTypeServiceOptionsTest(TestCase):
    def test_returns_active_options(self):
        make_recharge_type("BAU", is_active=True)
        make_recharge_type("PROJECT", is_active=False)
        result = _svc().options()
        names = [o["name"] for o in result]
        self.assertIn("BAU", names)
        self.assertNotIn("PROJECT", names)

    def test_result_contains_code_and_name(self):
        make_recharge_type("BAU")
        result = _svc().options()
        self.assertIn("code", result[0])
        self.assertIn("name", result[0])


# ── RechargeTypeService.stats ─────────────────────────────────────────────────


class RechargeTypeServiceStatsTest(TestCase):
    def test_returns_correct_totals(self):
        make_recharge_type("BAU", is_active=True)
        make_recharge_type("PROJECT", is_active=False)
        stats = _svc().stats()
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["active"], 1)
        self.assertEqual(stats["inactive"], 1)

    def test_fields_filter_returned_keys(self):
        make_recharge_type("BAU")
        stats = _svc().stats(fields=["total"])
        self.assertIn("total", stats)
        self.assertNotIn("active", stats)


# ── RechargeTypeImportService ────────────────────────────────────────────────


class RechargeTypeImportServiceTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = RechargeTypeImportService(user=self.user)

    def _make_csv(self, rows: list[str]) -> FakeCsvFile:
        content = "name\n" + "\n".join(rows)
        return FakeCsvFile(content, "recharges.csv")

    def test_imports_valid_row(self):
        f = self._make_csv(["BAU"])
        result = self.svc.bulk_import(f)
        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["errors"]), 0)
        self.assertTrue(RechargeType.objects.filter(name="BAU").exists())

    def test_dry_run_does_not_create_record(self):
        f = self._make_csv(["BAU"])
        result = self.svc.bulk_import(f, dry_run=True)
        self.assertTrue(result["dry_run"])
        self.assertFalse(RechargeType.objects.filter(name="BAU").exists())

    def test_missing_name_produces_error(self):
        f = self._make_csv([" "])
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["field"], "name")

    def test_invalid_name_format_produces_error(self):
        f = self._make_csv(["lowercase"])
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["field"], "name")

    def test_duplicate_name_skips_row_with_error(self):
        make_recharge_type("BAU")
        f = self._make_csv(["BAU"])
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)

    def test_missing_required_column_raises_validation_error(self):
        f = FakeCsvFile("description\nSome desc", "bad.csv")
        with self.assertRaises(ValidationException):
            self.svc.bulk_import(f)

    def test_name_exceeding_50_chars_produces_error(self):
        f = self._make_csv(["A" * 51])
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)


# ── ProjectTypeMappingService.get ─────────────────────────────────────────────


class ProjectTypeMappingServiceGetTest(TestCase):
    def test_returns_mapping_by_pk(self):
        rt = make_recharge_type("BAU")
        pt = make_project_type("Internal")
        mapping = make_project_type_mapping(rt, pt)
        result = _mapping_svc(rt.code).get(pk=mapping.pk)
        self.assertEqual(result.pk, mapping.pk)

    def test_raises_not_found_for_unknown_pk(self):
        rt = make_recharge_type("BAU")
        with self.assertRaises(NotFoundException):
            _mapping_svc(rt.code).get(pk=999999)

    def test_raises_not_found_when_recharge_type_code_mismatch(self):
        rt1 = make_recharge_type("BAU")
        rt2 = make_recharge_type("PROJECT")
        pt = make_project_type("Internal")
        mapping = make_project_type_mapping(rt1, pt)
        with self.assertRaises(NotFoundException):
            _mapping_svc(rt2.code).get(pk=mapping.pk)


# ── ProjectTypeMappingService.list ────────────────────────────────────────────


class ProjectTypeMappingServiceListTest(TestCase):
    def test_returns_mappings_for_recharge_type(self):
        rt = make_recharge_type("BAU")
        pt1 = make_project_type("Internal")
        pt2 = make_project_type("External")
        make_project_type_mapping(rt, pt1)
        make_project_type_mapping(rt, pt2)
        result = _mapping_svc(rt.code).list()
        self.assertEqual(result.pagination.total_count, 2)

    def test_excludes_mappings_from_other_recharge_types(self):
        rt1 = make_recharge_type("BAU")
        rt2 = make_recharge_type("PROJECT")
        pt = make_project_type("Shared")
        make_project_type_mapping(rt1, pt)
        result = _mapping_svc(rt2.code).list()
        self.assertEqual(result.pagination.total_count, 0)


# ── ProjectTypeMappingService.create ─────────────────────────────────────────


class ProjectTypeMappingServiceCreateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.rt = make_recharge_type("BAU")
        self.pt = make_project_type("Internal")
        self.svc = _mapping_svc(self.rt.code, self.user)

    def test_creates_mapping(self):
        mapping = self.svc.create(project_type_code=self.pt.code)
        self.assertIsNotNone(mapping.pk)
        self.assertEqual(mapping.project_type, self.pt)
        self.assertEqual(mapping.recharge_type, self.rt)

    def test_sets_created_by(self):
        mapping = self.svc.create(project_type_code=self.pt.code)
        self.assertEqual(mapping.created_by, self.user)

    def test_raises_already_exists_for_duplicate(self):
        make_project_type_mapping(self.rt, self.pt)
        with self.assertRaises(AlreadyExistsException):
            self.svc.create(project_type_code=self.pt.code)

    def test_raises_validation_error_for_unknown_project_type(self):
        with self.assertRaises(ValidationException):
            self.svc.create(project_type_code="PROJTYPE-999999")

    def test_raises_not_found_when_recharge_type_invalid(self):
        svc = _mapping_svc("RECHTY-999999", self.user)
        with self.assertRaises(NotFoundException):
            svc.create(project_type_code=self.pt.code)


# ── ProjectTypeMappingService.update ─────────────────────────────────────────


class ProjectTypeMappingServiceUpdateTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.rt = make_recharge_type("BAU")
        self.pt_a = make_project_type("Type A")
        self.pt_b = make_project_type("Type B")
        self.mapping = make_project_type_mapping(self.rt, self.pt_a)
        self.svc = _mapping_svc(self.rt.code, self.user)

    def test_updates_project_type(self):
        updated = self.svc.update(pk=self.mapping.pk, project_type_code=self.pt_b.code)
        self.assertEqual(updated.project_type, self.pt_b)

    def test_raises_already_exists_on_duplicate(self):
        make_project_type_mapping(self.rt, self.pt_b)
        with self.assertRaises(AlreadyExistsException):
            self.svc.update(pk=self.mapping.pk, project_type_code=self.pt_b.code)

    def test_raises_not_found_for_unknown_pk(self):
        with self.assertRaises(NotFoundException):
            self.svc.update(pk=999999, project_type_code=self.pt_b.code)

    def test_raises_validation_error_for_unknown_project_type(self):
        with self.assertRaises(ValidationException):
            self.svc.update(pk=self.mapping.pk, project_type_code="PROJTYPE-999999")


# ── ProjectTypeMappingService.delete ─────────────────────────────────────────


class ProjectTypeMappingServiceDeleteTest(TestCase):
    def setUp(self):
        self.rt = make_recharge_type("BAU")
        self.pt = make_project_type("Internal")
        self.mapping = make_project_type_mapping(self.rt, self.pt)
        self.svc = _mapping_svc(self.rt.code)

    def test_deletes_mapping(self):
        pk = self.mapping.pk
        self.svc.delete(pk=pk)
        self.assertFalse(ProjectTypeMapping.objects.filter(pk=pk).exists())

    def test_raises_not_found_for_unknown_pk(self):
        with self.assertRaises(NotFoundException):
            self.svc.delete(pk=999999)


# ── ProjectTypeMappingImportService ──────────────────────────────────────────


class ProjectTypeMappingImportServiceTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.rt = make_recharge_type("BAU")
        self.pt = make_project_type("Internal")
        self.svc = ProjectTypeMappingImportService(
            user=self.user, recharge_type_code=self.rt.code
        )

    def _make_csv(self, rows: list[str]) -> FakeCsvFile:
        content = "project_type_code\n" + "\n".join(rows)
        return FakeCsvFile(content, "mappings.csv")

    def test_imports_valid_row(self):
        f = self._make_csv([self.pt.code])
        result = self.svc.bulk_import(f)
        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["errors"]), 0)
        self.assertTrue(
            ProjectTypeMapping.objects.filter(
                recharge_type=self.rt, project_type=self.pt
            ).exists()
        )

    def test_dry_run_does_not_create_mapping(self):
        f = self._make_csv([self.pt.code])
        result = self.svc.bulk_import(f, dry_run=True)
        self.assertTrue(result["dry_run"])
        self.assertFalse(
            ProjectTypeMapping.objects.filter(
                recharge_type=self.rt, project_type=self.pt
            ).exists()
        )

    def test_missing_project_type_code_produces_error(self):
        f = self._make_csv([" "])
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["field"], "project_type_code")

    def test_unknown_project_type_code_produces_error(self):
        f = self._make_csv(["PROJTYPE-999999"])
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)

    def test_duplicate_mapping_skips_row_with_error(self):
        make_project_type_mapping(self.rt, self.pt)
        f = self._make_csv([self.pt.code])
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)

    def test_missing_required_column_raises_validation_error(self):
        f = FakeCsvFile("name\nInternal", "bad.csv")
        with self.assertRaises(ValidationException):
            self.svc.bulk_import(f)

    def test_invalid_recharge_type_code_raises_validation_error(self):
        svc = ProjectTypeMappingImportService(
            user=self.user, recharge_type_code="RECHTY-999999"
        )
        f = self._make_csv([self.pt.code])
        with self.assertRaises(ValidationException):
            svc.bulk_import(f)


# ── RechargeDetailService.populate_from_sprint_forecast ──────────────────────


def _confirm_forecast(sprint, team, user):
    """Upload, review, and confirm a forecast import for a sprint/team."""
    svc = SprintDataImportForecastService(user=user)
    import_record = svc.upload(
        sprint_code=sprint.code,
        team_code=team.code,
        file=_make_valid_csv(),
    )
    svc.review(import_code=import_record.code)
    svc.confirm(import_code=import_record.code, notes="override")
    return import_record


class RechargeDetailServicePopulateForecastTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.user = make_user()
        self.sprint = make_sprint()
        self.team = make_team()
        self.svc = RechargeDetailService(user=self.user)

    def test_returns_zero_when_no_confirmed_imports(self):
        count = self.svc.populate_from_sprint_forecast(self.sprint.id)
        self.assertEqual(count, 0)

    def test_creates_no_recharge_details_when_no_confirmed_imports(self):
        self.svc.populate_from_sprint_forecast(self.sprint.id)
        self.assertEqual(
            RechargeDetail.objects.filter(
                sprint=self.sprint, type=RechargeTypeChoice.FORECAST
            ).count(),
            0,
        )

    def test_returns_count_of_created_details(self):
        _confirm_forecast(self.sprint, self.team, self.user)
        count = self.svc.populate_from_sprint_forecast(self.sprint.id)
        self.assertGreater(count, 0)

    def test_creates_recharge_detail_records(self):
        _confirm_forecast(self.sprint, self.team, self.user)
        self.svc.populate_from_sprint_forecast(self.sprint.id)
        self.assertTrue(
            RechargeDetail.objects.filter(
                sprint=self.sprint, type=RechargeTypeChoice.FORECAST
            ).exists()
        )

    def test_type_is_forecast_on_created_details(self):
        _confirm_forecast(self.sprint, self.team, self.user)
        self.svc.populate_from_sprint_forecast(self.sprint.id)
        types = list(
            RechargeDetail.objects.filter(sprint=self.sprint).values_list(
                "type", flat=True
            )
        )
        self.assertTrue(all(t == RechargeTypeChoice.FORECAST for t in types))

    def test_team_is_set_on_created_details(self):
        _confirm_forecast(self.sprint, self.team, self.user)
        self.svc.populate_from_sprint_forecast(self.sprint.id)
        detail = RechargeDetail.objects.filter(sprint=self.sprint).first()
        self.assertIsNotNone(detail)
        self.assertEqual(detail.team, self.team)

    def test_deletes_existing_forecast_details_before_recreating(self):
        _confirm_forecast(self.sprint, self.team, self.user)
        self.svc.populate_from_sprint_forecast(self.sprint.id)
        count_first = RechargeDetail.objects.filter(
            sprint=self.sprint, type=RechargeTypeChoice.FORECAST
        ).count()

        self.svc.populate_from_sprint_forecast(self.sprint.id)
        count_second = RechargeDetail.objects.filter(
            sprint=self.sprint, type=RechargeTypeChoice.FORECAST
        ).count()

        self.assertEqual(count_first, count_second)

    def test_does_not_delete_actuals_details(self):
        import_record = _make_import(self.sprint, self.team, self.user)
        RechargeDetail.objects.create(
            sprint=self.sprint,
            team=self.team,
            import_record=import_record,
            type=RechargeTypeChoice.ACTUAL,
        )
        self.svc.populate_from_sprint_forecast(self.sprint.id)
        self.assertTrue(
            RechargeDetail.objects.filter(
                sprint=self.sprint, type=RechargeTypeChoice.ACTUAL
            ).exists()
        )

    def test_creates_recharge_aggregate_records(self):
        _confirm_forecast(self.sprint, self.team, self.user)
        self.svc.populate_from_sprint_forecast(self.sprint.id)
        self.assertTrue(
            Recharge.objects.filter(
                sprint=self.sprint, type=RechargeTypeChoice.FORECAST
            ).exists()
        )

    def test_syncs_recharges_even_when_no_confirmed_imports(self):
        Recharge.objects.create(sprint=self.sprint, type=RechargeTypeChoice.FORECAST)
        self.svc.populate_from_sprint_forecast(self.sprint.id)
        self.assertFalse(
            Recharge.objects.filter(
                sprint=self.sprint, type=RechargeTypeChoice.FORECAST
            ).exists()
        )


# ── RechargeDetailService.populate_from_sprint_actuals ───────────────────────


class RechargeDetailServicePopulateActualsTest(TestCase):
    def setUp(self):
        mark_setup_complete()
        self.user = make_user()
        self.sprint = make_sprint()
        self.team = make_team()
        self.svc = RechargeDetailService(user=self.user)

    def test_returns_zero_when_no_confirmed_actuals(self):
        count = self.svc.populate_from_sprint_actuals(self.sprint.id)
        self.assertEqual(count, 0)

    def test_creates_no_recharge_details_when_no_confirmed_actuals(self):
        self.svc.populate_from_sprint_actuals(self.sprint.id)
        self.assertEqual(
            RechargeDetail.objects.filter(
                sprint=self.sprint, type=RechargeTypeChoice.ACTUAL
            ).count(),
            0,
        )

    def test_does_not_delete_forecast_details(self):
        import_record = _make_import(self.sprint, self.team, self.user)
        RechargeDetail.objects.create(
            sprint=self.sprint,
            team=self.team,
            import_record=import_record,
            type=RechargeTypeChoice.FORECAST,
        )
        self.svc.populate_from_sprint_actuals(self.sprint.id)
        self.assertTrue(
            RechargeDetail.objects.filter(
                sprint=self.sprint, type=RechargeTypeChoice.FORECAST
            ).exists()
        )
