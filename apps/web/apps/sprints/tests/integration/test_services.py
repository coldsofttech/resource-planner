from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.core.exceptions import NotFoundException, ValidationException
from apps.financial_years.tests.factories import make_financial_year
from apps.sprints.constants import SprintStatus
from apps.sprints.engine import SprintCapacityEngine
from apps.sprints.models import Capacity, Sprint
from apps.sprints.services import SprintImportService, SprintService
from apps.sprints.tests.factories import FakeCsvFile, make_sprint
from apps.users.tests.factories import make_profile, make_user


def _svc(user=None):
    return SprintService(user=user or make_user())


# ── SprintService.get ─────────────────────────────────────────────────────────


class SprintServiceGetTest(TestCase):
    def test_get_by_code_returns_sprint(self):
        sprint = make_sprint()
        result = _svc().get(code=sprint.code)
        self.assertEqual(result.pk, sprint.pk)

    def test_get_unknown_code_raises_not_found(self):
        with self.assertRaises(NotFoundException):
            _svc().get(code="SPRINT-9999")


# ── SprintService.get_active ──────────────────────────────────────────────────


class SprintServiceGetActiveTest(TestCase):
    def test_returns_in_progress_sprint(self):
        sprint = make_sprint(status=SprintStatus.IN_PROGRESS, is_active=True)
        result = _svc().get_active()
        self.assertEqual(result.pk, sprint.pk)

    def test_raises_not_found_when_no_in_progress(self):
        make_sprint(status=SprintStatus.FUTURE)
        with self.assertRaises(NotFoundException):
            _svc().get_active()


# ── SprintService.create ──────────────────────────────────────────────────────


class SprintServiceCreateTest(TestCase):
    def setUp(self):
        self.fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        self.user = make_user()

    def test_create_returns_sprint_instance(self):
        svc = SprintService(user=self.user)
        sprint = svc.create(
            fy_code=self.fy.code,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        self.assertIsNotNone(sprint.pk)
        self.assertEqual(sprint.sprint_number, 1)

    def test_create_sets_created_by(self):
        svc = SprintService(user=self.user)
        sprint = svc.create(
            fy_code=self.fy.code,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        self.assertEqual(sprint.created_by, self.user)

    def test_create_auto_generates_name_from_sprint_number(self):
        svc = SprintService(user=self.user)
        sprint = svc.create(
            fy_code=self.fy.code,
            sprint_number=5,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        self.assertIn("5", sprint.name)

    def test_create_uses_provided_name(self):
        svc = SprintService(user=self.user)
        sprint = svc.create(
            fy_code=self.fy.code,
            sprint_number=1,
            name="My Sprint",
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        self.assertEqual(sprint.name, "My Sprint")

    def test_create_raises_not_found_for_unknown_fy(self):
        with self.assertRaises(NotFoundException):
            SprintService(user=self.user).create(
                fy_code="FY-9999",
                sprint_number=1,
                start_date=date(2024, 4, 1),
                end_date=date(2024, 4, 14),
            )

    def test_create_raises_validation_for_end_before_start(self):
        with self.assertRaises(ValidationException):
            SprintService(user=self.user).create(
                fy_code=self.fy.code,
                sprint_number=1,
                start_date=date(2024, 4, 14),
                end_date=date(2024, 4, 1),
            )

    def test_create_raises_validation_when_dates_outside_fy(self):
        with self.assertRaises(ValidationException):
            SprintService(user=self.user).create(
                fy_code=self.fy.code,
                sprint_number=1,
                start_date=date(2025, 4, 1),
                end_date=date(2025, 4, 14),
            )

    def test_create_raises_validation_for_overlapping_sprint(self):
        svc = SprintService(user=self.user)
        svc.create(
            fy_code=self.fy.code,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        with self.assertRaises(ValidationException):
            svc.create(
                fy_code=self.fy.code,
                sprint_number=2,
                start_date=date(2024, 4, 7),
                end_date=date(2024, 4, 21),
            )

    def test_create_in_progress_retires_existing_in_progress(self):
        existing = make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
            status=SprintStatus.IN_PROGRESS,
        )
        svc = SprintService(user=self.user)
        svc.create(
            fy_code=self.fy.code,
            sprint_number=2,
            start_date=date(2024, 4, 15),
            end_date=date(2024, 4, 28),
            status=SprintStatus.IN_PROGRESS,
        )
        existing.refresh_from_db()
        self.assertEqual(existing.status, SprintStatus.COMPLETED)


# ── SprintService.update ──────────────────────────────────────────────────────


class SprintServiceUpdateTest(TestCase):
    def setUp(self):
        self.fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        self.user = make_user()
        self.sprint = make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )

    def test_update_name(self):
        result = SprintService(user=self.user).update(
            code=self.sprint.code, name="Updated Name"
        )
        self.assertEqual(result.name, "Updated Name")

    def test_update_sets_is_overridden(self):
        result = SprintService(user=self.user).update(
            code=self.sprint.code, name="Any Name"
        )
        self.assertTrue(result.is_overridden)

    def test_update_note(self):
        result = SprintService(user=self.user).update(
            code=self.sprint.code, note="A note"
        )
        self.assertEqual(result.note, "A note")

    def test_update_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            SprintService(user=self.user).update(code="SPRINT-9999", name="X")

    def test_update_raises_validation_for_overlapping_dates(self):
        fy = self.fy
        make_sprint(
            financial_year=fy,
            sprint_number=2,
            start_date=date(2024, 4, 15),
            end_date=date(2024, 4, 28),
        )
        with self.assertRaises(ValidationException):
            SprintService(user=self.user).update(
                code=self.sprint.code,
                start_date=date(2024, 4, 10),
                end_date=date(2024, 4, 20),
            )

    def test_update_status_to_in_progress_retires_current(self):
        other = make_sprint(
            financial_year=self.fy,
            sprint_number=2,
            start_date=date(2024, 4, 15),
            end_date=date(2024, 4, 28),
            status=SprintStatus.IN_PROGRESS,
        )
        SprintService(user=self.user).update(
            code=self.sprint.code, status=SprintStatus.IN_PROGRESS
        )
        other.refresh_from_db()
        self.assertEqual(other.status, SprintStatus.COMPLETED)


# ── SprintService.activate / deactivate ──────────────────────────────────────


class SprintServiceActivateDeactivateTest(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_activate_sets_is_active(self):
        sprint = make_sprint(is_active=False)
        result = SprintService(user=self.user).activate(code=sprint.code)
        self.assertTrue(result.is_active)

    def test_activate_is_idempotent(self):
        sprint = make_sprint(is_active=True)
        result = SprintService(user=self.user).activate(code=sprint.code)
        self.assertTrue(result.is_active)

    def test_deactivate_clears_is_active(self):
        sprint = make_sprint(is_active=True)
        result = SprintService(user=self.user).deactivate(code=sprint.code)
        self.assertFalse(result.is_active)

    def test_deactivate_is_idempotent(self):
        sprint = make_sprint(is_active=False)
        result = SprintService(user=self.user).deactivate(code=sprint.code)
        self.assertFalse(result.is_active)

    def test_activate_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            SprintService(user=self.user).activate(code="SPRINT-9999")

    def test_deactivate_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            SprintService(user=self.user).deactivate(code="SPRINT-9999")


# ── SprintService.set_active ──────────────────────────────────────────────────


class SprintServiceSetActiveTest(TestCase):
    def setUp(self):
        self.fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        self.user = make_user()

    def test_set_active_changes_status_to_in_progress(self):
        sprint = make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
            status=SprintStatus.FUTURE,
        )
        result = SprintService(user=self.user).set_active(code=sprint.code)
        self.assertEqual(result.status, SprintStatus.IN_PROGRESS)

    def test_set_active_retires_previous_in_progress(self):
        old = make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
            status=SprintStatus.IN_PROGRESS,
        )
        new = make_sprint(
            financial_year=self.fy,
            sprint_number=2,
            start_date=date(2024, 4, 15),
            end_date=date(2024, 4, 28),
            status=SprintStatus.FUTURE,
        )
        SprintService(user=self.user).set_active(code=new.code)
        old.refresh_from_db()
        new.refresh_from_db()
        self.assertEqual(old.status, SprintStatus.COMPLETED)
        self.assertEqual(new.status, SprintStatus.IN_PROGRESS)

    def test_set_active_idempotent_when_already_in_progress(self):
        sprint = make_sprint(status=SprintStatus.IN_PROGRESS)
        result = SprintService(user=self.user).set_active(code=sprint.code)
        self.assertEqual(result.status, SprintStatus.IN_PROGRESS)

    def test_set_active_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            SprintService(user=self.user).set_active(code="SPRINT-9999")


# ── SprintService.close ───────────────────────────────────────────────────────


class SprintServiceCloseTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.sprint = make_sprint()

    def test_close_sets_is_closed(self):
        result = SprintService(user=self.user).close(code=self.sprint.code, lock=True)
        self.assertTrue(result.is_closed)

    def test_close_sets_closed_on(self):
        result = SprintService(user=self.user).close(code=self.sprint.code, lock=True)
        self.assertIsNotNone(result.closed_on)

    def test_close_sets_closed_by(self):
        result = SprintService(user=self.user).close(code=self.sprint.code, lock=True)
        self.assertEqual(result.closed_by, self.user)

    def test_unlock_clears_is_closed(self):
        SprintService(user=self.user).close(code=self.sprint.code, lock=True)
        result = SprintService(user=self.user).close(code=self.sprint.code, lock=False)
        self.assertFalse(result.is_closed)
        self.assertIsNone(result.closed_on)
        self.assertIsNone(result.closed_by)

    def test_close_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            SprintService(user=self.user).close(code="SPRINT-9999")


# ── SprintService.delete ──────────────────────────────────────────────────────


class SprintServiceDeleteTest(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_delete_removes_sprint(self):
        sprint = make_sprint()
        SprintService(user=self.user).delete(code=sprint.code)
        self.assertFalse(Sprint.objects.filter(pk=sprint.pk).exists())

    def test_delete_raises_not_found_for_unknown_code(self):
        with self.assertRaises(NotFoundException):
            SprintService(user=self.user).delete(code="SPRINT-9999")


# ── SprintService.options ─────────────────────────────────────────────────────


class SprintServiceOptionsTest(TestCase):
    def test_returns_list_of_dicts(self):
        make_sprint()
        result = _svc().options()
        self.assertIsInstance(result, list)
        self.assertGreater(len(result), 0)

    def test_each_entry_has_required_keys(self):
        make_sprint()
        result = _svc().options()
        for entry in result:
            for key in (
                "code",
                "sprint_number",
                "name",
                "start_date",
                "end_date",
                "month",
                "status",
            ):
                self.assertIn(key, entry)

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
        result = _svc().options(fy_code=fy1.code)
        self.assertEqual(len(result), 1)


# ── SprintService.stats ───────────────────────────────────────────────────────


class SprintServiceStatsTest(TestCase):
    def test_returns_dict_with_all_stat_keys(self):
        stats = _svc().stats()
        for key in ("total", "active", "inactive", "in_progress", "future"):
            self.assertIn(key, stats)

    def test_returns_only_requested_fields(self):
        make_sprint(status=SprintStatus.IN_PROGRESS)
        stats = _svc().stats(fields=["total", "in_progress"])
        self.assertIn("total", stats)
        self.assertIn("in_progress", stats)
        self.assertNotIn("future", stats)


# ── SprintService.generate ────────────────────────────────────────────────────


class SprintServiceGenerateTest(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_generate_raises_not_found_for_unknown_fy(self):
        with self.assertRaises(NotFoundException):
            SprintService(user=self.user).generate(fy_code="FY-9999")

    def test_generate_raises_validation_when_sprints_exist(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        make_sprint(
            financial_year=fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        with self.assertRaises(ValidationException):
            SprintService(user=self.user).generate(fy_code=fy.code)

    def test_generate_creates_sprints_for_fy(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2024, 4, 28)
        )
        created = SprintService(user=self.user).generate(fy_code=fy.code)
        self.assertGreater(len(created), 0)
        for sprint in created:
            self.assertEqual(sprint.financial_year, fy)

    def test_generate_persists_sprints_to_db(self):
        fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2024, 4, 28)
        )
        created = SprintService(user=self.user).generate(fy_code=fy.code)
        self.assertEqual(Sprint.objects.filter(financial_year=fy).count(), len(created))

    def test_generate_uses_sequential_sprint_numbers(self):
        existing_fy = make_financial_year(
            start_date=date(2023, 4, 1), end_date=date(2024, 3, 31)
        )
        make_sprint(
            financial_year=existing_fy,
            sprint_number=10,
            start_date=date(2023, 4, 1),
            end_date=date(2023, 4, 14),
        )
        new_fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2024, 4, 28)
        )
        created = SprintService(user=self.user).generate(fy_code=new_fy.code)
        self.assertEqual(created[0].sprint_number, 11)


# ── SprintCapacityEngine.compute_working_days ─────────────────────────────────


class SprintCapacityEngineWorkingDaysTest(TestCase):
    def test_full_week_mon_to_fri(self):
        result = SprintCapacityEngine.compute_working_days(
            date(2024, 4, 1), date(2024, 4, 5)
        )
        self.assertEqual(result, Decimal(5))

    def test_excludes_weekend_days(self):
        result = SprintCapacityEngine.compute_working_days(
            date(2024, 4, 1), date(2024, 4, 7)
        )
        self.assertEqual(result, Decimal(5))

    def test_single_weekday(self):
        result = SprintCapacityEngine.compute_working_days(
            date(2024, 4, 1), date(2024, 4, 1)
        )
        self.assertEqual(result, Decimal(1))

    def test_single_weekend_day_returns_zero(self):
        result = SprintCapacityEngine.compute_working_days(
            date(2024, 4, 6), date(2024, 4, 6)
        )
        self.assertEqual(result, Decimal(0))

    def test_two_full_weeks(self):
        result = SprintCapacityEngine.compute_working_days(
            date(2024, 4, 1), date(2024, 4, 14)
        )
        self.assertEqual(result, Decimal(10))


# ── SprintImportService ───────────────────────────────────────────────────────


class SprintImportServiceValidateFileTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.svc = SprintImportService(user=self.user)

    def test_raises_for_unsupported_extension(self):
        f = FakeCsvFile("content", name="sprints.xlsx")
        with self.assertRaises(ValidationException):
            self.svc.validate_file(f)

    def test_passes_for_csv_extension(self):
        f = FakeCsvFile("content", name="sprints.csv")
        self.svc.validate_file(f)

    def test_raises_for_oversized_file(self):
        large_content = "x" * (6 * 1024 * 1024)
        f = FakeCsvFile(large_content, name="sprints.csv")
        with self.assertRaises(ValidationException):
            self.svc.validate_file(f)


class SprintImportServiceValidateRowTest(TestCase):
    def setUp(self):
        self.svc = SprintImportService(user=make_user())

    def test_valid_row_returns_no_errors(self):
        row = {
            "fy_code": "FY-1",
            "sprint_number": "1",
            "start_date": "2024-04-01",
            "end_date": "2024-04-14",
        }
        errors = self.svc.validate_row(row, 2)
        self.assertEqual(errors, [])

    def test_missing_fy_code_returns_error(self):
        row = {
            "fy_code": "",
            "sprint_number": "1",
            "start_date": "2024-04-01",
            "end_date": "2024-04-14",
        }
        errors = self.svc.validate_row(row, 2)
        self.assertTrue(any(e["field"] == "fy_code" for e in errors))

    def test_missing_sprint_number_returns_error(self):
        row = {
            "fy_code": "FY-1",
            "sprint_number": "",
            "start_date": "2024-04-01",
            "end_date": "2024-04-14",
        }
        errors = self.svc.validate_row(row, 2)
        self.assertTrue(any(e["field"] == "sprint_number" for e in errors))


class SprintBulkImportTest(TestCase):
    def setUp(self):
        self.fy = make_financial_year(
            start_date=date(2024, 4, 1), end_date=date(2025, 3, 31)
        )
        self.user = make_user()
        self.svc = SprintImportService(user=self.user)

    def test_raises_for_missing_required_columns(self):
        csv_content = "start_date,end_date\n2024-04-01,2024-04-14\n"
        f = FakeCsvFile(csv_content)
        with self.assertRaises(ValidationException):
            self.svc.bulk_import(f)

    def test_creates_sprint_on_valid_csv(self):
        csv_content = (
            "fy_code,sprint_number,start_date,end_date\n"
            f"{self.fy.code},1,2024-04-01,2024-04-14\n"
        )
        f = FakeCsvFile(csv_content)
        result = self.svc.bulk_import(f)
        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["errors"]), 0)
        self.assertTrue(
            Sprint.objects.filter(sprint_number=1, financial_year=self.fy).exists()
        )

    def test_dry_run_does_not_persist(self):
        csv_content = (
            "fy_code,sprint_number,start_date,end_date\n"
            f"{self.fy.code},1,2024-04-01,2024-04-14\n"
        )
        f = FakeCsvFile(csv_content)
        result = self.svc.bulk_import(f, dry_run=True)
        self.assertTrue(result["dry_run"])
        self.assertFalse(Sprint.objects.filter(financial_year=self.fy).exists())

    def test_unknown_fy_code_adds_error(self):
        csv_content = (
            "fy_code,sprint_number,start_date,end_date"
            "\nFY-9999,1,2024-04-01,2024-04-14\n"
        )
        f = FakeCsvFile(csv_content)
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["field"], "fy_code")

    def test_overlapping_dates_adds_error(self):
        make_sprint(
            financial_year=self.fy,
            sprint_number=1,
            start_date=date(2024, 4, 1),
            end_date=date(2024, 4, 14),
        )
        csv_content = (
            "fy_code,sprint_number,start_date,end_date\n"
            f"{self.fy.code},2,2024-04-07,2024-04-21\n"
        )
        f = FakeCsvFile(csv_content)
        result = self.svc.bulk_import(f)
        self.assertEqual(len(result["errors"]), 1)


# ── SprintCapacityEngine.compute_for_member ───────────────────────────────────
#
# Sprint window: Mon 2024-04-01 → Sun 2024-04-14 (10 working days)
#   Week 1: Apr 1–5 (Mon–Fri) = 5 days | Apr 6–7 weekend
#   Week 2: Apr 8–12 (Mon–Fri) = 5 days | Apr 13–14 weekend


class SprintCapacityEngineComputeForMemberTest(TestCase):
    def setUp(self):
        self.sprint = make_sprint(
            start_date=date(2024, 4, 1), end_date=date(2024, 4, 14)
        )
        self.member = make_user(email="member@example.com")

    def test_no_date_limits_uses_full_sprint_window(self):
        result = SprintCapacityEngine.compute_for_member(
            self.sprint, self.member.pk, None
        )
        self.assertEqual(result["working_days"], Decimal(10))
        self.assertEqual(result["holiday_days"], Decimal(0))
        self.assertEqual(result["leave_days"], Decimal(0))
        self.assertEqual(result["net_capacity"], Decimal(10))

    def test_joined_date_after_sprint_start_clips_effective_start(self):
        # Joins Apr 8 (Mon week 2) → only 5 working days remain
        result = SprintCapacityEngine.compute_for_member(
            self.sprint, self.member.pk, None, joined_date=date(2024, 4, 8)
        )
        self.assertEqual(result["working_days"], Decimal(5))
        self.assertEqual(result["net_capacity"], Decimal(5))

    def test_joined_date_before_sprint_start_does_not_clip(self):
        # Joined before sprint starts — no effect
        result = SprintCapacityEngine.compute_for_member(
            self.sprint, self.member.pk, None, joined_date=date(2024, 3, 1)
        )
        self.assertEqual(result["working_days"], Decimal(10))
        self.assertEqual(result["net_capacity"], Decimal(10))

    def test_joined_date_equal_to_sprint_start_does_not_clip(self):
        # Joined exactly on start date — not strictly greater, so no clipping
        result = SprintCapacityEngine.compute_for_member(
            self.sprint, self.member.pk, None, joined_date=date(2024, 4, 1)
        )
        self.assertEqual(result["working_days"], Decimal(10))

    def test_leaving_date_before_sprint_end_clips_effective_end(self):
        # Leaves Apr 7 (Sun, end of week 1) → only 5 working days counted
        result = SprintCapacityEngine.compute_for_member(
            self.sprint, self.member.pk, None, leaving_date=date(2024, 4, 7)
        )
        self.assertEqual(result["working_days"], Decimal(5))
        self.assertEqual(result["net_capacity"], Decimal(5))

    def test_leaving_date_after_sprint_end_does_not_clip(self):
        # Leaves after sprint ends — no effect
        result = SprintCapacityEngine.compute_for_member(
            self.sprint, self.member.pk, None, leaving_date=date(2024, 5, 1)
        )
        self.assertEqual(result["working_days"], Decimal(10))
        self.assertEqual(result["net_capacity"], Decimal(10))

    def test_leaving_date_equal_to_sprint_end_does_not_clip(self):
        # Leaves exactly on end date — not strictly less, so no clipping
        result = SprintCapacityEngine.compute_for_member(
            self.sprint, self.member.pk, None, leaving_date=date(2024, 4, 14)
        )
        self.assertEqual(result["working_days"], Decimal(10))

    def test_both_dates_clip_both_ends(self):
        # Joined Apr 8 (Mon), leaves Apr 10 (Wed) → 3 working days
        result = SprintCapacityEngine.compute_for_member(
            self.sprint,
            self.member.pk,
            None,
            joined_date=date(2024, 4, 8),
            leaving_date=date(2024, 4, 10),
        )
        self.assertEqual(result["working_days"], Decimal(3))
        self.assertEqual(result["net_capacity"], Decimal(3))

    def test_joined_after_sprint_ends_returns_all_zeros(self):
        # Joins Apr 15 — after sprint ends Apr 14 → eff_end < eff_start
        result = SprintCapacityEngine.compute_for_member(
            self.sprint, self.member.pk, None, joined_date=date(2024, 4, 15)
        )
        self.assertEqual(result["working_days"], Decimal(0))
        self.assertEqual(result["holiday_days"], Decimal(0))
        self.assertEqual(result["leave_days"], Decimal(0))
        self.assertEqual(result["net_capacity"], Decimal(0))

    def test_left_before_sprint_starts_returns_all_zeros(self):
        # Left Mar 31 — before sprint starts Apr 1 → eff_end < eff_start
        result = SprintCapacityEngine.compute_for_member(
            self.sprint, self.member.pk, None, leaving_date=date(2024, 3, 31)
        )
        self.assertEqual(result["working_days"], Decimal(0))
        self.assertEqual(result["holiday_days"], Decimal(0))
        self.assertEqual(result["leave_days"], Decimal(0))
        self.assertEqual(result["net_capacity"], Decimal(0))

    def test_joined_and_left_on_same_day_within_sprint(self):
        # Joined and left Apr 3 (Wed) → 1 working day
        result = SprintCapacityEngine.compute_for_member(
            self.sprint,
            self.member.pk,
            None,
            joined_date=date(2024, 4, 3),
            leaving_date=date(2024, 4, 3),
        )
        self.assertEqual(result["working_days"], Decimal(1))
        self.assertEqual(result["net_capacity"], Decimal(1))


# ── SprintCapacityEngine.rebuild_for_sprint ───────────────────────────────────


class SprintCapacityEngineRebuildTest(TestCase):
    def setUp(self):
        self.sprint = make_sprint(
            start_date=date(2024, 4, 1), end_date=date(2024, 4, 14)
        )

    def test_rebuild_creates_capacity_row_for_each_active_member(self):
        member = make_user(email="rebuild@example.com")
        count = SprintCapacityEngine.rebuild_for_sprint(self.sprint)
        self.assertEqual(count, 1)
        self.assertTrue(
            Capacity.objects.filter(sprint=self.sprint, member=member).exists()
        )

    def test_rebuild_without_profile_uses_full_sprint_window(self):
        # No profile → joined_date/leaving_date default to None → full window
        member = make_user(email="noprofile@example.com")
        SprintCapacityEngine.rebuild_for_sprint(self.sprint)
        cap = Capacity.objects.get(sprint=self.sprint, member=member)
        self.assertEqual(cap.working_days, Decimal(10))
        self.assertEqual(cap.net_capacity, Decimal(10))

    def test_rebuild_reads_joined_date_from_profile(self):
        # Member joined mid-sprint — capacity should reflect clipped window
        member = make_user(email="joined@example.com")
        make_profile(user=member, joined_date=date(2024, 4, 8))
        SprintCapacityEngine.rebuild_for_sprint(self.sprint)
        cap = Capacity.objects.get(sprint=self.sprint, member=member)
        self.assertEqual(cap.working_days, Decimal(5))
        self.assertEqual(cap.net_capacity, Decimal(5))

    def test_rebuild_reads_leaving_date_from_profile(self):
        # Member leaves mid-sprint — capacity should reflect clipped window
        member = make_user(email="leaving@example.com")
        make_profile(user=member, leaving_date=date(2024, 4, 7))
        SprintCapacityEngine.rebuild_for_sprint(self.sprint)
        cap = Capacity.objects.get(sprint=self.sprint, member=member)
        self.assertEqual(cap.working_days, Decimal(5))
        self.assertEqual(cap.net_capacity, Decimal(5))

    def test_rebuild_returns_zero_capacity_when_member_outside_sprint(self):
        # Member left before sprint started → zero capacity record persisted
        member = make_user(email="outside@example.com")
        make_profile(user=member, leaving_date=date(2024, 3, 31))
        SprintCapacityEngine.rebuild_for_sprint(self.sprint)
        cap = Capacity.objects.get(sprint=self.sprint, member=member)
        self.assertEqual(cap.working_days, Decimal(0))
        self.assertEqual(cap.net_capacity, Decimal(0))

    def test_rebuild_upserts_existing_capacity_row(self):
        # Calling rebuild twice should update, not duplicate
        member = make_user(email="upsert@example.com")
        SprintCapacityEngine.rebuild_for_sprint(self.sprint)
        SprintCapacityEngine.rebuild_for_sprint(self.sprint)
        count = Capacity.objects.filter(sprint=self.sprint, member=member).count()
        self.assertEqual(count, 1)

    def test_rebuild_sets_updated_by_from_actor(self):
        actor = make_user(email="actor@example.com")
        member = make_user(email="member2@example.com")
        SprintCapacityEngine.rebuild_for_sprint(self.sprint, actor=actor)
        cap = Capacity.objects.get(sprint=self.sprint, member=member)
        self.assertEqual(cap.updated_by, actor)
