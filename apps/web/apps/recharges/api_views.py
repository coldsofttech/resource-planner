from __future__ import annotations

import math

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet, ExportMixin, ImportMixin, StatisticsMixin
from apps.recharges import selectors as recharge_selectors
from apps.recharges.engine import RechargeEmailEngine
from apps.recharges.serializers import (
    ProjectTypeMappingCreateSerializer,
    ProjectTypeMappingDetailSerializer,
    ProjectTypeMappingListSerializer,
    ProjectTypeMappingUpdateSerializer,
    RechargeEmailGroupSerializer,
    RechargeEmailTriggerSerializer,
    RechargeProjectGroupCreateSerializer,
    RechargeProjectGroupDetailSerializer,
    RechargeProjectGroupListSerializer,
    RechargeProjectGroupUpdateSerializer,
    RechargeTypeCreateSerializer,
    RechargeTypeDetailSerializer,
    RechargeTypeListSerializer,
    RechargeTypeUpdateSerializer,
)
from apps.recharges.services import (
    ProjectTypeMappingExportService,
    ProjectTypeMappingImportService,
    ProjectTypeMappingService,
    RechargeProjectGroupService,
    RechargeTypeExportService,
    RechargeTypeImportService,
    RechargeTypeService,
)


@extend_schema(tags=["Recharges: Types"])
class RechargeTypeViewSet(ImportMixin, ExportMixin, StatisticsMixin, BaseViewSet):
    service_class = RechargeTypeService
    import_service_class = RechargeTypeImportService
    export_service_class = RechargeTypeExportService

    import_fields = [
        {
            "name": "name",
            "type": "string",
            "required": True,
            "description": (
                "Recharge type name (max 50 chars, UPPER_SNAKE_CASE, must be unique)."
            ),
        },
        {
            "name": "description",
            "type": "string",
            "required": False,
            "description": "Optional description.",
        },
        {
            "name": "is_active",
            "type": "boolean",
            "required": False,
            "description": "true/false/yes/no/1/0 — defaults to true.",
        },
    ]
    import_notes = [
        "The first row must be a header row.",
        "The 'name' column is required; all other columns are optional.",
        "Names must be UPPER_SNAKE_CASE (e.g. PROJECT, BAU, HOLIDAY).",
        "Rows with duplicate recharge type names are skipped and reported in errors.",
        f"Maximum {RechargeTypeImportService.MAX_IMPORT_ROWS} data rows per file.",
        f"Maximum file size: {RechargeTypeImportService.MAX_IMPORT_FILE_SIZE_MB} MB.",
    ]
    import_sample_filename = "recharge_types_import_template.csv"

    export_columns = [
        {"key": "name", "label": "Recharge Type Name", "default": True},
        {"key": "code", "label": "Code", "default": True},
        {"key": "description", "label": "Description", "default": True},
        {"key": "is_active", "label": "Active", "default": True},
        {"key": "created_at", "label": "Created On", "default": True},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def get_import_sample_row(self):
        return ["BAU", "Business as usual recharges", "true"]

    def get_permissions(self):
        action_perms = {
            "list": "recharges.view_rechargetype",
            "retrieve": "recharges.view_rechargetype",
            "options": "recharges.view_rechargetype",
            "statistics": "recharges.view_rechargetype",
            "create": "recharges.add_rechargetype",
            "partial_update": "recharges.change_rechargetype",
            "destroy": "recharges.delete_rechargetype",
            "activate": "recharges.change_rechargetype",
            "deactivate": "recharges.change_rechargetype",
            "import_specs": "recharges.import_rechargetype",
            "import_sample": "recharges.import_rechargetype",
            "import_bulk": "recharges.import_rechargetype",
            "export_specs": "recharges.export_rechargetype",
            "export": "recharges.export_rechargetype",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return RechargeTypeListSerializer

    def get_retrieve_serializer_class(self):
        return RechargeTypeDetailSerializer

    def get_create_serializer_class(self):
        return RechargeTypeCreateSerializer

    def get_update_serializer_class(self):
        return RechargeTypeUpdateSerializer

    def get_create_response_serializer_class(self):
        return RechargeTypeDetailSerializer

    @extend_schema(
        summary="List recharge type options",
        responses={
            200: OpenApiResponse(description="List of active recharge type options.")
        },
    )
    def options(self, request: Request):
        """GET /recharges/types/options/"""
        return self.response(
            data=self.service.options(),
            message="Recharge type options retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="List recharge types",
        responses={200: RechargeTypeListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /recharges/types/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a recharge type",
        responses={
            200: RechargeTypeDetailSerializer,
            404: OpenApiResponse(description="Recharge type not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /recharges/types/<code>/"""
        obj = self.service.get(code=code)
        serializer = RechargeTypeDetailSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Create a recharge type",
        request=RechargeTypeCreateSerializer,
        responses={
            201: RechargeTypeDetailSerializer,
            409: OpenApiResponse(
                description="A recharge type with this name already exists."
            ),
        },
    )
    def create(self, request: Request):
        """POST /recharges/types/"""
        return super().create(request)

    @extend_schema(
        summary="Update a recharge type",
        request=RechargeTypeUpdateSerializer,
        responses={
            200: RechargeTypeDetailSerializer,
            404: OpenApiResponse(description="Recharge type not found."),
            409: OpenApiResponse(
                description="A recharge type with this name already exists."
            ),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /recharges/types/<code>/"""
        serializer = RechargeTypeUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(code=code, **serializer.validated_data)
        data = RechargeTypeDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete a recharge type",
        responses={
            204: OpenApiResponse(description="Recharge type deleted successfully."),
            404: OpenApiResponse(description="Recharge type not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /recharges/types/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )

    @extend_schema(
        summary="Activate a recharge type",
        responses={
            200: RechargeTypeDetailSerializer,
            404: OpenApiResponse(description="Recharge type not found."),
        },
    )
    def activate(self, request: Request, code=None):
        """POST /recharges/types/<code>/activate/"""
        obj = self.service.activate(code=code)
        data = RechargeTypeDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_activate_custom_message(),
            status_code=self.get_activate_status_code(),
        )

    @extend_schema(
        summary="Deactivate a recharge type",
        responses={
            200: RechargeTypeDetailSerializer,
            404: OpenApiResponse(description="Recharge type not found."),
        },
    )
    def deactivate(self, request: Request, code=None):
        """POST /recharges/types/<code>/deactivate/"""
        obj = self.service.deactivate(code=code)
        data = RechargeTypeDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_deactivate_custom_message(),
            status_code=self.get_deactivate_status_code(),
        )


@extend_schema(tags=["Recharges: Project Type Mappings"])
class ProjectTypeMappingViewSet(ImportMixin, ExportMixin, BaseViewSet):
    service_class = ProjectTypeMappingService
    import_service_class = ProjectTypeMappingImportService
    export_service_class = ProjectTypeMappingExportService

    import_fields = [
        {
            "name": "project_type_code",
            "type": "string",
            "required": True,
            "description": "Project type code to map to this recharge type.",
        },
    ]
    import_notes = [
        "The first row must be a header row.",
        "The 'project_type_code' column is required.",
        "Rows with duplicate or non-existent project type codes are skipped.",
        (
            f"Maximum {ProjectTypeMappingImportService.MAX_IMPORT_ROWS} "
            "data rows per file."
        ),
        (
            "Maximum file size: "
            f"{ProjectTypeMappingImportService.MAX_IMPORT_FILE_SIZE_MB} MB."
        ),
    ]
    import_sample_filename = "project_type_mappings_import_template.csv"

    export_columns = [
        {"key": "project_type_code", "label": "Project Type Code", "default": True},
        {"key": "project_type_name", "label": "Project Type Name", "default": True},
        {"key": "recharge_type_code", "label": "Recharge Type Code", "default": True},
        {"key": "created_at", "label": "Created On", "default": True},
        {"key": "created_by", "label": "Created By", "default": False},
    ]

    def _get_recharge_type_code(self) -> str:
        return self.kwargs.get("recharge_type_code", "")

    @property
    def service(self):
        if not hasattr(self, "_service"):
            self._service = self.service_class(
                user=self.request.user,
                request=self.request,
                recharge_type_code=self._get_recharge_type_code(),
            )
        return self._service

    @property
    def import_service(self):
        if not hasattr(self, "_import_service"):
            self._import_service = self.import_service_class(
                user=self.request.user,
                request=self.request,
                recharge_type_code=self._get_recharge_type_code(),
            )
        return self._import_service

    @property
    def export_service(self):
        if not hasattr(self, "_export_service"):
            self._export_service = self.export_service_class(
                user=self.request.user,
                request=self.request,
                recharge_type_code=self._get_recharge_type_code(),
            )
        return self._export_service

    def get_import_sample_row(self):
        return ["PROJECTTYPE-1"]

    def get_permissions(self):
        action_perms = {
            "list": "recharges.view_projecttypemapping",
            "retrieve": "recharges.view_projecttypemapping",
            "create": "recharges.add_projecttypemapping",
            "partial_update": "recharges.change_projecttypemapping",
            "destroy": "recharges.delete_projecttypemapping",
            "import_specs": "recharges.import_projecttypemapping",
            "import_sample": "recharges.import_projecttypemapping",
            "import_bulk": "recharges.import_projecttypemapping",
            "export_specs": "recharges.export_projecttypemapping",
            "export": "recharges.export_projecttypemapping",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return ProjectTypeMappingListSerializer

    def get_retrieve_serializer_class(self):
        return ProjectTypeMappingDetailSerializer

    def get_create_serializer_class(self):
        return ProjectTypeMappingCreateSerializer

    def get_update_serializer_class(self):
        return ProjectTypeMappingUpdateSerializer

    def get_create_response_serializer_class(self):
        return ProjectTypeMappingDetailSerializer

    @extend_schema(
        summary="List project type mappings",
        responses={200: ProjectTypeMappingListSerializer(many=True)},
    )
    def list(self, request: Request, recharge_type_code=None):
        """GET /recharges/types/<code>/mappings/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a project type mapping",
        responses={
            200: ProjectTypeMappingDetailSerializer,
            404: OpenApiResponse(description="Mapping not found."),
        },
    )
    def retrieve(self, request: Request, pk=None, **kwargs):
        """GET /recharges/types/<code>/mappings/<pk>/"""
        obj = self.service.get(pk=int(pk))
        serializer = ProjectTypeMappingDetailSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Create a project type mapping",
        request=ProjectTypeMappingCreateSerializer,
        responses={
            201: ProjectTypeMappingDetailSerializer,
            409: OpenApiResponse(description="Mapping already exists."),
        },
    )
    def create(self, request: Request, recharge_type_code=None):
        """POST /recharges/types/<code>/mappings/"""
        serializer = ProjectTypeMappingCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.create(**serializer.validated_data)
        data = ProjectTypeMappingDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_create_custom_message(),
            status_code=self.get_create_status_code(),
        )

    @extend_schema(
        summary="Update a project type mapping",
        request=ProjectTypeMappingUpdateSerializer,
        responses={
            200: ProjectTypeMappingDetailSerializer,
            404: OpenApiResponse(description="Mapping not found."),
            409: OpenApiResponse(description="Mapping already exists."),
        },
    )
    def partial_update(self, request: Request, pk=None, **kwargs):
        """PATCH /recharges/types/<code>/mappings/<pk>/"""
        serializer = ProjectTypeMappingUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(pk=int(pk), **serializer.validated_data)
        data = ProjectTypeMappingDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete a project type mapping",
        responses={
            204: OpenApiResponse(description="Mapping deleted successfully."),
            404: OpenApiResponse(description="Mapping not found."),
        },
    )
    def destroy(self, request: Request, pk=None, **kwargs):
        """DELETE /recharges/types/<code>/mappings/<pk>/"""
        self.service.delete(pk=int(pk))
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )


@extend_schema(tags=["Recharges: Project Groups"])
class RechargeProjectGroupViewSet(StatisticsMixin, BaseViewSet):
    service_class = RechargeProjectGroupService

    def get_permissions(self):
        action_perms = {
            "list": "recharges.view_rechargeprojectgroup",
            "retrieve": "recharges.view_rechargeprojectgroup",
            "statistics": "recharges.view_rechargeprojectgroup",
            "create": "recharges.add_rechargeprojectgroup",
            "partial_update": "recharges.change_rechargeprojectgroup",
            "destroy": "recharges.delete_rechargeprojectgroup",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return RechargeProjectGroupListSerializer

    def get_retrieve_serializer_class(self):
        return RechargeProjectGroupDetailSerializer

    def get_create_serializer_class(self):
        return RechargeProjectGroupCreateSerializer

    def get_update_serializer_class(self):
        return RechargeProjectGroupUpdateSerializer

    def get_create_response_serializer_class(self):
        return RechargeProjectGroupDetailSerializer

    @extend_schema(
        summary="List recharge project groups",
        responses={200: RechargeProjectGroupListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /recharges/project-groups/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a recharge project group",
        responses={
            200: RechargeProjectGroupDetailSerializer,
            404: OpenApiResponse(description="Project group not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /recharges/project-groups/<code>/"""
        obj = self.service.get(code=code)
        serializer = RechargeProjectGroupDetailSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Create a recharge project group",
        request=RechargeProjectGroupCreateSerializer,
        responses={
            201: RechargeProjectGroupDetailSerializer,
            409: OpenApiResponse(description="A group with this name already exists."),
        },
    )
    def create(self, request: Request):
        """POST /recharges/project-groups/"""
        return super().create(request)

    @extend_schema(
        summary="Update a recharge project group",
        request=RechargeProjectGroupUpdateSerializer,
        responses={
            200: RechargeProjectGroupDetailSerializer,
            404: OpenApiResponse(description="Project group not found."),
            409: OpenApiResponse(description="A group with this name already exists."),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /recharges/project-groups/<code>/"""
        serializer = RechargeProjectGroupUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(code=code, **serializer.validated_data)
        data = RechargeProjectGroupDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete a recharge project group",
        responses={
            204: OpenApiResponse(description="Project group deleted successfully."),
            404: OpenApiResponse(description="Project group not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /recharges/project-groups/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )


@extend_schema(tags=["Recharges"])
class RechargeViewSet(BaseViewSet):
    """Read-only dashboard APIs for the Recharges page."""

    def get_permissions(self):
        return [IsAuthenticated()]

    @extend_schema(
        summary="Recharge summary and finance type breakdown for a sprint",
        responses={200: OpenApiResponse(description="Summary + by-type breakdown.")},
    )
    def summary(self, request: Request):
        """GET /api/v1/recharges/summary/?sprint=<code>"""
        sprint_code = request.query_params.get("sprint", "").strip()
        if not sprint_code:
            return self.response(
                data={
                    "summary": {},
                    "results": [],
                    "pagination": {
                        "total_count": 0,
                        "total_pages": 1,
                        "current_page": 1,
                        "page_size": 100,
                        "has_next": False,
                        "has_previous": False,
                    },
                },
                message="sprint query parameter is required.",
            )
        data = recharge_selectors.get_recharge_summary(sprint_code)
        return self.response(data=data, message="Recharge summary retrieved.")

    @extend_schema(
        summary="Paginated list of recharge records for a sprint",
        responses={200: OpenApiResponse(description="Paginated recharge rows.")},
    )
    def list(self, request: Request):
        """GET /api/v1/recharges/?sprint=<code>&type=forecast|actual"""
        sprint_code = request.query_params.get("sprint", "").strip()
        type_val = request.query_params.get("type", "forecast").strip()

        empty_pagination = {
            "total_count": 0,
            "total_pages": 1,
            "current_page": 1,
            "page_size": self.DEFAULT_PAGE_SIZE,
            "has_next": False,
            "has_previous": False,
        }
        if not sprint_code:
            return self.response(
                data={"results": [], "pagination": empty_pagination},
                message="sprint query parameter is required.",
            )

        qs = recharge_selectors.get_recharges_for_sprint(sprint_code, type_val)
        page, page_size = self.get_pagination_params(request)
        total = qs.count()
        offset = (page - 1) * page_size
        rows = list(qs[offset : offset + page_size])

        results = []
        for r in rows:
            results.append(
                {
                    "code": r.code,
                    "programme_name": r.programme.name if r.programme else "",
                    "project_name": r.project.name if r.project else "",
                    "recharge_type_name": (
                        r.recharge_type.name if r.recharge_type else ""
                    ),
                    "total_days": str(r.total_days),
                    "total_cost": str(r.total_cost),
                    "project_contacts": [
                        {"name": pc.contact.name, "email": pc.contact.email}
                        for pc in r.project_contacts.all()
                    ],
                    "finance_contacts": [
                        {"name": fc.contact.name, "email": fc.contact.email}
                        for fc in r.finance_contacts.all()
                    ],
                }
            )

        total_pages = max(1, math.ceil(total / page_size))
        return self.response(
            data={
                "results": results,
                "pagination": {
                    "total_count": total,
                    "total_pages": total_pages,
                    "current_page": page,
                    "page_size": page_size,
                    "has_next": page < total_pages,
                    "has_previous": page > 1,
                },
            },
            message="Recharges retrieved.",
        )

    @extend_schema(
        summary="Grouped RechargeDetail breakdown for a single Recharge",
        responses={200: OpenApiResponse(description="Grouped detail rows.")},
    )
    def details(self, request: Request, code: str):
        """GET /api/v1/recharges/<code>/details/?group_by=engineer|team|label"""
        group_by = request.query_params.get("group_by", "engineer").strip()
        if group_by not in ("engineer", "team", "label"):
            group_by = "engineer"

        rows = recharge_selectors.get_recharge_details_grouped(code, group_by)
        return self.response(
            data={
                "results": rows,
                "pagination": {
                    "total_count": len(rows),
                    "total_pages": 1,
                    "current_page": 1,
                    "page_size": len(rows) or 1,
                    "has_next": False,
                    "has_previous": False,
                },
            },
            message="Recharge details retrieved.",
        )

    @extend_schema(
        summary="Jira stories for a single Recharge",
        responses={200: OpenApiResponse(description="RechargeDetail Jira story rows.")},
    )
    def jira(self, request: Request, code: str):
        """GET /api/v1/recharges/<code>/jira/"""
        qs = recharge_selectors.get_recharge_jira_stories(code)

        page, page_size = self.get_pagination_params(request)
        total = qs.count()
        offset = (page - 1) * page_size
        rows = list(qs[offset : offset + page_size])

        results = [
            {
                "jira_id": r.jira_id,
                "title": r.title,
                "team": r.team.name if r.team else "",
                "engineer": (
                    r.assignee.user.get_full_name() or r.assignee.user.email
                    if r.assignee
                    else "Unassigned"
                ),
                "label": r.label.label if r.label else "",
                "total_days": str(r.total_days),
                "total_cost": str(r.total_cost),
            }
            for r in rows
        ]

        total_pages = max(1, math.ceil(total / page_size))
        return self.response(
            data={
                "results": results,
                "pagination": {
                    "total_count": total,
                    "total_pages": total_pages,
                    "current_page": page,
                    "page_size": page_size,
                    "has_next": page < total_pages,
                    "has_previous": page > 1,
                },
            },
            message="Recharge Jira stories retrieved.",
        )


@extend_schema(tags=["Recharges: Email Review"])
class RechargeEmailViewSet(BaseViewSet):
    """APIs for the Email Review flow: listing groups, triggering, and resending."""

    def get_permissions(self):
        return [IsAuthenticated()]

    @extend_schema(
        summary="List email review groups for a sprint and type",
        responses={200: OpenApiResponse(description="Email review group list.")},
    )
    def list(self, request: Request):
        """GET /api/v1/recharges/email-review/?sprint=<code>&type=forecast|actual"""
        sprint_code = request.query_params.get("sprint", "").strip()
        type_val = request.query_params.get("type", "forecast").strip()
        if type_val not in ("forecast", "actual"):
            type_val = "forecast"

        if not sprint_code:
            return self.response(
                data={
                    "results": [],
                    "pagination": {
                        "total_count": 0,
                        "total_pages": 1,
                        "current_page": 1,
                        "page_size": 100,
                        "has_next": False,
                        "has_previous": False,
                    },
                },
                message="sprint query parameter is required.",
            )

        groups = recharge_selectors.get_email_review_groups(sprint_code, type_val)
        serializer = RechargeEmailGroupSerializer(groups, many=True)
        return self.response(
            data={
                "results": serializer.data,
                "pagination": {
                    "total_count": len(groups),
                    "total_pages": 1,
                    "current_page": 1,
                    "page_size": len(groups) or 1,
                    "has_next": False,
                    "has_previous": False,
                },
            },
            message="Email review groups retrieved.",
        )

    @extend_schema(
        summary="Trigger all emails for a sprint and type",
        request=RechargeEmailTriggerSerializer,
        responses={200: OpenApiResponse(description="Engine result summary.")},
    )
    def trigger_all(self, request: Request):
        """POST /api/v1/recharges/email-review/trigger/"""
        serializer = RechargeEmailTriggerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sprint_code = serializer.validated_data["sprint"]
        type_val = serializer.validated_data["type"]

        engine = RechargeEmailEngine(user=request.user)
        result = engine.trigger_all(sprint_code, type_val)
        return self.response(data=result, message="Email trigger completed.")

    @extend_schema(
        summary="Resend a single recharge email",
        responses={
            200: OpenApiResponse(description="Email resent."),
            404: OpenApiResponse(description="RechargeEmail not found."),
        },
    )
    def resend(self, request: Request, code: str):
        """POST /api/v1/recharges/email-review/<code>/resend/"""
        engine = RechargeEmailEngine(user=request.user)
        engine.trigger_single(code)
        return self.response(
            data={"code": code},
            message="Email resent.",
        )
