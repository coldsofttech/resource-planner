from __future__ import annotations

from decimal import Decimal

from django.db.models import F, Sum

from apps.recharges.constants import RechargeType as RechargeTypeChoice


class ProjectSprintActualService:
    """
    Populates ProjectSprintActual records from confirmed actuals RechargeDetail data.
    """

    def __init__(self, user: object) -> None:
        self.user = user

    def populate_for_sprint(
        self, sprint_id: int, project_ids: list[int] | None = None
    ) -> int:
        """
        Delete existing ProjectSprintActual records for the sprint (or only for
        the specified projects when project_ids is given) and recreate them by
        aggregating actuals RechargeDetail rows where the recharge_type is
        mapped to the project's project_type via ProjectTypeMapping.

        Returns the number of ProjectSprintActual records created.
        """
        from apps.projects.models import ProjectCode, ProjectSprintActual
        from apps.recharges.models import RechargeDetail

        if project_ids is not None:
            ProjectSprintActual.objects.filter(
                sprint_id=sprint_id, project_id__in=project_ids
            ).delete()
        else:
            ProjectSprintActual.objects.filter(sprint_id=sprint_id).delete()

        groups_qs = RechargeDetail.objects.filter(
            sprint_id=sprint_id,
            type=RechargeTypeChoice.ACTUAL,
            project__isnull=False,
            recharge_type__isnull=False,
        ).filter(
            recharge_type__project_type_mappings__project_type=F(
                "project__project_type"
            )
        )

        if project_ids is not None:
            groups_qs = groups_qs.filter(project_id__in=project_ids)

        groups = groups_qs.values("project_id", "label_id").annotate(
            agg_days=Sum("total_days"),
            agg_cost=Sum("total_cost"),
        )

        groups_list = list(groups)

        # Pre-fetch ProjectCode per project to avoid N+1
        affected_project_ids = {g["project_id"] for g in groups_list}
        code_map: dict[int, object] = {
            pc.project_id: pc
            for pc in ProjectCode.objects.filter(project_id__in=affected_project_ids)
        }

        count = 0
        for g in groups_list:
            project_id = g["project_id"]
            ProjectSprintActual.objects.create(
                sprint_id=sprint_id,
                project_id=project_id,
                label_id=g["label_id"],
                project_code=code_map.get(project_id),
                total_days=g["agg_days"] or Decimal("0"),
                total_cost=g["agg_cost"] or Decimal("0"),
                created_by=self.user,
                updated_by=self.user,
            )
            count += 1

        from apps.projects.services.project_actuals import ProjectActualsService

        ProjectActualsService(user=self.user).sync_for_fy(
            sprint_id=sprint_id, project_ids=project_ids
        )

        return count
