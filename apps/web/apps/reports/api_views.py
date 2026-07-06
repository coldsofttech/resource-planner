from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet, ExportMixin
from apps.reports import engine as report_engine
from apps.reports.data_sources import get_data_source
from apps.reports.serializers import (
    CustomReportCreateSerializer,
    CustomReportDetailSerializer,
    CustomReportExecuteRequestSerializer,
    CustomReportListSerializer,
    CustomReportPreviewRequestSerializer,
    CustomReportShareCreateSerializer,
    CustomReportShareListSerializer,
    CustomReportUpdateSerializer,
    DataSourceSerializer,
    DemandCapacityReportConfigCreateSerializer,
    DemandCapacityReportConfigDetailSerializer,
    DemandCapacityReportConfigListSerializer,
    DemandCapacityReportConfigUpdateSerializer,
    DemandVsCapacityDataSerializer,
    DemandVsCapacityQuerySerializer,
    KPIEstimateAccuracyConfigCreateSerializer,
    KPIEstimateAccuracyConfigDetailSerializer,
    KPIEstimateAccuracyConfigListSerializer,
    KPIEstimateAccuracyConfigUpdateSerializer,
    KPIEstimateAccuracyDataSerializer,
    KPIEstimateAccuracyQuerySerializer,
    MonthlyFinanceReportDataSerializer,
    MonthlyFinanceReportQuerySerializer,
    MonthlyWinsDataSerializer,
    MonthlyWinsQuerySerializer,
    ReportCreateSerializer,
    ReportDetailSerializer,
    ReportListSerializer,
    ReportUpdateSerializer,
    SprintForecastVsActualsDataSerializer,
    SprintForecastVsActualsQuerySerializer,
    WeeklyWinsDataSerializer,
    WeeklyWinsQuerySerializer,
)
from apps.reports.services import (
    CustomReportExecutionService,
    CustomReportExportService,
    CustomReportService,
    CustomReportShareService,
    DemandCapacityReportConfigService,
    DemandVsCapacityExportService,
    DemandVsCapacityReportService,
    KPIEstimateAccuracyConfigService,
    KPIEstimateAccuracyExportService,
    KPIEstimateAccuracyReportService,
    MonthlyFinanceReportExportService,
    MonthlyFinanceReportService,
    MonthlyWinsExportService,
    MonthlyWinsReportService,
    ReportService,
    SprintForecastVsActualsExportService,
    SprintForecastVsActualsReportService,
    WeeklyWinsExportService,
    WeeklyWinsReportService,
)


@extend_schema(tags=["Reports"])
class ReportViewSet(BaseViewSet):
    """Standard report catalog. Rows are registered by the feature that
    implements a given standard report — no create/edit UI exists yet."""

    service_class = ReportService

    def get_permissions(self):
        action_perms = {
            "list": "reports.view_report",
            "retrieve": "reports.view_report",
            "create": "reports.add_report",
            "partial_update": "reports.change_report",
            "destroy": "reports.delete_report",
            "activate": "reports.change_report",
            "deactivate": "reports.change_report",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return ReportListSerializer

    def get_retrieve_serializer_class(self):
        return ReportDetailSerializer

    def get_create_serializer_class(self):
        return ReportCreateSerializer

    def get_update_serializer_class(self):
        return ReportUpdateSerializer

    @extend_schema(
        summary="List standard reports",
        description=(
            "Returns a paginated list of the standard report catalog. "
            "Defaults to active reports only."
        ),
        responses={200: ReportListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /reports/standard/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a standard report",
        responses={
            200: ReportDetailSerializer,
            404: OpenApiResponse(description="Report not found."),
        },
    )
    def retrieve(self, request: Request, slug=None):
        """GET /reports/standard/<slug>/"""
        obj = self.service.get(slug=slug)
        serializer = ReportDetailSerializer(obj, context=self.get_serializer_context())
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Register a standard report",
        request=ReportCreateSerializer,
        responses={
            201: ReportDetailSerializer,
            409: OpenApiResponse(description="A report with this slug already exists."),
        },
    )
    def create(self, request: Request):
        """POST /reports/standard/"""
        return super().create(request)

    @extend_schema(
        summary="Update a standard report",
        request=ReportUpdateSerializer,
        responses={
            200: ReportDetailSerializer,
            404: OpenApiResponse(description="Report not found."),
        },
    )
    def partial_update(self, request: Request, slug=None):
        """PATCH /reports/standard/<slug>/"""
        serializer = ReportUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        existing = self.service.get(slug=slug)
        obj = self.service.update(code=existing.code, **serializer.validated_data)
        data = ReportDetailSerializer(obj, context=self.get_serializer_context()).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete a standard report",
        responses={
            204: OpenApiResponse(description="Report deleted successfully."),
            404: OpenApiResponse(description="Report not found."),
        },
    )
    def destroy(self, request: Request, slug=None):
        """DELETE /reports/standard/<slug>/"""
        obj = self.service.get(slug=slug)
        self.service.delete(code=obj.code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )

    @extend_schema(
        summary="Activate a standard report",
        responses={
            200: ReportDetailSerializer,
            404: OpenApiResponse(description="Report not found."),
        },
    )
    def activate(self, request: Request, slug=None):
        """POST /reports/standard/<slug>/activate/"""
        obj = self.service.get(slug=slug)
        obj = self.service.activate(code=obj.code)
        data = ReportDetailSerializer(obj, context=self.get_serializer_context()).data
        return self.response(
            data=data,
            message=self.get_activate_custom_message(),
            status_code=self.get_activate_status_code(),
        )

    @extend_schema(
        summary="Deactivate a standard report",
        responses={
            200: ReportDetailSerializer,
            404: OpenApiResponse(description="Report not found."),
        },
    )
    def deactivate(self, request: Request, slug=None):
        """POST /reports/standard/<slug>/deactivate/"""
        obj = self.service.get(slug=slug)
        obj = self.service.deactivate(code=obj.code)
        data = ReportDetailSerializer(obj, context=self.get_serializer_context()).data
        return self.response(
            data=data,
            message=self.get_deactivate_custom_message(),
            status_code=self.get_deactivate_status_code(),
        )


@extend_schema(tags=["Reports"])
class CustomReportViewSet(ExportMixin, BaseViewSet):
    """User-owned custom reports, backed by the data-source/query-engine
    builder (`apps.reports.data_sources` + `apps.reports.engine`)."""

    service_class = CustomReportService
    export_service_class = CustomReportExportService

    @property
    def execution_service(self) -> CustomReportExecutionService:
        if not hasattr(self, "_execution_service"):
            self._execution_service = CustomReportExecutionService(
                user=self.request.user, request=self.request
            )
        return self._execution_service

    @property
    def share_service(self) -> CustomReportShareService:
        if not hasattr(self, "_share_service"):
            self._share_service = CustomReportShareService(
                user=self.request.user, request=self.request
            )
        return self._share_service

    def get_permissions(self):
        action_perms = {
            "list": "reports.view_customreport",
            "retrieve": "reports.view_customreport",
            "create": "reports.add_customreport",
            "partial_update": "reports.change_customreport",
            "destroy": "reports.delete_customreport",
            "data_sources": "reports.view_customreport",
            "preview": "reports.view_customreport",
            "execute": "reports.view_customreport",
            "export_specs": "reports.view_customreport",
            "export": "reports.view_customreport",
            "share": "reports.change_customreport",
            "share_detail": "reports.change_customreport",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return CustomReportListSerializer

    def get_retrieve_serializer_class(self):
        return CustomReportDetailSerializer

    def get_create_serializer_class(self):
        return CustomReportCreateSerializer

    def get_update_serializer_class(self):
        return CustomReportUpdateSerializer

    @extend_schema(
        summary="List custom reports",
        description=(
            "Returns custom reports owned by, or shared with, the current user."
        ),
        responses={200: CustomReportListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /reports/custom/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a custom report",
        responses={
            200: CustomReportDetailSerializer,
            404: OpenApiResponse(description="Custom report not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /reports/custom/<code>/"""
        obj = self.service.get(code=code)
        serializer = CustomReportDetailSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Create a custom report",
        request=CustomReportCreateSerializer,
        responses={201: CustomReportDetailSerializer},
    )
    def create(self, request: Request):
        """POST /reports/custom/"""
        return super().create(request)

    @extend_schema(
        summary="Update a custom report",
        request=CustomReportUpdateSerializer,
        responses={
            200: CustomReportDetailSerializer,
            403: OpenApiResponse(description="Not the owner of this custom report."),
            404: OpenApiResponse(description="Custom report not found."),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /reports/custom/<code>/"""
        serializer = CustomReportUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(code=code, **serializer.validated_data)
        data = CustomReportDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete a custom report",
        responses={
            204: OpenApiResponse(description="Custom report deleted successfully."),
            403: OpenApiResponse(description="Not the owner of this custom report."),
            404: OpenApiResponse(description="Custom report not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /reports/custom/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )

    @extend_schema(
        summary="List available data sources",
        description=(
            "Returns the reportable data sources (and their fields) the "
            "current user has module-level permission to browse."
        ),
        responses={200: DataSourceSerializer(many=True)},
    )
    def data_sources(self, request: Request):
        """GET /reports/custom/data-sources/"""
        sources = self.execution_service.list_data_sources()
        serializer = DataSourceSerializer(
            sources, many=True, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Preview an ad-hoc custom report",
        description=(
            "Executes a data source/visualization/config combination without "
            "saving it — used by the builder to live-preview changes."
        ),
        request=CustomReportPreviewRequestSerializer,
        responses={
            200: OpenApiResponse(
                description="Execution result (shape varies by visualization)."
            ),
            403: OpenApiResponse(description="No permission to use this data source."),
            422: OpenApiResponse(description="Validation error."),
        },
    )
    def preview(self, request: Request):
        """POST /reports/custom/preview/"""
        serializer = CustomReportPreviewRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        result = self.execution_service.preview(
            data_source=validated["data_source"],
            visualization=validated["visualization"],
            config=validated.get("config") or {},
        )
        return self.response(data=result)

    @extend_schema(
        summary="Execute a saved custom report",
        description=(
            "Runs the saved report's configuration. Optionally override "
            "`data_source`/`visualization`/`config` in the body to preview "
            "unsaved builder changes against a report you can already view."
        ),
        request=CustomReportExecuteRequestSerializer,
        responses={
            200: OpenApiResponse(
                description="Execution result (shape varies by visualization)."
            ),
            404: OpenApiResponse(description="Custom report not found."),
            422: OpenApiResponse(description="Validation error."),
        },
    )
    def execute(self, request: Request, code=None):
        """POST /reports/custom/<code>/execute/"""
        serializer = CustomReportExecuteRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data
        result = self.execution_service.execute_saved(
            code=code,
            data_source=validated.get("data_source") or None,
            visualization=validated.get("visualization") or None,
            config=validated.get("config") or None,
        )
        return self.response(data=result)

    @extend_schema(
        summary="Export column specs for a saved custom report",
        parameters=[
            OpenApiParameter(
                name="code", type=str, location=OpenApiParameter.QUERY, required=True
            ),
        ],
        responses={200: OpenApiResponse(description="{'columns': [...]}")},
    )
    def export_specs(self, request: Request, **kwargs):
        """GET /reports/custom/export/specs/?code=..."""
        code = request.query_params.get("code")
        obj = self.service.get(code=code) if code else None
        columns = []
        if obj is not None and obj.data_source:
            ds = get_data_source(obj.data_source)
            if ds is not None:
                columns = report_engine.table_columns(ds, obj.config or {})
        return self.response(data={"columns": columns})

    @extend_schema(
        summary="List shares for a custom report",
        responses={200: CustomReportShareListSerializer(many=True)},
    )
    def share(self, request: Request, code=None):
        """GET/POST /reports/custom/<code>/share/"""
        if request.method == "POST":
            serializer = CustomReportShareCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            validated = serializer.validated_data
            share_obj = self.share_service.add_share(
                report_code=code,
                member_code=validated["member_code"],
                permission=validated["permission"],
            )
            data = CustomReportShareListSerializer(
                share_obj, context=self.get_serializer_context()
            ).data
            return self.response(data=data, status_code=201)

        shares = self.share_service.list_shares(code)
        data = CustomReportShareListSerializer(
            shares, many=True, context=self.get_serializer_context()
        ).data
        return self.response(data=data)

    @extend_schema(
        summary="Remove a custom report share",
        responses={
            204: OpenApiResponse(description="Share removed successfully."),
            404: OpenApiResponse(description="Share not found."),
        },
    )
    def share_detail(self, request: Request, code=None, member_code=None):
        """DELETE /reports/custom/<code>/share/<member_code>/"""
        self.share_service.remove_share(report_code=code, member_code=member_code)
        return self.response(message="Share removed successfully.", status_code=204)


@extend_schema(tags=["Reports"])
class WeeklyWinsReportViewSet(ExportMixin, BaseViewSet):
    """Data + export endpoints for the Weekly Wins standard report."""

    service_class = WeeklyWinsReportService
    export_service_class = WeeklyWinsExportService

    export_columns = [
        {"key": "team", "label": "Team", "default": True},
        {"key": "week", "label": "Week", "default": True},
        {"key": "date_range", "label": "Date Range", "default": True},
        {"key": "title", "label": "Title", "default": True},
        {"key": "description", "label": "Description", "default": True},
        {"key": "status_display", "label": "Status", "default": True},
    ]

    def get_permissions(self):
        return [IsAuthenticated(), HasPermission("reports.view_report")]

    @extend_schema(
        summary="Get Weekly Wins report data",
        description=(
            "Resolves the Weekly Win week for the requested mode (a specific "
            "week, or the week containing a given date) and returns its "
            "entries in report row shape."
        ),
        parameters=[
            OpenApiParameter(
                name="mode", type=str, location=OpenApiParameter.QUERY, required=True
            ),
            OpenApiParameter(
                name="date",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Required when mode=date. Format YYYY-MM-DD.",
            ),
            OpenApiParameter(
                name="win",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Win code. Required when mode=week.",
            ),
        ],
        responses={
            200: WeeklyWinsDataSerializer,
            404: OpenApiResponse(description="No Weekly Win found for the request."),
            422: OpenApiResponse(description="Validation error."),
        },
    )
    def data(self, request: Request):
        """GET /reports/standard/weekly-wins/data/"""
        query = WeeklyWinsQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        validated = query.validated_data
        result = self.service.get_data(
            mode=validated["mode"],
            date=validated.get("date"),
            win_code=validated.get("win"),
        )
        serializer = WeeklyWinsDataSerializer(
            result, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)


@extend_schema(tags=["Reports"])
class MonthlyWinsReportViewSet(ExportMixin, BaseViewSet):
    """Data + export endpoints for the Monthly Wins standard report."""

    service_class = MonthlyWinsReportService
    export_service_class = MonthlyWinsExportService

    export_columns = [
        {"key": "phase", "label": "Phase", "default": True},
        {"key": "label", "label": "Label", "default": True},
        {"key": "phase1_votes", "label": "Phase 1 Votes", "default": True},
        {"key": "status_display", "label": "Status", "default": True},
        {"key": "team", "label": "Team", "default": True},
        {"key": "week", "label": "Week", "default": True},
        {"key": "date_range", "label": "Date Range", "default": True},
        {"key": "win", "label": "Win", "default": True},
        {"key": "category_display", "label": "Selected As", "default": True},
    ]

    def get_permissions(self):
        return [IsAuthenticated(), HasPermission("reports.view_report")]

    @extend_schema(
        summary="Get Monthly Wins report data",
        description=(
            "Resolves the requested Monthly Win and returns its Phase 1 "
            "nomination rows and Phase 2 declared results grouped by category."
        ),
        parameters=[
            OpenApiParameter(
                name="code", type=str, location=OpenApiParameter.QUERY, required=True
            ),
        ],
        responses={
            200: MonthlyWinsDataSerializer,
            404: OpenApiResponse(description="Monthly Win not found."),
            422: OpenApiResponse(description="Validation error."),
        },
    )
    def data(self, request: Request):
        """GET /reports/standard/monthly-wins/data/"""
        query = MonthlyWinsQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        result = self.service.get_data(code=query.validated_data["code"])
        serializer = MonthlyWinsDataSerializer(
            result, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)


@extend_schema(tags=["Reports"])
class SprintForecastVsActualsReportViewSet(ExportMixin, BaseViewSet):
    """Data + export endpoints for the Sprint Forecast vs. Actuals standard
    report."""

    service_class = SprintForecastVsActualsReportService
    export_service_class = SprintForecastVsActualsExportService

    export_columns = [
        {"key": "team", "label": "Team", "default": True},
        {"key": "engineer", "label": "Engineer", "default": True},
        {"key": "label", "label": "Label", "default": True},
        {"key": "project", "label": "Project", "default": True},
        {"key": "programme", "label": "Programme", "default": True},
        {"key": "finance_type", "label": "Finance Type", "default": True},
        {"key": "forecast_days", "label": "Forecast (Days)", "default": True},
        {"key": "actual_days", "label": "Actuals (Days)", "default": True},
        {"key": "variance_days", "label": "Variance (Days)", "default": True},
    ]

    def get_permissions(self):
        return [IsAuthenticated(), HasPermission("reports.view_report")]

    @extend_schema(
        summary="Get Sprint Forecast vs. Actuals report data",
        description=(
            "Returns fully granular Forecast-vs-Actuals comparison rows for "
            "the requested sprint (optionally scoped to a team), plus "
            "pre-aggregated groupings by label/project/programme/team/"
            "engineer/finance type."
        ),
        parameters=[
            OpenApiParameter(
                name="sprint", type=str, location=OpenApiParameter.QUERY, required=True
            ),
            OpenApiParameter(
                name="team",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Optional team code to scope the report to.",
            ),
        ],
        responses={
            200: SprintForecastVsActualsDataSerializer,
            404: OpenApiResponse(description="Sprint or team not found."),
            422: OpenApiResponse(description="Validation error."),
        },
    )
    def data(self, request: Request):
        """GET /reports/standard/sprint-forecast-vs-actuals/data/"""
        query = SprintForecastVsActualsQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        validated = query.validated_data
        result = self.service.get_data(
            sprint_code=validated["sprint"],
            team_code=validated.get("team"),
        )
        serializer = SprintForecastVsActualsDataSerializer(
            result, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)


@extend_schema(tags=["Reports"])
class DemandCapacityReportConfigViewSet(BaseViewSet):
    """Programme → Category mappings for the Demand vs. Capacity standard
    report, scoped to a single Resource Plan version."""

    service_class = DemandCapacityReportConfigService

    def get_permissions(self):
        action_perms = {
            "list": "reports.view_demandcapacityreportconfig",
            "retrieve": "reports.view_demandcapacityreportconfig",
            "create": "reports.add_demandcapacityreportconfig",
            "partial_update": "reports.change_demandcapacityreportconfig",
            "destroy": "reports.delete_demandcapacityreportconfig",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return DemandCapacityReportConfigListSerializer

    def get_retrieve_serializer_class(self):
        return DemandCapacityReportConfigDetailSerializer

    def get_create_serializer_class(self):
        return DemandCapacityReportConfigCreateSerializer

    def get_update_serializer_class(self):
        return DemandCapacityReportConfigUpdateSerializer

    @extend_schema(
        summary="List Demand vs. Capacity report configs",
        description=(
            "Returns the Programme → Category mappings, filterable by "
            "`plan` (code) and `version` (number)."
        ),
        responses={200: DemandCapacityReportConfigListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /reports/standard/demand-vs-capacity/configs/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a Demand vs. Capacity report config",
        responses={
            200: DemandCapacityReportConfigDetailSerializer,
            404: OpenApiResponse(description="Config not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /reports/standard/demand-vs-capacity/configs/<code>/"""
        obj = self.service.get(code=code)
        serializer = DemandCapacityReportConfigDetailSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Map a Programme to a category",
        request=DemandCapacityReportConfigCreateSerializer,
        responses={
            201: DemandCapacityReportConfigDetailSerializer,
            404: OpenApiResponse(description="Plan, version, or programme not found."),
            409: OpenApiResponse(
                description="Programme is already mapped for this plan version."
            ),
        },
    )
    def create(self, request: Request):
        """POST /reports/standard/demand-vs-capacity/configs/"""
        return super().create(request)

    @extend_schema(
        summary="Update a Demand vs. Capacity report config",
        request=DemandCapacityReportConfigUpdateSerializer,
        responses={
            200: DemandCapacityReportConfigDetailSerializer,
            404: OpenApiResponse(description="Config not found."),
            409: OpenApiResponse(
                description="Programme is already mapped for this plan version."
            ),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /reports/standard/demand-vs-capacity/configs/<code>/"""
        serializer = DemandCapacityReportConfigUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(code=code, **serializer.validated_data)
        data = DemandCapacityReportConfigDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete a Demand vs. Capacity report config",
        responses={
            204: OpenApiResponse(description="Config deleted successfully."),
            404: OpenApiResponse(description="Config not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /reports/standard/demand-vs-capacity/configs/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )


@extend_schema(tags=["Reports"])
class DemandVsCapacityReportViewSet(ExportMixin, BaseViewSet):
    """Data + export endpoints for the Demand vs. Capacity standard report."""

    service_class = DemandVsCapacityReportService
    export_service_class = DemandVsCapacityExportService

    export_columns = [
        {"key": "scope", "label": "Scope", "default": True},
        {"key": "row_label", "label": "Row", "default": True},
        {"key": "row_type", "label": "Type", "default": True},
        {"key": "month", "label": "Month", "default": True},
        {"key": "value", "label": "Value", "default": True},
    ]

    def get_permissions(self):
        return [IsAuthenticated(), HasPermission("reports.view_report")]

    @extend_schema(
        summary="Get Demand vs. Capacity report data",
        description=(
            "Returns monthly demand (by configured category), capacity, "
            "holidays/leaves, FTE risk, and utilisation % for the requested "
            "Resource Plan version — overall and broken down per team."
        ),
        parameters=[
            OpenApiParameter(
                name="plan", type=str, location=OpenApiParameter.QUERY, required=True
            ),
            OpenApiParameter(
                name="version",
                type=int,
                location=OpenApiParameter.QUERY,
                required=True,
            ),
            OpenApiParameter(
                name="team",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Optional team code to scope the report to.",
            ),
            OpenApiParameter(
                name="employment_type",
                type=str,
                location=OpenApiParameter.QUERY,
                required=False,
                description="Optional employment type code to scope the report to.",
            ),
        ],
        responses={
            200: DemandVsCapacityDataSerializer,
            404: OpenApiResponse(
                description="Plan, version, team, or employment type not found."
            ),
            422: OpenApiResponse(description="Validation error."),
        },
    )
    def data(self, request: Request):
        """GET /reports/standard/demand-vs-capacity/data/"""
        query = DemandVsCapacityQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        validated = query.validated_data
        result = self.service.get_data(
            plan_code=validated["plan"],
            version=validated["version"],
            team_code=validated.get("team"),
            employment_type_code=validated.get("employment_type"),
        )
        serializer = DemandVsCapacityDataSerializer(
            result, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)


@extend_schema(tags=["Reports"])
class KPIEstimateAccuracyConfigViewSet(BaseViewSet):
    """Exception comments recorded against completed projects for the KPI
    Report — Estimate % Accuracy standard report, scoped to a month."""

    service_class = KPIEstimateAccuracyConfigService

    def get_permissions(self):
        action_perms = {
            "list": "reports.view_kpiestimateaccuracyconfig",
            "retrieve": "reports.view_kpiestimateaccuracyconfig",
            "create": "reports.add_kpiestimateaccuracyconfig",
            "partial_update": "reports.change_kpiestimateaccuracyconfig",
            "destroy": "reports.delete_kpiestimateaccuracyconfig",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return KPIEstimateAccuracyConfigListSerializer

    def get_retrieve_serializer_class(self):
        return KPIEstimateAccuracyConfigDetailSerializer

    def get_create_serializer_class(self):
        return KPIEstimateAccuracyConfigCreateSerializer

    def get_update_serializer_class(self):
        return KPIEstimateAccuracyConfigUpdateSerializer

    @extend_schema(
        summary="List KPI Report — Estimate % Accuracy exception comments",
        description="Returns exception comments, filterable by `month` (YYYY-MM).",
        responses={200: KPIEstimateAccuracyConfigListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /reports/standard/kpi-estimate-accuracy/configs/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a KPI Report exception comment",
        responses={
            200: KPIEstimateAccuracyConfigDetailSerializer,
            404: OpenApiResponse(description="Config not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /reports/standard/kpi-estimate-accuracy/configs/<code>/"""
        obj = self.service.get(code=code)
        serializer = KPIEstimateAccuracyConfigDetailSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Record an exception comment for a project/month",
        request=KPIEstimateAccuracyConfigCreateSerializer,
        responses={
            201: KPIEstimateAccuracyConfigDetailSerializer,
            404: OpenApiResponse(description="Project not found."),
            409: OpenApiResponse(
                description="A comment already exists for this project/month."
            ),
        },
    )
    def create(self, request: Request):
        """POST /reports/standard/kpi-estimate-accuracy/configs/"""
        return super().create(request)

    @extend_schema(
        summary="Update a KPI Report exception comment",
        request=KPIEstimateAccuracyConfigUpdateSerializer,
        responses={
            200: KPIEstimateAccuracyConfigDetailSerializer,
            404: OpenApiResponse(description="Config not found."),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /reports/standard/kpi-estimate-accuracy/configs/<code>/"""
        serializer = KPIEstimateAccuracyConfigUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(code=code, **serializer.validated_data)
        data = KPIEstimateAccuracyConfigDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete a KPI Report exception comment",
        responses={
            204: OpenApiResponse(description="Config deleted successfully."),
            404: OpenApiResponse(description="Config not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /reports/standard/kpi-estimate-accuracy/configs/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )


@extend_schema(tags=["Reports"])
class KPIEstimateAccuracyReportViewSet(ExportMixin, BaseViewSet):
    """Data + export endpoints for the KPI Report — Estimate % Accuracy
    standard report."""

    service_class = KPIEstimateAccuracyReportService
    export_service_class = KPIEstimateAccuracyExportService

    export_columns = [
        {"key": "programme", "label": "Programme", "default": True},
        {"key": "project", "label": "Project", "default": True},
        {"key": "team", "label": "Team", "default": True},
        {"key": "collaborators_display", "label": "Collaborators", "default": True},
        {"key": "estimate_value", "label": "Estimate Value", "default": True},
        {
            "key": "estimate_value_with_contingency",
            "label": "Estimate with Contingency",
            "default": True,
        },
        {
            "key": "total_cost_till_date",
            "label": "Total Cost till Date",
            "default": True,
        },
        {"key": "tshirt_size", "label": "T-Shirt Size", "default": True},
        {"key": "accuracy_pct", "label": "% Accuracy", "default": True},
        {"key": "band", "label": "Band", "default": True},
        {"key": "comment", "label": "Comment", "default": True},
    ]

    def get_permissions(self):
        return [IsAuthenticated(), HasPermission("reports.view_report")]

    @extend_schema(
        summary="Get KPI Report — Estimate % Accuracy data",
        description=(
            "Returns projects completed in the given month (scoped to the "
            "given financial year), comparing estimate value/estimate with "
            "contingency against total cost till date, with T-shirt size, "
            "% accuracy, and accuracy banding."
        ),
        parameters=[
            OpenApiParameter(
                name="fy", type=str, location=OpenApiParameter.QUERY, required=True
            ),
            OpenApiParameter(
                name="month",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Month in YYYY-MM format.",
            ),
        ],
        responses={
            200: KPIEstimateAccuracyDataSerializer,
            404: OpenApiResponse(description="Financial year not found."),
            422: OpenApiResponse(description="Validation error."),
        },
    )
    def data(self, request: Request):
        """GET /reports/standard/kpi-estimate-accuracy/data/"""
        query = KPIEstimateAccuracyQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        validated = query.validated_data
        result = self.service.get_data(
            fy_code=validated["fy"], month=validated["month"]
        )
        serializer = KPIEstimateAccuracyDataSerializer(
            result, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)


@extend_schema(tags=["Reports"])
class MonthlyFinanceReportViewSet(ExportMixin, BaseViewSet):
    """Data + export endpoints for the Monthly Finance Report standard
    report."""

    service_class = MonthlyFinanceReportService
    export_service_class = MonthlyFinanceReportExportService

    export_columns = [
        {"key": "project_code", "label": "Project Code", "default": True},
        {"key": "project", "label": "Project", "default": True},
        {"key": "programme", "label": "Programme", "default": True},
        {"key": "total_days", "label": "Total Days", "default": True},
        {"key": "total_cost", "label": "Total Cost", "default": True},
    ]

    def get_permissions(self):
        return [IsAuthenticated(), HasPermission("reports.view_report")]

    @extend_schema(
        summary="Get Monthly Finance Report data",
        description=(
            "Returns the sprints associated with the requested financial "
            "year + month, and — once every sprint in that month has "
            "confirmed actuals — the per-project total days/cost totals "
            "aggregated across those sprints."
        ),
        parameters=[
            OpenApiParameter(
                name="fy", type=str, location=OpenApiParameter.QUERY, required=True
            ),
            OpenApiParameter(
                name="month",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="Month in YYYY-MM format.",
            ),
        ],
        responses={
            200: MonthlyFinanceReportDataSerializer,
            404: OpenApiResponse(description="Financial year not found."),
            422: OpenApiResponse(description="Validation error."),
        },
    )
    def data(self, request: Request):
        """GET /reports/standard/monthly-finance-report/data/"""
        query = MonthlyFinanceReportQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        validated = query.validated_data
        result = self.service.get_data(
            fy_code=validated["fy"], month=validated["month"]
        )
        serializer = MonthlyFinanceReportDataSerializer(
            result, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)
