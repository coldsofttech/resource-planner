from __future__ import annotations

from typing import List

from django.db import transaction
from django.http import HttpResponse

from apps.audit.services import AuditService
from apps.configurations.selectors import Sprint as SprintConfig
from apps.core.exceptions import NotFoundException, ValidationException
from apps.core.services import AuditableService, ExportService, FilterableQueryService
from apps.core.types import ListParams, PaginatedResult
from apps.projects import selectors
from apps.projects.constants import ProjectEstimateStatus
from apps.projects.models import (
    Project,
    ProjectEstimate,
    ProjectEstimateAction,
    ProjectEstimateStatusHistory,
)
from apps.users.models import User

_MODULE = "projects"
_RESOURCE_TYPE = "project_estimate"


def _get_project(project_code: str) -> Project:
    obj = selectors.get_project_by_code(project_code)
    if obj is None:
        raise NotFoundException(
            resource="Project", lookup_field="code", lookup_value=project_code
        )
    return obj


def _get_users(user_codes: list[str]) -> list[User]:
    users = list(User.objects.filter(profile__code__in=user_codes))
    found_codes = {u.profile.code for u in users}
    missing = set(user_codes) - found_codes
    if missing:
        raise ValidationException(f"User(s) not found: {', '.join(sorted(missing))}.")
    return users


def _record_history(
    estimate: ProjectEstimate,
    action: str,
    previous_status: str | None,
    new_status: str,
    note: str,
    actor: User | None,
) -> None:
    ProjectEstimateStatusHistory.objects.create(
        estimate=estimate,
        action=action,
        previous_status=previous_status,
        new_status=new_status,
        note=note,
        changed_by=actor,
    )


class ProjectEstimateService(AuditableService, FilterableQueryService):
    _MODULE = _MODULE
    _RESOURCE_TYPE = _RESOURCE_TYPE

    filterable_fields: dict[str, str] = {"status": "status"}
    search_fields: list[str] = ["status"]
    sortable_fields: list[str] = ["version", "status", "estimate_days", "created_at"]
    default_ordering: list[str] = ["-version"]
    filter_active_by_default: bool = False

    def get_queryset(self):
        return selectors.get_estimates_for_project(self._require_project())

    def _require_project(self) -> Project:
        project_code = getattr(self, "_project_code", None)
        if not project_code:
            raise ValidationException("project_code context is required.")
        return _get_project(project_code)

    def _snapshot(self, obj: ProjectEstimate) -> dict:
        return {
            "code": obj.code,
            "project_code": obj.project.code,
            "version": obj.version,
            "status": obj.status,
            "estimate_days": str(obj.estimate_days),
            "contingency_percentage": str(obj.contingency_percentage),
            "day_rate": obj.day_rate,
            "is_active": obj.is_active,
        }

    def get(self, code: str, *args, **kwargs) -> ProjectEstimate:
        obj = selectors.get_estimate_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="ProjectEstimate", lookup_field="code", lookup_value=code
            )
        return obj

    def list(self, params: ListParams | None = None, **kwargs) -> PaginatedResult:
        self._project_code = kwargs.pop("project_code", "")
        return super().list(params=params, **kwargs)

    @transaction.atomic
    def create(
        self,
        *,
        project_code: str,
        estimate_link: str = "",
        shared_by_codes: List[str] | None = None,
        reviewed_by_codes: List[str] | None = None,
        status: str = ProjectEstimateStatus.DRAFT[0],
        estimate_days: float = 0,
        contingency_percentage: float = 0,
        day_rate: int | None = None,
        note: str = "",
        is_active: bool = True,
    ) -> ProjectEstimate:
        project = _get_project(project_code)
        version = selectors.get_next_version(project)
        snapshot_day_rate = (
            day_rate if day_rate is not None else SprintConfig.get_sprint_point_price()
        )

        obj = ProjectEstimate.objects.create(
            project=project,
            version=version,
            estimate_link=estimate_link,
            status=status,
            estimate_days=estimate_days,
            contingency_percentage=contingency_percentage,
            day_rate=snapshot_day_rate,
            approval_email_sent=False,
            is_active=is_active,
            created_by=self.user,
            updated_by=self.user,
        )

        if shared_by_codes:
            obj.shared_by.set(_get_users(shared_by_codes))
        if reviewed_by_codes:
            obj.reviewed_by.set(_get_users(reviewed_by_codes))

        _record_history(
            obj,
            action=ProjectEstimateAction.CREATED[0],
            previous_status=None,
            new_status=obj.status,
            note=note,
            actor=self.user,
        )
        AuditService.log_create(
            module=_MODULE,
            resource_type=_RESOURCE_TYPE,
            resource_code=obj.code,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def update(self, code: str, **kwargs) -> ProjectEstimate:
        obj = self.get(code)
        before = self._snapshot(obj)
        previous_status = obj.status
        update_fields: list[str] = ["updated_by", "updated_at"]

        for field in (
            "estimate_link",
            "status",
            "estimate_days",
            "contingency_percentage",
            "day_rate",
            "is_active",
            "approval_email_sent",
        ):
            if field in kwargs:
                setattr(obj, field, kwargs[field])
                update_fields.append(field)

        obj.updated_by = self.user
        obj.save(update_fields=update_fields)

        if "shared_by_codes" in kwargs:
            obj.shared_by.set(_get_users(kwargs["shared_by_codes"] or []))
        if "reviewed_by_codes" in kwargs:
            obj.reviewed_by.set(_get_users(kwargs["reviewed_by_codes"] or []))

        new_status = obj.status
        action: str = ProjectEstimateAction.UPDATED[0]
        if "status" in kwargs and new_status == ProjectEstimateStatus.APPROVED:
            action = ProjectEstimateAction.APPROVED[0]
        elif "status" in kwargs and new_status == ProjectEstimateStatus.SUPERSEDED:
            action = ProjectEstimateAction.SUPERSEDED[0]

        _record_history(
            obj,
            action=action,
            previous_status=previous_status if previous_status != new_status else None,
            new_status=new_status,
            note=kwargs.get("note", ""),
            actor=self.user,
        )
        AuditService.log_update(
            module=_MODULE,
            resource_type=_RESOURCE_TYPE,
            resource_code=obj.code,
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def activate(self, code: str) -> ProjectEstimate:
        obj = self.get(code)
        if not obj.is_active:
            before = self._snapshot(obj)
            obj.is_active = True
            obj.updated_by = self.user
            obj.save(update_fields=["is_active", "updated_by", "updated_at"])
            AuditService.log_activate(
                module=_MODULE,
                resource_type=_RESOURCE_TYPE,
                resource_code=obj.code,
                before=before,
                after=self._snapshot(obj),
                actor=self.user,
            )
        return obj

    @transaction.atomic
    def deactivate(self, code: str) -> ProjectEstimate:
        obj = self.get(code)
        if obj.is_active:
            before = self._snapshot(obj)
            obj.is_active = False
            obj.updated_by = self.user
            obj.save(update_fields=["is_active", "updated_by", "updated_at"])
            AuditService.log_deactivate(
                module=_MODULE,
                resource_type=_RESOURCE_TYPE,
                resource_code=obj.code,
                before=before,
                after=self._snapshot(obj),
                actor=self.user,
            )
        return obj

    @transaction.atomic
    def delete(self, code: str) -> None:
        obj = self.get(code)
        obj_code = obj.code
        before = self._snapshot(obj)
        obj.delete()
        AuditService.log_delete(
            module=_MODULE,
            resource_type=_RESOURCE_TYPE,
            resource_code=obj_code,
            before=before,
            actor=self.user,
        )

    def history(self, code: str):
        obj = self.get(code)
        return selectors.get_estimate_status_history(obj)


class ProjectEstimateExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "code": "Code",
        "project": "Project",
        "version": "Version",
        "status": "Status",
        "estimate_days": "Estimate Days",
        "contingency_percentage": "Contingency %",
        "day_rate": "Day Rate (£)",
        "total_cost": "Total Cost (£)",
        "estimate_link": "Estimate Link",
        "approval_email_sent": "Approval Email Sent",
        "is_active": "Active",
        "created_at": "Created On",
        "created_by": "Created By",
        "updated_at": "Updated On",
        "updated_by": "Updated By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "code",
        "project",
        "version",
        "status",
        "estimate_days",
        "contingency_percentage",
        "day_rate",
        "total_cost",
        "is_active",
        "created_at",
    ]
    EXPORT_FILENAME = "project_estimates_export"
    EXPORT_MODULE_NAME = "Project Estimates"

    def export(
        self,
        fields: list[str] | None = None,
        export_format: str = "csv",
        filters: dict | None = None,
    ) -> HttpResponse:
        resolved = [
            f
            for f in (fields or self.DEFAULT_EXPORT_FIELDS)
            if f in self.EXPORT_FIELD_LABELS
        ] or self.DEFAULT_EXPORT_FIELDS

        from apps.projects.models import ProjectEstimate as PE

        qs = PE.objects.select_related("project", "created_by", "updated_by").order_by(
            "project__name", "-version"
        )
        if filters:
            project_code = (filters.get("project_code") or "").strip()
            if project_code:
                qs = qs.filter(project__code=project_code)
            status_filter = (filters.get("status") or "").strip()
            if status_filter:
                qs = qs.filter(status=status_filter)
            is_active_raw = filters.get("is_active")
            if is_active_raw not in (None, ""):
                if str(is_active_raw).lower() != "all":
                    qs = qs.filter(
                        is_active=str(is_active_raw).lower() not in ("false", "0")
                    )

        rows = self._prepare_rows(list(qs), resolved)

        fmt = export_format.lower()
        if fmt == "csv":
            return self._export_csv(rows)
        if fmt == "xlsx":
            return self._export_xlsx(rows)
        if fmt == "pdf":
            return self._export_pdf(rows)
        if fmt == "json":
            return self._export_json(rows)
        raise ValidationException(
            f"Unsupported export format '{export_format}'. "
            "Allowed: csv, xlsx, pdf, json."
        )
