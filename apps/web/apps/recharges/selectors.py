from __future__ import annotations

from django.db.models import Count, Q, QuerySet

from apps.recharges.models import ProjectTypeMapping, RechargeType


def get_all_recharge_types() -> QuerySet[RechargeType]:
    return RechargeType.objects.select_related("created_by", "updated_by").all()


def get_active_recharge_types() -> QuerySet[RechargeType]:
    return RechargeType.objects.select_related("created_by", "updated_by").filter(
        is_active=True
    )


def get_recharge_type_by_code(code: str) -> RechargeType | None:
    try:
        return RechargeType.objects.select_related("created_by", "updated_by").get(
            code=code
        )
    except RechargeType.DoesNotExist:
        return None


def recharge_type_exists(name: str, exclude_pk: int | None = None) -> bool:
    qs = RechargeType.objects.filter(name__iexact=name)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_recharge_type_options() -> QuerySet[RechargeType]:
    return (
        RechargeType.objects.filter(is_active=True)
        .only("code", "name")
        .order_by("name")
    )


def get_recharge_type_stats() -> dict:
    return RechargeType.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        inactive=Count("id", filter=Q(is_active=False)),
    )


def get_all_project_type_mappings(
    recharge_type_code: str,
) -> QuerySet[ProjectTypeMapping]:
    return (
        ProjectTypeMapping.objects.select_related(
            "project_type", "recharge_type", "created_by", "updated_by"
        )
        .filter(recharge_type__code=recharge_type_code)
        .order_by("project_type__name")
    )


def get_project_type_mapping_by_id(
    recharge_type_code: str, pk: int
) -> ProjectTypeMapping | None:
    try:
        return ProjectTypeMapping.objects.select_related(
            "project_type", "recharge_type", "created_by", "updated_by"
        ).get(recharge_type__code=recharge_type_code, pk=pk)
    except ProjectTypeMapping.DoesNotExist:
        return None


def project_type_mapping_exists(
    recharge_type_id: int,
    project_type_id: int,
    exclude_pk: int | None = None,
) -> bool:
    qs = ProjectTypeMapping.objects.filter(
        recharge_type_id=recharge_type_id,
        project_type_id=project_type_id,
    )
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()
