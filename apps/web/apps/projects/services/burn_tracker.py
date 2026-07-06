from __future__ import annotations

import math
from decimal import Decimal

from apps.core.exceptions import NotFoundException
from apps.core.services import ContextService


class BurnTrackerService(ContextService):
    """Cross-project burn tracker for a given financial year."""

    def list_data(
        self,
        fy_code: str,
        search: str | None = None,
        programme_code: str | None = None,
        team_code: str | None = None,
        status_code: str | None = None,
        risk_filter: str | None = None,
        sort: str | None = None,
        order_by: str | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> dict:
        """Return paginated burn tracker rows for all projects in the given FY."""
        from apps.financial_years.models import FinancialYear
        from apps.projects.constants import ActualsRiskType, ProjectEstimateStatus
        from apps.projects.models import (
            ProjectActualConfig,
            ProjectActuals,
            ProjectEstimate,
            ProjectSprintActual,
        )

        try:
            fy = FinancialYear.objects.get(code=fy_code)
        except FinancialYear.DoesNotExist:
            raise NotFoundException(
                resource="Financial Year", lookup_field="code", lookup_value=fy_code
            ) from None

        from django.db.models import Q

        qs = (
            ProjectActuals.objects.filter(fy=fy)
            .select_related(
                "project",
                "project__programme",
                "project__assigned_team",
                "project__status",
                "fy",
            )
            .prefetch_related(
                "project__collaborators__team",
                "project__labels",
                "project__codes",
            )
        )

        if search:
            qs = qs.filter(
                Q(project__name__icontains=search)
                | Q(project__display_name__icontains=search)
            )
        if programme_code:
            qs = qs.filter(project__programme__code=programme_code)
        if team_code:
            qs = qs.filter(
                Q(project__assigned_team__code=team_code)
                | Q(project__collaborators__team__code=team_code)
            ).distinct()
        if status_code:
            qs = qs.filter(project__status__code=status_code)

        all_actuals = list(qs)
        project_ids = [a.project_id for a in all_actuals]

        if not project_ids:
            return self._empty_paginated(page, page_size)

        # Bulk fetch: one approved estimate per project (latest version)
        estimate_map: dict[int, tuple[Decimal, Decimal]] = {}
        seen: set[int] = set()
        for est in ProjectEstimate.objects.filter(
            project_id__in=project_ids,
            status=ProjectEstimateStatus.APPROVED,
        ).order_by("project_id", "-version"):
            pid = est.project_id
            if pid not in seen:
                seen.add(pid)
                base = Decimal(str(est.estimate_days)) * Decimal(str(est.day_rate))
                contingency = (
                    base * Decimal(str(est.contingency_percentage)) / Decimal("100")
                )
                estimate_map[pid] = (base, base + contingency)

        # Bulk fetch: actuals config per project
        config_map: dict[int, ProjectActualConfig] = {
            c.project_id: c
            for c in ProjectActualConfig.objects.filter(project_id__in=project_ids)
        }

        # All sprints for this FY (independent of project filter) — defines column order
        from apps.sprints.models import Sprint

        sprint_columns = list(
            Sprint.objects.filter(financial_year=fy)
            .values("name", "sprint_number")
            .order_by("sprint_number")
        )

        # Bulk fetch: cost per project per sprint within the FY
        sprint_cost_map: dict[int, dict[str, float]] = {}
        for entry in ProjectSprintActual.objects.filter(
            project_id__in=project_ids,
            sprint__financial_year=fy,
        ).values("project_id", "sprint__name", "total_cost"):
            pid = entry["project_id"]
            sprint_cost_map.setdefault(pid, {})[entry["sprint__name"]] = float(
                entry["total_cost"]
            )

        results = []
        for actual in all_actuals:
            project = actual.project
            config = config_map.get(project.pk)
            ignore_risk = config.ignore_risk if config else False
            ignore_prev = config.ignore_prev_fy_actuals if config else False

            estimate_cost: float | None = None
            estimate_cost_with_contingency: float | None = None
            remaining_cost: float | None = None
            risk: str | None = None

            if project.pk in estimate_map:
                base, base_with_conting = estimate_map[project.pk]
                estimate_cost = float(base)
                estimate_cost_with_contingency = float(base_with_conting)

                total = (
                    actual.total_cost_to_date
                    if ignore_prev
                    else actual.total_cost_to_date + actual.prev_fy_actuals
                )
                if total <= base:
                    remaining_cost = float(base - total)
                else:
                    remaining_cost = float(base_with_conting - total)

                if not ignore_risk and base > 0 and total > base:
                    if total <= base_with_conting:
                        risk = ActualsRiskType.WARNING  # type: ignore[assignment]
                    else:
                        risk = ActualsRiskType.AT_RISK  # type: ignore[assignment]

            labels = [
                {"label": lbl.label, "is_default": lbl.is_default, "code": lbl.code}
                for lbl in project.labels.all()
            ]

            project_code_value: str | None = None
            codes = list(project.codes.all())
            if codes:
                project_code_value = codes[0].value

            collaborators = [c.team.name for c in project.collaborators.all()]

            row = {
                "project_code": project.code,
                "project_name": project.display_name or project.name,
                "programme_name": project.programme.name if project.programme else None,
                "financial_year": fy.short_fy,
                "fy_code": fy.code,
                "labels": labels,
                "project_code_value": project_code_value,
                "assigned_team_name": (
                    project.assigned_team.name if project.assigned_team else None
                ),
                "collaborators": collaborators,
                "estimate_cost": estimate_cost,
                "estimate_cost_with_contingency": estimate_cost_with_contingency,
                "total_cost_to_date": float(actual.total_cost_to_date),
                "prev_fy_actuals": float(actual.prev_fy_actuals),
                "remaining_cost": remaining_cost,
                "sprint_costs": {
                    s["name"]: sprint_cost_map.get(project.pk, {}).get(s["name"])
                    for s in sprint_columns
                },
                "risk": risk,
                "ignore_risk": ignore_risk,
                "ignore_prev_fy_actuals": ignore_prev,
                "status_name": project.status.name if project.status else None,
                "is_active": project.is_active,
            }
            results.append(row)

        # Apply risk filter (post-computed, so applied in Python)
        if risk_filter == "none":
            results = [r for r in results if r["risk"] is None]
        elif risk_filter == "warning":
            results = [r for r in results if r["risk"] == ActualsRiskType.WARNING]
        elif risk_filter == "at_risk":
            results = [r for r in results if r["risk"] == ActualsRiskType.AT_RISK]

        # Sort
        sort_field = sort or "project_name"
        reverse = (order_by or "ASC").upper() == "DESC"
        results.sort(key=lambda r: r.get(sort_field) or "", reverse=reverse)

        # Paginate
        total_count = len(results)
        total_pages = max(1, math.ceil(total_count / page_size))
        start = (page - 1) * page_size
        end = start + page_size

        return {
            "results": results[start:end],
            "pagination": {
                "total_count": total_count,
                "total_pages": total_pages,
                "current_page": page,
                "page_size": page_size,
                "has_next": page < total_pages,
                "has_previous": page > 1,
            },
            "sprint_columns": sprint_columns,
        }

    def mark_done(self, project_code: str, sprint_code: str) -> dict:
        """Mark a project as Completed, setting the sprint it was completed in."""
        from apps.projects import selectors
        from apps.projects.models import ProjectStatus
        from apps.sprints.models import Sprint

        project = selectors.get_project_by_code(project_code)
        if project is None:
            raise NotFoundException(
                resource="Project", lookup_field="code", lookup_value=project_code
            )

        try:
            sprint = Sprint.objects.get(code=sprint_code)
        except Sprint.DoesNotExist:
            raise NotFoundException(
                resource="Sprint", lookup_field="code", lookup_value=sprint_code
            ) from None

        completed_status = ProjectStatus.objects.filter(name="Completed").first()

        update_fields = ["is_active", "sprint_completed_in", "updated_by", "updated_at"]
        project.is_active = False
        project.sprint_completed_in = sprint
        project.updated_by = self.user
        if completed_status:
            project.status = completed_status
            update_fields.append("status")
        project.save(update_fields=update_fields)

        return {"project_code": project.code, "is_active": False}

    @staticmethod
    def _empty_paginated(page: int, page_size: int) -> dict:
        return {
            "results": [],
            "pagination": {
                "total_count": 0,
                "total_pages": 1,
                "current_page": page,
                "page_size": page_size,
                "has_next": False,
                "has_previous": False,
            },
            "sprint_columns": [],
        }
