from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from django.db import transaction

from apps.sprints.constants import ImportRowCheck, ImportRowCheckStatus


def _fail_message(check_type: str, row) -> str:
    if check_type == ImportRowCheck.ASSIGNEE:
        raw = row.effective_assignee or "—"
        return f'Assignee "{raw}" not found or is inactive.'
    if check_type == ImportRowCheck.SPRINT:
        raw = row.effective_sprint or "—"
        return f'Sprint "{raw}" not found or is inactive.'
    if check_type == ImportRowCheck.LABEL:
        raw = row.effective_label or "—"
        return f'Label "{raw}" not found in the system.'
    if check_type == ImportRowCheck.MAPPING:
        raw = row.effective_mapping or "—"
        return f'Mapping "{raw}" is not valid for the project type.'
    return ""


def _efforts_to_days(efforts_str: str, per_day: Decimal) -> Decimal:
    """Convert an efforts string (seconds) to days, returning 0 on invalid input."""
    try:
        val = Decimal(str(efforts_str))
    except Exception:
        return Decimal("0")
    if val <= 0 or per_day <= 0:
        return Decimal("0")
    return (val / per_day).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class SprintDataImportEngine:
    """Review engine for sprint data import rows."""

    @staticmethod
    @transaction.atomic
    def run_review(import_record_id: int, user=None):
        """Run all import row checks plus per-engineer capacity checks, persist
        the results, and return ``(review, row_results)`` where ``row_results``
        is a dict mapping ``row.code → {check_type: pass_bool}``.
        """
        from apps.configurations.selectors import Sprint as SprintConfig
        from apps.recharges.models import ProjectTypeMapping
        from apps.sprints.models import (
            Capacity,
            SprintDataImport,
            SprintDataImportRow,
        )
        from apps.sprints.models.sprint_data_import_review import SprintDataImportReview
        from apps.sprints.models.sprint_data_import_review_capacity_result import (
            SprintDataImportReviewCapacityResult,
        )
        from apps.sprints.models.sprint_data_import_review_result import (
            SprintDataImportReviewResult,
        )

        rows = list(
            SprintDataImportRow.objects.select_related(
                "assignee_code__user",
                "assignee_code_override__user",
                "label_code__project__project_type",
                "label_code_override__project__project_type",
                "mapping_code",
                "mapping_code_override",
                "sprint_code",
                "sprint_code_override",
            )
            .filter(import_record_id=import_record_id, is_deleted=False)
            .order_by("pk")
        )

        # Pre-load hours_per_day once for days calculation
        hours_per_day = SprintConfig.get_hours_per_day()
        per_day = (
            Decimal(str(hours_per_day * 3_600)) if hours_per_day > 0 else Decimal("0")
        )

        # Pre-load project type → allowed recharge type IDs for batch checking
        pt_to_rt: dict[int, set[int]] = {}
        for pt_id, rt_id in ProjectTypeMapping.objects.all().values_list(
            "project_type_id", "recharge_type_id"
        ):
            pt_to_rt.setdefault(pt_id, set()).add(rt_id)

        # Look up sprint_id for this import (needed for capacity lookup)
        import_record = SprintDataImport.objects.select_related("sprint").get(
            pk=import_record_id
        )
        sprint_id = import_record.sprint_id

        # Pre-load capacity records for this sprint: member_id → net_capacity
        capacity_map: dict[int, Decimal] = {
            c.member_id: c.net_capacity
            for c in Capacity.objects.filter(sprint_id=sprint_id)
        }

        review = SprintDataImportReview.objects.create(
            import_record_id=import_record_id,
            reviewed_by=user,
        )

        result_objs: list[SprintDataImportReviewResult] = []
        row_results: dict[str, dict[str, bool]] = {}

        # Accumulate allocated days per member for capacity check
        member_days: dict[int, Decimal] = {}

        for row in rows:
            eff_assignee = row.effective_assignee_code
            eff_sprint = row.effective_sprint_code
            eff_label = row.effective_label_code
            eff_mapping = row.effective_mapping_code

            assignee_ok = eff_assignee is not None and eff_assignee.user.is_active

            sprint_ok = eff_sprint is not None and eff_sprint.is_active

            label_ok = eff_label is not None

            mapping_ok = False
            if (
                eff_mapping is not None
                and eff_mapping.is_active
                and eff_label is not None
                and eff_label.project is not None
                and eff_label.project.project_type_id is not None
            ):
                allowed = pt_to_rt.get(eff_label.project.project_type_id, set())
                mapping_ok = eff_mapping.pk in allowed

            checks = {
                ImportRowCheck.ASSIGNEE: assignee_ok,
                ImportRowCheck.SPRINT: sprint_ok,
                ImportRowCheck.LABEL: label_ok,
                ImportRowCheck.MAPPING: mapping_ok,
            }
            row_results[row.code] = checks

            for check_type, passed in checks.items():
                result_objs.append(
                    SprintDataImportReviewResult(
                        review=review,
                        row=row,
                        check_type=check_type,
                        status=ImportRowCheckStatus.PASS
                        if passed
                        else ImportRowCheckStatus.FAIL,
                        message="" if passed else _fail_message(check_type, row),
                    )
                )

            # Accumulate days for the effective assignee (must be a valid User)
            if eff_assignee is not None:
                user_id = eff_assignee.user_id
                if user_id is not None:
                    days = _efforts_to_days(row.effective_efforts, per_day)
                    member_days[user_id] = member_days.get(user_id, Decimal("0")) + days

        SprintDataImportReviewResult.objects.bulk_create(result_objs)

        # ── Capacity checks (one result per assignee found in the import) ─────
        capacity_result_objs: list[SprintDataImportReviewCapacityResult] = []
        for user_id, allocated in member_days.items():
            net = capacity_map.get(user_id, Decimal("0"))
            # PASS: allocated_days >= net_capacity; FAIL: allocated_days < net_capacity
            passed = allocated >= net
            capacity_result_objs.append(
                SprintDataImportReviewCapacityResult(
                    review=review,
                    member_id=user_id,
                    allocated_days=allocated,
                    net_capacity=net,
                    status=ImportRowCheckStatus.PASS
                    if passed
                    else ImportRowCheckStatus.FAIL,
                )
            )

        SprintDataImportReviewCapacityResult.objects.bulk_create(capacity_result_objs)

        return review, row_results
