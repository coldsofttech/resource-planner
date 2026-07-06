from __future__ import annotations

from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.audit.services import AuditService
from apps.configurations.selectors import Sprint as SprintConfig
from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.core.services import AuditableService, paginate_queryset
from apps.core.types import ListParams, PaginatedResult
from apps.projects import selectors as project_selectors
from apps.projects.models import Project, ProjectBudget
from apps.resource_plans import selectors
from apps.resource_plans.constants import Basis
from apps.resource_plans.models import Plan, PlanVersion, PlanVersionProject
from apps.sprints import selectors as sprint_selectors
from apps.sprints.models import Sprint


class PlanVersionProjectService(AuditableService):
    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "plan_version_project"

    def _snapshot(self, obj: PlanVersionProject) -> dict:
        return {
            "version": obj.version.version,
            "plan_code": obj.version.plan.code,
            "project_code": obj.project.code,
            "basis": obj.basis,
            "basis_amount": float(obj.basis_amount),
            "days_required": float(obj.days_required),
            "priority_snapshot": obj.priority_snapshot,
            "priority_override": obj.priority_override,
            "confidence_snapshot": obj.confidence_snapshot,
            "confidence_override": obj.confidence_override,
            "start_sprint_code": obj.start_sprint.code if obj.start_sprint_id else None,
            "end_sprint_code": obj.end_sprint.code if obj.end_sprint_id else None,
            "dates_strict": obj.dates_strict,
        }

    def _resource_code(self, plan: Plan, version_number: int, project: Project) -> str:
        return f"{plan.code}-v{version_number}-{project.code}"

    def _get_plan(self, plan_code: str) -> Plan:
        obj = selectors.get_resource_plan_by_code(plan_code)
        if obj is None:
            raise NotFoundException(
                resource="Plan", lookup_field="code", lookup_value=plan_code
            )
        return obj

    def _get_version(self, plan_code: str, version: int) -> PlanVersion:
        plan = self._get_plan(plan_code)
        obj = selectors.get_version_by_number(plan, version)
        if obj is None:
            raise NotFoundException(
                resource="PlanVersion",
                lookup_field="version",
                lookup_value=version,
            )
        return obj

    def _get_project(self, project_code: str) -> Project:
        obj = project_selectors.get_project_by_code(project_code)
        if obj is None:
            raise NotFoundException(
                resource="Project", lookup_field="code", lookup_value=project_code
            )
        return obj

    def list_unmapped(
        self, *, plan_code: str, version: int, params: ListParams | None = None
    ) -> PaginatedResult[Project]:
        params = params or ListParams()
        version_obj = self._get_version(plan_code, version)
        qs = selectors.get_unmapped_projects(version_obj)
        if params.search:
            qs = qs.filter(name__icontains=params.search)
        return paginate_queryset(qs, params.page, params.page_size)

    def get_budget_for_project(
        self, *, plan_code: str, version: int, project_code: str
    ) -> ProjectBudget | None:
        plan = self._get_plan(plan_code)
        self._get_version(plan_code, version)
        project = self._get_project(project_code)
        return project_selectors.get_budget_for_project_and_fy(
            project, plan.financial_year
        )

    @transaction.atomic
    def create(
        self,
        *,
        plan_code: str,
        version: int,
        project_code: str,
        basis: str,
        estimate_code: str | None = None,
        basis_amount: Decimal | None = None,
        priority_override: str | None = None,
        confidence_override: str | None = None,
    ) -> PlanVersionProject:
        version_obj = self._get_version(plan_code, version)
        plan = version_obj.plan
        project = self._get_project(project_code)

        if selectors.version_project_exists(version_obj, project):
            raise AlreadyExistsException(
                detail=f"Project {project_code} is already mapped to this version."
            )

        snapshotted_budget = None
        snapshotted_estimate = None
        basis_synced_at = None

        if basis == Basis.BUDGET:
            budget = project_selectors.get_budget_for_project_and_fy(
                project, plan.financial_year
            )
            if budget is None:
                raise ValidationException(
                    "No budget is configured for this project in the "
                    "plan's financial year."
                )
            basis_amount = Decimal(str(budget.actual_budget))
            snapshotted_budget = budget
            basis_synced_at = timezone.now()
        elif basis == Basis.ESTIMATE:
            if not estimate_code:
                raise ValidationException("An estimate must be selected.")
            estimate = project_selectors.get_estimate_by_code(estimate_code)
            if estimate is None or estimate.project_id != project.id:
                raise NotFoundException(
                    resource="ProjectEstimate",
                    lookup_field="code",
                    lookup_value=estimate_code,
                )
            basis_amount = Decimal(str(estimate.total_cost))
            snapshotted_estimate = estimate
            basis_synced_at = timezone.now()
        else:
            if basis_amount is None:
                raise ValidationException("A basis amount is required.")

        sprint_point_price = Decimal(str(SprintConfig.get_sprint_point_price()))
        days_required = (
            (basis_amount / sprint_point_price) if sprint_point_price else Decimal("0")
        )

        obj = PlanVersionProject.objects.create(
            version=version_obj,
            project=project,
            basis=basis,
            basis_amount=basis_amount,
            basis_synced_at=basis_synced_at,
            snapshotted_budget=snapshotted_budget,
            snapshotted_estimate=snapshotted_estimate,
            days_required=days_required,
            priority_snapshot=project.priority,
            priority_override=priority_override or None,
            confidence_snapshot=project.confidence,
            confidence_override=confidence_override or None,
            created_by=self.user,
            updated_by=self.user,
        )

        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=self._resource_code(plan, version_obj.version, project),
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    def _current_basis_value(self, obj: PlanVersionProject) -> Decimal | None:
        if obj.basis == Basis.BUDGET and obj.snapshotted_budget_id:
            return Decimal(str(obj.snapshotted_budget.actual_budget))
        if obj.basis == Basis.ESTIMATE and obj.snapshotted_estimate_id:
            return Decimal(str(obj.snapshotted_estimate.total_cost))
        return None

    def _is_resync_eligible(self, obj: PlanVersionProject) -> bool:
        current = self._current_basis_value(obj)
        return current is not None and current != obj.basis_amount

    def _get_version_project(
        self, *, plan_code: str, version: int, project_version_code: str
    ) -> PlanVersionProject:
        version_obj = self._get_version(plan_code, version)
        obj = selectors.get_version_project_by_code(project_version_code)
        if obj is None or obj.version_id != version_obj.id:
            raise NotFoundException(
                resource="PlanVersionProject",
                lookup_field="code",
                lookup_value=project_version_code,
            )
        return obj

    def get(
        self, *, plan_code: str, version: int, project_version_code: str
    ) -> PlanVersionProject:
        return self._get_version_project(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
        )

    def _resolve_sprint(self, sprint_code: str | None) -> Sprint | None:
        if not sprint_code:
            return None
        sprint = sprint_selectors.get_sprint_by_code(sprint_code)
        if sprint is None:
            raise NotFoundException(
                resource="Sprint", lookup_field="code", lookup_value=sprint_code
            )
        return sprint

    @transaction.atomic
    def update_config(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        basis: str,
        estimate_code: str | None = None,
        basis_amount: Decimal | None = None,
        priority_override: str | None = None,
        confidence_override: str | None = None,
        start_sprint_code: str | None = None,
        end_sprint_code: str | None = None,
        dates_strict: bool = False,
    ) -> PlanVersionProject:
        obj = self._get_version_project(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
        )
        plan = obj.version.plan
        project = obj.project
        before = self._snapshot(obj)

        snapshotted_budget = None
        snapshotted_estimate = None
        basis_synced_at = None

        if basis == Basis.BUDGET:
            budget = project_selectors.get_budget_for_project_and_fy(
                project, plan.financial_year
            )
            if budget is None:
                raise ValidationException(
                    "No budget is configured for this project in the "
                    "plan's financial year."
                )
            basis_amount = Decimal(str(budget.actual_budget))
            snapshotted_budget = budget
            basis_synced_at = timezone.now()
        elif basis == Basis.ESTIMATE:
            if not estimate_code:
                raise ValidationException("An estimate must be selected.")
            estimate = project_selectors.get_estimate_by_code(estimate_code)
            if estimate is None or estimate.project_id != project.id:
                raise NotFoundException(
                    resource="ProjectEstimate",
                    lookup_field="code",
                    lookup_value=estimate_code,
                )
            basis_amount = Decimal(str(estimate.total_cost))
            snapshotted_estimate = estimate
            basis_synced_at = timezone.now()
        else:
            if basis_amount is None:
                raise ValidationException("A basis amount is required.")

        start_sprint = self._resolve_sprint(start_sprint_code)
        end_sprint = self._resolve_sprint(end_sprint_code)

        sprint_point_price = Decimal(str(SprintConfig.get_sprint_point_price()))
        days_required = (
            (basis_amount / sprint_point_price) if sprint_point_price else Decimal("0")
        )

        obj.basis = basis
        obj.basis_amount = basis_amount
        obj.basis_synced_at = basis_synced_at
        obj.snapshotted_budget = snapshotted_budget
        obj.snapshotted_estimate = snapshotted_estimate
        obj.days_required = days_required
        obj.priority_override = priority_override or None
        obj.confidence_override = confidence_override or None
        obj.start_sprint = start_sprint
        obj.end_sprint = end_sprint
        obj.dates_strict = dates_strict
        obj.updated_by = self.user
        obj.save(
            update_fields=[
                "basis",
                "basis_amount",
                "basis_synced_at",
                "snapshotted_budget",
                "snapshotted_estimate",
                "days_required",
                "priority_override",
                "confidence_override",
                "start_sprint",
                "end_sprint",
                "dates_strict",
                "updated_by",
                "updated_at",
            ]
        )

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=self._resource_code(plan, obj.version.version, project),
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    def list_configured(
        self, *, plan_code: str, version: int, params: ListParams | None = None
    ) -> PaginatedResult[PlanVersionProject]:
        params = params or ListParams()
        version_obj = self._get_version(plan_code, version)
        qs = selectors.get_configured_projects(version_obj)
        if params.search:
            qs = qs.filter(project__name__icontains=params.search)
        programme_code = params.filters.get("programme")
        if programme_code:
            qs = qs.filter(project__programme__code=programme_code)
        result = paginate_queryset(qs, params.page, params.page_size)
        for obj in result.results:
            obj.resync_hidden = not self._is_resync_eligible(obj)  # type: ignore[attr-defined]
        return result

    @transaction.atomic
    def resync(
        self, *, plan_code: str, version: int, project_version_code: str
    ) -> PlanVersionProject:
        obj = self._get_version_project(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
        )
        current = self._current_basis_value(obj)
        if current is None or current == obj.basis_amount:
            raise ValidationException("This project is already up to date.")

        before = self._snapshot(obj)

        sprint_point_price = Decimal(str(SprintConfig.get_sprint_point_price()))
        obj.basis_amount = current
        obj.basis_synced_at = timezone.now()
        obj.days_required = (
            (current / sprint_point_price) if sprint_point_price else Decimal("0")
        )
        obj.updated_by = self.user
        obj.save(
            update_fields=[
                "basis_amount",
                "basis_synced_at",
                "days_required",
                "updated_by",
                "updated_at",
            ]
        )

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=self._resource_code(
                obj.version.plan, obj.version.version, obj.project
            ),
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def delete(
        self, *, plan_code: str, version: int, project_version_code: str
    ) -> None:
        obj = self._get_version_project(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
        )
        before = self._snapshot(obj)
        resource_code = self._resource_code(
            obj.version.plan, obj.version.version, obj.project
        )
        obj.delete()

        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=resource_code,
            before=before,
            actor=self.user,
        )
