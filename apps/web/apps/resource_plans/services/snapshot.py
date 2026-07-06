from __future__ import annotations

from django.db import transaction

from apps.audit.services import AuditService
from apps.core.exceptions import NotFoundException
from apps.core.services import AuditableService, paginate_queryset
from apps.core.types import ListParams, PaginatedResult
from apps.resource_plans import selectors
from apps.resource_plans.constants import AssignmentType, SnapshotStatus
from apps.resource_plans.engine.snapshot import SnapshotEngine
from apps.resource_plans.models import Plan, PlanVersion, Snapshot, SnapshotAllocation


class SnapshotService(AuditableService):
    _MODULE = "resource_plans"
    _RESOURCE_TYPE = "snapshot"

    def _snapshot(self, obj: Snapshot) -> dict:
        return {
            "label": obj.label,
            "notes": obj.notes,
            "status": obj.status,
        }

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

    def _get_snapshot(
        self, *, plan_code: str, version: int, snapshot_code: str
    ) -> Snapshot:
        version_obj = self._get_version(plan_code, version)
        obj = selectors.get_snapshot_by_code(snapshot_code)
        if obj is None or obj.version_id != version_obj.id:
            raise NotFoundException(
                resource="Snapshot", lookup_field="code", lookup_value=snapshot_code
            )
        return obj

    @transaction.atomic
    def create(
        self, *, plan_code: str, version: int, label: str, notes: str = ""
    ) -> Snapshot:
        version_obj = self._get_version(plan_code, version)
        snapshot = Snapshot.objects.create(
            plan=version_obj.plan,
            version=version_obj,
            label=label,
            notes=notes,
            status=SnapshotStatus.PENDING,
            created_by=self.user,
            updated_by=self.user,
        )

        # Deferred until the row (and this whole transaction) has actually
        # committed — the background thread uses its own DB connection and
        # must not race the request thread's still-uncommitted insert.
        transaction.on_commit(lambda: SnapshotEngine.run_in_background(snapshot.id))

        AuditService.log_create(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=snapshot.code,
            after=self._snapshot(snapshot),
            actor=self.user,
        )
        return snapshot

    def list_for_version(
        self, *, plan_code: str, version: int, params: ListParams | None = None
    ) -> PaginatedResult[Snapshot]:
        params = params or ListParams()
        version_obj = self._get_version(plan_code, version)
        qs = selectors.get_snapshots_for_version(version_obj)
        return paginate_queryset(qs, params.page, params.page_size)

    def get(self, *, plan_code: str, version: int, snapshot_code: str) -> Snapshot:
        return self._get_snapshot(
            plan_code=plan_code, version=version, snapshot_code=snapshot_code
        )

    @transaction.atomic
    def delete(self, *, plan_code: str, version: int, snapshot_code: str) -> None:
        snapshot = self._get_snapshot(
            plan_code=plan_code, version=version, snapshot_code=snapshot_code
        )
        before = self._snapshot(snapshot)
        resource_code = snapshot.code
        snapshot.delete()

        AuditService.log_delete(
            module=self._MODULE,
            resource_type=self._RESOURCE_TYPE,
            resource_code=resource_code,
            before=before,
            actor=self.user,
        )

    def list_allocations(
        self,
        *,
        plan_code: str,
        version: int,
        snapshot_code: str,
        params: ListParams | None = None,
    ) -> PaginatedResult[SnapshotAllocation]:
        params = params or ListParams()
        snapshot = self._get_snapshot(
            plan_code=plan_code, version=version, snapshot_code=snapshot_code
        )
        sprint_number = params.filters.get("sprint")
        qs = selectors.get_snapshot_allocations(
            snapshot,
            sprint_number=int(sprint_number) if sprint_number else None,
            member_name=params.filters.get("member") or None,
            team_name=params.filters.get("team") or None,
            project_name=params.filters.get("project") or None,
            assignment_type=params.filters.get("type") or None,
        )
        return paginate_queryset(qs, params.page, params.page_size)

    def get_allocation_filter_options(
        self, *, plan_code: str, version: int, snapshot_code: str
    ) -> dict:
        snapshot = self._get_snapshot(
            plan_code=plan_code, version=version, snapshot_code=snapshot_code
        )
        options = selectors.get_snapshot_allocation_filter_options(snapshot)
        options["types"] = [
            {"value": value, "label": label} for value, label in AssignmentType.choices
        ]
        return options

    def compare(
        self,
        *,
        plan_code: str,
        version: int,
        snapshot_a_code: str,
        snapshot_b_code: str,
    ) -> dict:
        snapshot_a = self._get_snapshot(
            plan_code=plan_code, version=version, snapshot_code=snapshot_a_code
        )
        snapshot_b = self._get_snapshot(
            plan_code=plan_code, version=version, snapshot_code=snapshot_b_code
        )

        def _key(row: SnapshotAllocation) -> tuple:
            return (
                row.sprint_number,
                row.member_name,
                row.project_name,
                row.phase_name,
                row.assignment_type,
            )

        rows_a = {_key(r): r for r in snapshot_a.allocations.all()}
        rows_b = {_key(r): r for r in snapshot_b.allocations.all()}

        def _cells(row: SnapshotAllocation) -> dict:
            return {
                "sprintName": row.sprint_name,
                "memberName": row.member_name,
                "teamName": row.team_name,
                "projectName": row.project_name,
                "phaseName": row.phase_name,
                "assignmentType": row.assignment_type,
                "days": str(row.days),
            }

        diff_rows = []
        for key in sorted(set(rows_a) | set(rows_b)):
            row_a = rows_a.get(key)
            row_b = rows_b.get(key)
            if row_a is not None and row_b is None:
                diff_rows.append({"type": "del", "cells": _cells(row_a)})
            elif row_a is None and row_b is not None:
                diff_rows.append({"type": "add", "cells": _cells(row_b)})
            elif row_a is not None and row_b is not None and row_a.days != row_b.days:
                diff_rows.append({"type": "del", "cells": _cells(row_a)})
                diff_rows.append({"type": "add", "cells": _cells(row_b)})
            # Equal days in both — unchanged, omitted from the diff.

        return {
            "snapshot_a": {"code": snapshot_a.code, "label": snapshot_a.label},
            "snapshot_b": {"code": snapshot_b.code, "label": snapshot_b.label},
            "rows": diff_rows,
        }
