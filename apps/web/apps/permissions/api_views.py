from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.permissions.serializers import (
    GroupPermissionCategoryAssignSerializer,
    GroupPermissionCategorySerializer,
    GroupPermissionCategoryUpdateSerializer,
    PermissionCategoryDetailSerializer,
    PermissionCategoryListSerializer,
    UserEffectivePermissionSerializer,
    UserPermissionCategoryAssignSerializer,
    UserPermissionCategorySerializer,
    UserPermissionCategoryUpdateSerializer,
)
from apps.permissions.services import (
    GroupPermissionCategoryService,
    PermissionCategoryService,
    UserPermissionCategoryService,
)


class PermissionCategoryViewSet(BaseViewSet):
    service_class = PermissionCategoryService
    permission_classes = [IsAuthenticated]

    def get_list_serializer_class(self):
        return PermissionCategoryListSerializer

    def get_retrieve_serializer_class(self):
        return PermissionCategoryDetailSerializer

    @extend_schema(
        summary="List permission categories",
        description=(
            "Returns the catalog of all seeded permission categories. "
            "Filterable by `module`. Supports `search` and `ordering`."
        ),
        responses={200: PermissionCategoryListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /permissions/categories/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a permission category",
        responses={
            200: PermissionCategoryDetailSerializer,
            404: OpenApiResponse(description="Permission category not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /permissions/categories/<code>/"""
        obj = self.service.get(pk=code)
        serializer = self.get_retrieve_serializer_class()(
            obj, context=self.get_serializer_context()
        )
        return self.response(
            data=serializer.data,
            message=self.get_retrieve_custom_message(),
            status_code=self.get_retrieve_status_code(),
        )


class GroupPermissionCategoryViewSet(BaseViewSet):
    service_class = GroupPermissionCategoryService
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        action_perms = {
            "list": "permissions.view_grouppermissioncategory",
            "create": "permissions.add_grouppermissioncategory",
            "partial_update": "permissions.change_grouppermissioncategory",
            "destroy": "permissions.delete_grouppermissioncategory",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return GroupPermissionCategorySerializer

    @extend_schema(
        summary="List group permission assignments",
        description="Returns all permission category assignments for a group.",
        responses={
            200: GroupPermissionCategorySerializer(many=True),
            404: OpenApiResponse(description="Group not found."),
        },
    )
    def list(self, request: Request, group_code=None):
        """GET /permissions/groups/<group_code>/"""
        params = self.get_list_params(request)
        result = self.service.list(group_code=group_code, params=params)
        return self.paginated_response(
            result=result,
            serializer_class=GroupPermissionCategorySerializer,
            message="Group assignments retrieved successfully.",
        )

    @extend_schema(
        summary="Assign a permission category to a group",
        request=GroupPermissionCategoryAssignSerializer,
        responses={
            201: GroupPermissionCategorySerializer,
            404: OpenApiResponse(description="Group or category not found."),
            409: OpenApiResponse(
                description="Category already assigned to this group."
            ),
        },
    )
    def create(self, request: Request, group_code=None):
        """POST /permissions/groups/<group_code>/"""
        serializer = GroupPermissionCategoryAssignSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        assignment = self.service.assign(
            group_code=group_code,
            category_code=serializer.validated_data["category_code"],
            scope=serializer.validated_data["scope"],
        )
        return self.response(
            data=GroupPermissionCategorySerializer(
                assignment, context=self.get_serializer_context()
            ).data,
            message="Category assigned successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Update scope on a group assignment",
        request=GroupPermissionCategoryUpdateSerializer,
        responses={
            200: GroupPermissionCategorySerializer,
            404: OpenApiResponse(description="Group or assignment not found."),
        },
    )
    def partial_update(self, request: Request, group_code=None, code=None):
        """PATCH /permissions/groups/<group_code>/<code>/"""
        serializer = GroupPermissionCategoryUpdateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        assignment = self.service.update_scope(
            group_code=group_code,
            code=code,
            scope=serializer.validated_data["scope"],
        )
        return self.response(
            data=GroupPermissionCategorySerializer(
                assignment, context=self.get_serializer_context()
            ).data,
            message="Scope updated successfully.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Remove a permission category from a group",
        responses={
            204: OpenApiResponse(description="Assignment removed."),
            404: OpenApiResponse(description="Group or assignment not found."),
        },
    )
    def destroy(self, request: Request, group_code=None, code=None):
        """DELETE /permissions/groups/<group_code>/<code>/"""
        self.service.remove(group_code=group_code, code=code)
        return self.response(
            message="Assignment removed successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )


class UserPermissionCategoryViewSet(BaseViewSet):
    service_class = UserPermissionCategoryService
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        action_perms = {
            "list": "permissions.view_userpermissioncategory",
            "create": "permissions.add_userpermissioncategory",
            "partial_update": "permissions.change_userpermissioncategory",
            "destroy": "permissions.delete_userpermissioncategory",
            "effective": "permissions.view_userpermissioncategory",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return UserPermissionCategorySerializer

    @extend_schema(
        summary="List user permission assignments",
        description="Returns all permission category assignments for a user.",
        responses={
            200: UserPermissionCategorySerializer(many=True),
            404: OpenApiResponse(description="User not found."),
        },
    )
    def list(self, request: Request, user_code=None):
        """GET /permissions/users/<user_code>/"""
        params = self.get_list_params(request)
        result = self.service.list(user_code=user_code, params=params)
        return self.paginated_response(
            result=result,
            serializer_class=UserPermissionCategorySerializer,
            message="User assignments retrieved successfully.",
        )

    @extend_schema(
        summary="Assign a permission category to a user",
        request=UserPermissionCategoryAssignSerializer,
        responses={
            201: UserPermissionCategorySerializer,
            404: OpenApiResponse(description="User or category not found."),
            409: OpenApiResponse(description="Category already assigned to this user."),
        },
    )
    def create(self, request: Request, user_code=None):
        """POST /permissions/users/<user_code>/"""
        serializer = UserPermissionCategoryAssignSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        assignment = self.service.assign(
            user_code=user_code,
            category_code=serializer.validated_data["category_code"],
            scope=serializer.validated_data["scope"],
        )
        return self.response(
            data=UserPermissionCategorySerializer(
                assignment, context=self.get_serializer_context()
            ).data,
            message="Category assigned successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Update scope on a user assignment",
        request=UserPermissionCategoryUpdateSerializer,
        responses={
            200: UserPermissionCategorySerializer,
            404: OpenApiResponse(description="User or assignment not found."),
        },
    )
    def partial_update(self, request: Request, user_code=None, code=None):
        """PATCH /permissions/users/<user_code>/<code>/"""
        serializer = UserPermissionCategoryUpdateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        assignment = self.service.update_scope(
            user_code=user_code,
            code=code,
            scope=serializer.validated_data["scope"],
        )
        return self.response(
            data=UserPermissionCategorySerializer(
                assignment, context=self.get_serializer_context()
            ).data,
            message="Scope updated successfully.",
            status_code=status.HTTP_200_OK,
        )

    @extend_schema(
        summary="Remove a permission category from a user",
        responses={
            204: OpenApiResponse(description="Assignment removed."),
            404: OpenApiResponse(description="User or assignment not found."),
        },
    )
    def destroy(self, request: Request, user_code=None, code=None):
        """DELETE /permissions/users/<user_code>/<code>/"""
        self.service.remove(user_code=user_code, code=code)
        return self.response(
            message="Assignment removed successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )

    @extend_schema(
        summary="Effective permissions for a user",
        description=(
            "Returns the resolved union of group and direct permission category "
            "assignments. Each entry shows the effective (highest) scope and "
            "whether access comes via a group, directly, or both."
        ),
        responses={
            200: UserEffectivePermissionSerializer(many=True),
            404: OpenApiResponse(description="User not found."),
        },
    )
    def effective(self, request: Request, user_code=None):
        """GET /permissions/users/<user_code>/effective/"""
        results = self.service.effective(user_code=user_code)
        serializer = UserEffectivePermissionSerializer(results, many=True)
        return self.response(
            data=serializer.data,
            message="Effective permissions retrieved successfully.",
        )
