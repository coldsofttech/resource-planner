from __future__ import annotations

import math
from decimal import Decimal

from django.db.models import Count, Q, QuerySet, Sum

from apps.recharges.models import ProjectTypeMapping, RechargeProjectGroup, RechargeType


def get_all_recharge_project_groups() -> QuerySet[RechargeProjectGroup]:
    return (
        RechargeProjectGroup.objects.select_related("created_by", "updated_by")
        .prefetch_related("projects")
        .all()
    )


def get_recharge_project_group_by_code(code: str) -> RechargeProjectGroup | None:
    try:
        return (
            RechargeProjectGroup.objects.select_related("created_by", "updated_by")
            .prefetch_related("projects")
            .get(code=code)
        )
    except RechargeProjectGroup.DoesNotExist:
        return None


def recharge_project_group_exists(name: str, exclude_pk: int | None = None) -> bool:
    qs = RechargeProjectGroup.objects.filter(name__iexact=name)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_recharge_project_group_stats() -> dict:
    return RechargeProjectGroup.objects.aggregate(total=Count("id"))


def get_project_codes_already_in_groups(
    project_codes: list[str],
    exclude_pk: int | None = None,
) -> list[str]:
    """Return which project codes are already assigned to an existing group."""
    qs = RechargeProjectGroup.objects.filter(projects__code__in=project_codes)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return list(qs.values_list("projects__code", flat=True).distinct())


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


def get_recharge_summary(sprint_code: str) -> dict:
    """Aggregate forecast/actual totals and per-type breakdown for a sprint."""
    from apps.recharges.models import (
        Recharge,  # noqa: PLC0415 — avoid circular at module level
    )

    qs = Recharge.objects.filter(sprint__code=sprint_code)

    def _agg(type_val: str) -> tuple[Decimal, Decimal]:
        r = qs.filter(type=type_val).aggregate(d=Sum("total_days"), c=Sum("total_cost"))
        return Decimal(str(r["d"] or 0)), Decimal(str(r["c"] or 0))

    fd, fc = _agg("forecast")
    ad, ac = _agg("actual")

    groups = (
        qs.values("recharge_type__code", "recharge_type__name", "type")
        .annotate(d=Sum("total_days"), c=Sum("total_cost"))
        .order_by("recharge_type__name")
    )

    type_map: dict[str, dict] = {}
    for g in groups:
        tc = g["recharge_type__code"] or ""
        tn = g["recharge_type__name"] or "Untyped"
        if tc not in type_map:
            type_map[tc] = {
                "type_code": tc,
                "type_name": tn,
                "forecast_days": Decimal("0"),
                "forecast_cost": Decimal("0"),
                "actual_days": Decimal("0"),
                "actual_cost": Decimal("0"),
            }
        row = type_map[tc]
        d_val = Decimal(str(g["d"] or 0))
        c_val = Decimal(str(g["c"] or 0))
        if g["type"] == "forecast":
            row["forecast_days"] += d_val
            row["forecast_cost"] += c_val
        else:
            row["actual_days"] += d_val
            row["actual_cost"] += c_val

    by_type = []
    for row in sorted(type_map.values(), key=lambda x: x["type_name"]):
        fdays = row["forecast_days"]
        fcost = row["forecast_cost"]
        adays = row["actual_days"]
        acost = row["actual_cost"]
        by_type.append(
            {
                "type_code": row["type_code"],
                "type_name": row["type_name"],
                "forecast_days": str(fdays),
                "forecast_cost": str(fcost),
                "actual_days": str(adays),
                "actual_cost": str(acost),
                "variance_days": str(adays - fdays),
                "variance_cost": str(acost - fcost),
            }
        )

    total_pages = max(1, math.ceil(len(by_type) / 100))
    return {
        "summary": {
            "forecast_days": str(fd),
            "forecast_cost": str(fc),
            "actual_days": str(ad),
            "actual_cost": str(ac),
            "variance_days": str(ad - fd),
            "variance_cost": str(ac - fc),
        },
        "results": by_type,
        "pagination": {
            "total_count": len(by_type),
            "total_pages": total_pages,
            "current_page": 1,
            "page_size": 100,
            "has_next": False,
            "has_previous": False,
        },
    }


def get_recharges_for_sprint(sprint_code: str, type_val: str) -> QuerySet:
    """Return recharge rows for a sprint and type, with contacts prefetched."""
    from apps.recharges.models import Recharge  # noqa: PLC0415

    return (
        Recharge.objects.select_related("programme", "project", "recharge_type")
        .prefetch_related(
            "finance_contacts__contact",
            "project_contacts__contact",
        )
        .filter(sprint__code=sprint_code, type=type_val)
        .order_by("programme__name", "project__name")
    )


def get_project_forecast_cost_by_sprint(project_ids: list[int]) -> QuerySet:
    """Sum(total_cost) grouped by sprint for forecast-type Recharge rows
    scoped to the given project ids. Used by the Utilisation Graph's
    Programmes tab (#204) to roll up per-sprint forecast cost to a
    programme's projects that are configured on a specific resource plan
    version."""
    from apps.recharges.constants import (
        RechargeType as RechargeTypeChoice,  # noqa: PLC0415
    )
    from apps.recharges.models import Recharge  # noqa: PLC0415

    return (
        Recharge.objects.filter(
            project_id__in=project_ids, type=RechargeTypeChoice.FORECAST
        )
        .values("sprint_id")
        .annotate(total_cost=Sum("total_cost"))
    )


def get_recharge_by_code(code: str):
    """Return the Recharge with the given code, or None."""
    from apps.recharges.models import Recharge  # noqa: PLC0415

    try:
        return Recharge.objects.select_related(
            "sprint", "project", "programme", "recharge_type"
        ).get(code=code)
    except Recharge.DoesNotExist:
        return None


def _recharge_detail_base_qs(recharge):
    """Return a RechargeDetail queryset scoped to the given Recharge."""
    from apps.recharges.models import RechargeDetail  # noqa: PLC0415

    filters: dict = {
        "sprint": recharge.sprint,
        "project": recharge.project,
        "type": recharge.type,
    }
    if recharge.programme_id:
        filters["programme"] = recharge.programme
    if recharge.recharge_type_id:
        filters["recharge_type"] = recharge.recharge_type

    return RechargeDetail.objects.filter(**filters)


def get_recharge_details_grouped(recharge_code: str, group_by: str) -> list[dict]:
    """Return RechargeDetail totals grouped by engineer, team, or label."""
    recharge = get_recharge_by_code(recharge_code)
    if not recharge:
        return []

    qs = _recharge_detail_base_qs(recharge)

    if group_by == "team":
        rows = (
            qs.values("team__name")
            .annotate(days=Sum("total_days"), cost=Sum("total_cost"))
            .order_by("team__name")
        )
        return [
            {
                "team": r["team__name"] or "No team",
                "engineer": None,
                "label": None,
                "total_days": str(r["days"] or 0),
                "total_cost": str(r["cost"] or 0),
            }
            for r in rows
        ]

    if group_by == "label":
        rows = (
            qs.values("label__label")
            .annotate(days=Sum("total_days"), cost=Sum("total_cost"))
            .order_by("label__label")
        )
        return [
            {
                "team": None,
                "engineer": None,
                "label": r["label__label"] or "No label",
                "total_days": str(r["days"] or 0),
                "total_cost": str(r["cost"] or 0),
            }
            for r in rows
        ]

    # Default: by engineer
    rows = (
        qs.values(
            "team__name",
            "assignee__user__first_name",
            "assignee__user__last_name",
            "assignee__user__email",
        )
        .annotate(days=Sum("total_days"), cost=Sum("total_cost"))
        .order_by("assignee__user__first_name", "assignee__user__last_name")
    )
    return [
        {
            "team": r["team__name"] or "",
            "engineer": (
                f"{r['assignee__user__first_name'] or ''} "
                f"{r['assignee__user__last_name'] or ''}".strip()
                or r["assignee__user__email"]
                or "Unassigned"
            ),
            "label": None,
            "total_days": str(r["days"] or 0),
            "total_cost": str(r["cost"] or 0),
        }
        for r in rows
    ]


def get_email_review_groups(sprint_code: str, review_type: str) -> list[dict]:
    """
    Aggregate recharge email preview data grouped by RechargeProjectGroup.

    Returns a list of dicts with group metadata, aggregated totals, contacts,
    and the current RechargeEmail record (if any) for status/sent_at.
    """
    from decimal import Decimal

    from apps.recharges.models import Recharge, RechargeEmail  # noqa: PLC0415

    recharges = (
        Recharge.objects.select_related("project", "programme", "recharge_type")
        .prefetch_related(
            "finance_contacts__contact",
            "project_contacts__contact",
        )
        .filter(sprint__code=sprint_code, type=review_type)
    )

    # Map project_id → recharge row(s)
    project_recharge_map: dict[int, list] = {}
    for r in recharges:
        if r.project_id:
            project_recharge_map.setdefault(r.project_id, []).append(r)

    if not project_recharge_map:
        return []

    project_ids = list(project_recharge_map.keys())

    groups = (
        RechargeProjectGroup.objects.prefetch_related("projects")
        .filter(projects__id__in=project_ids)
        .distinct()
        .order_by("name")
    )

    # Fetch existing email records keyed by group_id
    existing_emails = {
        e.group_id: e
        for e in RechargeEmail.objects.filter(
            sprint__code=sprint_code,
            type=review_type,
        ).select_related("group")
    }

    results = []
    for group in groups:
        group_project_ids = {p.id for p in group.projects.all()}
        total_days = Decimal("0")
        total_cost = Decimal("0")
        finance_contacts: list[dict] = []
        project_contacts: list[dict] = []
        seen_finance: set[str] = set()
        seen_project: set[str] = set()
        project_count = 0

        for pid in group_project_ids:
            for r in project_recharge_map.get(pid, []):
                project_count += 1
                total_days += r.total_days or Decimal("0")
                total_cost += r.total_cost or Decimal("0")
                for fc in r.finance_contacts.all():
                    key = fc.contact.email if fc.contact else fc.pk
                    if key not in seen_finance:
                        seen_finance.add(key)
                        finance_contacts.append(
                            {
                                "name": fc.contact.name if fc.contact else "",
                                "email": fc.contact.email if fc.contact else "",
                            }
                        )
                for pc in r.project_contacts.all():
                    key = pc.contact.email if pc.contact else pc.pk
                    if key not in seen_project:
                        seen_project.add(key)
                        project_contacts.append(
                            {
                                "name": pc.contact.name if pc.contact else "",
                                "email": pc.contact.email if pc.contact else "",
                            }
                        )

        existing = existing_emails.get(group.pk)
        results.append(
            {
                "email_code": existing.code if existing else None,
                "group_code": group.code,
                "group_name": group.name,
                "total_days": str(total_days),
                "total_cost": str(total_cost),
                "project_count": project_count,
                "status": existing.status if existing else "pending",
                "sent_at": (
                    existing.sent_at.isoformat()
                    if (existing and existing.sent_at)
                    else None
                ),
                "to": existing.to if existing else finance_contacts,
                "cc": existing.cc if existing else project_contacts,
                "subject": existing.subject if existing else "",
                "body": existing.body if existing else "",
            }
        )

    return results


def get_recharge_email_by_code(code: str):
    """Return a RechargeEmail by its code, or None."""
    from apps.recharges.models import RechargeEmail  # noqa: PLC0415

    try:
        return RechargeEmail.objects.select_related("sprint", "group").get(code=code)
    except RechargeEmail.DoesNotExist:
        return None


def get_recharge_email_by_sprint_type_group(
    sprint_code: str, type_val: str, group_code: str
):
    """Return a RechargeEmail for a specific sprint, type, and group, or None."""
    from apps.recharges.models import RechargeEmail  # noqa: PLC0415

    try:
        return RechargeEmail.objects.select_related("sprint", "group").get(
            sprint__code=sprint_code,
            type=type_val,
            group__code=group_code,
        )
    except RechargeEmail.DoesNotExist:
        return None


def get_recharge_jira_stories(recharge_code: str) -> QuerySet:
    """Return flat RechargeDetail rows for the Jira stories view."""
    from apps.recharges.models import RechargeDetail  # noqa: PLC0415

    recharge = get_recharge_by_code(recharge_code)
    if not recharge:
        return RechargeDetail.objects.none()

    return (
        _recharge_detail_base_qs(recharge)
        .select_related("team", "assignee__user", "label")
        .order_by("team__name", "assignee__user__first_name")
    )
