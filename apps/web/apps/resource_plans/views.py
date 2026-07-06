from apps.core.views import ProtectedView
from apps.permissions.selectors import get_user_permissions


class ResourcePlanListView(ProtectedView):
    template_name = "resource_plans/index.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_add_resource_plan"] = "resource_plans.add_plan" in perms
        ctx["can_change_resource_plan"] = "resource_plans.change_plan" in perms
        ctx["can_delete_resource_plan"] = "resource_plans.delete_plan" in perms
        return ctx


class ResourcePlanDetailView(ProtectedView):
    template_name = "resource_plans/detail.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_change_resource_plan"] = "resource_plans.change_plan" in perms
        ctx["can_delete_resource_plan"] = "resource_plans.delete_plan" in perms
        ctx["can_add_resource_plan_comment"] = "resource_plans.add_plancomment" in perms
        ctx["can_change_resource_plan_comment"] = (
            "resource_plans.change_plancomment" in perms
        )
        ctx["can_delete_resource_plan_comment"] = (
            "resource_plans.delete_plancomment" in perms
        )
        ctx["can_add_resource_plan_version"] = "resource_plans.add_planversion" in perms
        ctx["can_change_resource_plan_version"] = (
            "resource_plans.change_planversion" in perms
        )
        ctx["can_delete_resource_plan_version"] = (
            "resource_plans.delete_planversion" in perms
        )
        ctx["plan_code"] = kwargs.get("code", "")
        return ctx


class ResourcePlanVersionDetailView(ProtectedView):
    template_name = "resource_plans/version_detail.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_change_resource_plan_version"] = (
            "resource_plans.change_planversion" in perms
        )
        ctx["can_delete_resource_plan_version"] = (
            "resource_plans.delete_planversion" in perms
        )
        ctx["can_add_resource_plan_version_project"] = (
            "resource_plans.add_planversionproject" in perms
        )
        ctx["can_change_resource_plan_version_project"] = (
            "resource_plans.change_planversionproject" in perms
        )
        ctx["can_delete_resource_plan_version_project"] = (
            "resource_plans.delete_planversionproject" in perms
        )
        ctx["can_view_resource_plan_version_project_budget_release"] = (
            "resource_plans.view_planbudgetrelease" in perms
        )
        ctx["can_add_resource_plan_version_project_budget_release"] = (
            "resource_plans.add_planbudgetrelease" in perms
        )
        ctx["can_change_resource_plan_version_project_budget_release"] = (
            "resource_plans.change_planbudgetrelease" in perms
        )
        ctx["can_delete_resource_plan_version_project_budget_release"] = (
            "resource_plans.delete_planbudgetrelease" in perms
        )
        ctx["can_view_resource_plan_engine_job"] = (
            "resource_plans.view_enginejob" in perms
        )
        ctx["can_add_resource_plan_engine_job"] = (
            "resource_plans.add_enginejob" in perms
        )
        ctx["can_delete_resource_plan_engine_job"] = (
            "resource_plans.delete_enginejob" in perms
        )
        ctx["can_view_resource_plan_version_team"] = (
            "resource_plans.view_planversionteam" in perms
        )
        ctx["can_add_resource_plan_version_team"] = (
            "resource_plans.add_planversionteam" in perms
        )
        ctx["can_change_resource_plan_version_team"] = (
            "resource_plans.change_planversionteam" in perms
        )
        ctx["can_delete_resource_plan_version_team"] = (
            "resource_plans.delete_planversionteam" in perms
        )
        ctx["can_view_resource_plan_phase"] = "resource_plans.view_planphase" in perms
        ctx["can_add_resource_plan_phase"] = "resource_plans.add_planphase" in perms
        ctx["can_change_resource_plan_phase"] = (
            "resource_plans.change_planphase" in perms
        )
        ctx["can_delete_resource_plan_phase"] = (
            "resource_plans.delete_planphase" in perms
        )
        ctx["phase_permissions"] = {
            "can_add": ctx["can_add_resource_plan_phase"],
            "can_change": ctx["can_change_resource_plan_phase"],
            "can_delete": ctx["can_delete_resource_plan_phase"],
        }
        ctx["can_view_resource_plan_phase_segment"] = (
            "resource_plans.view_planphasesegment" in perms
        )
        ctx["can_add_resource_plan_phase_segment"] = (
            "resource_plans.add_planphasesegment" in perms
        )
        ctx["can_delete_resource_plan_phase_segment"] = (
            "resource_plans.delete_planphasesegment" in perms
        )
        ctx["segment_permissions"] = {
            "can_view": ctx["can_view_resource_plan_phase_segment"],
            "can_add": ctx["can_add_resource_plan_phase_segment"],
            "can_delete": ctx["can_delete_resource_plan_phase_segment"],
        }
        ctx["can_view_resource_plan_phase_dependency"] = (
            "resource_plans.view_planphasedependency" in perms
        )
        ctx["can_add_resource_plan_phase_dependency"] = (
            "resource_plans.add_planphasedependency" in perms
        )
        ctx["can_change_resource_plan_phase_dependency"] = (
            "resource_plans.change_planphasedependency" in perms
        )
        ctx["can_delete_resource_plan_phase_dependency"] = (
            "resource_plans.delete_planphasedependency" in perms
        )
        ctx["dependency_permissions"] = {
            "can_view": ctx["can_view_resource_plan_phase_dependency"],
            "can_add": ctx["can_add_resource_plan_phase_dependency"],
            "can_change": ctx["can_change_resource_plan_phase_dependency"],
            "can_delete": ctx["can_delete_resource_plan_phase_dependency"],
        }
        ctx["can_view_resource_plan_phase_pause"] = (
            "resource_plans.view_planphasepause" in perms
        )
        ctx["can_add_resource_plan_phase_pause"] = (
            "resource_plans.add_planphasepause" in perms
        )
        ctx["can_change_resource_plan_phase_pause"] = (
            "resource_plans.change_planphasepause" in perms
        )
        ctx["can_delete_resource_plan_phase_pause"] = (
            "resource_plans.delete_planphasepause" in perms
        )
        ctx["pause_permissions"] = {
            "can_view": ctx["can_view_resource_plan_phase_pause"],
            "can_add": ctx["can_add_resource_plan_phase_pause"],
            "can_change": ctx["can_change_resource_plan_phase_pause"],
            "can_delete": ctx["can_delete_resource_plan_phase_pause"],
        }
        ctx["can_view_resource_plan_assignment"] = (
            "resource_plans.view_planassignment" in perms
        )
        ctx["can_add_resource_plan_assignment"] = (
            "resource_plans.add_planassignment" in perms
        )
        ctx["can_change_resource_plan_assignment"] = (
            "resource_plans.change_planassignment" in perms
        )
        ctx["can_delete_resource_plan_assignment"] = (
            "resource_plans.delete_planassignment" in perms
        )
        ctx["assignment_permissions"] = {
            "can_view": ctx["can_view_resource_plan_assignment"],
            "can_add": ctx["can_add_resource_plan_assignment"],
            "can_change": ctx["can_change_resource_plan_assignment"],
            "can_delete": ctx["can_delete_resource_plan_assignment"],
        }
        ctx["plan_code"] = kwargs.get("code", "")
        ctx["version"] = kwargs.get("version", "")
        return ctx


class ResourcePlanAllocationGridView(ProtectedView):
    template_name = "resource_plans/grid.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_view_allocation_set"] = "resource_plans.view_allocationset" in perms
        ctx["can_change_allocation_set"] = (
            "resource_plans.change_allocationset" in perms
        )
        ctx["can_change_allocation"] = "resource_plans.change_allocation" in perms
        ctx["can_view_resource_plan_engine_job"] = (
            "resource_plans.view_enginejob" in perms
        )
        ctx["can_add_resource_plan_engine_job"] = (
            "resource_plans.add_enginejob" in perms
        )
        ctx["plan_code"] = kwargs.get("code", "")
        ctx["version"] = kwargs.get("version", "")
        return ctx


class ResourcePlanPlaceholderLeavesView(ProtectedView):
    template_name = "resource_plans/placeholder_leaves.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_view_placeholder_leave"] = (
            "resource_plans.view_placeholderleave" in perms
        )
        ctx["can_add_placeholder_leave"] = (
            "resource_plans.add_placeholderleave" in perms
        )
        ctx["can_change_placeholder_leave"] = (
            "resource_plans.change_placeholderleave" in perms
        )
        ctx["can_delete_placeholder_leave"] = (
            "resource_plans.delete_placeholderleave" in perms
        )
        ctx["plan_code"] = kwargs.get("code", "")
        ctx["version"] = kwargs.get("version", "")
        return ctx


class ResourcePlanUtilisationView(ProtectedView):
    template_name = "resource_plans/utilisation.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_view_allocation_set"] = "resource_plans.view_allocationset" in perms
        ctx["plan_code"] = kwargs.get("code", "")
        ctx["version"] = kwargs.get("version", "")
        return ctx


class ResourcePlanConflictsView(ProtectedView):
    template_name = "resource_plans/conflicts.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_view_allocation_set"] = "resource_plans.view_allocationset" in perms
        ctx["can_view_conflict"] = "resource_plans.view_conflict" in perms
        ctx["can_change_conflict"] = "resource_plans.change_conflict" in perms
        ctx["can_view_manpower_request"] = (
            "resource_plans.view_manpowerrequest" in perms
        )
        ctx["can_change_manpower_request"] = (
            "resource_plans.change_manpowerrequest" in perms
        )
        ctx["plan_code"] = kwargs.get("code", "")
        ctx["version"] = kwargs.get("version", "")
        return ctx


class ResourcePlanSnapshotsView(ProtectedView):
    template_name = "resource_plans/snapshots.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_view_snapshot"] = "resource_plans.view_snapshot" in perms
        ctx["can_add_snapshot"] = "resource_plans.add_snapshot" in perms
        ctx["can_delete_snapshot"] = "resource_plans.delete_snapshot" in perms
        ctx["plan_code"] = kwargs.get("code", "")
        ctx["version"] = kwargs.get("version", "")
        return ctx


class ResourcePlanSnapshotAllocationsView(ProtectedView):
    template_name = "resource_plans/snapshot_allocations.html"

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        ctx = super().get_context_data(**kwargs)
        perms = get_user_permissions(self.request.user)
        ctx["can_view_snapshot"] = "resource_plans.view_snapshot" in perms
        ctx["plan_code"] = kwargs.get("code", "")
        ctx["version"] = kwargs.get("version", "")
        ctx["snapshot_code"] = kwargs.get("snapshot_code", "")
        return ctx
