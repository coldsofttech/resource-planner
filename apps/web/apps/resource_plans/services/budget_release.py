from __future__ import annotations

from decimal import Decimal

from django.db import transaction

from apps.audit.services import AuditService
from apps.core.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from apps.core.services import AuditableService
from apps.resource_plans import selectors
from apps.resource_plans.constants import BudgetReleaseEntryType
from apps.resource_plans.models import (
    Plan,
    PlanBudgetRelease,
    PlanVersion,
    PlanVersionProject,
)
from apps.sprints import selectors as sprint_selectors
from apps.sprints.models import Sprint


class PlanBudgetReleaseService(AuditableService):
    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "plan_budget_release"

    def _snapshot(self, obj: PlanBudgetRelease) -> dict:
        return {
            "plan_version_project_code": obj.plan_version_project.code,
            "entry_type": obj.entry_type,
            "sprint_code": obj.sprint.code if obj.sprint_id else None,
            "month": obj.month,
            "amount": float(obj.amount),
            "notes": obj.notes,
        }

    def _resource_code(
        self, plan: Plan, version_number: int, release: PlanBudgetRelease
    ) -> str:
        return f"{plan.code}-v{version_number}-{release.code}"

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

    def _get_plan_project(
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

    def _get_budget_release(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        budget_release_version_code: str,
    ) -> PlanBudgetRelease:
        plan_project = self._get_plan_project(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
        )
        obj = selectors.get_budget_release_by_code(budget_release_version_code)
        if obj is None or obj.plan_version_project_id != plan_project.id:
            raise NotFoundException(
                resource="PlanBudgetRelease",
                lookup_field="code",
                lookup_value=budget_release_version_code,
            )
        return obj

    def _resolve_sprint(self, sprint_code: str) -> Sprint:
        sprint = sprint_selectors.get_sprint_by_code(sprint_code)
        if sprint is None:
            raise NotFoundException(
                resource="Sprint", lookup_field="code", lookup_value=sprint_code
            )
        return sprint

    def _validate_entry_type_lock(
        self, plan_project: PlanVersionProject, entry_type: str
    ) -> None:
        locked_type = selectors.get_locked_entry_type_for_project(plan_project)
        if locked_type is not None and locked_type != entry_type:
            raise ValidationException(
                "All budget releases for this project must use the same "
                "release type. Delete existing releases before switching."
            )

    def _check_no_duplicate(
        self,
        plan_project: PlanVersionProject,
        entry_type: str,
        sprint: Sprint | None,
        month: str | None,
        exclude_pk: int | None = None,
    ) -> None:
        if entry_type == BudgetReleaseEntryType.SPRINT:
            if sprint is None:
                raise ValidationException("A sprint is required.")
            if selectors.budget_release_exists_for_sprint(
                plan_project, sprint, exclude_pk=exclude_pk
            ):
                raise AlreadyExistsException(
                    detail=f"A budget release already exists for sprint "
                    f"{sprint.code} on this project."
                )
        else:
            if month is None:
                raise ValidationException("A month is required.")
            if selectors.budget_release_exists_for_month(
                plan_project, month, exclude_pk=exclude_pk
            ):
                raise AlreadyExistsException(
                    detail=f"A budget release already exists for month "
                    f"{month} on this project."
                )

    def list_for_project(
        self, *, plan_code: str, version: int, project_version_code: str
    ) -> list[PlanBudgetRelease]:
        plan_project = self._get_plan_project(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
        )
        return list(selectors.get_budget_releases_for_project(plan_project))

    @transaction.atomic
    def create(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        entry_type: str,
        sprint_code: str | None,
        month: str | None,
        amount: Decimal,
        notes: str,
    ) -> PlanBudgetRelease:
        plan_project = self._get_plan_project(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
        )
        self._validate_entry_type_lock(plan_project, entry_type)

        sprint = None
        if entry_type == BudgetReleaseEntryType.SPRINT:
            if not sprint_code:
                raise ValidationException("A sprint is required.")
            sprint = self._resolve_sprint(sprint_code)
            month = None

        self._check_no_duplicate(plan_project, entry_type, sprint, month)

        obj = PlanBudgetRelease.objects.create(
            plan_version_project=plan_project,
            entry_type=entry_type,
            sprint=sprint,
            month=month,
            amount=amount,
            notes=notes,
            created_by=self.user,
            updated_by=self.user,
        )

        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=self._resource_code(
                plan_project.version.plan, plan_project.version.version, obj
            ),
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def update(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        budget_release_version_code: str,
        sprint_code: str | None,
        month: str | None,
        amount: Decimal,
        notes: str,
    ) -> PlanBudgetRelease:
        obj = self._get_budget_release(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            budget_release_version_code=budget_release_version_code,
        )
        before = self._snapshot(obj)

        sprint = None
        if obj.entry_type == BudgetReleaseEntryType.SPRINT:
            if not sprint_code:
                raise ValidationException("A sprint is required.")
            sprint = self._resolve_sprint(sprint_code)
            month = None
        else:
            if not month:
                raise ValidationException("A month is required.")

        self._check_no_duplicate(
            obj.plan_version_project,
            obj.entry_type,
            sprint,
            month,
            exclude_pk=obj.pk,
        )

        obj.sprint = sprint
        obj.month = month
        obj.amount = amount
        obj.notes = notes
        obj.updated_by = self.user
        obj.save(
            update_fields=[
                "sprint",
                "month",
                "amount",
                "notes",
                "updated_by",
                "updated_at",
            ]
        )

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=self._resource_code(
                obj.plan_version_project.version.plan,
                obj.plan_version_project.version.version,
                obj,
            ),
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def delete(
        self,
        *,
        plan_code: str,
        version: int,
        project_version_code: str,
        budget_release_version_code: str,
    ) -> None:
        obj = self._get_budget_release(
            plan_code=plan_code,
            version=version,
            project_version_code=project_version_code,
            budget_release_version_code=budget_release_version_code,
        )
        before = self._snapshot(obj)
        resource_code = self._resource_code(
            obj.plan_version_project.version.plan,
            obj.plan_version_project.version.version,
            obj,
        )
        obj.delete()

        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=resource_code,
            before=before,
            actor=self.user,
        )
