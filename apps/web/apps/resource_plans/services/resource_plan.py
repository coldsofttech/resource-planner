from __future__ import annotations

from django.db import transaction

from apps.audit.services import AuditService
from apps.core.exceptions import AlreadyExistsException, NotFoundException
from apps.core.services import AuditableService, FilterableQueryService
from apps.resource_plans import selectors
from apps.resource_plans.constants import VersionStatus
from apps.resource_plans.models import (
    Plan,
    PlanScope,
    PlanVersion,
)


class ResourcePlanService(AuditableService, FilterableQueryService):
    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "resource_plan"

    filterable_fields: dict[str, str] = {
        "plan_type": "plan_type",
        "financial_year": "financial_year__code",
    }
    search_fields: list[str] = ["name"]
    sortable_fields: list[str] = ["name", "plan_type", "is_active", "created_at"]
    default_ordering: list[str] = ["name"]
    filter_active_by_default: bool = True

    def get_queryset(self):
        return selectors.get_all_resource_plans()

    def _snapshot(self, plan: Plan) -> dict:
        return {
            "code": plan.code,
            "name": plan.name,
            "description": plan.description,
            "plan_type": plan.plan_type,
            "financial_year": plan.financial_year.code if plan.financial_year else None,
            "is_active": plan.is_active,
            "is_head": plan.is_head,
        }

    def get(self, code: str, *args, **kwargs) -> Plan:
        obj = selectors.get_resource_plan_by_code(code)
        if obj is None:
            raise NotFoundException(
                resource="Plan", lookup_field="code", lookup_value=code
            )
        return obj

    @transaction.atomic
    def create(
        self,
        *,
        name: str,
        plan_type: str,
        financial_year_code: str,
        description: str = "",
        is_active: bool = True,
        is_head: bool = False,
        threshold_percentage: float = 10.0,
        scope_financial_year_code: str | None = None,
        scope_programme_code: str | None = None,
        scope_project_code: str | None = None,
        scope_team_code: str | None = None,
    ) -> Plan:
        if selectors.resource_plan_exists(name):
            raise AlreadyExistsException(
                detail=f"A resource plan named '{name}' already exists."
            )

        from apps.financial_years.selectors import get_financial_year_by_code

        fy = get_financial_year_by_code(financial_year_code)
        if fy is None:
            raise NotFoundException(
                resource="FinancialYear",
                lookup_field="code",
                lookup_value=financial_year_code,
            )

        plan = Plan.objects.create(
            name=name,
            description=description,
            plan_type=plan_type,
            financial_year=fy,
            is_active=is_active,
            is_head=is_head,
            created_by=self.user,
            updated_by=self.user,
        )

        PlanVersion.objects.create(
            plan=plan,
            version=1,
            status=VersionStatus.DRAFT,
            threshold_percentage=threshold_percentage,
            created_by=self.user,
            updated_by=self.user,
        )

        scope_fy = None
        scope_programme = None
        scope_project = None
        scope_team = None

        if scope_financial_year_code:
            scope_fy = get_financial_year_by_code(scope_financial_year_code)

        if scope_programme_code:
            from apps.projects.selectors import get_programme_by_code

            scope_programme = get_programme_by_code(scope_programme_code)

        if scope_project_code:
            from apps.projects.selectors import get_project_by_code

            scope_project = get_project_by_code(scope_project_code)

        if scope_team_code:
            from apps.teams.selectors import get_team_by_code

            scope_team = get_team_by_code(scope_team_code)

        PlanScope.objects.create(
            plan=plan,
            financial_year=scope_fy,
            programme=scope_programme,
            project=scope_project,
            team=scope_team,
            created_by=self.user,
            updated_by=self.user,
        )

        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=plan.code,
            after=self._snapshot(plan),
            actor=self.user,
        )
        return plan

    @transaction.atomic
    def update(self, code: str, **kwargs) -> Plan:
        obj = self.get(code=code)
        before = self._snapshot(obj)
        update_fields: list[str] = ["updated_by", "updated_at"]

        new_name = kwargs.get("name", obj.name)
        if new_name != obj.name and selectors.resource_plan_exists(
            new_name, exclude_pk=obj.pk
        ):
            raise AlreadyExistsException(
                detail=f"A resource plan named '{new_name}' already exists."
            )

        if "name" in kwargs:
            obj.name = kwargs["name"]
            update_fields.append("name")

        if "description" in kwargs:
            obj.description = kwargs["description"]
            update_fields.append("description")

        obj.updated_by = self.user
        obj.save(update_fields=update_fields)

        if "threshold_percentage" in kwargs:
            latest_version = obj.versions.order_by("-version").first()
            if latest_version is not None:
                latest_version.threshold_percentage = kwargs["threshold_percentage"]
                latest_version.updated_by = self.user
                latest_version.save(
                    update_fields=["threshold_percentage", "updated_by", "updated_at"]
                )

        AuditService.log_update(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=obj.code,
            before=before,
            after=self._snapshot(obj),
            actor=self.user,
        )
        return obj

    @transaction.atomic
    def activate(self, code: str) -> Plan:
        obj = self.get(code=code)
        if not obj.is_active:
            before = self._snapshot(obj)
            obj.is_active = True
            obj.updated_by = self.user
            obj.save(update_fields=["is_active", "updated_by", "updated_at"])
            AuditService.log_activate(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=obj.code,
                before=before,
                after=self._snapshot(obj),
                actor=self.user,
            )
        return obj

    @transaction.atomic
    def deactivate(self, code: str) -> Plan:
        obj = self.get(code=code)
        if obj.is_active:
            before = self._snapshot(obj)
            obj.is_active = False
            obj.updated_by = self.user
            obj.save(update_fields=["is_active", "updated_by", "updated_at"])
            AuditService.log_deactivate(
                module=self._MODULE,
                resource_type=self._RESOURCE_TYPE,
                resource_code=obj.code,
                before=before,
                after=self._snapshot(obj),
                actor=self.user,
            )
        return obj

    @transaction.atomic
    def delete(self, code: str, *args, **kwargs) -> None:
        obj = self.get(code=code)
        plan_code = obj.code
        before = self._snapshot(obj)
        obj.delete()
        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=plan_code,
            before=before,
            actor=self.user,
        )

    def options(self) -> list[dict]:
        return [
            {"code": p.code, "name": p.name}
            for p in selectors.get_resource_plan_options()
        ]

    def stats(self, fields=None, *args, **kwargs) -> dict:
        all_stats = selectors.get_resource_plan_stats()
        if fields:
            return {k: v for k, v in all_stats.items() if k in fields}
        return all_stats
