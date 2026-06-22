from __future__ import annotations

from django.db.models import QuerySet

from apps.sprints.models import SprintDataImport, SprintDataImportRow


def get_imports_for_sprint_team(
    sprint_id: int,
    team_id: int,
    import_type: str | None = None,
) -> QuerySet[SprintDataImport]:
    qs = SprintDataImport.objects.select_related(
        "sprint", "team", "created_by", "updated_by"
    ).filter(sprint_id=sprint_id, team_id=team_id)
    if import_type:
        qs = qs.filter(import_type=import_type)
    return qs


def get_import_by_code(import_code: str) -> SprintDataImport | None:
    try:
        return SprintDataImport.objects.select_related(
            "sprint", "team", "created_by"
        ).get(code=import_code)
    except SprintDataImport.DoesNotExist:
        return None


def get_rows_for_import(import_id: int) -> QuerySet[SprintDataImportRow]:
    return (
        SprintDataImportRow.objects.select_related(
            "assignee_code__user",
            "label_code",
            "mapping_code",
            "sprint_code",
            "assignee_code_override__user",
            "label_code_override",
            "mapping_code_override",
            "sprint_code_override",
        )
        .filter(import_record_id=import_id, is_deleted=False)
        .order_by("pk")
    )


def get_has_review_for_import(import_id: int) -> bool:
    from apps.sprints.models.sprint_data_import_review import SprintDataImportReview

    return SprintDataImportReview.objects.filter(import_record_id=import_id).exists()


def get_failing_row_ids_for_check(import_id: int, check_type: str) -> set[int]:
    """Return the set of SprintDataImportRow PKs that failed ``check_type`` in the
    most recent review for the given import record. Returns an empty set when no
    review exists yet or no rows failed the given check.
    """
    from apps.sprints.constants import ImportRowCheckStatus
    from apps.sprints.models.sprint_data_import_review import SprintDataImportReview
    from apps.sprints.models.sprint_data_import_review_result import (
        SprintDataImportReviewResult,
    )

    latest = (
        SprintDataImportReview.objects.filter(import_record_id=import_id)
        .order_by("-reviewed_at")
        .values_list("pk", flat=True)
        .first()
    )
    if latest is None:
        return set()

    return set(
        SprintDataImportReviewResult.objects.filter(
            review_id=latest,
            check_type=check_type,
            status=ImportRowCheckStatus.FAIL,
        ).values_list("row_id", flat=True)
    )


def get_capacity_check_results_for_import(import_id: int) -> dict[int, dict]:
    """Return a dict keyed by User PK with capacity check data from the most
    recent review for the given import. Returns an empty dict when no review
    exists.

    Shape: ``{user_id: {"allocated_days": Decimal, "net_capacity": Decimal,
    "status": str}}``
    """
    from apps.sprints.models.sprint_data_import_review import SprintDataImportReview
    from apps.sprints.models.sprint_data_import_review_capacity_result import (
        SprintDataImportReviewCapacityResult,
    )

    latest = (
        SprintDataImportReview.objects.filter(import_record_id=import_id)
        .order_by("-reviewed_at")
        .values_list("pk", flat=True)
        .first()
    )
    if latest is None:
        return {}

    return {
        r.member_id: {
            "allocated_days": r.allocated_days,
            "net_capacity": r.net_capacity,
            "status": r.status,
        }
        for r in SprintDataImportReviewCapacityResult.objects.filter(review_id=latest)
    }


def get_completion_for_import(import_id: int):
    """Return the SprintDataImportReviewComplete for the sprint/import_type of the
    given import record, or None if no confirmation exists yet."""
    from apps.sprints.models.sprint_data_import_review_complete import (
        SprintDataImportReviewComplete,
    )

    try:
        record = SprintDataImport.objects.select_related("sprint").get(pk=import_id)
    except SprintDataImport.DoesNotExist:
        return None

    try:
        return SprintDataImportReviewComplete.objects.get(
            sprint=record.sprint,
            import_type=record.import_type,
        )
    except SprintDataImportReviewComplete.DoesNotExist:
        return None


def get_latest_active_import(
    sprint_id: int,
    team_id: int,
    import_type: str,
) -> SprintDataImport | None:
    from apps.sprints.constants import SprintDataImportStatus

    try:
        return SprintDataImport.objects.select_related(
            "sprint", "team", "created_by"
        ).get(
            sprint_id=sprint_id,
            team_id=team_id,
            import_type=import_type,
            status=SprintDataImportStatus.ACTIVE,
        )
    except SprintDataImport.DoesNotExist:
        return None
