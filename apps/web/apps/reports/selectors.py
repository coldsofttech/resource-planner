from django.db.models import Q, QuerySet

from apps.reports.models import (
    CustomReport,
    CustomReportShare,
    DemandCapacityReportConfig,
    KPIEstimateAccuracyConfig,
    Report,
)


def get_all_reports() -> QuerySet[Report]:
    return Report.objects.select_related("created_by", "updated_by").all()


def get_report_by_code(code: str) -> Report | None:
    try:
        return Report.objects.select_related("created_by", "updated_by").get(code=code)
    except Report.DoesNotExist:
        return None


def get_report_by_slug(slug: str) -> Report | None:
    try:
        return Report.objects.select_related("created_by", "updated_by").get(slug=slug)
    except Report.DoesNotExist:
        return None


def report_slug_exists(slug: str, exclude_pk: int | None = None) -> bool:
    qs = Report.objects.filter(slug=slug)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_visible_custom_reports(user) -> QuerySet[CustomReport]:
    """Custom reports owned by, or shared with, the given user."""
    return (
        CustomReport.objects.select_related("owner", "created_by", "updated_by")
        .filter(Q(owner=user) | Q(is_shared=True) | Q(shares__user=user))
        .distinct()
    )


def get_custom_report_by_code(code: str) -> CustomReport | None:
    try:
        return CustomReport.objects.select_related(
            "owner", "created_by", "updated_by"
        ).get(code=code)
    except CustomReport.DoesNotExist:
        return None


def get_custom_report_shares(report_id: int) -> QuerySet[CustomReportShare]:
    return CustomReportShare.objects.select_related(
        "user", "user__profile", "created_by", "updated_by"
    ).filter(report_id=report_id)


def get_demand_capacity_configs(
    *, plan_version_id: int | None = None
) -> QuerySet[DemandCapacityReportConfig]:
    qs = DemandCapacityReportConfig.objects.select_related(
        "plan", "plan_version", "programme", "created_by", "updated_by"
    )
    if plan_version_id is not None:
        qs = qs.filter(plan_version_id=plan_version_id)
    return qs


def get_demand_capacity_config_by_code(code: str) -> DemandCapacityReportConfig | None:
    try:
        return DemandCapacityReportConfig.objects.select_related(
            "plan", "plan_version", "programme", "created_by", "updated_by"
        ).get(code=code)
    except DemandCapacityReportConfig.DoesNotExist:
        return None


def demand_capacity_config_exists(
    plan_version_id: int, programme_id: int, exclude_pk: int | None = None
) -> bool:
    qs = DemandCapacityReportConfig.objects.filter(
        plan_version_id=plan_version_id, programme_id=programme_id
    )
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_kpi_estimate_accuracy_configs(
    *, month: str | None = None
) -> QuerySet[KPIEstimateAccuracyConfig]:
    qs = KPIEstimateAccuracyConfig.objects.select_related(
        "project", "created_by", "updated_by"
    )
    if month is not None:
        qs = qs.filter(month=month)
    return qs


def get_kpi_estimate_accuracy_config_by_code(
    code: str,
) -> KPIEstimateAccuracyConfig | None:
    try:
        return KPIEstimateAccuracyConfig.objects.select_related(
            "project", "created_by", "updated_by"
        ).get(code=code)
    except KPIEstimateAccuracyConfig.DoesNotExist:
        return None


def kpi_estimate_accuracy_config_exists(
    project_id: int, month: str, exclude_pk: int | None = None
) -> bool:
    qs = KPIEstimateAccuracyConfig.objects.filter(project_id=project_id, month=month)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()
