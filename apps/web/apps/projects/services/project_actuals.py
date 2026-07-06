from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.db.models import OuterRef, Subquery, Sum

from apps.core.exceptions import NotFoundException
from apps.core.services import ContextService

if TYPE_CHECKING:
    from apps.financial_years.models import FinancialYear


class ProjectActualsService(ContextService):
    """Rebuilds and reads ProjectActuals records."""

    def sync_for_fy(self, sprint_id: int, project_ids: list[int] | None = None) -> int:
        """
        Rebuild ProjectActuals for the FY that contains the given sprint, then
        cascade forward to any subsequent FYs that already have ProjectActuals
        records for the affected projects (so their prev_fy_actuals stays current).

        When project_ids is provided only those projects are resynced; otherwise
        all projects active in the FY are rebuilt.

        Returns the number of ProjectActuals records created for the target FY.
        """
        from apps.projects.models import ProjectActuals
        from apps.sprints.models import Sprint

        sprint = Sprint.objects.select_related("financial_year").get(pk=sprint_id)
        fy = sprint.financial_year

        created = self._rebuild_fy(fy, project_ids)

        # Cascade: find subsequent FYs that already have ProjectActuals for
        # these projects and rebuild them in chronological order so that each
        # FY's prev_fy_actuals chains correctly from the one before it.
        cascade_project_ids = list(
            ProjectActuals.objects.filter(fy=fy).values_list("project_id", flat=True)
        )
        if project_ids is not None:
            scope = set(project_ids)
            cascade_project_ids = [p for p in cascade_project_ids if p in scope]

        if cascade_project_ids:
            from apps.financial_years.models import FinancialYear

            subsequent_fys = (
                FinancialYear.objects.filter(
                    start_date__gt=fy.start_date,
                    project_actuals__project_id__in=cascade_project_ids,
                )
                .distinct()
                .order_by("start_date")
            )
            for subsequent_fy in subsequent_fys:
                self._rebuild_fy(subsequent_fy, cascade_project_ids)

        return created

    def summary(self, project_code: str) -> dict:
        """Return the four summary card values for the project actuals tab."""
        from apps.projects import selectors
        from apps.projects.constants import ActualsRiskType, ProjectEstimateStatus
        from apps.projects.models import ProjectActuals, ProjectEstimate
        from apps.projects.models.project_actual_config import ProjectActualConfig

        project = selectors.get_project_by_code(project_code)
        if project is None:
            raise NotFoundException(
                resource="Project", lookup_field="code", lookup_value=project_code
            )

        config = ProjectActualConfig.objects.filter(project=project).first()
        ignore_risk = config.ignore_risk if config else False
        ignore_prev = config.ignore_prev_fy_actuals if config else False

        estimate = (
            ProjectEstimate.objects.filter(
                project=project, status=ProjectEstimateStatus.APPROVED
            )
            .order_by("-version")
            .first()
        )

        estimate_cost = Decimal("0")
        estimate_cost_with_contingency = Decimal("0")
        if estimate:
            base = Decimal(str(estimate.estimate_days)) * Decimal(
                str(estimate.day_rate)
            )
            contingency = (
                base * Decimal(str(estimate.contingency_percentage)) / Decimal("100")
            )
            estimate_cost = base
            estimate_cost_with_contingency = base + contingency

        latest_actual = (
            ProjectActuals.objects.filter(project=project)
            .select_related("fy")
            .order_by("-fy__start_date")
            .first()
        )

        total_actuals = Decimal("0")
        remaining_amount: Decimal | None = None
        if latest_actual:
            prev = Decimal("0") if ignore_prev else latest_actual.prev_fy_actuals
            total_actuals = latest_actual.total_cost_to_date + prev
            if estimate:
                if total_actuals <= estimate_cost:
                    remaining_amount = estimate_cost - total_actuals
                else:
                    remaining_amount = estimate_cost_with_contingency - total_actuals

        risk: str | None = None
        if (
            not ignore_risk
            and estimate
            and estimate_cost > 0
            and total_actuals > estimate_cost
        ):
            if total_actuals <= estimate_cost_with_contingency:
                risk = ActualsRiskType.WARNING  # type: ignore[assignment]
            else:
                risk = ActualsRiskType.AT_RISK  # type: ignore[assignment]

        return {
            "estimate_cost": float(estimate_cost),
            "estimate_cost_with_contingency": float(estimate_cost_with_contingency),
            "total_actuals": float(total_actuals),
            "remaining_amount": (
                float(remaining_amount) if remaining_amount is not None else None
            ),
            "risk": risk,
        }

    def get_config(self, project_code: str) -> dict:
        """Return actuals configuration for the project (defaults if none set)."""
        from apps.projects import selectors
        from apps.projects.models.project_actual_config import ProjectActualConfig

        project = selectors.get_project_by_code(project_code)
        if project is None:
            raise NotFoundException(
                resource="Project", lookup_field="code", lookup_value=project_code
            )

        config = ProjectActualConfig.objects.filter(project=project).first()
        return {
            "ignore_risk": config.ignore_risk if config else False,
            "ignore_prev_fy_actuals": (
                config.ignore_prev_fy_actuals if config else False
            ),
            "notes": config.notes if config else "",
        }

    def update_config(
        self,
        project_code: str,
        ignore_risk: bool | None = None,
        ignore_prev_fy_actuals: bool | None = None,
        notes: str | None = None,
    ) -> dict:
        """Upsert actuals configuration for the project."""
        from apps.projects import selectors
        from apps.projects.models.project_actual_config import ProjectActualConfig

        project = selectors.get_project_by_code(project_code)
        if project is None:
            raise NotFoundException(
                resource="Project", lookup_field="code", lookup_value=project_code
            )

        config, _ = ProjectActualConfig.objects.get_or_create(
            project=project,
            defaults={"created_by": self.user, "updated_by": self.user},
        )

        if ignore_risk is not None:
            config.ignore_risk = ignore_risk
        if ignore_prev_fy_actuals is not None:
            config.ignore_prev_fy_actuals = ignore_prev_fy_actuals
        if notes is not None:
            config.notes = notes

        config.updated_by = self.user
        config.save(
            update_fields=[
                "ignore_risk",
                "ignore_prev_fy_actuals",
                "notes",
                "updated_by",
                "updated_at",
            ]
        )

        return {
            "ignore_risk": config.ignore_risk,
            "ignore_prev_fy_actuals": config.ignore_prev_fy_actuals,
            "notes": config.notes,
        }

    def table_data(self, project_code: str, fy_code: str | None = None) -> list[dict]:
        """
        Return actuals table rows for the project.

        Without fy_code → one row per financial year (from ProjectActuals).
        With fy_code    → one row per sprint (from ProjectSprintActual),
                          cumulative cost resets at the start of the FY.
        """
        from apps.projects import selectors

        project = selectors.get_project_by_code(project_code)
        if project is None:
            raise NotFoundException(
                resource="Project", lookup_field="code", lookup_value=project_code
            )

        if fy_code:
            return self._sprint_rows(project, fy_code)
        return self._fy_rows(project)

    def _rebuild_fy(
        self,
        fy: FinancialYear,
        project_ids: list[int] | None = None,
    ) -> int:
        """
        Delete and recreate ProjectActuals for the given FY.

        Excludes terminal projects (Completed / Cancelled).
        Uses the chain formula:
            prev_fy_actuals = prior_fy.total_cost_to_date + prior_fy.prev_fy_actuals
        where prior_fy is the most-recent ProjectActuals record with
        fy.start_date < current fy.start_date.
        """
        from apps.projects.models import ProjectActuals, ProjectSprintActual

        # --- delete phase ---
        delete_qs = ProjectActuals.objects.filter(fy=fy)
        if project_ids is not None:
            delete_qs = delete_qs.filter(project_id__in=project_ids)
        delete_qs.delete()

        # --- FY totals — only non-terminal projects ---
        fy_qs = ProjectSprintActual.objects.filter(
            sprint__financial_year=fy,
            project__status__is_terminal=False,
        )
        if project_ids is not None:
            fy_qs = fy_qs.filter(project_id__in=project_ids)

        fy_totals: dict[int, Decimal] = {
            r["project_id"]: r["total"]
            for r in fy_qs.values("project_id").annotate(total=Sum("total_cost"))
        }

        if not fy_totals:
            return 0

        all_project_ids = list(fy_totals.keys())

        # --- chain: fetch the most recent prior-FY ProjectActuals per project ---
        prior_id_sq = (
            ProjectActuals.objects.filter(
                project_id=OuterRef("project_id"),
                fy__start_date__lt=fy.start_date,
            )
            .order_by("-fy__start_date")
            .values("id")[:1]
        )
        prev_chain_map: dict[int, Decimal] = {
            r.project_id: r.total_cost_to_date + r.prev_fy_actuals
            for r in ProjectActuals.objects.filter(
                project_id__in=all_project_ids,
                pk=Subquery(prior_id_sq),
            )
        }

        # --- create phase ---
        count = 0
        for project_id, fy_total in fy_totals.items():
            ProjectActuals.objects.create(
                project_id=project_id,
                fy=fy,
                total_cost_to_date=fy_total or Decimal("0"),
                prev_fy_actuals=prev_chain_map.get(project_id, Decimal("0")),
                created_by=self.user,
                updated_by=self.user,
            )
            count += 1

        return count

    def _fy_rows(self, project: object) -> list[dict]:
        """Per-FY breakdown from stored ProjectActuals."""
        from apps.projects.models import ProjectActuals, ProjectSprintActual

        actuals = (
            ProjectActuals.objects.filter(project=project)
            .select_related("fy")
            .order_by("fy__start_date")
        )

        fy_days_map: dict[int, Decimal] = {
            r["sprint__financial_year_id"]: r["days"]
            for r in ProjectSprintActual.objects.filter(project=project)
            .values("sprint__financial_year_id")
            .annotate(days=Sum("total_days"))
        }

        results = []
        for a in actuals:
            results.append(
                {
                    "fy": a.fy.long_fy,
                    "fy_code": a.fy.code,
                    "total_days": float(fy_days_map.get(a.fy_id) or Decimal("0")),
                    "total_cost": float(a.total_cost_to_date),
                    "cumulative_cost": float(a.total_cost_to_date + a.prev_fy_actuals),
                }
            )
        return results

    def _sprint_rows(self, project: object, fy_code: str) -> list[dict]:
        """Per-sprint breakdown for a specific FY.

        Returns every non-future sprint in the FY (from the first sprint up to
        and including the currently active sprint), ordered by sprint number.
        Sprints that have no actuals for this project are included with zeros;
        the cumulative cost is calculated in sequence so it carries forward
        correctly across zero-actuals sprints.
        """
        from apps.projects.models import ProjectSprintActual
        from apps.sprints.constants import SprintStatus
        from apps.sprints.models import Sprint

        # All started/active/completed sprints in the FY, in order
        sprints = list(
            Sprint.objects.filter(financial_year__code=fy_code)
            .exclude(status=SprintStatus.FUTURE)
            .order_by("sprint_number")
            .values("id", "name", "sprint_number")
        )

        if not sprints:
            return []

        sprint_ids = [s["id"] for s in sprints]

        # Aggregate actuals per sprint for this project
        actuals_map: dict[int, dict] = {
            r["sprint_id"]: r
            for r in ProjectSprintActual.objects.filter(
                project=project,
                sprint_id__in=sprint_ids,
            )
            .values("sprint_id")
            .annotate(
                agg_days=Sum("total_days"),
                agg_cost=Sum("total_cost"),
            )
        }

        results = []
        cumulative = Decimal("0")
        for s in sprints:
            actual = actuals_map.get(s["id"])
            cost = (actual["agg_cost"] or Decimal("0")) if actual else Decimal("0")
            days = (actual["agg_days"] or Decimal("0")) if actual else Decimal("0")
            cumulative += cost
            results.append(
                {
                    "sprint": s["name"],
                    "sprint_number": s["sprint_number"],
                    "total_days": float(days),
                    "total_cost": float(cost),
                    "cumulative_cost": float(cumulative),
                }
            )
        return results
