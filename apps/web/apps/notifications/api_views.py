from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.viewsets import BaseViewSet
from apps.notifications.serializers import (
    NotificationCreateSerializer,
    NotificationDetailSerializer,
    NotificationListSerializer,
    NotificationPreferenceSerializer,
    NotificationPreferenceUpdateSerializer,
)
from apps.notifications.services import (
    NotificationPreferenceService,
    NotificationService,
)


@extend_schema(tags=["Notifications"])
class NotificationViewSet(BaseViewSet):
    service_class = NotificationService

    def get_permissions(self):
        return [IsAuthenticated()]

    def get_list_serializer_class(self):
        return NotificationListSerializer

    def get_retrieve_serializer_class(self):
        return NotificationDetailSerializer

    def get_create_serializer_class(self):
        return NotificationCreateSerializer

    def get_create_response_serializer_class(self):
        return NotificationDetailSerializer

    @extend_schema(
        summary="List notifications",
        description=(
            "Returns a paginated list of the current user's notifications. "
            "Excludes dismissed notifications by default; pass `is_dismissed=true` "
            "or `is_dismissed=all` to include them. Supports `category`, "
            "`notification_type`, and `is_read` filters."
        ),
        responses={200: NotificationListSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /notifications/"""
        return super().list(request)

    @extend_schema(
        summary="Retrieve a notification",
        responses={
            200: NotificationDetailSerializer,
            404: OpenApiResponse(description="Notification not found."),
        },
    )
    def retrieve(self, request: Request, code=None):
        """GET /notifications/<code>/"""
        obj = self.service.get(code=code)
        serializer = NotificationDetailSerializer(
            obj, context=self.get_serializer_context()
        )
        return self.response(data=serializer.data)

    @extend_schema(
        summary="Create a notification for the current user",
        description=(
            "Creates a notification owned by the current user. Used to persist "
            "in-app toast notifications. Suppressed silently (200, no data) if the "
            "user has disabled notifications for the given category."
        ),
        request=NotificationCreateSerializer,
        responses={201: NotificationDetailSerializer},
    )
    def create(self, request: Request):
        """POST /notifications/"""
        serializer = NotificationCreateSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)

        notification = self.service.create(
            user=request.user, **serializer.validated_data
        )
        if notification is None:
            return self.response(
                data=None,
                message="Notification suppressed by user preference.",
                status_code=status.HTTP_200_OK,
            )

        data = NotificationDetailSerializer(
            notification, context=self.get_serializer_context()
        ).data
        return self.response(
            data=data,
            message="Created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    @extend_schema(
        summary="Delete a notification",
        responses={
            204: OpenApiResponse(description="Notification deleted successfully."),
            404: OpenApiResponse(description="Notification not found."),
        },
    )
    def destroy(self, request: Request, code=None):
        """DELETE /notifications/<code>/"""
        self.service.delete(code=code)
        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )

    @extend_schema(
        summary="Mark a notification as read",
        responses={200: NotificationDetailSerializer},
    )
    @action(detail=True, methods=["post"], url_path="read")
    def mark_read(self, request: Request, code=None):
        """POST /notifications/<code>/read/"""
        notification = self.service.mark_read(code=code)
        data = NotificationDetailSerializer(
            notification, context=self.get_serializer_context()
        ).data
        return self.response(data=data, message="Notification marked as read.")

    @extend_schema(
        summary="Mark a notification as unread",
        responses={200: NotificationDetailSerializer},
    )
    @action(detail=True, methods=["post"], url_path="unread")
    def mark_unread(self, request: Request, code=None):
        """POST /notifications/<code>/unread/"""
        notification = self.service.mark_unread(code=code)
        data = NotificationDetailSerializer(
            notification, context=self.get_serializer_context()
        ).data
        return self.response(data=data, message="Notification marked as unread.")

    @extend_schema(
        summary="Dismiss a notification",
        description="Hides the notification from the default list without deleting it.",
        responses={200: NotificationDetailSerializer},
    )
    @action(detail=True, methods=["post"], url_path="dismiss")
    def dismiss(self, request: Request, code=None):
        """POST /notifications/<code>/dismiss/"""
        notification = self.service.dismiss(code=code)
        data = NotificationDetailSerializer(
            notification, context=self.get_serializer_context()
        ).data
        return self.response(data=data, message="Notification dismissed.")

    @extend_schema(
        summary="Mark all notifications as read",
        responses={200: OpenApiResponse(description="Count of notifications updated.")},
    )
    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_read(self, request: Request):
        """POST /notifications/mark-all-read/"""
        count = self.service.mark_all_read()
        return self.response(
            data={"updated": count}, message="All notifications marked as read."
        )

    @extend_schema(
        summary="Unread notification count",
        responses={200: OpenApiResponse(description="Unread notification count.")},
    )
    @action(detail=False, methods=["get"], url_path="unread-count")
    def unread_count(self, request: Request):
        """GET /notifications/unread-count/"""
        return self.response(data={"unread_count": self.service.unread_count()})


@extend_schema(tags=["Notifications"])
class NotificationPreferenceViewSet(BaseViewSet):
    service_class = NotificationPreferenceService

    def get_permissions(self):
        return [IsAuthenticated()]

    @extend_schema(
        summary="List notification preferences",
        description=(
            "Returns the current user's notification category preferences, "
            "creating default (enabled) rows for categories not yet configured. "
            "Mention and to-do categories are always enabled and not suppressible."
        ),
        responses={200: NotificationPreferenceSerializer(many=True)},
    )
    def list(self, request: Request):
        """GET /notifications/preferences/"""
        prefs = self.service.list_with_defaults()
        data = NotificationPreferenceSerializer(
            prefs, many=True, context=self.get_serializer_context()
        ).data
        return self.response(data=data)

    @extend_schema(
        summary="Update a notification preference",
        request=NotificationPreferenceUpdateSerializer,
        responses={
            200: NotificationPreferenceSerializer,
            422: OpenApiResponse(description="Category cannot be suppressed."),
        },
    )
    def partial_update(self, request: Request, pk=None):
        """PATCH /notifications/preferences/<category>/"""
        serializer = NotificationPreferenceUpdateSerializer(
            data=request.data, partial=True, context=self.get_serializer_context()
        )
        serializer.is_valid(raise_exception=True)

        pref = self.service.update_preference(
            category=pk, is_enabled=serializer.validated_data["is_enabled"]
        )
        data = NotificationPreferenceSerializer(
            pref, context=self.get_serializer_context()
        ).data
        return self.response(data=data, message="Preference updated successfully.")
