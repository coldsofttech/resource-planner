from __future__ import annotations

from django.db.models import Count, Q, QuerySet

from apps.audit.models import Audit
from apps.audit.selectors import get_audit_entries_for_resource_prefix
from apps.resource_plans.models import Plan, PlanVersion

VERSION_AUDIT_MODULE = "resource_plans"
VERSION_AUDIT_RESOURCE_TYPE = "resource_plan_version"


def get_all_resource_plans() -> QuerySet[Plan]:
    return (
        Plan.objects.select_related(
            "financial_year",
            "cloned_from",
            "created_by",
            "updated_by",
        )
        .prefetch_related("versions", "scope")
        .all()
    )


def get_active_resource_plans() -> QuerySet[Plan]:
    return get_all_resource_plans().filter(is_active=True)


def get_resource_plan_by_code(code: str) -> Plan | None:
    try:
        return (
            Plan.objects.select_related(
                "financial_year",
                "cloned_from",
                "created_by",
                "updated_by",
                "scope__financial_year",
                "scope__programme",
                "scope__project",
                "scope__team",
            )
            .prefetch_related("versions__created_by", "versions__updated_by")
            .get(code=code)
        )
    except Plan.DoesNotExist:
        return None


def resource_plan_exists(name: str, exclude_pk: int | None = None) -> bool:
    qs = Plan.objects.filter(name__iexact=name)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_resource_plan_options() -> QuerySet[Plan]:
    return Plan.objects.filter(is_active=True).only("code", "name").order_by("name")


def get_resource_plan_stats() -> dict:
    return Plan.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        inactive=Count("id", filter=Q(is_active=False)),
    )


def get_latest_version(plan: Plan) -> PlanVersion | None:
    return (
        PlanVersion.objects.filter(plan=plan)
        .select_related("created_by", "updated_by")
        .order_by("-version")
        .first()
    )


def get_version_by_number(plan: Plan, version: int) -> PlanVersion | None:
    try:
        return PlanVersion.objects.select_related(
            "plan",
            "plan__financial_year",
            "cloned_from",
            "created_by",
            "updated_by",
        ).get(plan=plan, version=version)
    except PlanVersion.DoesNotExist:
        return None


def get_version_history(plan: Plan) -> QuerySet[Audit]:
    return get_audit_entries_for_resource_prefix(
        module=VERSION_AUDIT_MODULE,
        resource_type=VERSION_AUDIT_RESOURCE_TYPE,
        resource_code_prefix=f"{plan.code}-v",
    )
