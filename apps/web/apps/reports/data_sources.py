"""Registry of reportable data sources for the Custom Report builder.

Each `DataSource` maps a builder-facing key to a real Django model, plus the
set of fields a report can select/filter/group/aggregate on. Joins are not a
separate mechanism — a field's `key` is a normal Django ORM lookup path
(`__`-traversal), so `apps.reports.engine.execute()` can pass it straight
into `.values()`/`.filter()`/`.annotate()` and the ORM performs the join.

Kept separate from `engine.py` so the registry (declarative data) stays
readable independently of the query execution logic that consumes it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from django.apps import apps as django_apps
from django.db.models import Model

from apps.reports.constants import FieldType


@dataclass(frozen=True)
class ReportField:
    key: str
    label: str
    type: str
    filterable: bool = True
    groupable: bool = False
    aggregatable: bool = False
    choices: list[tuple[str, str]] | None = None


@dataclass(frozen=True)
class DataSource:
    key: str
    label: str
    app_label: str
    model_name: str
    fields: list[ReportField] = field(default_factory=list)
    base_filters: list[dict] = field(default_factory=list)

    def get_model(self) -> type[Model]:
        return django_apps.get_model(self.app_label, self.model_name)

    def get_field(self, field_key: str) -> ReportField | None:
        return next((f for f in self.fields if f.key == field_key), None)


def _f(
    key: str,
    label: str,
    type_: str,
    *,
    filterable: bool = True,
    groupable: bool = False,
    aggregatable: bool = False,
    choices: list[tuple[str, str]] | None = None,
) -> ReportField:
    return ReportField(
        key=key,
        label=label,
        type=type_,
        filterable=filterable,
        groupable=groupable,
        aggregatable=aggregatable,
        choices=choices,
    )


_CONFIDENCE_CHOICES = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
    ("very_high", "Very High"),
]
_PRIORITY_CHOICES = _CONFIDENCE_CHOICES
_ESTIMATE_STATUS_CHOICES = [
    ("DRAFT", "Draft"),
    ("SUBMITTED", "Submitted"),
    ("APPROVED", "Approved"),
    ("REJECTED", "Rejected"),
]
_RECHARGE_TYPE_CHOICES = [("forecast", "Forecast"), ("actual", "Actual")]

DATA_SOURCES: list[DataSource] = [
    DataSource(
        key="projects",
        label="Projects",
        app_label="projects",
        model_name="Project",
        fields=[
            _f("name", "Name", FieldType.TEXT, groupable=True),
            _f("display_name", "Display Name", FieldType.TEXT),
            _f("status__name", "Status", FieldType.TEXT, groupable=True),
            _f("sub_status__name", "Sub-Status", FieldType.TEXT, groupable=True),
            _f("project_type__name", "Project Type", FieldType.TEXT, groupable=True),
            _f("programme__name", "Programme", FieldType.TEXT, groupable=True),
            _f("assigned_team__name", "Team", FieldType.TEXT, groupable=True),
            _f(
                "confidence",
                "Confidence",
                FieldType.CHOICE,
                groupable=True,
                choices=_CONFIDENCE_CHOICES,
            ),
            _f(
                "priority",
                "Priority",
                FieldType.CHOICE,
                groupable=True,
                choices=_PRIORITY_CHOICES,
            ),
            _f("efforts_issued", "Efforts Issued", FieldType.BOOLEAN, groupable=True),
            _f(
                "run_cost_applies",
                "Run Cost Applies",
                FieldType.BOOLEAN,
                groupable=True,
            ),
            _f("commitment_date", "Commitment Date", FieldType.DATE),
            _f("start_date", "Start Date", FieldType.DATE),
            _f("end_date", "End Date", FieldType.DATE),
            _f("is_active", "Active", FieldType.BOOLEAN, groupable=True),
            _f("created_at", "Created At", FieldType.DATETIME),
        ],
    ),
    DataSource(
        key="programmes",
        label="Programmes",
        app_label="projects",
        model_name="Programme",
        fields=[
            _f("name", "Name", FieldType.TEXT, groupable=True),
            _f("description", "Description", FieldType.TEXT, filterable=False),
            _f("is_protected", "Protected", FieldType.BOOLEAN, groupable=True),
            _f("is_active", "Active", FieldType.BOOLEAN, groupable=True),
            _f("created_at", "Created At", FieldType.DATETIME),
        ],
    ),
    DataSource(
        key="project_estimates",
        label="Project Estimates",
        app_label="projects",
        model_name="ProjectEstimate",
        fields=[
            _f("project__name", "Project", FieldType.TEXT, groupable=True),
            _f("project__programme__name", "Programme", FieldType.TEXT, groupable=True),
            _f("version", "Version", FieldType.NUMBER, aggregatable=True),
            _f(
                "status",
                "Status",
                FieldType.CHOICE,
                groupable=True,
                choices=_ESTIMATE_STATUS_CHOICES,
            ),
            _f("estimate_days", "Estimate Days", FieldType.NUMBER, aggregatable=True),
            _f(
                "contingency_percentage",
                "Contingency %",
                FieldType.NUMBER,
                aggregatable=True,
            ),
            _f("day_rate", "Day Rate", FieldType.NUMBER, aggregatable=True),
            _f("is_active", "Active", FieldType.BOOLEAN, groupable=True),
            _f("created_at", "Created At", FieldType.DATETIME),
        ],
    ),
    DataSource(
        key="project_budgets",
        label="Project Budgets",
        app_label="projects",
        model_name="ProjectBudget",
        fields=[
            _f("project__name", "Project", FieldType.TEXT, groupable=True),
            _f("project__programme__name", "Programme", FieldType.TEXT, groupable=True),
            _f(
                "financial_year__short_fy",
                "Financial Year",
                FieldType.TEXT,
                groupable=True,
            ),
            _f(
                "allocated_budget",
                "Allocated Budget",
                FieldType.NUMBER,
                aggregatable=True,
            ),
            _f("refined_budget", "Refined Budget", FieldType.NUMBER, aggregatable=True),
            _f("created_at", "Created At", FieldType.DATETIME),
        ],
    ),
    DataSource(
        key="project_sprint_actuals",
        label="Project Sprint Actuals",
        app_label="projects",
        model_name="ProjectSprintActual",
        fields=[
            _f("project__name", "Project", FieldType.TEXT, groupable=True),
            _f("project__programme__name", "Programme", FieldType.TEXT, groupable=True),
            _f("project_code__value", "Project Code", FieldType.TEXT, groupable=True),
            _f("sprint__name", "Sprint", FieldType.TEXT, groupable=True),
            _f("sprint__month", "Month", FieldType.TEXT, groupable=True),
            _f(
                "sprint__financial_year__short_fy",
                "Financial Year",
                FieldType.TEXT,
                groupable=True,
            ),
            _f("label__label", "Label", FieldType.TEXT, groupable=True),
            _f("total_days", "Total Days", FieldType.NUMBER, aggregatable=True),
            _f("total_cost", "Total Cost", FieldType.NUMBER, aggregatable=True),
            _f("created_at", "Created At", FieldType.DATETIME),
        ],
    ),
    DataSource(
        key="teams",
        label="Teams",
        app_label="teams",
        model_name="Team",
        fields=[
            _f("name", "Name", FieldType.TEXT, groupable=True),
            _f("description", "Description", FieldType.TEXT, filterable=False),
            _f("is_active", "Active", FieldType.BOOLEAN, groupable=True),
            _f("created_at", "Created At", FieldType.DATETIME),
        ],
    ),
    DataSource(
        key="sprints",
        label="Sprints",
        app_label="sprints",
        model_name="Sprint",
        fields=[
            _f("name", "Name", FieldType.TEXT, groupable=True),
            _f("sprint_number", "Sprint Number", FieldType.NUMBER, aggregatable=True),
            _f(
                "financial_year__short_fy",
                "Financial Year",
                FieldType.TEXT,
                groupable=True,
            ),
            _f("start_date", "Start Date", FieldType.DATE),
            _f("end_date", "End Date", FieldType.DATE),
            _f("month", "Month", FieldType.TEXT, groupable=True),
            _f("status", "Status", FieldType.CHOICE, groupable=True),
            _f("is_closed", "Closed", FieldType.BOOLEAN, groupable=True),
            _f("is_overridden", "Overridden", FieldType.BOOLEAN, groupable=True),
            _f("created_at", "Created At", FieldType.DATETIME),
        ],
    ),
    DataSource(
        key="financial_years",
        label="Financial Years",
        app_label="financial_years",
        model_name="FinancialYear",
        fields=[
            _f("long_fy", "Financial Year", FieldType.TEXT, groupable=True),
            _f("short_fy", "Short FY", FieldType.TEXT, groupable=True),
            _f("start_date", "Start Date", FieldType.DATE),
            _f("end_date", "End Date", FieldType.DATE),
            _f("span_days", "Span (Days)", FieldType.NUMBER, aggregatable=True),
            _f("status", "Status", FieldType.CHOICE, groupable=True),
            _f("is_active", "Active", FieldType.BOOLEAN, groupable=True),
            _f("created_at", "Created At", FieldType.DATETIME),
        ],
    ),
    DataSource(
        key="recharge_details",
        label="Recharge Details",
        app_label="recharges",
        model_name="RechargeDetail",
        fields=[
            _f("sprint__name", "Sprint", FieldType.TEXT, groupable=True),
            _f("sprint__month", "Month", FieldType.TEXT, groupable=True),
            _f(
                "sprint__financial_year__short_fy",
                "Financial Year",
                FieldType.TEXT,
                groupable=True,
            ),
            _f("team__name", "Team", FieldType.TEXT, groupable=True),
            _f("assignee__display_name", "Assignee", FieldType.TEXT, groupable=True),
            _f("programme__name", "Programme", FieldType.TEXT, groupable=True),
            _f("project__name", "Project", FieldType.TEXT, groupable=True),
            _f("label__label", "Label", FieldType.TEXT, groupable=True),
            _f("recharge_type__name", "Recharge Type", FieldType.TEXT, groupable=True),
            _f(
                "type",
                "Forecast/Actual",
                FieldType.CHOICE,
                groupable=True,
                choices=_RECHARGE_TYPE_CHOICES,
            ),
            _f("jira_id", "Jira ID", FieldType.TEXT),
            _f("title", "Title", FieldType.TEXT, filterable=False),
            _f("total_days", "Total Days", FieldType.NUMBER, aggregatable=True),
            _f("total_cost", "Total Cost", FieldType.NUMBER, aggregatable=True),
            _f("created_at", "Created At", FieldType.DATETIME),
        ],
    ),
]

_BY_KEY: dict[str, DataSource] = {ds.key: ds for ds in DATA_SOURCES}


def list_data_sources() -> list[DataSource]:
    return DATA_SOURCES


def get_data_source(key: str) -> DataSource | None:
    return _BY_KEY.get(key)
