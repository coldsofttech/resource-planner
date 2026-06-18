import csv
import io
from dataclasses import asdict

from django.http import HttpResponse
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.core.exceptions import ValidationException
from apps.core.types import ListParams, SortParam


class BaseViewSet(ViewSet):
    """Base ViewSet for all APIs."""

    DEFAULT_PAGE = 1
    DEFAULT_PAGE_SIZE = 25
    MAX_PAGE_SIZE = 100

    service_class: type | None = None
    import_service_class: type | None = None
    export_service_class: type | None = None

    @property
    def service(self):
        if not hasattr(self, "_service"):
            if self.service_class is None:
                raise NotImplementedError("service_class must be defined.")
            self._service = self.service_class(
                user=self.request.user,
                request=self.request,
            )
        return self._service

    @property
    def import_service(self):
        if not hasattr(self, "_import_service"):
            if self.import_service_class is None:
                raise NotImplementedError("import_service_class must be defined.")
            self._import_service = self.import_service_class(
                user=self.request.user,
                request=self.request,
            )
        return self._import_service

    @property
    def export_service(self):
        if not hasattr(self, "_export_service"):
            if self.export_service_class is None:
                raise NotImplementedError("export_service_class must be defined.")
            self._export_service = self.export_service_class(
                user=self.request.user,
                request=self.request,
            )
        return self._export_service

    def get_pagination_params(self, request):
        """Extract pagination params safely."""

        try:
            page = int(
                request.query_params.get(
                    "page",
                    self.DEFAULT_PAGE,
                )
            )

            page_size = int(
                request.query_params.get(
                    "page_size",
                    self.DEFAULT_PAGE_SIZE,
                )
            )
        except (ValueError, TypeError):
            page = self.DEFAULT_PAGE
            page_size = self.DEFAULT_PAGE_SIZE

        page = max(page, 1)
        page_size = max(
            1,
            min(page_size, self.MAX_PAGE_SIZE),
        )

        return page, page_size

    def get_serializer_context(self):
        return {
            "request": self.request,
            "user": self.request.user,
        }

    def response(
        self,
        *,
        data=None,
        message="Success",
        status_code=status.HTTP_200_OK,
    ):
        """Standard success response."""

        return Response(
            {
                "success": True,
                "message": message,
                "data": data,
            },
            status=status_code,
        )

    def paginated_response(
        self,
        *,
        result,
        serializer_class,
        message="Success",
        status_code=status.HTTP_200_OK,
    ):
        """Standard paginated response."""

        serializer = serializer_class(
            result.results,
            many=True,
            context=self.get_serializer_context(),
        )

        return self.response(
            data={
                "results": serializer.data,
                "pagination": asdict(result.pagination),
            },
            message=message,
            status_code=status_code,
        )

    def _parse_fields_param(self, request):
        fields_param = request.query_params.get("fields")
        if not fields_param:
            return None
        return [f.strip() for f in fields_param.split(",") if f.strip()]

    def get_list_params(self, request) -> ListParams:
        page, page_size = self.get_pagination_params(request)
        sort_key = request.query_params.get("sort", "").strip()
        sort_dir = request.query_params.get("order_by", "ASC").upper()
        if sort_key:
            direction: str = "desc" if sort_dir == "DESC" else "asc"
            sorts = [SortParam(sort_by=sort_key, direction=direction)]
        else:
            sorts = []
        return ListParams(
            filters=request.query_params.dict(),
            search=request.query_params.get("search", ""),
            sorts=sorts or [SortParam()],
            page=page,
            page_size=page_size,
        )

    def get_list_serializer_class(self):
        """Override in child ViewSet."""
        raise NotImplementedError("get_list_serializer_class() must be implemented.")

    def get_list_custom_message(self):
        """Uses 'Success' by default. Implement in child ViewSet to override."""
        return "Success"

    def get_list_status_code(self):
        """Uses HTTP 200 OK by default. Implement in child ViewSet to override."""
        return status.HTTP_200_OK

    def list(self, request):
        """GET /module/"""
        params = self.get_list_params(request)
        result = self.service.list(params=params)
        return self.paginated_response(
            result=result,
            serializer_class=self.get_list_serializer_class(),
            message=self.get_list_custom_message(),
            status_code=self.get_list_status_code(),
        )

    def get_retrieve_serializer_class(self):
        """Must be implemented in child ViewSet."""
        raise NotImplementedError(
            "get_retrieve_serializer_class() must be implemented."
        )

    def get_retrieve_custom_message(self):
        """Uses 'Success' by default. Implement in child ViewSet to override."""
        return "Success"

    def get_retrieve_status_code(self):
        """Uses HTTP 200 OK by default. Implement in child ViewSet to override."""
        return status.HTTP_200_OK

    def retrieve(self, request, pk=None):
        """GET /module/<id>/"""
        obj = self.service.get(pk=pk)

        serializer_class = self.get_retrieve_serializer_class()
        serializer = serializer_class(
            obj,
            context=self.get_serializer_context(),
        )

        return self.response(
            data=serializer.data,
            message=self.get_retrieve_custom_message(),
            status_code=self.get_retrieve_status_code(),
        )

    def get_create_serializer_class(self):
        """Must be implemented in child ViewSet."""
        raise NotImplementedError("get_create_serializer_class() must be implemented.")

    def get_create_response_serializer_class(self):
        """
        Override to use a different serializer for the create response.
        Defaults to the retrieve serializer.
        """
        return self.get_retrieve_serializer_class()

    def get_create_custom_message(self):
        """
        Uses 'Created successfully.' by default. Implement in child ViewSet to override.
        """
        return "Created successfully."

    def get_create_status_code(self):
        """Uses HTTP 201 CREATED by default. Implement in child ViewSet to override."""
        return status.HTTP_201_CREATED

    def create(self, request):
        """POST /module/"""
        serializer_class = self.get_create_serializer_class()
        serializer = serializer_class(
            data=request.data,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)

        obj = self.service.create(**serializer.validated_data)
        response_serializer_class = self.get_create_response_serializer_class()
        if response_serializer_class is not None:
            data = response_serializer_class(
                obj,
                context=self.get_serializer_context(),
            ).data
        else:
            data = None

        return self.response(
            data=data,
            message=self.get_create_custom_message(),
            status_code=self.get_create_status_code(),
        )

    def get_update_serializer_class(self):
        """Must be implemented in child ViewSet."""
        raise NotImplementedError("get_update_serializer_class() must be implemented.")

    def get_update_response_serializer_class(self):
        """
        Override to use a different serializer for update responses.
        Defaults to retrieve serializer.
        """
        return self.get_retrieve_serializer_class()

    def get_update_custom_message(self):
        """
        Uses 'Updated successfully.' by default. Implement in child ViewSet to override.
        """
        return "Updated successfully."

    def get_update_status_code(self):
        """Uses HTTP 200 OK by default. Implement in child ViewSet to override."""
        return status.HTTP_200_OK

    def _update(self, request, pk, partial: bool):
        """Shared logic for PUT and PATCH."""
        serializer_class = self.get_update_serializer_class()
        serializer = serializer_class(
            data=request.data,
            partial=partial,
            context=self.get_serializer_context(),
        )
        serializer.is_valid(raise_exception=True)

        obj = self.service.update(pk=pk, **serializer.validated_data)
        response_serializer_class = self.get_update_response_serializer_class()
        if response_serializer_class is not None:
            data = response_serializer_class(
                obj,
                context=self.get_serializer_context(),
            ).data
        else:
            data = None

        return self.response(
            data=data,
            message=self.get_update_custom_message(),
            status_code=self.get_update_status_code(),
        )

    def update(self, request, pk=None):
        """PUT /module/<id>/"""
        return self._update(request, pk, partial=False)

    def partial_update(self, request, pk=None):
        """PATCH /module/id/"""
        return self._update(request, pk, partial=True)

    def get_delete_custom_message(self):
        """
        Uses 'Deleted successfully.' by default. Implement in child ViewSet to override.
        """
        return "Deleted successfully."

    def get_delete_status_code(self):
        """
        Uses HTTP 204 NO CONTENT by default. Implement in child ViewSet to override.
        """
        return status.HTTP_204_NO_CONTENT

    def destroy(self, request, pk=None):
        """DELETE /module/<id>/"""
        self.service.delete(pk=pk)

        return self.response(
            message=self.get_delete_custom_message(),
            status_code=self.get_delete_status_code(),
        )

    def get_activate_custom_message(self):
        """Uses 'Activated successfully.' by default."""
        return "Activated successfully."

    def get_activate_status_code(self):
        """Uses HTTP 200 OK by default."""
        return status.HTTP_200_OK

    def get_deactivate_custom_message(self):
        """Uses 'Deactivated successfully.' by default."""
        return "Deactivated successfully."

    def get_deactivate_status_code(self):
        """Uses HTTP 200 OK by default."""
        return status.HTTP_200_OK

    def get_set_default_custom_message(self):
        """Uses 'Set as default successfully.' by default."""
        return "Set as default successfully."

    def get_set_default_status_code(self):
        """Uses HTTP 200 OK by default."""
        return status.HTTP_200_OK


class StatisticsMixin:
    """ViewSet with /stats API endpoint."""

    def get_stats_custom_message(self):
        """
        Uses 'Statistics retrieved successfully.' by default.
        Implement in child ViewSet to override.
        """
        return "Statistics retrieved successfully."

    def get_stats_status_code(self):
        """Uses HTTP 200 OK by default. Implement in child ViewSet to override."""
        return status.HTTP_200_OK

    @extend_schema(
        summary="Statistics",
        description=(
            "Returns aggregate counts and statistics for the resource. "
            "Use the `fields` parameter to limit which stat keys are returned."
        ),
        parameters=[
            OpenApiParameter(
                name="fields",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Comma-separated list of stat field names to include.",
                required=False,
            ),
        ],
        responses={200: OpenApiResponse(description="Statistics data.")},
    )
    @action(detail=False, methods=["get"], url_path="stats")
    def statistics(self, request):
        """GET /module/stats/"""
        fields = self._parse_fields_param(request)
        result = self.service.stats(fields=fields)

        return self.response(
            data=result,
            message=self.get_stats_custom_message(),
            status_code=self.get_stats_status_code(),
        )


class OptionsMixin:
    """ViewSet with /options API endpoint."""

    def get_options_custom_message(self):
        """
        Uses 'Options retrieved successfully.' by default.
        Implement in child ViewSet to override.
        """
        return "Options retrieved successfully."

    def get_options_status_code(self):
        """Uses HTTP 200 OK by default. Implement in child ViewSet to override."""
        return status.HTTP_200_OK

    @extend_schema(
        summary="Options",
        description=(
            "Returns a lightweight list of active records (code + name) "
            "suitable for picker and dropdown fields."
        ),
        parameters=[
            OpenApiParameter(
                name="fields",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Comma-separated list of fields to include in each option.",
                required=False,
            ),
        ],
        responses={200: OpenApiResponse(description="List of options.")},
    )
    @action(detail=False, methods=["get"], url_path="options")
    def option_choices(self, request):
        """GET /module/options/"""
        fields = self._parse_fields_param(request)
        result = self.service.options(fields=fields)

        return self.response(
            data=result,
            message=self.get_options_custom_message(),
            status_code=self.get_options_status_code(),
        )


class ImportMixin:
    """
    ViewSet with /import API endpoints. Supports POST /import, GET /import/sample,
    and GET /import/specs.
    """

    import_fields: list[dict] = []
    import_notes: list[str] = []
    import_sample_filename = "import_template.csv"

    def get_import_specs_custom_message(self):
        """Uses 'Success.' by default. Implement in child ViewSet to override."""
        return "Success."

    def get_import_specs_status_code(self):
        """Uses HTTP 200 OK by default. Implement in child ViewSet to override."""
        return status.HTTP_200_OK

    @extend_schema(
        summary="Import specifications",
        description=(
            "Returns the import format specification: supported formats,"
            " max row count, max file size, field definitions, and notes."
        ),
        responses={
            200: OpenApiResponse(
                description=(
                    "Spec including `supported_formats`, `max_rows`,"
                    " `max_file_size_mb`, `fields`, and `notes`."
                )
            )
        },
    )
    @action(detail=False, methods=["get"], url_path="import/specs")
    def import_specs(self, request):
        """GET /module/import/specs"""
        svc = self.import_service
        return self.response(
            data={
                "supported_formats": svc.SUPPORTED_IMPORT_FORMATS,
                "max_rows": svc.MAX_IMPORT_ROWS,
                "max_file_size_mb": svc.MAX_IMPORT_FILE_SIZE_MB,
                "fields": self.import_fields,
                "notes": self.import_notes,
            },
            message=self.get_import_specs_custom_message(),
            status_code=self.get_import_specs_status_code(),
        )

    @extend_schema(
        summary="Download import template",
        description=(
            "Returns a sample CSV file with column headers and an example"
            " row. Use as a fill-in template before uploading."
        ),
        responses={200: OpenApiResponse(description="Sample CSV file attachment.")},
    )
    @action(detail=False, methods=["get"], url_path="import/sample")
    def import_sample(self, request):
        """GET /module/import/sample/"""
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        headers = [field["name"] for field in self.import_fields]

        writer.writerow(headers)
        sample_row = self.get_import_sample_row()

        if sample_row:
            writer.writerow(sample_row)

        buffer.seek(0)

        response = HttpResponse(
            buffer.getvalue(),
            content_type="text/csv",
        )
        response["Content-Disposition"] = (
            f"attachment; filename={self.import_sample_filename}"
        )

        return response

    def get_import_bulk_custom_message(self):
        """
        Uses 'Import completed..' by default. Implement in child ViewSet to override.
        """
        return "Import completed."

    def get_import_bulk_status_code(self):
        """
        Uses HTTP 207 MULTI STATUS by default. Implement in child ViewSet to override.
        """
        return status.HTTP_207_MULTI_STATUS

    @extend_schema(
        summary="Bulk import",
        description=(
            "Upload a CSV or Excel file to bulk-import records. "
            "Pass `validate=true` for a dry-run (validates without saving). "
            "Returns per-row results with success/error counts."
        ),
        parameters=[
            OpenApiParameter(
                name="validate",
                type=bool,
                location=OpenApiParameter.QUERY,
                description=(
                    "If `true`, validates rows without saving (dry run)."
                    " Defaults to `false`."
                ),
                required=False,
            ),
        ],
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {
                        "type": "string",
                        "format": "binary",
                        "description": "CSV or Excel (.xlsx) file to import.",
                    }
                },
                "required": ["file"],
            }
        },
        responses={
            207: OpenApiResponse(
                description=(
                    "Multi-status result with `success_count`,"
                    " `error_count`, and per-row status."
                )
            ),
            400: OpenApiResponse(
                description="No file uploaded or file validation failed."
            ),
        },
    )
    @action(detail=False, methods=["post"], url_path="import")
    def import_bulk(self, request):
        """POST /module/import/"""
        uploaded_file = request.FILES.get("file")
        if not uploaded_file:
            raise ValidationException("No import file uploaded.")

        svc = self.import_service
        svc.validate_file(uploaded_file)

        dry_run = request.query_params.get("validate", "false").lower() == "true"

        result = svc.bulk_import(file=uploaded_file, dry_run=dry_run)

        return self.response(
            data=result,
            message=self.get_import_bulk_custom_message(),
            status_code=self.get_import_bulk_status_code(),
        )

    def get_import_sample_row(self):
        """Override in subclasses if needed."""
        return []


class ExportMixin:
    """
    ViewSet with /export API endpoints. Supports GET /export and GET /export/specs.
    """

    export_columns: list[dict] = []

    def get_export_specs_custom_message(self):
        """Uses 'Success.' by default. Implement in child ViewSet to override."""
        return "Success."

    def get_export_specs_status_code(self):
        """Uses HTTP 200 OK by default. Implement in child ViewSet to override."""
        return status.HTTP_200_OK

    @extend_schema(
        summary="Export specifications",
        description=(
            "Returns the available export columns with their keys,"
            " labels, and whether each is included by default."
        ),
        responses={
            200: OpenApiResponse(
                description=("Column specs with `key`, `label`, and `default` flag.")
            )
        },
    )
    @action(detail=False, methods=["get"], url_path="export/specs")
    def export_specs(self, request, **kwargs):
        """GET /module/export/specs/"""
        return self.response(
            data={"columns": self.export_columns},
            message=self.get_export_specs_custom_message(),
            status_code=self.get_export_specs_status_code(),
        )

    def get_export_custom_message(self):
        """
        Uses 'Data exported successfully.' by default.
        Implement in child ViewSet to override.
        """
        return "Data exported successfully."

    def get_export_status_code(self):
        """Uses HTTP 200 OK by default. Implement in child ViewSet to override."""
        return status.HTTP_200_OK

    @extend_schema(
        summary="Export data",
        description=(
            "Exports resource data as a downloadable file. "
            "Formats: `csv` (default), `xlsx`, `pdf`, `json`. "
            "Use `fields` to select columns; list filters are also applied."
        ),
        parameters=[
            OpenApiParameter(
                name="type",
                type=str,
                location=OpenApiParameter.QUERY,
                description=(
                    "Export format: `csv`, `xlsx`, `pdf`, or `json`. Defaults to `csv`."
                ),
                required=False,
                enum=["csv", "xlsx", "pdf", "json"],
            ),
            OpenApiParameter(
                name="fields",
                type=str,
                location=OpenApiParameter.QUERY,
                description=(
                    "Comma-separated column keys to include."
                    " See export/specs for available keys."
                ),
                required=False,
            ),
        ],
        responses={
            200: OpenApiResponse(description="Exported file as a binary attachment.")
        },
    )
    @action(detail=False, methods=["get"], url_path="export")
    def export(self, request, **kwargs):
        """GET /module/export/?type=csv|xlsx|pdf|json&fields=f1,f2"""
        fields = self._parse_fields_param(request)
        export_format = request.query_params.get("type", "csv").lower()
        return self.export_service.export(
            fields=fields,
            export_format=export_format,
            filters=request.query_params.dict(),
        )
