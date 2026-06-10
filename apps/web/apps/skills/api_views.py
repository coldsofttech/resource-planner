from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet, ExportMixin, ImportMixin, StatisticsMixin
from apps.skills.serializers import (
    SkillCreateSerializer,
    SkillDetailSerializer,
    SkillListSerializer,
    SkillUpdateSerializer,
)
from apps.skills.services import SkillExportService, SkillImportService, SkillService
from apps.users.serializers import MemberMiniListSerializer
from apps.users.services import MembersService


class SkillViewSet(ImportMixin, ExportMixin, StatisticsMixin, BaseViewSet):
    service_class = SkillService
    import_service_class = SkillImportService
    export_service_class = SkillExportService

    # Import metadata surfaced via GET /skills/import/specs/
    import_fields = [
        {
            "name": "skill",
            "type": "string",
            "required": True,
            "description": "Skill name (max 20 chars).",
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
        "The 'skill' column is required; all other columns are optional.",
        "Rows with duplicate skill names are skipped and reported in errors.",
        f"Maximum {SkillImportService.MAX_IMPORT_ROWS} data rows per file.",
        f"Maximum file size: {SkillImportService.MAX_IMPORT_FILE_SIZE_MB} MB.",
    ]
    import_sample_filename = "skills_import_template.csv"

    # Export column specs surfaced via GET /skills/export/specs/
    export_columns = [
        {"key": "skill", "label": "Skill", "default": True},
        {"key": "code", "label": "Code", "default": True},
        {"key": "description", "label": "Description", "default": True},
        {"key": "is_active", "label": "Active", "default": True},
        {"key": "created_at", "label": "Created On", "default": True},
        {"key": "created_by", "label": "Created By", "default": False},
        {"key": "updated_at", "label": "Updated On", "default": False},
        {"key": "updated_by", "label": "Updated By", "default": False},
    ]

    def get_import_sample_row(self):
        return ["Python", "Core programming language", "true"]

    def get_permissions(self):
        action_perms = {
            "list": "skills.view_skill",
            "retrieve": "skills.view_skill",
            "options": "skills.view_skill",
            "create": "skills.add_skill",
            "partial_update": "skills.change_skill",
            "destroy": "skills.delete_skill",
            "activate": "skills.change_skill",
            "deactivate": "skills.change_skill",
            "statistics": "skills.view_skill",
            "import_specs": "skills.import_skill",
            "import_sample": "skills.import_skill",
            "import_bulk": "skills.import_skill",
            "export_specs": "skills.export_skill",
            "export": "skills.export_skill",
            "members": "skills.view_skill",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return SkillListSerializer

    def get_retrieve_serializer_class(self):
        return SkillDetailSerializer

    def get_create_serializer_class(self):
        return SkillCreateSerializer

    def get_update_serializer_class(self):
        return SkillUpdateSerializer

    def get_create_response_serializer_class(self):
        return SkillDetailSerializer

    @extend_schema(
        summary="List skill options",
        description=(
            "Returns a lightweight list of active skills (code + name only) for use in "
            "picker fields."
        ),
        responses={200: OpenApiResponse(description="List of active skill options.")},
    )
    def options(self, request: Request):
        """GET /skills/options/"""
        return self.response(
            data=self.service.options(),
            message="Skill options retrieved successfully.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="List skills",
        description=(
            "Returns a paginated list of engineer skills. "
            "Defaults to active skills only. Pass `is_active=false` to list "
            "inactive skills. Supports `search` by skill name and `ordering`."
        ),
        responses={200: SkillListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /skills/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a skill",
        responses={
            200: SkillDetailSerializer,
            404: OpenApiResponse(description="Skill not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /skills/<code>/"""
        obj = self.service.get(code=code)
        serializer = SkillDetailSerializer(obj, context=self.get_serializer_context())
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Create a skill",
        request=SkillCreateSerializer,
        responses={
            201: SkillDetailSerializer,
            409: OpenApiResponse(description="A skill with this name already exists."),
        },
    )
    def create(self, request: Request):
        """POST /skills/"""
        return super().create(request)

    @extend_schema(
        summary="Update a skill",
        request=SkillUpdateSerializer,
        responses={
            200: SkillDetailSerializer,
            404: OpenApiResponse(description="Skill not found."),
            409: OpenApiResponse(description="A skill with this name already exists."),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /skills/<code>/"""
        serializer = SkillUpdateSerializer(
            data=request.data,
            partial=True,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)
        skill_obj = self.service.update(code=code, **serializer.validated_data)
        data = SkillDetailSerializer(
            skill_obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    @extend_schema(
        summary="Delete a skill",
        responses={
            204: OpenApiResponse(description="Skill deleted successfully."),
            404: OpenApiResponse(description="Skill not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /skills/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )

    @extend_schema(
        summary="Activate a skill",
        responses={
            200: SkillDetailSerializer,
            404: OpenApiResponse(description="Skill not found."),
        },
    )
    def activate(self, request: Request, code=None):
        """POST /skills/<code>/activate/"""
        skill_obj = self.service.activate(code=code)
        data = SkillDetailSerializer(
            skill_obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_activate_custom_message(),
            status_code=self.get_activate_status_code(),
        )

    @extend_schema(
        summary="Deactivate a skill",
        responses={
            200: SkillDetailSerializer,
            404: OpenApiResponse(description="Skill not found."),
        },
    )
    def deactivate(self, request: Request, code=None):
        """POST /skills/<code>/deactivate/"""
        skill_obj = self.service.deactivate(code=code)
        data = SkillDetailSerializer(
            skill_obj, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message=self.get_deactivate_custom_message(),
            status_code=self.get_deactivate_status_code(),
        )

    @extend_schema(
        summary="List skill members",
        description="Returns a paginated list of members who have this skill.",
        responses={
            200: MemberMiniListSerializer(many=True),
            404: OpenApiResponse(description="Skill not found."),
        },
    )
    def members(self, request: Request, code=None):
        """GET /skills/<code>/members/"""
        self.service.get(code=code)
        svc = MembersService(user=request.user, request=request)
        params = self.get_list_params(request)
        params.filters["skill"] = code
        result = svc.list(params=params)
        return self.paginated_response(
            result=result,
            serializer_class=MemberMiniListSerializer,
        )
