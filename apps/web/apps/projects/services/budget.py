from __future__ import annotations

from django.db import transaction
from django.http import HttpResponse

from apps.audit.services import AuditService
from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.core.services import AuditableService, ExportService, FilterableQueryService
from apps.core.types import ListParams, PaginatedResult
from apps.financial_years.models import FinancialYear
from apps.projects import selectors
from apps.projects.constants import ProjectBudgetAction
from apps.projects.models import (
    Project,
    ProjectBudget,
    ProjectBudgetStatusHistory,
    ProjectEstimate,
)
from apps.users.models import User

_MODULE = "projects"
_RESOURCE_TYPE = "project_budget"


def _get_project(project_code: str) -> Project:
    obj = selectors.get_project_by_code(project_code)
    if obj is None:
        raise NotFoundException(
            resource="Project", lookup_field="code", lookup_value=project_code
        )
    return obj


def _get_financial_year(fy_code: str) -> FinancialYear:
    try:
        return FinancialYear.objects.get(code=fy_code)
    except FinancialYear.DoesNotExist as exc:
        raise NotFoundException(
            resource="FinancialYear", lookup_field="code", lookup_value=fy_code
        ) from exc


def _get_estimate(estimate_code: str) -> ProjectEstimate:
    obj = selectors.get_estimate_by_code(estimate_code)
    if obj is None:
        raise NotFoundException(
            resource="ProjectEstimate", lookup_field="code", lookup_value=estimate_code
        )
    return obj


def _record_history(
    budget: ProjectBudget,
    action: str,
    previous_allocated_budget=None,
    previous_refined_budget=None,
    previous_estimate_version: ProjectEstimate | None = None,
    previous_total_cost=None,
    new_allocated_budget=None,
    new_refined_budget=None,
    new_estimate_version: ProjectEstimate | None = None,
    new_total_cost=None,
    note: str = "",
    actor: User | None = None,
) -> None:
    ProjectBudgetStatusHistory.objects.create(
        budget=budget,
        action=action,
        previous_allocated_budget=previous_allocated_budget,
        previous_refined_budget=previous_refined_budget,
        previous_estimate_version=previous_estimate_version,
        previous_total_cost=previous_total_cost,
        new_allocated_budget=new_allocated_budget,
        new_refined_budget=new_refined_budget,
        new_estimate_version=new_estimate_version,
        new_total_cost=new_total_cost,
        note=note,
        changed_by=actor,
    )


class ProjectBudgetService(AuditableService, FilterableQueryService):
    _MODULE = _MODULE
    _RESOURCE_TYPE = _RESOURCE_TYPE

    search_fields: list[str] = []
    sortable_fields: list[str] = ["allocated_budget", "refined_budget", "created_at"]
    default_ordering: list[str] = ["-financial_year__start_date"]
    filter_active_by_default: bool = False

    def get_queryset(self):
        return selectors.get_budgets_for_project(self._require_project())

    def _require_project(self) -> Project:
        project_code = getattr(self, "_project_code", None)
        if not project_code:
            raise ValidationException("project_code context is required.")
        return _get_project(project_code)

    def _snapshot(self, obj: ProjectBudget) -> dict:
        return {
            "code": obj.code,
            "project_code": obj.project.code,
            "financial_year_code": obj.financial_year.code,
            "allocated_budget": str(obj.allocated_budget),
            "refined_budget": str(obj.refined_budget)
            if obj.refined_budget is not None
            else None,
            "estimate_version_code": obj.estimate_version.code
            if obj.estimate_version
            else None,
        }

    def get(self, code: str, *args, **kwargs) -> ProjectBudget:
        obj = selectors.get_budget_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="ProjectBudget", lookup_field="code", lookup_value=code
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
        financial_year_code: str,
        allocated_budget: float,
        refined_budget: float | None = None,
        estimate_version_code: str | None = None,
        note: str = "",
    ) -> ProjectBudget:
        project = _get_project(project_code)
        financial_year = _get_financial_year(financial_year_code)

        if selectors.budget_exists_for_project_and_fy(project, financial_year):
            raise AlreadyExistsException(
                detail=(
                    f"A budget for project '{project_code}' and financial year "
                    f"'{financial_year_code}' already exists."
                )
            )

        estimate_version = (
            _get_estimate(estimate_version_code) if estimate_version_code else None
        )

        obj = ProjectBudget.objects.create(
            project=project,
            financial_year=financial_year,
            allocated_budget=allocated_budget,
            refined_budget=refined_budget,
            estimate_version=estimate_version,
            note=note,
            created_by=self.user,
            updated_by=self.user,
        )

        _record_history(
            obj,
            action=ProjectBudgetAction.CREATED,  # type: ignore[arg-type]
            new_allocated_budget=obj.allocated_budget,
            new_refined_budget=obj.refined_budget,
            new_estimate_version=obj.estimate_version,
            new_total_cost=obj.estimate_version.total_cost
            if obj.estimate_version
            else None,
            note="",
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
    def update(self, code: str, **kwargs) -> ProjectBudget:
        obj = self.get(code)
        before = self._snapshot(obj)

        prev_allocated = obj.allocated_budget
        prev_refined = obj.refined_budget
        prev_estimate = obj.estimate_version
        prev_total_cost = (
            obj.estimate_version.total_cost if obj.estimate_version else None
        )

        update_fields: list[str] = ["updated_by", "updated_at"]

        if "allocated_budget" in kwargs:
            obj.allocated_budget = kwargs["allocated_budget"]
            update_fields.append("allocated_budget")

        if "refined_budget" in kwargs:
            obj.refined_budget = kwargs["refined_budget"]
            update_fields.append("refined_budget")

        if "note" in kwargs:
            obj.note = kwargs["note"]
            update_fields.append("note")

        if "estimate_version_code" in kwargs:
            ev_code = kwargs["estimate_version_code"]
            obj.estimate_version = _get_estimate(ev_code) if ev_code else None
            update_fields.append("estimate_version")

        obj.updated_by = self.user
        obj.save(update_fields=update_fields)

        _record_history(
            obj,
            action=ProjectBudgetAction.UPDATED,  # type: ignore[arg-type]
            previous_allocated_budget=prev_allocated,
            previous_refined_budget=prev_refined,
            previous_estimate_version=prev_estimate,
            previous_total_cost=prev_total_cost,
            new_allocated_budget=obj.allocated_budget,
            new_refined_budget=obj.refined_budget,
            new_estimate_version=obj.estimate_version,
            new_total_cost=obj.estimate_version.total_cost
            if obj.estimate_version
            else None,
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
        return selectors.get_budget_status_history(obj)

    def lifetime(self, project_code: str) -> dict:
        project = _get_project(project_code)
        return selectors.get_lifetime_budget_summary(project)


class ProjectBudgetExportService(ExportService):
    EXPORT_FIELD_LABELS: dict[str, str] = {
        "code": "Code",
        "project": "Project",
        "financial_year": "Financial Year",
        "allocated_budget": "Allocated Budget (£)",
        "refined_budget": "Refined Budget (£)",
        "actual_budget": "Actual Budget (£)",
        "estimate_version": "Estimate Version",
        "remaining_budget": "Remaining Budget (£)",
        "note": "Note",
        "created_at": "Created On",
        "created_by": "Created By",
        "updated_at": "Updated On",
        "updated_by": "Updated By",
    }
    DEFAULT_EXPORT_FIELDS: list[str] = [
        "code",
        "project",
        "financial_year",
        "allocated_budget",
        "refined_budget",
        "actual_budget",
        "estimate_version",
        "remaining_budget",
        "created_at",
    ]
    EXPORT_FILENAME = "project_budgets_export"
    EXPORT_MODULE_NAME = "Project Budgets"

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

        from apps.projects.models import ProjectBudget as PB

        qs = PB.objects.select_related(
            "project", "financial_year", "estimate_version", "created_by", "updated_by"
        ).order_by("project__name", "-financial_year__start_date")
        if filters:
            project_code = (filters.get("project_code") or "").strip()
            if project_code:
                qs = qs.filter(project__code=project_code)
            fy_code = (filters.get("financial_year_code") or "").strip()
            if fy_code:
                qs = qs.filter(financial_year__code=fy_code)

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
