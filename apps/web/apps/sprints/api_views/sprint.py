from __future__ import annotations

from django.db.models import Q
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.core.exceptions import NotFoundException
from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet, ExportMixin, ImportMixin, StatisticsMixin
from apps.sprints.serializers import (
    CapacitySerializer,
    SprintCloseSerializer,
    SprintCreateSerializer,
    SprintDetailSerializer,
    SprintGenerateSerializer,
    SprintListSerializer,
    SprintUpdateSerializer,
)
from apps.sprints.services import (
    CapacityService,
    SprintExportService,
    SprintImportService,
    SprintService,
)


@extend_schema(tags=["Sprints"])
class SprintViewSet(ImportMixin, ExportMixin, StatisticsMixin, BaseViewSet):
    service_class = SprintService
    import_service_class = SprintImportService
    export_service_class = SprintExportService

    import_fields = [
        {
            "name": "fy_code",
            "type": "string",
            "required": True,
            "description": "Financial year code (e.g. FY-1).",
        },
        {
            "name": "sprint_number",
            "type": "integer",
            "required": True,
            "description": "Unique sprint number.",
        },
        {
            "name": "name",
            "type": "string",
            "required": False,
            "description": "Sprint name. Auto-generated from prefix if omitted.",
        },
        {
            "name": "start_date",
            "type": "date",
            "required": True,
            "description": "Start date of the sprint (YYYY-MM-DD).",
        },
        {
            "name": "end_date",
            "type": "date",
            "required": True,
            "description": "End date of the sprint (YYYY-MM-DD).",
        },
        {
            "name": "status",
            "type": "string",
            "required": False,
            "description": (
                "in_progress / future / completed / expired — defaults to future."
            ),
        },
        {
            "name": "note",
            "type": "string",
            "required": False,
            "description": "Optional note.",
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
        "fy_code, sprint_number, start_date, and end_date are required.",
        "Dates must be in YYYY-MM-DD format.",
        "Rows whose date range overlaps an existing sprint in the same FY are skipped.",
        f"Maximum {SprintImportService.MAX_IMPORT_ROWS} data rows per file.",
        f"Maximum file size: {SprintImportService.MAX_IMPORT_FILE_SIZE_MB} MB.",
    ]
    import_sample_filename = "sprints_import_template.csv"

    export_columns = [
        {"key": "code", "label": "Code", "default": True},
        {"key": "sprint_number", "label": "Sprint Number", "default": True},
        {"key": "name", "label": "Name", "default": True},
        {"key": "financial_year", "label": "Financial Year", "default": True},
        {"key": "start_date", "label": "Start Date", "default": True},
        {"key": "end_date", "label": "End Date", "default": True},
        {"key": "month", "label": "Month", "default": True},
        {"key": "status", "label": "Status", "default": True},
        {"key": "is_active", "label": "Active", "default": True},
        {"key": "is_closed", "label": "Closed", "default": True},
        {"key": "is_overridden", "label": "Overridden", "default": False},
        {"key": "note", "label": "Note", "default": False},
        {"key": "closed_on", "label": "Closed On", "default": False},
        {"key": "closed_by", "label": "Closed By", "default": False},
        {"key": "created_at", "label": "Created On", "default": False},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def get_import_sample_row(self):
        return [
            "FY-1",
            "1",
            "Sprint 1",
            "2025-04-01",
            "2025-04-14",
            "future",
            "",
            "true",
        ]

    def get_permissions(self):
        action_perms = {
            "list": "sprints.view_sprint",
            "retrieve": "sprints.view_sprint",
            "active": "sprints.view_sprint",
            "options": "sprints.view_sprint",
            "create": "sprints.add_sprint",
            "partial_update": "sprints.change_sprint",
            "destroy": "sprints.delete_sprint",
            "activate": "sprints.change_sprint",
            "deactivate": "sprints.change_sprint",
            "set_active": "sprints.change_sprint",
            "close": "sprints.close_sprint",
            "generate": "sprints.generate_sprint",
            "capacity": "sprints.view_sprint",
            "capacity_rebuild": "sprints.change_sprint",
            "statistics": "sprints.view_sprint",
            "import_specs": "sprints.import_sprint",
            "import_sample": "sprints.import_sprint",
            "import_bulk": "sprints.import_sprint",
            "export_specs": "sprints.export_sprint",
            "export": "sprints.export_sprint",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return SprintListSerializer

    def get_retrieve_serializer_class(self):
        return SprintDetailSerializer

    def get_create_serializer_class(self):
        return SprintCreateSerializer

    def get_update_serializer_class(self):
        return SprintUpdateSerializer

    def get_create_response_serializer_class(self):
        return SprintDetailSerializer

    @extend_schema(
        summary="List sprints",
        description=(
            "Returns a paginated list of sprints. "
            "Defaults to active records. Supports `search`, `status`, "
            "`financial_year`, `is_closed`, and `is_active` filters."
        ),
        responses={200: SprintListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /sprints/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a sprint",
        responses={
            200: SprintDetailSerializer,
            404: OpenApiResponse(description="Sprint not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /sprints/<code>/"""
        obj = self.service.get(code=code)
        serializer = SprintDetailSerializer(obj, context=self.get_serializer_context())
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Get active sprint",
        description="Returns the currently active (In Progress) sprint.",
        responses={
            200: SprintDetailSerializer,
            404: OpenApiResponse(description="No active sprint found."),
        },
    )
    def active(self, request: Request):
        """GET /sprints/active/"""
        try:
            obj = self.service.get_active()
        except NotFoundException:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "not_found",
                        "message": "No active sprint found.",
                    },
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = SprintDetailSerializer(obj, context=self.get_serializer_context())
        return self.response(
            data=serializer.data,
            message="Active sprint retrieved successfully.",
        )

    @extend_schema(
        summary="Create a sprint",
        request=SprintCreateSerializer,
        responses={
            201: SprintDetailSerializer,
            400: OpenApiResponse(description="Validation error."),
        },
    )
    def create(self, request: Request):
        """POST /sprints/"""
        serializer = SprintCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        obj = self.service.create(
            fy_code=data["fy_code"],
            sprint_number=data["sprint_number"],
            name=data.get("name") or "",
            start_date=data["start_date"],
            end_date=data["end_date"],
            status=data.get("status", "future"),
            note=data.get("note", ""),
            is_active=data.get("is_active", True),
        )
        response_data = SprintDetailSerializer(
            obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=response_data,
            message=self.get_create_custom_message(),
            status_code=self.get_create_status_code(),
        )

    @extend_schema(
        summary="Update a sprint",
        request=SprintUpdateSerializer,
        responses={
            200: SprintDetailSerializer,
            404: OpenApiResponse(description="Sprint not found."),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /sprints/<code>/"""
        serializer = SprintUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(code=code, **serializer.validated_data)
        data = SprintDetailSerializer(obj, context=self.get_serializer_context()).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete a sprint",
        responses={
            204: OpenApiResponse(description="Sprint deleted successfully."),
            404: OpenApiResponse(description="Sprint not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /sprints/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )

    @extend_schema(
        summary="Activate a sprint record",
        responses={
            200: SprintDetailSerializer,
            404: OpenApiResponse(description="Sprint not found."),
        },
    )
    def activate(self, request: Request, code=None):
        """POST /sprints/<code>/activate/"""
        obj = self.service.activate(code=code)
        data = SprintDetailSerializer(obj, context=self.get_serializer_context()).data
        return self.response(data=data, message=self.get_activate_custom_message())

    @extend_schema(
        summary="Deactivate a sprint record",
        responses={
            200: SprintDetailSerializer,
            404: OpenApiResponse(description="Sprint not found."),
        },
    )
    def deactivate(self, request: Request, code=None):
        """POST /sprints/<code>/deactivate/"""
        obj = self.service.deactivate(code=code)
        data = SprintDetailSerializer(obj, context=self.get_serializer_context()).data
        return self.response(data=data, message=self.get_deactivate_custom_message())

    @extend_schema(
        summary="Set sprint status to In Progress",
        description=(
            "Changes the sprint's status to 'in_progress'. "
            "Transitions any currently in-progress sprint to completed."
        ),
        responses={
            200: SprintDetailSerializer,
            404: OpenApiResponse(description="Sprint not found."),
        },
    )
    def set_active(self, request: Request, code=None):
        """POST /sprints/<code>/set-active/"""
        obj = self.service.set_active(code=code)
        data = SprintDetailSerializer(obj, context=self.get_serializer_context()).data
        return self.response(data=data, message="Sprint set to In Progress.")

    @extend_schema(
        summary="Lock or unlock a sprint",
        description=(
            "Closes (locks) or reopens (unlocks) a sprint. "
            "Pass `lock: true` to close, `lock: false` to reopen."
        ),
        request=SprintCloseSerializer,
        responses={
            200: SprintDetailSerializer,
            404: OpenApiResponse(description="Sprint not found."),
        },
    )
    def close(self, request: Request, code=None):
        """POST /sprints/<code>/close/"""
        serializer = SprintCloseSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        lock = serializer.validated_data.get("lock", True)
        obj = self.service.close(code=code, lock=lock)
        data = SprintDetailSerializer(obj, context=self.get_serializer_context()).data
        action = "locked" if lock else "unlocked"
        return self.response(data=data, message=f"Sprint {action} successfully.")

    @extend_schema(
        summary="Generate sprints for a financial year",
        description=(
            "Runs SprintGenerationEngine to create all sprints for the given "
            "financial year based on the configured sprint duration. "
            "The FY must have no existing sprints."
        ),
        request=SprintGenerateSerializer,
        responses={
            201: SprintListSerializer(many=True),
            400: OpenApiResponse(
                description="Validation error or sprints already exist."
            ),
            404: OpenApiResponse(description="Financial year not found."),
        },
    )
    def generate(self, request: Request):
        """POST /sprints/generate/"""
        serializer = SprintGenerateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        sprints = self.service.generate(fy_code=serializer.validated_data["fy_code"])
        data = SprintListSerializer(
            sprints, many=True, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=f"{len(sprints)} sprint(s) generated successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="List sprint options",
        description=(
            "Returns a lightweight list of active sprints for picker fields. "
            "Filter by financial year using `?fy_code=FY-1`."
        ),
        responses={200: OpenApiResponse(description="List of sprint options.")},
    )
    def options(self, request: Request):
        """GET /sprints/options/"""
        fy_code = request.query_params.get("fy_code") or None
        return self.response(
            data=self.service.options(fy_code=fy_code),
            message="Sprint options retrieved successfully.",
        )

    @extend_schema(
        summary="Get sprint capacity",
        description="Returns per-member capacity breakdown for the given sprint.",
        responses={
            200: CapacitySerializer(many=True),
            404: OpenApiResponse(description="Sprint not found."),
        },
    )
    def capacity(self, request: Request, code=None):
        """GET /sprints/<code>/capacity/"""
        search = request.query_params.get("search", "").strip()
        import_code = request.query_params.get("import", "").strip()

        # When an import code is provided, drive the response from that import's
        # latest review capacity results rather than the sprint Capacity model.
        # This populates allocated_days and capacity_status for the import view.
        if import_code:
            from apps.sprints.models.sprint_data_import_review import (
                SprintDataImportReview,
            )
            from apps.sprints.models.sprint_data_import_review_capacity_result import (
                SprintDataImportReviewCapacityResult,
            )
            from apps.sprints.selectors import get_import_by_code

            record = get_import_by_code(import_code)
            if record is not None:
                latest_review = (
                    SprintDataImportReview.objects.filter(import_record_id=record.pk)
                    .order_by("-reviewed_at")
                    .first()
                )
                if latest_review is not None:
                    results = (
                        SprintDataImportReviewCapacityResult.objects.filter(
                            review=latest_review
                        )
                        .select_related("member")
                        .order_by("member__first_name", "member__last_name")
                    )
                    if search:
                        results = results.filter(
                            Q(member__first_name__icontains=search)
                            | Q(member__last_name__icontains=search)
                            | Q(member__email__icontains=search)
                        )
                    data = [
                        {
                            "member": {
                                "id": r.member_id,
                                "email": r.member.email,
                                "full_name": r.member.get_full_name() or r.member.email,
                            },
                            "net_capacity": r.net_capacity,
                            "allocated_days": r.allocated_days,
                            "capacity_status": r.status,
                        }
                        for r in results
                    ]
                    return self.response(
                        data=data, message="Sprint capacity retrieved successfully."
                    )

        svc = CapacityService(user=request.user)
        rows = svc.get_for_sprint(sprint_code=code)

        team_code = request.query_params.get("team", "").strip()

        if search:
            rows = rows.filter(
                Q(member__first_name__icontains=search)
                | Q(member__last_name__icontains=search)
                | Q(member__email__icontains=search)
            )
        if team_code:
            rows = rows.filter(
                member__team_assignments__team__code=team_code
            ).distinct()

        data = CapacitySerializer(rows, many=True).data
        return self.response(
            data=data, message="Sprint capacity retrieved successfully."
        )

    @extend_schema(
        summary="Rebuild sprint capacity",
        description=(
            "Recomputes and persists capacity for every active member for the "
            "given sprint. Returns the number of rows upserted."
        ),
        responses={
            200: OpenApiResponse(description="Rebuild complete."),
            404: OpenApiResponse(description="Sprint not found."),
        },
    )
    def capacity_rebuild(self, request: Request, code=None):
        """POST /sprints/<code>/capacity/rebuild/"""
        svc = CapacityService(user=request.user)
        count = svc.rebuild(sprint_code=code)
        return self.response(
            data={"rebuilt": count},
            message=f"Capacity rebuilt for {count} member(s).",
        )
