from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.permissions import HasPermission
from apps.core.viewsets import BaseViewSet
from apps.projects.serializers import (
    ProjectLabelCreateSerializer,
    ProjectLabelSerializer,
    ProjectLabelUpdateSerializer,
)
from apps.projects.services import ProjectLabelService


@extend_schema(tags=["Projects: Labels"])
class ProjectLabelViewSet(BaseViewSet):
    service_class = ProjectLabelService

    def get_permissions(self):
        action_perms = {
            "list": "projects.view_projectlabel",
            "retrieve": "projects.view_projectlabel",
            "create": "projects.add_projectlabel",
            "partial_update": "projects.change_projectlabel",
            "destroy": "projects.delete_projectlabel",
            "set_default": "projects.change_projectlabel",
            "suggest": "projects.view_projectlabel",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List labels for a project",
        responses={200: ProjectLabelSerializer(many=True)},
    )
    def list(self, request: Request, code=None):
        """GET /projects/<code>/labels/"""
        labels = self.service.list(project_code=code)
        data = ProjectLabelSerializer(labels, many=True).data
        return self.response(data=data, message="Labels retrieved successfully.")

    @extend_schema(
        summary="Retrieve a project label",
        responses={
            200: ProjectLabelSerializer,
            404: OpenApiResponse(description="Label not found."),
        },
    )
    def retrieve(self, request: Request, code=None, label_code=None):
        """GET /projects/<code>/labels/<label_code>/"""
        obj = self.service.get(code=label_code)
        return self.response(data=ProjectLabelSerializer(obj).data)

    @extend_schema(
        summary="Create a label for a project",
        request=ProjectLabelCreateSerializer,
        responses={
            201: ProjectLabelSerializer,
            409: OpenApiResponse(description="Label already exists for this project."),
        },
    )
    def create(self, request: Request, code=None):
        """POST /projects/<code>/labels/"""
        serializer = ProjectLabelCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.create(project_code=code, **serializer.validated_data)
        return self.response(
            data=ProjectLabelSerializer(obj).data,
            message="Label created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Update a project label",
        request=ProjectLabelUpdateSerializer,
        responses={
            200: ProjectLabelSerializer,
            404: OpenApiResponse(description="Label not found."),
            409: OpenApiResponse(description="Label already exists for this project."),
        },
    )
    def partial_update(self, request: Request, code=None, label_code=None):
        """PATCH /projects/<code>/labels/<label_code>/"""
        serializer = ProjectLabelUpdateSerializer(
            data=request.data, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)
        obj = self.service.update(code=label_code, **serializer.validated_data)
        return self.response(
            data=ProjectLabelSerializer(obj).data,
            message="Label updated successfully.",
        )

    @extend_schema(
        summary="Delete a project label",
        responses={
            204: OpenApiResponse(description="Label deleted."),
            404: OpenApiResponse(description="Label not found."),
        },
    )
    def destroy(self, request: Request, code=None, label_code=None):
        """DELETE /projects/<code>/labels/<label_code>/"""
        self.service.delete(code=label_code)
        return self.response(
            message="Label deleted successfully.",
            status_code=status.HTTP_204_NO_CONTENT,
        )

    @extend_schema(
        summary="Set a label as the default for the project",
        responses={
            200: ProjectLabelSerializer,
            404: OpenApiResponse(description="Label not found."),
        },
    )
    def set_default(self, request: Request, code=None, label_code=None):
        """POST /projects/<code>/labels/<label_code>/set-default/"""
        obj = self.service.set_default(code=label_code)
        return self.response(
            data=ProjectLabelSerializer(obj).data,
            message="Label set as default.",
        )

    @extend_schema(
        summary="Suggest a label for a project",
        responses={200: OpenApiResponse(description="Suggested label string.")},
    )
    def suggest(self, request: Request, code=None):
        """GET /projects/<code>/labels/suggest/"""
        suggested = self.service.suggest(project_code=code)
        return self.response(
            data={"label": suggested},
            message="Label suggestion generated.",
        )

    @extend_schema(
        summary="List all project labels across all projects",
        responses={200: OpenApiResponse(description="Global label options.")},
    )
    def options_global(self, request: Request):
        """GET /projects/labels/options/"""
        from apps.projects.selectors.label import get_all_labels_as_options

        return self.response(
            data=get_all_labels_as_options(),
            message="Label options retrieved successfully.",
        )
