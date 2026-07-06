from django.urls import path

from apps.resource_plans.api_views import (
    AllocationSetViewSet,
    AllocationViewSet,
    ConflictViewSet,
    EngineJobViewSet,
    GridViewSet,
    ManpowerRequestViewSet,
    PlaceholderLeaveViewSet,
    PlanAssignmentViewSet,
    PlanBudgetReleaseViewSet,
    PlanPhaseDependencyViewSet,
    PlanPhasePauseViewSet,
    PlanPhaseSegmentViewSet,
    PlanPhaseViewSet,
    PlanVersionProjectViewSet,
    PlanVersionTeamViewSet,
    ResourcePlanCommentViewSet,
    ResourcePlanVersionViewSet,
    ResourcePlanViewSet,
    SnapshotViewSet,
    UtilisationViewSet,
)

urlpatterns = [
    path(
        "resource-plans/",
        ResourcePlanViewSet.as_view({"get": "list", "post": "create"}),
        name="resource-plans-list",
    ),
    path(
        "resource-plans/stats/",
        ResourcePlanViewSet.as_view({"get": "statistics"}),
        name="resource-plans-stats",
    ),
    path(
        "resource-plans/options/",
        ResourcePlanViewSet.as_view({"get": "options"}),
        name="resource-plans-options",
    ),
    path(
        "resource-plans/<str:code>/",
        ResourcePlanViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="resource-plans-detail",
    ),
    path(
        "resource-plans/<str:code>/activate/",
        ResourcePlanViewSet.as_view({"post": "activate"}),
        name="resource-plans-activate",
    ),
    path(
        "resource-plans/<str:code>/deactivate/",
        ResourcePlanViewSet.as_view({"post": "deactivate"}),
        name="resource-plans-deactivate",
    ),
    path(
        "resource-plans/<str:code>/comments/",
        ResourcePlanCommentViewSet.as_view({"get": "list", "post": "create"}),
        name="resource-plans-comments-list",
    ),
    path(
        "resource-plans/<str:code>/comments/<str:comment_code>/",
        ResourcePlanCommentViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="resource-plans-comments-detail",
    ),
    path(
        "resource-plans/<str:code>/comments/<str:comment_code>/pin/",
        ResourcePlanCommentViewSet.as_view({"post": "pin"}),
        name="resource-plans-comments-pin",
    ),
    path(
        "resource-plans/<str:code>/comments/<str:comment_code>/unpin/",
        ResourcePlanCommentViewSet.as_view({"post": "unpin"}),
        name="resource-plans-comments-unpin",
    ),
    path(
        "resource-plans/<str:code>/versions/",
        ResourcePlanVersionViewSet.as_view({"post": "create"}),
        name="resource-plans-versions-list",
    ),
    path(
        "resource-plans/<str:code>/versions/history/",
        ResourcePlanVersionViewSet.as_view({"get": "history"}),
        name="resource-plans-versions-history",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/",
        ResourcePlanVersionViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="resource-plans-versions-detail",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/activate/",
        ResourcePlanVersionViewSet.as_view({"post": "activate"}),
        name="resource-plans-versions-activate",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/restore/",
        ResourcePlanVersionViewSet.as_view({"post": "restore"}),
        name="resource-plans-versions-restore",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/lock/",
        ResourcePlanVersionViewSet.as_view({"post": "lock"}),
        name="resource-plans-versions-lock",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/engine-jobs/",
        EngineJobViewSet.as_view({"get": "list", "post": "create"}),
        name="resource-plans-versions-engine-jobs-list",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/engine-jobs/<str:job_code>/",
        EngineJobViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="resource-plans-versions-engine-jobs-detail",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/snapshots/",
        SnapshotViewSet.as_view({"get": "list", "post": "create"}),
        name="resource-plans-versions-snapshots-list",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/snapshots/compare/",
        SnapshotViewSet.as_view({"get": "compare"}),
        name="resource-plans-versions-snapshots-compare",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/snapshots/<str:snapshot_code>/",
        SnapshotViewSet.as_view({"get": "retrieve", "delete": "destroy"}),
        name="resource-plans-versions-snapshots-detail",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/snapshots/<str:snapshot_code>/allocations/",
        SnapshotViewSet.as_view({"get": "allocations"}),
        name="resource-plans-versions-snapshots-allocations-list",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/snapshots/<str:snapshot_code>/allocations/filter-options/",
        SnapshotViewSet.as_view({"get": "allocation_filter_options"}),
        name="resource-plans-versions-snapshots-allocations-filter-options",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/placeholder-leaves/",
        PlaceholderLeaveViewSet.as_view({"get": "list"}),
        name="resource-plans-versions-placeholder-leaves-list",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/placeholder-leaves/regenerate/",
        PlaceholderLeaveViewSet.as_view({"post": "regenerate"}),
        name="resource-plans-versions-placeholder-leaves-regenerate",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/placeholder-leaves/<str:leave_code>/",
        PlaceholderLeaveViewSet.as_view(
            {"patch": "partial_update", "delete": "destroy"}
        ),
        name="resource-plans-versions-placeholder-leaves-detail",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/allocation-sets/",
        AllocationSetViewSet.as_view({"get": "list"}),
        name="resource-plans-versions-allocation-sets-list",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/allocation-sets/<str:allocation_set_code>/",
        AllocationSetViewSet.as_view({"get": "retrieve"}),
        name="resource-plans-versions-allocation-sets-detail",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/allocation-sets/<str:allocation_set_code>/activate/",
        AllocationSetViewSet.as_view({"post": "activate"}),
        name="resource-plans-versions-allocation-sets-activate",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/allocation-sets/<str:allocation_set_code>/allocations/<str:allocation_code>/override/",
        AllocationViewSet.as_view({"patch": "override"}),
        name="resource-plans-versions-allocation-sets-allocations-override",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/allocation-sets/<str:allocation_set_code>/conflicts/",
        ConflictViewSet.as_view({"get": "list"}),
        name="resource-plans-versions-allocation-sets-conflicts-list",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/allocation-sets/<str:allocation_set_code>/conflicts/<str:conflict_code>/",
        ConflictViewSet.as_view({"get": "retrieve"}),
        name="resource-plans-versions-allocation-sets-conflicts-detail",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/allocation-sets/<str:allocation_set_code>/conflicts/<str:conflict_code>/resolve/",
        ConflictViewSet.as_view({"post": "resolve"}),
        name="resource-plans-versions-allocation-sets-conflicts-resolve",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/allocation-sets/<str:allocation_set_code>/manpower-requests/",
        ManpowerRequestViewSet.as_view({"get": "list"}),
        name="resource-plans-versions-allocation-sets-manpower-requests-list",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/allocation-sets/<str:allocation_set_code>/manpower-requests/<str:manpower_request_code>/",
        ManpowerRequestViewSet.as_view({"get": "retrieve"}),
        name="resource-plans-versions-allocation-sets-manpower-requests-detail",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/allocation-sets/<str:allocation_set_code>/manpower-requests/<str:manpower_request_code>/hire/",
        ManpowerRequestViewSet.as_view({"post": "hire"}),
        name="resource-plans-versions-allocation-sets-manpower-requests-hire",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/allocation-sets/<str:allocation_set_code>/manpower-requests/<str:manpower_request_code>/rebalance/",
        ManpowerRequestViewSet.as_view({"post": "rebalance"}),
        name="resource-plans-versions-allocation-sets-manpower-requests-rebalance",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/allocation-sets/<str:allocation_set_code>/manpower-requests/<str:manpower_request_code>/dismiss/",
        ManpowerRequestViewSet.as_view({"post": "dismiss"}),
        name="resource-plans-versions-allocation-sets-manpower-requests-dismiss",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/grid/capacity/",
        GridViewSet.as_view({"get": "capacity"}),
        name="resource-plans-versions-grid-capacity",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/grid/absences/",
        GridViewSet.as_view({"get": "absences"}),
        name="resource-plans-versions-grid-absences",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/grid/allocated-capacity/",
        GridViewSet.as_view({"get": "allocated_capacity"}),
        name="resource-plans-versions-grid-allocated-capacity",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/grid/allocations/",
        GridViewSet.as_view({"get": "allocations"}),
        name="resource-plans-versions-grid-allocations",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/utilisation/teams/",
        UtilisationViewSet.as_view({"get": "teams"}),
        name="resource-plans-versions-utilisation-teams",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/utilisation/members/",
        UtilisationViewSet.as_view({"get": "members"}),
        name="resource-plans-versions-utilisation-members",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/utilisation/programmes/",
        UtilisationViewSet.as_view({"get": "programmes"}),
        name="resource-plans-versions-utilisation-programmes",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/projects/unmapped/",
        PlanVersionProjectViewSet.as_view({"get": "unmapped"}),
        name="resource-plans-versions-projects-unmapped",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/projects/budget/",
        PlanVersionProjectViewSet.as_view({"get": "budget"}),
        name="resource-plans-versions-projects-budget",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/projects/",
        PlanVersionProjectViewSet.as_view({"get": "list", "post": "create"}),
        name="resource-plans-versions-projects-list",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/projects/<str:project_version_code>/",
        PlanVersionProjectViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="resource-plans-versions-projects-detail",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/projects/<str:project_version_code>/resync/",
        PlanVersionProjectViewSet.as_view({"post": "resync"}),
        name="resource-plans-versions-projects-resync",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/projects/<str:project_version_code>/teams/",
        PlanVersionTeamViewSet.as_view({"get": "list", "post": "create"}),
        name="resource-plans-versions-projects-teams-list",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/projects/<str:project_version_code>/teams/<str:team_version_code>/",
        PlanVersionTeamViewSet.as_view(
            {"patch": "partial_update", "delete": "destroy"}
        ),
        name="resource-plans-versions-projects-teams-detail",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/projects/<str:project_version_code>/budget-releases/",
        PlanBudgetReleaseViewSet.as_view({"get": "list", "post": "create"}),
        name="resource-plans-versions-projects-budget-releases-list",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/projects/<str:project_version_code>/budget-releases/<str:budget_release_version_code>/",
        PlanBudgetReleaseViewSet.as_view(
            {"patch": "partial_update", "delete": "destroy"}
        ),
        name="resource-plans-versions-projects-budget-releases-detail",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/projects/<str:project_version_code>/teams/<str:team_version_code>/phases/",
        PlanPhaseViewSet.as_view({"get": "list", "post": "create"}),
        name="resource-plans-versions-projects-teams-phases-list",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/projects/<str:project_version_code>/teams/<str:team_version_code>/phases/<str:phase_version_code>/",
        PlanPhaseViewSet.as_view({"patch": "partial_update", "delete": "destroy"}),
        name="resource-plans-versions-projects-teams-phases-detail",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/projects/<str:project_version_code>/teams/<str:team_version_code>/phases/<str:phase_version_code>/segments/",
        PlanPhaseSegmentViewSet.as_view({"get": "list", "post": "create"}),
        name="resource-plans-versions-projects-teams-phases-segments-list",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/projects/<str:project_version_code>/teams/<str:team_version_code>/phases/<str:phase_version_code>/segments/<str:segment_version_code>/",
        PlanPhaseSegmentViewSet.as_view({"delete": "destroy"}),
        name="resource-plans-versions-projects-teams-phases-segments-detail",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/projects/<str:project_version_code>/teams/<str:team_version_code>/phases/<str:phase_version_code>/dependencies/available-predecessors/",
        PlanPhaseDependencyViewSet.as_view({"get": "available_predecessors"}),
        name="resource-plans-versions-projects-teams-phases-dependencies-available-predecessors",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/projects/<str:project_version_code>/teams/<str:team_version_code>/phases/<str:phase_version_code>/dependencies/",
        PlanPhaseDependencyViewSet.as_view({"get": "list", "post": "create"}),
        name="resource-plans-versions-projects-teams-phases-dependencies-list",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/projects/<str:project_version_code>/teams/<str:team_version_code>/phases/<str:phase_version_code>/dependencies/<str:dependency_version_code>/",
        PlanPhaseDependencyViewSet.as_view(
            {"patch": "partial_update", "delete": "destroy"}
        ),
        name="resource-plans-versions-projects-teams-phases-dependencies-detail",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/projects/<str:project_version_code>/teams/<str:team_version_code>/phases/<str:phase_version_code>/pauses/",
        PlanPhasePauseViewSet.as_view({"get": "list", "post": "create"}),
        name="resource-plans-versions-projects-teams-phases-pauses-list",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/projects/<str:project_version_code>/teams/<str:team_version_code>/phases/<str:phase_version_code>/pauses/<str:pause_version_code>/",
        PlanPhasePauseViewSet.as_view({"patch": "partial_update", "delete": "destroy"}),
        name="resource-plans-versions-projects-teams-phases-pauses-detail",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/projects/<str:project_version_code>/teams/<str:team_version_code>/phases/<str:phase_version_code>/assignments/",
        PlanAssignmentViewSet.as_view({"get": "list", "post": "create"}),
        name="resource-plans-versions-projects-teams-phases-assignments-list",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/projects/<str:project_version_code>/teams/<str:team_version_code>/phases/<str:phase_version_code>/assignments/<str:assignment_version_code>/",
        PlanAssignmentViewSet.as_view({"patch": "partial_update", "delete": "destroy"}),
        name="resource-plans-versions-projects-teams-phases-assignments-detail",
    ),
]
