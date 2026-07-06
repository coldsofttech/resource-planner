from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.viewsets import BaseViewSet
from apps.to_do.serializers import (
    TodoCreateSerializer,
    TodoDetailSerializer,
    TodoListSerializer,
    TodoPreferenceSerializer,
    TodoPreferenceUpdateSerializer,
    TodoUpdateSerializer,
)
from apps.to_do.services import TodoPreferenceService, TodoService


@extend_schema(tags=["To-Do"])
class TodoViewSet(BaseViewSet):
    service_class = TodoService

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return TodoListSerializer

    def get_retrieve_serializer_class(self):
        return TodoDetailSerializer

    def get_create_serializer_class(self):
        return TodoCreateSerializer

    def get_create_response_serializer_class(self):
        return TodoDetailSerializer

    @extend_schema(
        summary="List to-dos",
        description=(
            "Returns a paginated list of the current user's to-dos (created or "
            "assigned to them, e.g. via a '#todo' comment mention). Excludes "
            "completed to-dos by default; pass `status=done` or `status=all` to "
            "include them. Supports `priority`, `group`, and `due_filter` "
            "(`today`, `overdue`, `this_week`) filters."
        ),
        responses={200: TodoListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /to-do/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a to-do",
        responses={
            200: TodoDetailSerializer,
            404: OpenApiResponse(description="Todo not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /to-do/<code>/"""
        obj = self.service.get(code=code)
        serializer = TodoDetailSerializer(obj, context=self.get_serializer_context())
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Create a to-do",
        description="Creates a personal to-do owned by the current user.",
        request=TodoCreateSerializer,
        responses={201: TodoDetailSerializer},
    )
    def create(self, request: Request):
        """POST /to-do/"""
        serializer = TodoCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)

        obj = self.service.create(**serializer.validated_data)
        data = TodoDetailSerializer(obj, context=self.get_serializer_context()).data
        return self.response(
            data=data,
            message="Created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Update a to-do",
        request=TodoUpdateSerializer,
        responses={
            200: TodoDetailSerializer,
            404: OpenApiResponse(description="Todo not found."),
        },
    )
    def partial_update(self, request: Request, code=None):
        """PATCH /to-do/<code>/"""
        serializer = TodoUpdateSerializer(
            data=request.data, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)

        obj = self.service.update(code=code, **serializer.validated_data)
        data = TodoDetailSerializer(obj, context=self.get_serializer_context()).data
        return self.response(data=data, message="Updated successfully.")

    @extend_schema(
        summary="Delete a to-do",
        responses={
            204: OpenApiResponse(description="Todo deleted successfully."),
            404: OpenApiResponse(description="Todo not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /to-do/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )

    @extend_schema(
        summary="Mark a to-do as complete",
        description=(
            "Marks the to-do as done. If the to-do is recurring, the next "
            "occurrence is created automatically."
        ),
        responses={200: TodoDetailSerializer},
    )
    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request: Request, code=None):
        """POST /to-do/<code>/complete/"""
        obj = self.service.complete(code=code)
        data = TodoDetailSerializer(obj, context=self.get_serializer_context()).data
        return self.response(data=data, message="To-do marked as complete.")

    @extend_schema(
        summary="Reopen a completed to-do",
        responses={200: TodoDetailSerializer},
    )
    @action(detail=True, methods=["post"], url_path="reopen")
    def reopen(self, request: Request, code=None):
        """POST /to-do/<code>/reopen/"""
        obj = self.service.reopen(code=code)
        data = TodoDetailSerializer(obj, context=self.get_serializer_context()).data
        return self.response(data=data, message="To-do reopened.")

    @extend_schema(
        summary="Open to-do count",
        responses={200: OpenApiResponse(description="Open to-do count.")},
    )
    @action(detail=False, methods=["get"], url_path="open-count")
    def open_count(self, request: Request):
        """GET /to-do/open-count/"""
        return self.response(data={"open_count": self.service.open_count()})

    @extend_schema(
        summary="Due reminders",
        description=(
            "Returns to-dos whose reminder is due right now and marks them as "
            "sent. Intended to be polled while the user is logged in, to surface "
            "reminders as toasts."
        ),
        responses={200: TodoListSerializer(many=True)},
    )
    @action(detail=False, methods=["get"], url_path="due-reminders")
    def due_reminders(self, request: Request):
        """GET /to-do/due-reminders/"""
        todos = self.service.due_reminders()
        data = TodoListSerializer(
            todos, many=True, context=self.get_serializer_context()
        ).data
        return self.response(data=data)


@extend_schema(tags=["To-Do"])
class TodoPreferenceViewSet(BaseViewSet):
    service_class = TodoPreferenceService

    def get_permissions(self):
        return [IsAuthenticated()]

    @extend_schema(
        summary="List to-do reminder preferences",
        description=(
            "Returns the current user's to-do reminder preferences, creating "
            "default (enabled) rows for categories not yet configured."
        ),
        responses={200: TodoPreferenceSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /to-do/preferences/"""
        prefs = self.service.list_with_defaults()
        data = TodoPreferenceSerializer(
            prefs, many=True, context=self.get_serializer_context()
        ).data
        return self.response(data=data)

    @extend_schema(
        summary="Update a to-do reminder preference",
        request=TodoPreferenceUpdateSerializer,
        responses={
            200: TodoPreferenceSerializer,
            422: OpenApiResponse(description="Unknown reminder category."),
        },
    )
    def partial_update(self, request: Request, pk=None):
        """PATCH /to-do/preferences/<category>/"""
        serializer = TodoPreferenceUpdateSerializer(
            data=request.data, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)

        pref = self.service.update_preference(
            category=pk, is_enabled=serializer.validated_data["is_enabled"]
        )
        data = TodoPreferenceSerializer(
            pref, context=self.get_serializer_context()
        ).data
        return self.response(data=data, message="Preference updated successfully.")
