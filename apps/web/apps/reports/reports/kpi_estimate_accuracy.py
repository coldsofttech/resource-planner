"""Extraction logic for the KPI Report — Estimate % Accuracy standard report.

Kept separate from services.py so the report's data-shaping logic can grow
without bloating the reports app's service layer (see demand_vs_capacity.py).

For every project completed within a selected month, compares the latest
APPROVED estimate (base value and with contingency) against the cumulative
actual cost booked for that project up to and including that month, and
buckets the result into an accuracy band. A project with an exception
comment recorded against it (see `KPIEstimateAccuracyConfig`) is always
banded as "Exception" regardless of its computed % accuracy.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from django.db.models import Sum

from apps.financial_years.models import FinancialYear
from apps.projects.constants import ProjectEstimateStatus
from apps.projects.models import Project, ProjectEstimate, ProjectSprintActual
from apps.reports.models import KPIEstimateAccuracyConfig

REPORT_SLUG = "kpi-estimate-accuracy"

XS_S_SIZES = {"XS", "S"}
M_PLUS_SIZES = {"M", "L", "XL"}

NO_ESTIMATE_BAND = "—"
NO_ESTIMATE_KEY = "no_estimate"

# (key, label) — ordered best -> worst. Drives both band computation and the
# fixed display/legend order used by the data table and charts.
_BANDS: list[tuple[str, str]] = [
    ("gt90", "> 90%"),
    ("gt80", "> 80%"),
    ("in_range", "In Range"),
    ("gt70", "> 70%"),
    ("gt60", "> 60%"),
    ("gt50", "> 50%"),
    ("lt50", "< 50%"),
    ("exception", "Exception"),
]

BAND_LABELS: dict[str, str] = dict(_BANDS)
BAND_ORDER: list[str] = [key for key, _label in _BANDS]


def _month_label(month: str) -> str:
    return datetime.strptime(month, "%Y-%m").strftime("%b %Y")


def _accuracy_band(
    total_cost: Decimal, estimate_value: Decimal, estimate_wc: Decimal, comment: str
) -> tuple[str, str]:
    """Returns (band_key, band_label) for a single project row."""
    if comment and comment.strip():
        return "exception", BAND_LABELS["exception"]

    if estimate_value <= 0:
        return NO_ESTIMATE_KEY, NO_ESTIMATE_BAND

    # Over estimate but within contingency -> "In Range".
    if total_cost >= estimate_value and total_cost <= estimate_wc:
        return "in_range", BAND_LABELS["in_range"]

    accuracy = total_cost / estimate_value * 100
    if accuracy >= 90:
        return "gt90", BAND_LABELS["gt90"]
    if accuracy >= 80:
        return "gt80", BAND_LABELS["gt80"]
    if accuracy >= 70:
        return "gt70", BAND_LABELS["gt70"]
    if accuracy >= 60:
        return "gt60", BAND_LABELS["gt60"]
    if accuracy >= 50:
        return "gt50", BAND_LABELS["gt50"]
    return "lt50", BAND_LABELS["lt50"]


def _latest_approved_estimate(project: Project) -> ProjectEstimate | None:
    return (
        ProjectEstimate.objects.filter(
            project=project, status=ProjectEstimateStatus.APPROVED
        )
        .order_by("-version")
        .first()
    )


def _total_cost_till_month(project_ids: list[int], month: str) -> dict[int, Decimal]:
    rows = (
        ProjectSprintActual.objects.filter(
            project_id__in=project_ids, sprint__month__lte=month
        )
        .values("project_id")
        .annotate(total=Sum("total_cost"))
    )
    return {row["project_id"]: row["total"] or Decimal("0") for row in rows}


def get_completed_projects(fy: FinancialYear, month: str) -> list[Project]:
    return list(
        Project.objects.filter(
            status__name="Completed",
            sprint_completed_in__isnull=False,
            sprint_completed_in__financial_year=fy,
            sprint_completed_in__month=month,
        )
        .select_related("programme", "assigned_team", "status", "sprint_completed_in")
        .prefetch_related("collaborators__team")
        .order_by("name")
    )


def build_report_data(fy: FinancialYear, month: str) -> dict:
    projects = get_completed_projects(fy, month)
    project_ids = [p.id for p in projects]

    total_cost_map = _total_cost_till_month(project_ids, month)
    comment_map = {
        c.project_id: c.comment
        for c in KPIEstimateAccuracyConfig.objects.filter(
            project_id__in=project_ids, month=month
        )
    }

    rows: list[dict] = []
    for project in projects:
        estimate = _latest_approved_estimate(project)
        estimate_value = (
            Decimal(str(estimate.estimate_days)) * Decimal(str(estimate.day_rate))
            if estimate
            else Decimal("0")
        )
        estimate_wc = Decimal(str(estimate.total_cost)) if estimate else Decimal("0")
        total_cost = total_cost_map.get(project.id, Decimal("0"))
        comment = comment_map.get(project.id, "")

        tshirt_size = estimate.size if estimate and estimate_value > 0 else "—"
        band_key, band_label = _accuracy_band(
            total_cost, estimate_value, estimate_wc, comment
        )
        accuracy_pct = (
            round(float(total_cost / estimate_value * 100), 2)
            if estimate_value > 0
            else None
        )

        collaborators = [pc.team.name for pc in project.collaborators.all()]

        rows.append(
            {
                "project_code": project.code,
                "project": project.name,
                "programme": project.programme.name if project.programme else "—",
                "team": project.assigned_team.name if project.assigned_team else "—",
                "collaborators": collaborators,
                "collaborators_display": ", ".join(collaborators)
                if collaborators
                else "—",
                "estimate_value": str(estimate_value),
                "estimate_value_with_contingency": str(estimate_wc),
                "total_cost_till_date": str(total_cost),
                "tshirt_size": tshirt_size,
                "accuracy_pct": accuracy_pct,
                "band": band_label,
                "band_key": band_key,
                "comment": comment,
            }
        )

    def _chart_bands(sizes: set[str]) -> dict[str, int]:
        counts: dict[str, int] = {}
        for row in rows:
            if row["tshirt_size"] in sizes:
                counts[row["band_key"]] = counts.get(row["band_key"], 0) + 1
        return counts

    return {
        "fy": {"code": fy.code, "name": fy.long_fy},
        "month": month,
        "month_label": _month_label(month),
        "rows": rows,
        "band_labels": BAND_LABELS,
        "band_order": BAND_ORDER,
        "charts": {
            "xs_s": _chart_bands(XS_S_SIZES),
            "m_plus": _chart_bands(M_PLUS_SIZES),
        },
    }
