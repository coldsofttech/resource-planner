import logging

from django.db import DatabaseError
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


class DomainException(APIException):
    """Base exception for all domain/service exceptions."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Domain error occurred."
    default_code = "domain_error"


class ValidationException(DomainException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_detail = "Validation failed."
    default_code = "validation_error"


class AlreadyExistsException(DomainException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Resource already exists."
    default_code = "already_exists"


class ConflictException(DomainException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict occurred."
    default_code = "conflict"


class PermissionException(DomainException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = "You do not have permission to perform this action."
    default_code = "permission_denied"


class ServiceUnavailableException(DomainException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Service temporarily unavailable."
    default_code = "service_unavailable"


class NotFoundException(DomainException):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = "not_found"

    def __init__(
        self,
        *,
        resource="Resource",
        lookup_field="id",
        lookup_value=None,
    ):
        if lookup_value is not None:
            detail = f"{resource} with {lookup_field}={lookup_value} not found."
        else:
            detail = f"{resource} not found."

        self.resource = resource
        self.lookup_field = lookup_field
        self.lookup_value = lookup_value

        super().__init__(detail=detail)


def custom_exception_handler(exc, context):
    """Centralized DRF exception handler."""
    response = exception_handler(exc, context)

    if response is not None:
        data = response.data
        detail = data.get("detail") if isinstance(data, dict) else None
        if detail is not None:
            message = str(detail)
        elif isinstance(data, dict):
            parts = []
            for field, errors in data.items():
                if isinstance(errors, list):
                    parts.append(f"{field}: {'; '.join(str(e) for e in errors)}")
                else:
                    parts.append(str(errors))
            message = " | ".join(parts) if parts else "Request failed."
        else:
            message = "Request failed."
        return Response(
            {
                "success": False,
                "message": message,
                "errors": data,
            },
            status=response.status_code,
        )

    if isinstance(exc, DatabaseError):
        logger.exception(
            "Database error occurred",
            exc_info=exc,
        )
        return Response(
            {
                "success": False,
                "message": "Database temporarily unavailable.",
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    logger.exception(
        "Unhandled exception occurred",
        exc_info=exc,
    )
    return Response(
        {
            "success": False,
            "message": "Internal server error.",
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
