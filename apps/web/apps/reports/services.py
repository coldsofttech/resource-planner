from __future__ import annotations

from datetime import date as date_type
from datetime import datetime

from django.db import transaction
from django.http import HttpResponse

from apps.audit.services import AuditService
from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    PermissionException,
    ValidationException,
)
from apps.core.services import (
    AuditableService,
    ContextService,
    ExportService,
    FilterableQueryService,
)
from apps.reports import data_sources, selectors
from apps.reports import engine as report_engine
from apps.reports.constants import ReportVisualization
from apps.reports.models import (
    CustomReport,
    CustomReportShare,
    DemandCapacityReportConfig,
    KPIEstimateAccuracyConfig,
    Report,
)
from apps.reports.reports import demand_vs_capacity as dvc_report
from apps.reports.reports import kpi_estimate_accuracy as kpi_estimate_accuracy_report
from apps.reports.reports import monthly_finance_report as monthly_finance_report_report
from apps.reports.reports import monthly_wins as monthly_wins_report
from apps.reports.reports import sprint_forecast_vs_actuals as sfva_report
from apps.reports.reports import weekly_wins as weekly_wins_report


def _resolve_fy_month_scope(filters: dict) -> tuple:
    """Shared financial-year/month resolution used by any standard report
    scoped to a single FY + month (e.g. KPI Report, Monthly Finance Report)."""
    from apps.financial_years.selectors import get_financial_year_by_code

    fy_code = (filters.get("fy") or "").strip()
    if not fy_code:
        raise ValidationException("fy is required.")
    fy = get_financial_year_by_code(fy_code)
    if fy is None:
        raise NotFoundException(
            resource="FinancialYear", lookup_field="code", lookup_value=fy_code
        )

    month = (filters.get("month") or "").strip()
    if not month:
        raise ValidationException("month is required.")
    try:
        datetime.strptime(month, "%Y-%m")
    except ValueError:
        raise ValidationException("month must be in YYYY-MM format.") from None

    return fy, month


class ReportService(AuditableService, FilterableQueryService):
    """Read/manage the standard report catalog.

    Catalog rows are typically registered by the feature that implements a
    given standard report (e.g. Weekly Wins). This service exposes standard
    CRUD for completeness, though no UI currently drives create/update/delete.
    """

    _MODULE = "reports"
    _RESOURCE_TYPE = "report"

    filterable_fields: dict[str, str] = {"category": "category"}
    search_fields: list[str] = ["name", "description"]
    sortable_fields: list[str] = ["name", "sort_order", "created_at"]
    default_ordering: list[str] = ["sort_order", "name"]
    filter_active_by_default: bool = True

    def get_queryset(self):
        return selectors.get_all_reports()

    def _snapshot(self, obj: Report) -> dict:
        return {
            "code": obj.code,
            "slug": obj.slug,
            "name": obj.name,
            "category": obj.category,
            "icon": obj.icon,
            "is_active": obj.is_active,
            "sort_order": obj.sort_order,
        }

    def get(self, code: str | None = None, slug: str | None = None, **kwargs) -> Report:
        if slug is not None:
            obj = selectors.get_report_by_slug(slug)
        else:
            assert code is not None
            obj = selectors.get_report_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Report",
                lookup_field="slug" if slug is not None else "code",
                lookup_value=slug if slug is not None else code,
            )
        return obj

    @transaction.atomic
    def create(
        self,
        *,
        slug: str,
        name: str,
        description: str = "",
        category: str = "",
        icon: str = "bi-bar-chart",
        sort_order: int = 0,
        is_active: bool = True,
    ) -> Report:
        if selectors.report_slug_exists(slug):
            raise AlreadyExistsException(
                detail=f"A report with slug '{slug}' already exists."
            )
        obj = Report.objects.create(
            slug=slug,
            name=name,
            description=description,
            category=category,
            icon=icon,
            sort_order=sort_order,
            is_active=is_active,
            created_by=self.user,
            updated_by=self.user,
        )
        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj.code,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def update(self, code: str, **kwargs) -> Report:
        obj = self.get(code=code)
        before = self._snapshot(obj)
        update_fields: list[str] = ["updated_by", "updated_at"]

        if "slug" in kwargs:
            new_slug = kwargs["slug"]
            if new_slug != obj.slug and selectors.report_slug_exists(
                new_slug, exclude_pk=obj.pk
            ):
                raise AlreadyExistsException(
                    detail=f"A report with slug '{new_slug}' already exists."
                )
            obj.slug = new_slug
            update_fields.append("slug")

        for field in (
            "name",
            "description",
            "category",
            "icon",
            "sort_order",
            "is_active",
        ):
            if field in kwargs:
                setattr(obj, field, kwargs[field])
                update_fields.append(field)

        obj.updated_by = self.user
        obj.save(update_fields=update_fields)

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj.code,
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        obj = self.get(code=code)
        report_code = obj.code
        before = self._snapshot(obj)
        obj.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=report_code,
            before=before,
            actor=self.user,
        )

    @transaction.atomic
    def activate(self, code: str) -> Report:
        obj = self.get(code=code)
        if not obj.is_active:
            before = self._snapshot(obj)
            obj.is_active = True
            obj.updated_by = self.user
            obj.save(update_fields=["is_active", "updated_by", "updated_at"])
            AuditService.log_activate(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=obj.code,
                before=before,
                after=self._snapshot(obj),
                actor=self.user,
            )
        return obj

    @transaction.atomic
    def deactivate(self, code: str) -> Report:
        obj = self.get(code=code)
        if obj.is_active:
            before = self._snapshot(obj)
            obj.is_active = False
            obj.updated_by = self.user
            obj.save(update_fields=["is_active", "updated_by", "updated_at"])
            AuditService.log_deactivate(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=obj.code,
                before=before,
                after=self._snapshot(obj),
                actor=self.user,
            )
        return obj


class CustomReportService(AuditableService, FilterableQueryService):
    """Manage user-owned custom reports.

    Only the owner (or staff) may update/delete a custom report. Reports
    flagged `is_shared` are visible to all authenticated users in listings.
    """

    _MODULE = "reports"
    _RESOURCE_TYPE = "custom_report"

    filterable_fields: dict[str, str] = {"is_shared": "is_shared"}
    search_fields: list[str] = ["name", "description"]
    sortable_fields: list[str] = ["name", "created_at", "updated_at"]
    default_ordering: list[str] = ["-updated_at"]
    filter_active_by_default: bool = False

    def get_queryset(self):
        return selectors.get_visible_custom_reports(self.user)

    def _snapshot(self, obj: CustomReport) -> dict:
        return {
            "code": obj.code,
            "name": obj.name,
            "is_shared": obj.is_shared,
            "data_source": obj.data_source,
            "visualization": obj.visualization,
        }

    def _assert_owner(self, obj: CustomReport) -> None:
        if obj.owner_id != self.user.id and not self.user.is_staff:
            raise PermissionException(
                "You do not have permission to modify this custom report."
            )

    def _assert_can_edit(self, obj: CustomReport) -> None:
        if not obj.can_edit(self.user):
            raise PermissionException(
                "You do not have permission to modify this custom report."
            )

    def get(self, code: str, *args, **kwargs) -> CustomReport:
        obj = selectors.get_custom_report_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Custom report", lookup_field="code", lookup_value=code
            )
        if not obj.can_view(self.user):
            raise PermissionException(
                "You do not have permission to view this custom report."
            )
        return obj

    @transaction.atomic
    def create(
        self,
        *,
        name: str,
        description: str = "",
        is_shared: bool = False,
        data_source: str = "",
        visualization: str = ReportVisualization.TABLE,
        config: dict | None = None,
    ) -> CustomReport:
        obj = CustomReport.objects.create(
            name=name,
            description=description,
            is_shared=is_shared,
            data_source=data_source,
            visualization=visualization,
            config=config or {},
            owner=self.user,
            created_by=self.user,
            updated_by=self.user,
        )
        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj.code,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def update(self, code: str, **kwargs) -> CustomReport:
        obj = self.get(code=code)
        self._assert_can_edit(obj)
        before = self._snapshot(obj)
        update_fields: list[str] = ["updated_by", "updated_at"]

        for field in (
            "name",
            "description",
            "is_shared",
            "data_source",
            "visualization",
            "config",
        ):
            if field in kwargs:
                setattr(obj, field, kwargs[field])
                update_fields.append(field)

        obj.updated_by = self.user
        obj.save(update_fields=update_fields)

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj.code,
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        obj = self.get(code=code)
        self._assert_owner(obj)
        report_code = obj.code
        before = self._snapshot(obj)
        obj.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=report_code,
            before=before,
            actor=self.user,
        )


class CustomReportShareService(AuditableService):
    """Manage per-user view/edit shares on a `CustomReport`. Only the
    report's owner (or staff) may list/add/remove shares."""

    _MODULE = "reports"
    _RESOURCE_TYPE = "custom_report_share"

    def _get_report(self, report_code: str) -> CustomReport:
        obj = selectors.get_custom_report_by_code(report_code)
        if obj is None:
            raise NotFoundException(
                resource="Custom report", lookup_field="code", lookup_value=report_code
            )
        return obj

    def _assert_owner(self, report: CustomReport) -> None:
        if report.owner_id != self.user.id and not self.user.is_staff:
            raise PermissionException(
                "You do not have permission to manage sharing for this custom report."
            )

    def list_shares(self, report_code: str) -> list[CustomReportShare]:
        report = self._get_report(report_code)
        self._assert_owner(report)
        return list(selectors.get_custom_report_shares(report.id))

    @transaction.atomic
    def add_share(
        self, report_code: str, member_code: str, permission: str
    ) -> CustomReportShare:
        from apps.users.selectors import get_member_by_code

        report = self._get_report(report_code)
        self._assert_owner(report)

        profile = get_member_by_code(member_code)
        if profile is None:
            raise NotFoundException(
                resource="Member", lookup_field="code", lookup_value=member_code
            )
        if profile.user_id == report.owner_id:
            raise ValidationException("The report owner cannot be added as a share.")

        share, created = CustomReportShare.objects.update_or_create(
            report=report,
            user=profile.user,
            defaults={
                "permission": permission,
                "created_by": self.user,
                "updated_by": self.user,
            },
        )
        if not report.is_shared:
            report.is_shared = True
            report.save(update_fields=["is_shared", "updated_at"])

        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=report.code,
            after={"member": member_code, "permission": permission},
            actor=self.user,
        )
        return share

    @transaction.atomic
    def remove_share(self, report_code: str, member_code: str) -> None:
        from apps.users.selectors import get_member_by_code

        report = self._get_report(report_code)
        self._assert_owner(report)

        profile = get_member_by_code(member_code)
        if profile is None:
            raise NotFoundException(
                resource="Member", lookup_field="code", lookup_value=member_code
            )

        deleted, _ = CustomReportShare.objects.filter(
            report=report, user=profile.user
        ).delete()
        if deleted == 0:
            raise NotFoundException(
                resource="Custom report share",
                lookup_field="member",
                lookup_value=member_code,
            )

        if not selectors.get_custom_report_shares(report.id).exists():
            report.is_shared = False
            report.save(update_fields=["is_shared", "updated_at"])

        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=report.code,
            before={"member": member_code},
            actor=self.user,
        )


class CustomReportExecutionService(ContextService):
    """Data-source metadata + preview/execute for the Custom Report builder.

    All query-shaping logic lives in `apps.reports.engine` — this service
    only resolves permissions and the saved-report lookup around it.
    """

    def _visible_data_sources(self) -> list:
        return [
            ds
            for ds in data_sources.list_data_sources()
            if self.user is not None and self.user.has_module_perms(ds.app_label)
        ]

    def list_data_sources(self) -> list:
        return self._visible_data_sources()

    def _assert_source_permission(self, data_source_key: str) -> None:
        ds = data_sources.get_data_source(data_source_key)
        if ds is None:
            raise ValidationException(f"Unknown data source '{data_source_key}'.")
        if self.user is None or not self.user.has_module_perms(ds.app_label):
            raise PermissionException(
                "You do not have permission to use this data source."
            )

    def preview(self, *, data_source: str, visualization: str, config: dict) -> dict:
        self._assert_source_permission(data_source)
        return report_engine.execute(data_source, visualization, config or {})

    def execute_saved(
        self,
        *,
        code: str,
        data_source: str | None = None,
        visualization: str | None = None,
        config: dict | None = None,
    ) -> dict:
        obj = selectors.get_custom_report_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Custom report", lookup_field="code", lookup_value=code
            )
        if not obj.can_view(self.user):
            raise PermissionException(
                "You do not have permission to view this custom report."
            )

        resolved_source = data_source if data_source is not None else obj.data_source
        resolved_viz = visualization if visualization is not None else obj.visualization
        resolved_config = config if config is not None else obj.config

        if not resolved_source:
            raise ValidationException("This report has no data source configured yet.")

        self._assert_source_permission(resolved_source)
        return report_engine.execute(
            resolved_source, resolved_viz, resolved_config or {}
        )


class CustomReportExportService(ExportService):
    """Exports a saved custom report's currently configured table result.

    Only `table` visualizations are exportable — chart/card shapes aren't
    naturally tabular. `EXPORT_FILENAME`/`EXPORT_MODULE_NAME` are resolved
    per-report at export time rather than fixed class attributes.
    """

    EXPORT_FILENAME = "custom_report"
    EXPORT_MODULE_NAME = "Custom Report"

    def export(
        self,
        fields: list[str] | None = None,
        export_format: str = "csv",
        filters: dict | None = None,
    ) -> HttpResponse:
        code = (filters or {}).get("code")
        if not code:
            raise ValidationException("code is required.")

        obj = selectors.get_custom_report_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Custom report", lookup_field="code", lookup_value=code
            )
        if not obj.can_view(self.user):
            raise PermissionException(
                "You do not have permission to view this custom report."
            )
        if obj.visualization != ReportVisualization.TABLE:
            raise ValidationException(
                "Only table-visualization custom reports can be exported."
            )
        if not obj.data_source:
            raise ValidationException("This report has no data source configured yet.")

        result = report_engine.execute(obj.data_source, obj.visualization, obj.config)
        columns = result["columns"]
        rows = [
            {col["label"]: row.get(col["key"], "") for col in columns}
            for row in result["rows"]
        ]

        self.EXPORT_FILENAME = obj.code.lower().replace("-", "_")
        self.EXPORT_MODULE_NAME = obj.name

        fmt = export_format.lower()
        if fmt == "csv":
            return self._export_csv(rows)
        if fmt == "xlsx":
            return self._export_xlsx(rows)
        if fmt == "pdf":
            return self._export_pdf(rows)
        if fmt == "json":
            return self._export_json(rows)
        raise ValidationException(
            f"Unsupported export format '{export_format}'. "
            f"Allowed: csv, xlsx, pdf, json."
        )


def _parse_weekly_wins_filters(
    filters: dict,
) -> tuple[str, date_type | None, str | None]:
    """Shared query-param parsing for the Weekly Wins data + export actions."""
    mode = (filters.get("mode") or "").strip()
    if mode not in ("date", "week"):
        raise ValidationException("mode must be either 'date' or 'week'.")

    win_code = (filters.get("win") or "").strip() or None
    raw_date = (filters.get("date") or "").strip()
    resolved_date: date_type | None = None
    if raw_date:
        from django.utils.dateparse import parse_date

        resolved_date = parse_date(raw_date)
        if resolved_date is None:
            raise ValidationException("date must be a valid date in YYYY-MM-DD format.")

    if mode == "date" and resolved_date is None:
        raise ValidationException("date is required when mode is 'date'.")
    if mode == "week" and not win_code:
        raise ValidationException("win is required when mode is 'week'.")

    return mode, resolved_date, win_code


class WeeklyWinsReportService(ContextService):
    """Read-only data provider for the Weekly Wins standard report.

    All extraction/query logic lives in `apps.reports.reports.weekly_wins` —
    this service only resolves the requested week and raises when it can't be
    found.
    """

    def get_data(
        self, *, mode: str, date: date_type | None = None, win_code: str | None = None
    ) -> dict:
        win = weekly_wins_report.resolve_win(mode=mode, date=date, win_code=win_code)
        if win is None:
            raise NotFoundException(
                resource="Weekly Win",
                lookup_field="date" if mode == "date" else "win",
                lookup_value=str(date) if mode == "date" else win_code,
            )
        return weekly_wins_report.build_report_data(win)


class WeeklyWinsExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "team": "Team",
        "week": "Week",
        "date_range": "Date Range",
        "title": "Title",
        "description": "Description",
        "status_display": "Status",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "team",
        "week",
        "date_range",
        "title",
        "description",
        "status_display",
    ]
    EXPORT_FILENAME = "weekly_wins_report"
    EXPORT_MODULE_NAME = "Weekly Wins Report"

    def export(
        self,
        fields: list[str] | None = None,
        export_format: str = "csv",
        filters: dict | None = None,
    ) -> HttpResponse:
        mode, resolved_date, win_code = _parse_weekly_wins_filters(filters or {})

        win = weekly_wins_report.resolve_win(
            mode=mode, date=resolved_date, win_code=win_code
        )
        if win is None:
            raise NotFoundException(
                resource="Weekly Win",
                lookup_field="date" if mode == "date" else "win",
                lookup_value=str(resolved_date) if mode == "date" else win_code,
            )
        data = weekly_wins_report.build_report_data(win)

        resolved_fields = [
            f
            for f in (fields or self.DEFAULT_EXPORT_FIELDS)
            if f in self.EXPORT_FIELD_LABELS
        ] or self.DEFAULT_EXPORT_FIELDS
        rows = [
            {self.EXPORT_FIELD_LABELS[f]: entry.get(f, "") for f in resolved_fields}
            for entry in data["entries"]
        ]

        fmt = export_format.lower()
        if fmt == "csv":
            return self._export_csv(rows)
        if fmt == "xlsx":
            return self._export_xlsx(rows)
        if fmt == "pdf":
            return self._export_pdf(rows)
        if fmt == "json":
            return self._export_json(rows)
        raise ValidationException(
            f"Unsupported export format '{export_format}'. "
            f"Allowed: csv, xlsx, pdf, json."
        )


def _parse_monthly_wins_filters(filters: dict) -> str:
    """Shared query-param parsing for the Monthly Wins data + export actions."""
    code = (filters.get("code") or "").strip()
    if not code:
        raise ValidationException("code is required.")
    return code


def _build_monthly_wins_export_rows(data: dict) -> list[dict]:
    """Flattens Phase 1 rows and declared Phase 2 results into one dataset,
    distinguished by a leading 'Phase' column."""
    rows: list[dict] = []

    for row in data["phase1"]:
        rows.append(
            {
                "phase": "Phase 1",
                "label": row["label"],
                "phase1_votes": row["phase1_votes"],
                "status_display": row["status_display"],
                "team": row["team"],
                "week": row["week"],
                "date_range": row["date_range"],
                "win": row["win"],
                "category_display": row["category_display"],
            }
        )

    status_display = data["monthly_win"]["status_display"]
    for category_data in data["phase2"].values():
        for entry in category_data["entries"]:
            win_label = f"#{entry['rank']} — {entry['title']}: {entry['description']}"
            rows.append(
                {
                    "phase": "Phase 2",
                    "label": "",
                    "phase1_votes": "",
                    "status_display": status_display,
                    "team": entry["team"],
                    "week": "",
                    "date_range": "",
                    "win": win_label,
                    "category_display": category_data["label"],
                }
            )

    return rows


class MonthlyWinsReportService(ContextService):
    """Read-only data provider for the Monthly Wins standard report.

    All extraction/query logic lives in `apps.reports.reports.monthly_wins` —
    this service only resolves the requested Monthly Win and raises when it
    can't be found.
    """

    def get_data(self, *, code: str) -> dict:
        mw = monthly_wins_report.resolve_monthly_win(code=code)
        if mw is None:
            raise NotFoundException(
                resource="Monthly Win", lookup_field="code", lookup_value=code
            )
        return monthly_wins_report.build_report_data(mw)


class MonthlyWinsExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "phase": "Phase",
        "label": "Label",
        "phase1_votes": "Phase 1 Votes",
        "status_display": "Status",
        "team": "Team",
        "week": "Week",
        "date_range": "Date Range",
        "win": "Win",
        "category_display": "Selected As",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "phase",
        "label",
        "phase1_votes",
        "status_display",
        "team",
        "week",
        "date_range",
        "win",
        "category_display",
    ]
    EXPORT_FILENAME = "monthly_wins_report"
    EXPORT_MODULE_NAME = "Monthly Wins Report"

    def export(
        self,
        fields: list[str] | None = None,
        export_format: str = "csv",
        filters: dict | None = None,
    ) -> HttpResponse:
        code = _parse_monthly_wins_filters(filters or {})

        mw = monthly_wins_report.resolve_monthly_win(code=code)
        if mw is None:
            raise NotFoundException(
                resource="Monthly Win", lookup_field="code", lookup_value=code
            )
        data = monthly_wins_report.build_report_data(mw)

        resolved_fields = [
            f
            for f in (fields or self.DEFAULT_EXPORT_FIELDS)
            if f in self.EXPORT_FIELD_LABELS
        ] or self.DEFAULT_EXPORT_FIELDS
        raw_rows = _build_monthly_wins_export_rows(data)
        rows = [
            {self.EXPORT_FIELD_LABELS[f]: row.get(f, "") for f in resolved_fields}
            for row in raw_rows
        ]

        fmt = export_format.lower()
        if fmt == "csv":
            return self._export_csv(rows)
        if fmt == "xlsx":
            return self._export_xlsx(rows)
        if fmt == "pdf":
            return self._export_pdf(rows)
        if fmt == "json":
            return self._export_json(rows)
        raise ValidationException(
            f"Unsupported export format '{export_format}'. "
            f"Allowed: csv, xlsx, pdf, json."
        )


def _resolve_sprint_forecast_vs_actuals_scope(
    filters: dict,
) -> tuple:
    """Shared sprint/team resolution for the SFvA data + export actions."""
    from apps.sprints.selectors import get_sprint_by_code
    from apps.teams.selectors import get_team_by_code

    sprint_code = (filters.get("sprint") or "").strip()
    if not sprint_code:
        raise ValidationException("sprint is required.")

    sprint = get_sprint_by_code(sprint_code)
    if sprint is None:
        raise NotFoundException(
            resource="Sprint", lookup_field="code", lookup_value=sprint_code
        )

    team = None
    team_code = (filters.get("team") or "").strip()
    if team_code:
        team = get_team_by_code(team_code)
        if team is None:
            raise NotFoundException(
                resource="Team", lookup_field="code", lookup_value=team_code
            )

    return sprint, team


class SprintForecastVsActualsReportService(ContextService):
    """Read-only data provider for the Sprint Forecast vs. Actuals standard
    report. All extraction/aggregation logic lives in
    `apps.reports.reports.sprint_forecast_vs_actuals`."""

    def get_data(self, *, sprint_code: str, team_code: str | None = None) -> dict:
        sprint, team = _resolve_sprint_forecast_vs_actuals_scope(
            {"sprint": sprint_code, "team": team_code}
        )
        return sfva_report.build_report_data(sprint, team)


class SprintForecastVsActualsExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "team": "Team",
        "engineer": "Engineer",
        "label": "Label",
        "project": "Project",
        "programme": "Programme",
        "finance_type": "Finance Type",
        "forecast_days": "Forecast (Days)",
        "actual_days": "Actuals (Days)",
        "variance_days": "Variance (Days)",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "team",
        "engineer",
        "label",
        "project",
        "programme",
        "finance_type",
        "forecast_days",
        "actual_days",
        "variance_days",
    ]
    EXPORT_FILENAME = "sprint_forecast_vs_actuals_report"
    EXPORT_MODULE_NAME = "Sprint Forecast vs. Actuals Report"

    def export(
        self,
        fields: list[str] | None = None,
        export_format: str = "csv",
        filters: dict | None = None,
    ) -> HttpResponse:
        sprint, team = _resolve_sprint_forecast_vs_actuals_scope(filters or {})
        data = sfva_report.build_report_data(sprint, team)

        resolved_fields = [
            f
            for f in (fields or self.DEFAULT_EXPORT_FIELDS)
            if f in self.EXPORT_FIELD_LABELS
        ] or self.DEFAULT_EXPORT_FIELDS
        rows = [
            {self.EXPORT_FIELD_LABELS[f]: row.get(f, "") for f in resolved_fields}
            for row in data["all_rows"]
        ]

        fmt = export_format.lower()
        if fmt == "csv":
            return self._export_csv(rows)
        if fmt == "xlsx":
            return self._export_xlsx(rows)
        if fmt == "pdf":
            return self._export_pdf(rows)
        if fmt == "json":
            return self._export_json(rows)
        raise ValidationException(
            f"Unsupported export format '{export_format}'. "
            f"Allowed: csv, xlsx, pdf, json."
        )


def _resolve_kpi_estimate_accuracy_scope(filters: dict) -> tuple:
    """Shared financial-year/month resolution for the KPI Report — Estimate %
    Accuracy data + export actions."""
    return _resolve_fy_month_scope(filters)


class KPIEstimateAccuracyConfigService(AuditableService, FilterableQueryService):
    """Manage exception comments recorded against completed projects for the
    KPI Report — Estimate % Accuracy standard report, scoped to a month."""

    _MODULE = "reports"
    _RESOURCE_TYPE = "kpi_estimate_accuracy_config"

    filterable_fields: dict[str, str] = {"month": "month"}
    search_fields: list[str] = ["comment"]
    sortable_fields: list[str] = ["month", "created_at"]
    default_ordering: list[str] = ["month"]
    filter_active_by_default: bool = False

    def get_queryset(self):
        return selectors.get_kpi_estimate_accuracy_configs()

    def _snapshot(self, obj: KPIEstimateAccuracyConfig) -> dict:
        return {
            "code": obj.code,
            "project": obj.project.code,
            "month": obj.month,
            "comment": obj.comment,
        }

    def get(self, code: str, *args, **kwargs) -> KPIEstimateAccuracyConfig:
        obj = selectors.get_kpi_estimate_accuracy_config_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="KPI Estimate Accuracy Config",
                lookup_field="code",
                lookup_value=code,
            )
        return obj

    @transaction.atomic
    def create(
        self, *, project_code: str, month: str, comment: str
    ) -> KPIEstimateAccuracyConfig:
        from apps.projects import selectors as project_selectors

        project = project_selectors.get_project_by_code(project_code)
        if project is None:
            raise NotFoundException(
                resource="Project", lookup_field="code", lookup_value=project_code
            )
        if selectors.kpi_estimate_accuracy_config_exists(project.id, month):
            raise AlreadyExistsException(
                detail=(f"'{project.name}' already has a comment recorded for {month}.")
            )

        obj = KPIEstimateAccuracyConfig.objects.create(
            project=project,
            month=month,
            comment=comment,
            created_by=self.user,
            updated_by=self.user,
        )
        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj.code,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def update(self, code: str, **kwargs) -> KPIEstimateAccuracyConfig:
        obj = self.get(code=code)
        before = self._snapshot(obj)
        update_fields: list[str] = ["updated_by", "updated_at"]

        if "comment" in kwargs:
            obj.comment = kwargs["comment"]
            update_fields.append("comment")

        obj.updated_by = self.user
        obj.save(update_fields=update_fields)

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj.code,
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        obj = self.get(code=code)
        config_code = obj.code
        before = self._snapshot(obj)
        obj.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=config_code,
            before=before,
            actor=self.user,
        )


class KPIEstimateAccuracyReportService(ContextService):
    """Read-only data provider for the KPI Report — Estimate % Accuracy
    standard report. All extraction/aggregation logic lives in
    `apps.reports.reports.kpi_estimate_accuracy`."""

    def get_data(self, *, fy_code: str, month: str) -> dict:
        fy, resolved_month = _resolve_kpi_estimate_accuracy_scope(
            {"fy": fy_code, "month": month}
        )
        return kpi_estimate_accuracy_report.build_report_data(fy, resolved_month)


class KPIEstimateAccuracyExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "programme": "Programme",
        "project": "Project",
        "team": "Team",
        "collaborators_display": "Collaborators",
        "estimate_value": "Estimate Value",
        "estimate_value_with_contingency": "Estimate with Contingency",
        "total_cost_till_date": "Total Cost till Date",
        "tshirt_size": "T-Shirt Size",
        "accuracy_pct": "% Accuracy",
        "band": "Band",
        "comment": "Comment",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "programme",
        "project",
        "team",
        "collaborators_display",
        "estimate_value",
        "estimate_value_with_contingency",
        "total_cost_till_date",
        "tshirt_size",
        "accuracy_pct",
        "band",
        "comment",
    ]
    EXPORT_FILENAME = "kpi_estimate_accuracy_report"
    EXPORT_MODULE_NAME = "KPI Report - Estimate % Accuracy"

    def export(
        self,
        fields: list[str] | None = None,
        export_format: str = "csv",
        filters: dict | None = None,
    ) -> HttpResponse:
        fy, month = _resolve_kpi_estimate_accuracy_scope(filters or {})
        data = kpi_estimate_accuracy_report.build_report_data(fy, month)

        resolved_fields = [
            f
            for f in (fields or self.DEFAULT_EXPORT_FIELDS)
            if f in self.EXPORT_FIELD_LABELS
        ] or self.DEFAULT_EXPORT_FIELDS
        rows = [
            {self.EXPORT_FIELD_LABELS[f]: row.get(f, "") for f in resolved_fields}
            for row in data["rows"]
        ]

        fmt = export_format.lower()
        if fmt == "csv":
            return self._export_csv(rows)
        if fmt == "xlsx":
            return self._export_xlsx(rows)
        if fmt == "pdf":
            return self._export_pdf(rows)
        if fmt == "json":
            return self._export_json(rows)
        raise ValidationException(
            f"Unsupported export format '{export_format}'. "
            f"Allowed: csv, xlsx, pdf, json."
        )


class DemandCapacityReportConfigService(AuditableService, FilterableQueryService):
    """Manage Programme → Category mappings for the Demand vs. Capacity
    standard report, scoped to a single Resource Plan version."""

    _MODULE = "reports"
    _RESOURCE_TYPE = "demand_capacity_report_config"

    filterable_fields: dict[str, str] = {
        "plan": "plan__code",
        "version": "plan_version__version",
        "category": "category",
    }
    search_fields: list[str] = ["category"]
    sortable_fields: list[str] = ["category", "created_at"]
    default_ordering: list[str] = ["category"]
    filter_active_by_default: bool = False

    def get_queryset(self):
        return selectors.get_demand_capacity_configs()

    def _snapshot(self, obj: DemandCapacityReportConfig) -> dict:
        return {
            "code": obj.code,
            "plan": obj.plan.code,
            "version": obj.plan_version.version,
            "programme": obj.programme.code,
            "category": obj.category,
        }

    def get(self, code: str, *args, **kwargs) -> DemandCapacityReportConfig:
        obj = selectors.get_demand_capacity_config_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Demand vs. Capacity Config",
                lookup_field="code",
                lookup_value=code,
            )
        return obj

    @transaction.atomic
    def create(
        self, *, plan_code: str, version: int, programme_code: str, category: str
    ) -> DemandCapacityReportConfig:
        from apps.projects import selectors as project_selectors
        from apps.resource_plans import selectors as resource_plan_selectors

        plan = resource_plan_selectors.get_resource_plan_by_code(plan_code)
        if plan is None:
            raise NotFoundException(
                resource="Plan", lookup_field="code", lookup_value=plan_code
            )
        plan_version = resource_plan_selectors.get_version_by_number(plan, version)
        if plan_version is None:
            raise NotFoundException(
                resource="PlanVersion", lookup_field="version", lookup_value=version
            )
        programme = project_selectors.get_programme_by_code(programme_code)
        if programme is None:
            raise NotFoundException(
                resource="Programme", lookup_field="code", lookup_value=programme_code
            )
        if selectors.demand_capacity_config_exists(plan_version.id, programme.id):
            raise AlreadyExistsException(
                detail=(
                    f"Programme '{programme.name}' is already mapped to a "
                    f"category for this plan version."
                )
            )

        obj = DemandCapacityReportConfig.objects.create(
            plan=plan,
            plan_version=plan_version,
            programme=programme,
            category=category,
            created_by=self.user,
            updated_by=self.user,
        )
        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj.code,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def update(self, code: str, **kwargs) -> DemandCapacityReportConfig:
        from apps.projects import selectors as project_selectors

        obj = self.get(code=code)
        before = self._snapshot(obj)
        update_fields: list[str] = ["updated_by", "updated_at"]

        if "programme_code" in kwargs:
            programme = project_selectors.get_programme_by_code(
                kwargs["programme_code"]
            )
            if programme is None:
                raise NotFoundException(
                    resource="Programme",
                    lookup_field="code",
                    lookup_value=kwargs["programme_code"],
                )
            programme_changed = programme.id != obj.programme_id
            if programme_changed and selectors.demand_capacity_config_exists(
                obj.plan_version_id, programme.id, exclude_pk=obj.pk
            ):
                raise AlreadyExistsException(
                    detail=(
                        f"Programme '{programme.name}' is already mapped to a "
                        f"category for this plan version."
                    )
                )
            obj.programme = programme
            update_fields.append("programme")

        if "category" in kwargs:
            obj.category = kwargs["category"]
            update_fields.append("category")

        obj.updated_by = self.user
        obj.save(update_fields=update_fields)

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj.code,
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        obj = self.get(code=code)
        config_code = obj.code
        before = self._snapshot(obj)
        obj.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=config_code,
            before=before,
            actor=self.user,
        )


def _resolve_demand_vs_capacity_scope(filters: dict) -> tuple:
    """Shared plan/version/team/employment-type resolution for the Demand vs.
    Capacity data + export actions."""
    from apps.employment_types.selectors import get_employment_type_by_code
    from apps.resource_plans import selectors as resource_plan_selectors
    from apps.teams.selectors import get_team_by_code

    plan_code = (filters.get("plan") or "").strip()
    if not plan_code:
        raise ValidationException("plan is required.")
    plan = resource_plan_selectors.get_resource_plan_by_code(plan_code)
    if plan is None:
        raise NotFoundException(
            resource="Plan", lookup_field="code", lookup_value=plan_code
        )

    version_raw = filters.get("version")
    try:
        version_number = int(str(version_raw))
    except (TypeError, ValueError):
        raise ValidationException(
            "version is required and must be an integer."
        ) from None
    plan_version = resource_plan_selectors.get_version_by_number(plan, version_number)
    if plan_version is None:
        raise NotFoundException(
            resource="PlanVersion", lookup_field="version", lookup_value=version_number
        )

    team = None
    team_code = (filters.get("team") or "").strip()
    if team_code:
        team = get_team_by_code(team_code)
        if team is None:
            raise NotFoundException(
                resource="Team", lookup_field="code", lookup_value=team_code
            )

    employment_type = None
    employment_type_code = (filters.get("employment_type") or "").strip()
    if employment_type_code:
        employment_type = get_employment_type_by_code(employment_type_code)
        if employment_type is None:
            raise NotFoundException(
                resource="EmploymentType",
                lookup_field="code",
                lookup_value=employment_type_code,
            )

    return plan, plan_version, team, employment_type


class DemandVsCapacityReportService(ContextService):
    """Read-only data provider for the Demand vs. Capacity standard report.
    All extraction/aggregation logic lives in
    `apps.reports.reports.demand_vs_capacity`."""

    def get_data(
        self,
        *,
        plan_code: str,
        version: int,
        team_code: str | None = None,
        employment_type_code: str | None = None,
    ) -> dict:
        plan, plan_version, team, employment_type = _resolve_demand_vs_capacity_scope(
            {
                "plan": plan_code,
                "version": version,
                "team": team_code,
                "employment_type": employment_type_code,
            }
        )
        return dvc_report.build_report_data(
            plan, plan_version, team=team, employment_type=employment_type
        )


class DemandVsCapacityExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "scope": "Scope",
        "row_label": "Row",
        "row_type": "Type",
        "month": "Month",
        "value": "Value",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "scope",
        "row_label",
        "row_type",
        "month",
        "value",
    ]
    EXPORT_FILENAME = "demand_vs_capacity_report"
    EXPORT_MODULE_NAME = "Demand vs. Capacity Report"

    @staticmethod
    def _flatten(
        scope_label: str, rows: list[dict], month_labels: dict[str, str]
    ) -> list[dict]:
        flat = []
        for row in rows:
            for month, value in row["values"].items():
                flat.append(
                    {
                        "scope": scope_label,
                        "row_label": row["label"],
                        "row_type": row["type"],
                        "month": month_labels.get(month, month),
                        "value": value if value is not None else "",
                    }
                )
        return flat

    def export(
        self,
        fields: list[str] | None = None,
        export_format: str = "csv",
        filters: dict | None = None,
    ) -> HttpResponse:
        plan, plan_version, team, employment_type = _resolve_demand_vs_capacity_scope(
            filters or {}
        )
        data = dvc_report.build_report_data(
            plan, plan_version, team=team, employment_type=employment_type
        )

        raw_rows = self._flatten(
            "All Teams", data["overall"]["rows"], data["month_labels"]
        )
        for block in data["teams"]:
            raw_rows.extend(
                self._flatten(
                    block["team"]["name"], block["rows"], data["month_labels"]
                )
            )

        resolved_fields = [
            f
            for f in (fields or self.DEFAULT_EXPORT_FIELDS)
            if f in self.EXPORT_FIELD_LABELS
        ] or self.DEFAULT_EXPORT_FIELDS
        rows = [
            {self.EXPORT_FIELD_LABELS[f]: row.get(f, "") for f in resolved_fields}
            for row in raw_rows
        ]

        fmt = export_format.lower()
        if fmt == "csv":
            return self._export_csv(rows)
        if fmt == "xlsx":
            return self._export_xlsx(rows)
        if fmt == "pdf":
            return self._export_pdf(rows)
        if fmt == "json":
            return self._export_json(rows)
        raise ValidationException(
            f"Unsupported export format '{export_format}'. "
            f"Allowed: csv, xlsx, pdf, json."
        )


class MonthlyFinanceReportService(ContextService):
    """Read-only data provider for the Monthly Finance Report standard
    report. All extraction/aggregation logic lives in
    `apps.reports.reports.monthly_finance_report`."""

    def get_data(self, *, fy_code: str, month: str) -> dict:
        fy, resolved_month = _resolve_fy_month_scope({"fy": fy_code, "month": month})
        return monthly_finance_report_report.build_report_data(fy, resolved_month)


class MonthlyFinanceReportExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "project_code": "Project Code",
        "project": "Project",
        "programme": "Programme",
        "total_days": "Total Days",
        "total_cost": "Total Cost",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "project_code",
        "project",
        "programme",
        "total_days",
        "total_cost",
    ]
    EXPORT_FILENAME = "monthly_finance_report"
    EXPORT_MODULE_NAME = "Monthly Finance Report"

    def export(
        self,
        fields: list[str] | None = None,
        export_format: str = "csv",
        filters: dict | None = None,
    ) -> HttpResponse:
        fy, month = _resolve_fy_month_scope(filters or {})
        data = monthly_finance_report_report.build_report_data(fy, month)

        resolved_fields = [
            f
            for f in (fields or self.DEFAULT_EXPORT_FIELDS)
            if f in self.EXPORT_FIELD_LABELS
        ] or self.DEFAULT_EXPORT_FIELDS
        rows = [
            {self.EXPORT_FIELD_LABELS[f]: row.get(f, "") for f in resolved_fields}
            for row in data["rows"]
        ]

        fmt = export_format.lower()
        if fmt == "csv":
            return self._export_csv(rows)
        if fmt == "xlsx":
            return self._export_xlsx(rows)
        if fmt == "pdf":
            return self._export_pdf(rows)
        if fmt == "json":
            return self._export_json(rows)
        raise ValidationException(
            f"Unsupported export format '{export_format}'. "
            f"Allowed: csv, xlsx, pdf, json."
        )
