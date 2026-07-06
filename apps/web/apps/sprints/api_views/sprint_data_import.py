from __future__ import annotations

from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request

from apps.core.exceptions import NotFoundException, ValidationException
from apps.core.permissions import HasPermission
from apps.core.services import paginate_queryset
from apps.core.viewsets import BaseViewSet
from apps.sprints.selectors import (
    get_failing_row_ids_for_check,
    get_has_review_for_import,
    get_import_by_code,
    get_rows_for_import,
)
from apps.sprints.services import (
    SprintDataImportActualService,
    SprintDataImportForecastService,
)

_ROW_SORT_FIELDS = frozenset(
    {
        "story_type",
        "jira_id",
        "title",
        "assignee",
        "efforts",
        "days",
        "sprint",
        "label",
        "mapping",
    }
)


def _upload_response(record, viewset_instance):
    return viewset_instance.response(
        data={
            "id": record.pk,
            "code": record.code,
            "import_type": record.import_type,
            "version_number": record.version_number,
            "file_name": record.file_name,
            "status": record.status,
            "sprint": record.sprint.code if record.sprint else None,
            "team": record.team.code if record.team else None,
            "created_at": str(record.created_at),
        },
        message="File uploaded successfully.",
    )


def _profile_display(profile) -> str | None:
    if profile is None:
        return None
    return profile.display_name or profile.user.email


def _serialize_row(row) -> dict:
    eff_assignee = row.effective_assignee_code
    eff_sprint = row.effective_sprint_code
    eff_label = row.effective_label_code
    eff_mapping = row.effective_mapping_code
    return {
        "code": row.code,
        "is_manually_added": row.is_manually_added,
        # Effective (displayed) values — override wins over CSV
        "story_type": row.effective_story_type,
        "jira_id": row.effective_jira_id,
        "title": row.effective_title,
        "assignee": row.effective_assignee,
        "efforts": row.effective_efforts,
        "sprint": row.effective_sprint,
        "label": row.effective_label,
        "mapping": row.effective_mapping,
        # Effective FK display values (for row renderer)
        "assignee_code": _profile_display(eff_assignee),
        "label_code": eff_label.label if eff_label else None,
        "mapping_code": eff_mapping.name if eff_mapping else None,
        "sprint_code": eff_sprint.name if eff_sprint else None,
        # Effective FK codes for edit drawer dropdowns
        # (override wins, falls back to CSV FK)
        "edit_assignee_code": eff_assignee.code if eff_assignee else None,
        "edit_sprint_code": eff_sprint.code if eff_sprint else None,
        "edit_label_code": eff_label.code if eff_label else None,
        "edit_mapping_code": eff_mapping.code if eff_mapping else None,
        # Raw override values — used to detect whether an override is active
        "story_type_override": row.story_type_override,
        "jira_id_override": row.jira_id_override,
        "title_override": row.title_override,
        "efforts_override": row.efforts_override,
        "assignee_override_code": (
            row.assignee_code_override.code if row.assignee_code_override else None
        ),
        "sprint_override_code": (
            row.sprint_code_override.code if row.sprint_code_override else None
        ),
        "label_override_code": (
            row.label_code_override.code if row.label_code_override else None
        ),
        "mapping_override_code": (
            row.mapping_code_override.code if row.mapping_code_override else None
        ),
        "days": float(row.days),
    }


def _serialize_import(record) -> dict:
    created_by = record.created_by
    return {
        "id": record.pk,
        "code": record.code,
        "version_number": record.version_number,
        "file_name": record.file_name,
        "status": record.status,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "created_by": created_by.email if created_by else None,
    }


@extend_schema(tags=["Sprints"])
class SprintDataImportForecastViewSet(BaseViewSet):
    parser_classes = [MultiPartParser, JSONParser]

    def get_permissions(self):
        action_perms = {
            "upload": "sprints.import_forecast",
            "download_template": "sprints.import_forecast",
            "forecast_review_complete": "sprints.review_complete",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="Upload forecast CSV for a sprint team",
        responses={
            200: OpenApiResponse(description="Upload recorded."),
            400: OpenApiResponse(description="Validation error."),
            404: OpenApiResponse(description="Sprint or team not found."),
        },
    )
    def upload(self, request: Request, sprint_code: str, team_code: str):
        """POST /sprints/<sprint_code>/forecast/<team_code>/upload/"""
        file = request.FILES.get("file")
        if not file:
            raise ValidationException("No file provided.")
        svc = SprintDataImportForecastService(user=request.user)
        record = svc.upload(sprint_code=sprint_code, team_code=team_code, file=file)
        return _upload_response(record, self)

    @extend_schema(
        summary="List forecast imports for a sprint team",
        responses={200: OpenApiResponse(description="List of imports.")},
    )
    def list_imports(self, request: Request, sprint_code: str, team_code: str):
        """GET /sprints/<sprint_code>/forecast/<team_code>/imports/"""
        svc = SprintDataImportForecastService(user=request.user)
        records = svc.list_imports(sprint_code=sprint_code, team_code=team_code)
        return self.response(data={"results": [_serialize_import(r) for r in records]})

    @extend_schema(
        summary="Download forecast CSV template",
        responses={200: OpenApiResponse(description="CSV template file.")},
    )
    def download_template(self, request: Request, sprint_code: str):
        """GET /sprints/<sprint_code>/forecast/template/"""
        svc = SprintDataImportForecastService(user=request.user)
        return svc.get_template_response()

    @extend_schema(
        summary="Mark sprint forecast review complete and populate recharge details",
        responses={
            200: OpenApiResponse(description="Review marked complete."),
            404: OpenApiResponse(description="Sprint not found."),
        },
    )
    def forecast_review_complete(self, request: Request, sprint_code: str):
        """POST /sprints/<sprint_code>/forecast/review-complete/"""
        from apps.recharges.services import RechargeDetailService
        from apps.sprints.selectors import get_sprint_by_code

        sprint = get_sprint_by_code(sprint_code)
        if sprint is None:
            from apps.core.exceptions import NotFoundException

            raise NotFoundException(
                resource="Sprint", lookup_field="code", lookup_value=sprint_code
            )

        svc = RechargeDetailService(user=request.user)
        count = svc.populate_from_sprint_forecast(sprint_id=sprint.pk)
        return self.response(
            data={"created": count},
            message="Sprint forecast review marked complete.",
        )


@extend_schema(tags=["Sprints"])
class SprintDataImportRowViewSet(BaseViewSet):
    def get_permissions(self):
        action_perms = {
            "review_import": "sprints.review_forecast",
            "confirm_import": "sprints.confirm_forecast",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="List rows for a forecast/actuals import",
        responses={200: OpenApiResponse(description="List of import rows.")},
    )
    def retrieve_import(self, request: Request, sprint_code: str, import_code: str):
        """GET /sprints/<sprint_code>/forecast/<import_code>/"""
        record = get_import_by_code(import_code)
        if record is None:
            raise NotFoundException(
                resource="SprintDataImport",
                lookup_field="code",
                lookup_value=import_code,
            )
        from apps.sprints.constants import SprintDataImportStatus

        return self.response(
            data={
                "code": record.code,
                "version_number": record.version_number,
                "file_name": record.file_name,
                "status": record.status,
                "sprint_code": record.sprint.code if record.sprint else None,
                "sprint_name": record.sprint.name if record.sprint else None,
                "team_code": record.team.code if record.team else None,
                "team_name": record.team.name if record.team else None,
                "has_review": get_has_review_for_import(record.pk),
                "is_confirmed": record.status == SprintDataImportStatus.CONFIRMED,
            }
        )

    def list_rows(self, request: Request, sprint_code: str, import_code: str):
        """GET /sprints/<sprint_code>/forecast/<import_code>/rows/"""
        record = get_import_by_code(import_code)
        if record is None:
            raise NotFoundException(
                resource="SprintDataImport",
                lookup_field="code",
                lookup_value=import_code,
            )
        qs = get_rows_for_import(record.pk)

        check_type = request.query_params.get("check_type", "").strip()
        if check_type:
            from apps.sprints.constants import ImportRowCheck

            if check_type in ImportRowCheck.ALL:
                failing_ids = get_failing_row_ids_for_check(record.pk, check_type)
                qs = qs.filter(pk__in=failing_ids)

        sort_key = request.query_params.get("sort", "").strip()
        sort_dir = request.query_params.get("order_by", "ASC").upper()
        if sort_key in _ROW_SORT_FIELDS:
            from django.db.models import Case, FloatField, Value, When
            from django.db.models.functions import Cast

            if sort_key == "days":
                # Sort by effective efforts: override wins if not NULL, else CSV value
                qs = qs.annotate(
                    _efforts_num=Case(
                        When(
                            efforts_override__isnull=False,
                            then=Case(
                                When(efforts_override="", then=Value(0.0)),
                                default=Cast(
                                    "efforts_override", output_field=FloatField()
                                ),
                                output_field=FloatField(),
                            ),
                        ),
                        When(efforts="", then=Value(0.0)),
                        default=Cast("efforts", output_field=FloatField()),
                        output_field=FloatField(),
                    )
                )
                order_field = "_efforts_num"
            else:
                order_field = sort_key
            prefix = "-" if sort_dir == "DESC" else ""
            qs = qs.order_by(f"{prefix}{order_field}")

        page, page_size = self.get_pagination_params(request)
        result = paginate_queryset(qs, page, page_size)
        return self.response(
            data={
                "results": [_serialize_row(r) for r in result.results],
                "pagination": {
                    "total_count": result.pagination.total_count,
                    "total_pages": result.pagination.total_pages,
                    "current_page": result.pagination.current_page,
                    "page_size": result.pagination.page_size,
                    "has_next": result.pagination.has_next,
                    "has_previous": result.pagination.has_previous,
                },
            }
        )

    def create_row(self, request: Request, sprint_code: str, import_code: str):
        """POST /sprints/<sprint_code>/forecast/<import_code>/rows/"""
        data = request.data
        svc = SprintDataImportForecastService(user=request.user)
        row = svc.create_row(
            import_code=import_code,
            story_type=(data.get("story_type") or "").strip(),
            jira_id=(data.get("jira_id") or "").strip(),
            title=(data.get("title") or "").strip(),
            assignee_code_str=(data.get("assignee_code") or "").strip(),
            efforts=(data.get("efforts") or "").strip(),
            sprint_code_str=(data.get("sprint_code") or "").strip(),
            label_code_str=(data.get("label_code") or "").strip(),
            mapping_code_str=(data.get("mapping_code") or "").strip(),
        )
        # Re-fetch with select_related so _serialize_row can access FK fields
        # without extra queries
        row = get_rows_for_import(row.import_record_id).get(pk=row.pk)
        return self.response(
            data=_serialize_row(row),
            message="Row created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    def delete_row(
        self, request: Request, sprint_code: str, import_code: str, row_code: str
    ):
        """DELETE /sprints/<sprint_code>/forecast/<import_code>/rows/<row_code>/"""
        svc = SprintDataImportForecastService(user=request.user)
        svc.delete_row(row_code=row_code)
        return self.response(
            message="Row deleted successfully.", status_code=status.HTTP_200_OK
        )

    def update_row(
        self, request: Request, sprint_code: str, import_code: str, row_code: str
    ):
        """PATCH /sprints/<sprint_code>/forecast/<import_code>/rows/<row_code>/"""
        data = request.data
        svc = SprintDataImportForecastService(user=request.user)
        row = svc.update_row(
            row_code=row_code,
            story_type=(data.get("story_type") or "").strip(),
            jira_id=(data.get("jira_id") or "").strip(),
            title=(data.get("title") or "").strip(),
            assignee_code_str=(data.get("assignee_code") or "").strip(),
            efforts=(data.get("efforts") or "").strip(),
            sprint_code_str=(data.get("sprint_code") or "").strip(),
            label_code_str=(data.get("label_code") or "").strip(),
            mapping_code_str=(data.get("mapping_code") or "").strip(),
        )
        row = get_rows_for_import(row.import_record_id).get(pk=row.pk)
        return self.response(
            data=_serialize_row(row),
            message="Row updated successfully.",
        )

    def review_import(self, request: Request, sprint_code: str, import_code: str):
        """POST /sprints/<sprint_code>/forecast/<import_code>/review/"""
        from apps.sprints.constants import ImportRowCheckStatus
        from apps.sprints.models.sprint_data_import_review_capacity_result import (
            SprintDataImportReviewCapacityResult,
        )

        svc = SprintDataImportForecastService(user=request.user)
        review, row_results = svc.review(import_code=import_code)
        has_row_errors = any(
            not all(checks.values()) for checks in row_results.values()
        )
        has_capacity_errors = SprintDataImportReviewCapacityResult.objects.filter(
            review=review, status=ImportRowCheckStatus.FAIL
        ).exists()
        return self.response(
            data={
                "review_code": review.code,
                "results": row_results,
                "has_errors": has_row_errors or has_capacity_errors,
            }
        )

    def confirm_import(self, request: Request, sprint_code: str, import_code: str):
        """POST /sprints/<sprint_code>/forecast/<import_code>/confirm/"""
        notes = (request.data.get("notes") or "").strip()
        svc = SprintDataImportForecastService(user=request.user)
        completion = svc.confirm(import_code=import_code, notes=notes)
        return self.response(
            data={
                "import_type": completion.import_type,
                "completed_at": completion.completed_at.isoformat(),
                "override_applied": completion.override_applied,
            },
            message="Import confirmed successfully.",
        )


@extend_schema(tags=["Sprints"])
class SprintDataImportActualViewSet(BaseViewSet):
    parser_classes = [MultiPartParser, JSONParser]

    def get_permissions(self):
        action_perms = {
            "upload": "sprints.import_actuals",
            "download_template": "sprints.import_actuals",
            "actuals_review_complete": "sprints.review_complete",
            "sync_project_actuals": "sprints.review_complete",
            "list_actuals_projects": "sprints.review_complete",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="Upload actuals CSV for a sprint team",
        responses={
            200: OpenApiResponse(description="Upload recorded."),
            400: OpenApiResponse(description="Validation error."),
            404: OpenApiResponse(description="Sprint or team not found."),
        },
    )
    def upload(self, request: Request, sprint_code: str, team_code: str):
        """POST /sprints/<sprint_code>/actuals/<team_code>/upload/"""
        file = request.FILES.get("file")
        if not file:
            raise ValidationException("No file provided.")
        svc = SprintDataImportActualService(user=request.user)
        record = svc.upload(sprint_code=sprint_code, team_code=team_code, file=file)
        return _upload_response(record, self)

    @extend_schema(
        summary="List actuals imports for a sprint team",
        responses={200: OpenApiResponse(description="List of imports.")},
    )
    def list_imports(self, request: Request, sprint_code: str, team_code: str):
        """GET /sprints/<sprint_code>/actuals/<team_code>/imports/"""
        svc = SprintDataImportActualService(user=request.user)
        records = svc.list_imports(sprint_code=sprint_code, team_code=team_code)
        return self.response(data={"results": [_serialize_import(r) for r in records]})

    @extend_schema(
        summary="Download actuals CSV template",
        responses={200: OpenApiResponse(description="CSV template file.")},
    )
    def download_template(self, request: Request, sprint_code: str):
        """GET /sprints/<sprint_code>/actuals/template/"""
        svc = SprintDataImportActualService(user=request.user)
        return svc.get_template_response()

    @extend_schema(
        summary="Mark sprint actuals review complete and populate recharge details",
        responses={
            200: OpenApiResponse(description="Review marked complete."),
            404: OpenApiResponse(description="Sprint not found."),
        },
    )
    def actuals_review_complete(self, request: Request, sprint_code: str):
        """POST /sprints/<sprint_code>/actuals/review-complete/"""
        from apps.recharges.services import RechargeDetailService
        from apps.sprints.selectors import get_sprint_by_code

        sprint = get_sprint_by_code(sprint_code)
        if sprint is None:
            raise NotFoundException(
                resource="Sprint", lookup_field="code", lookup_value=sprint_code
            )

        svc = RechargeDetailService(user=request.user)
        count = svc.populate_from_sprint_actuals(sprint_id=sprint.pk)
        return self.response(
            data={"created": count},
            message="Sprint actuals review marked complete.",
        )

    @extend_schema(
        summary="List projects with actuals data for a sprint",
        responses={200: OpenApiResponse(description="List of projects.")},
    )
    def list_actuals_projects(self, request: Request, sprint_code: str):
        """GET /sprints/<sprint_code>/actuals/projects/"""
        from apps.projects.models import Project
        from apps.recharges.constants import RechargeType as RechargeTypeChoice
        from apps.recharges.models import RechargeDetail
        from apps.sprints.selectors import get_sprint_by_code

        sprint = get_sprint_by_code(sprint_code)
        if sprint is None:
            raise NotFoundException(
                resource="Sprint", lookup_field="code", lookup_value=sprint_code
            )

        project_ids = (
            RechargeDetail.objects.filter(
                sprint=sprint,
                type=RechargeTypeChoice.ACTUAL,
                project__isnull=False,
            )
            .values_list("project_id", flat=True)
            .distinct()
        )
        projects = (
            Project.objects.filter(pk__in=project_ids)
            .order_by("name")
            .values("code", "name")
        )
        return self.response(data={"results": list(projects)})

    @extend_schema(
        summary="Sync ProjectSprintActual records for a sprint",
        responses={
            200: OpenApiResponse(description="Sync complete."),
            404: OpenApiResponse(description="Sprint not found."),
        },
    )
    def sync_project_actuals(self, request: Request, sprint_code: str):
        """POST /sprints/<sprint_code>/actuals/sync-project-actuals/"""
        from apps.projects.services.project_sprint_actual import (
            ProjectSprintActualService,
        )
        from apps.sprints.selectors import get_sprint_by_code

        sprint = get_sprint_by_code(sprint_code)
        if sprint is None:
            raise NotFoundException(
                resource="Sprint", lookup_field="code", lookup_value=sprint_code
            )

        data = request.data
        all_projects: bool = data.get("all_projects", True)
        project_codes: list[str] = data.get("project_codes") or []

        project_ids: list[int] | None = None
        if not all_projects and project_codes:
            from apps.projects.models import Project

            project_ids = list(
                Project.objects.filter(code__in=project_codes).values_list(
                    "id", flat=True
                )
            )

        svc = ProjectSprintActualService(user=request.user)
        count = svc.populate_for_sprint(sprint_id=sprint.pk, project_ids=project_ids)
        return self.response(
            data={"created": count},
            message="Project actuals synced successfully.",
        )


@extend_schema(tags=["Sprints"])
class SprintDataImportActualRowViewSet(BaseViewSet):
    def get_permissions(self):
        action_perms = {
            "review_import": "sprints.review_forecast",
            "confirm_import": "sprints.confirm_forecast",
        }
        perm = action_perms.get(self.action)
        if perm:
            return [IsAuthenticated(), HasPermission(perm)]
        return [IsAuthenticated()]

    @extend_schema(
        summary="Retrieve an actuals import record",
        responses={200: OpenApiResponse(description="Import detail.")},
    )
    def retrieve_import(self, request: Request, sprint_code: str, import_code: str):
        """GET /sprints/<sprint_code>/actuals/<import_code>/"""
        record = get_import_by_code(import_code)
        if record is None:
            raise NotFoundException(
                resource="SprintDataImport",
                lookup_field="code",
                lookup_value=import_code,
            )
        from apps.sprints.constants import SprintDataImportStatus

        return self.response(
            data={
                "code": record.code,
                "version_number": record.version_number,
                "file_name": record.file_name,
                "status": record.status,
                "sprint_code": record.sprint.code if record.sprint else None,
                "sprint_name": record.sprint.name if record.sprint else None,
                "team_code": record.team.code if record.team else None,
                "team_name": record.team.name if record.team else None,
                "has_review": get_has_review_for_import(record.pk),
                "is_confirmed": record.status == SprintDataImportStatus.CONFIRMED,
            }
        )

    def list_rows(self, request: Request, sprint_code: str, import_code: str):
        """GET /sprints/<sprint_code>/actuals/<import_code>/rows/"""
        record = get_import_by_code(import_code)
        if record is None:
            raise NotFoundException(
                resource="SprintDataImport",
                lookup_field="code",
                lookup_value=import_code,
            )
        qs = get_rows_for_import(record.pk)

        check_type = request.query_params.get("check_type", "").strip()
        if check_type:
            from apps.sprints.constants import ImportRowCheck

            if check_type in ImportRowCheck.ALL:
                failing_ids = get_failing_row_ids_for_check(record.pk, check_type)
                qs = qs.filter(pk__in=failing_ids)

        sort_key = request.query_params.get("sort", "").strip()
        sort_dir = request.query_params.get("order_by", "ASC").upper()
        if sort_key in _ROW_SORT_FIELDS:
            from django.db.models import Case, FloatField, Value, When
            from django.db.models.functions import Cast

            if sort_key == "days":
                qs = qs.annotate(
                    _efforts_num=Case(
                        When(
                            efforts_override__isnull=False,
                            then=Case(
                                When(efforts_override="", then=Value(0.0)),
                                default=Cast(
                                    "efforts_override", output_field=FloatField()
                                ),
                                output_field=FloatField(),
                            ),
                        ),
                        When(efforts="", then=Value(0.0)),
                        default=Cast("efforts", output_field=FloatField()),
                        output_field=FloatField(),
                    )
                )
                order_field = "_efforts_num"
            else:
                order_field = sort_key
            prefix = "-" if sort_dir == "DESC" else ""
            qs = qs.order_by(f"{prefix}{order_field}")

        page, page_size = self.get_pagination_params(request)
        result = paginate_queryset(qs, page, page_size)
        return self.response(
            data={
                "results": [_serialize_row(r) for r in result.results],
                "pagination": {
                    "total_count": result.pagination.total_count,
                    "total_pages": result.pagination.total_pages,
                    "current_page": result.pagination.current_page,
                    "page_size": result.pagination.page_size,
                    "has_next": result.pagination.has_next,
                    "has_previous": result.pagination.has_previous,
                },
            }
        )

    def create_row(self, request: Request, sprint_code: str, import_code: str):
        """POST /sprints/<sprint_code>/actuals/<import_code>/rows/"""
        data = request.data
        svc = SprintDataImportActualService(user=request.user)
        row = svc.create_row(
            import_code=import_code,
            story_type=(data.get("story_type") or "").strip(),
            jira_id=(data.get("jira_id") or "").strip(),
            title=(data.get("title") or "").strip(),
            assignee_code_str=(data.get("assignee_code") or "").strip(),
            efforts=(data.get("efforts") or "").strip(),
            sprint_code_str=(data.get("sprint_code") or "").strip(),
            label_code_str=(data.get("label_code") or "").strip(),
            mapping_code_str=(data.get("mapping_code") or "").strip(),
        )
        row = get_rows_for_import(row.import_record_id).get(pk=row.pk)
        return self.response(
            data=_serialize_row(row),
            message="Row created successfully.",
            status_code=status.HTTP_201_CREATED,
        )

    def delete_row(
        self, request: Request, sprint_code: str, import_code: str, row_code: str
    ):
        """DELETE /sprints/<sprint_code>/actuals/<import_code>/rows/<row_code>/"""
        svc = SprintDataImportActualService(user=request.user)
        svc.delete_row(row_code=row_code)
        return self.response(
            message="Row deleted successfully.", status_code=status.HTTP_200_OK
        )

    def update_row(
        self, request: Request, sprint_code: str, import_code: str, row_code: str
    ):
        """PATCH /sprints/<sprint_code>/actuals/<import_code>/rows/<row_code>/"""
        data = request.data
        svc = SprintDataImportActualService(user=request.user)
        row = svc.update_row(
            row_code=row_code,
            story_type=(data.get("story_type") or "").strip(),
            jira_id=(data.get("jira_id") or "").strip(),
            title=(data.get("title") or "").strip(),
            assignee_code_str=(data.get("assignee_code") or "").strip(),
            efforts=(data.get("efforts") or "").strip(),
            sprint_code_str=(data.get("sprint_code") or "").strip(),
            label_code_str=(data.get("label_code") or "").strip(),
            mapping_code_str=(data.get("mapping_code") or "").strip(),
        )
        row = get_rows_for_import(row.import_record_id).get(pk=row.pk)
        return self.response(
            data=_serialize_row(row),
            message="Row updated successfully.",
        )

    def review_import(self, request: Request, sprint_code: str, import_code: str):
        """POST /sprints/<sprint_code>/actuals/<import_code>/review/"""
        from apps.sprints.constants import ImportRowCheckStatus
        from apps.sprints.models.sprint_data_import_review_capacity_result import (
            SprintDataImportReviewCapacityResult,
        )

        svc = SprintDataImportActualService(user=request.user)
        review, row_results = svc.review(import_code=import_code)
        has_row_errors = any(
            not all(checks.values()) for checks in row_results.values()
        )
        has_capacity_errors = SprintDataImportReviewCapacityResult.objects.filter(
            review=review, status=ImportRowCheckStatus.FAIL
        ).exists()
        return self.response(
            data={
                "review_code": review.code,
                "results": row_results,
                "has_errors": has_row_errors or has_capacity_errors,
            }
        )

    def confirm_import(self, request: Request, sprint_code: str, import_code: str):
        """POST /sprints/<sprint_code>/actuals/<import_code>/confirm/"""
        notes = (request.data.get("notes") or "").strip()
        svc = SprintDataImportActualService(user=request.user)
        completion = svc.confirm(import_code=import_code, notes=notes)
        return self.response(
            data={
                "import_type": completion.import_type,
                "completed_at": completion.completed_at.isoformat(),
                "override_applied": completion.override_applied,
            },
            message="Import confirmed successfully.",
        )
