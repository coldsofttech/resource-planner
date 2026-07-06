from django.urls import path

from apps.resource_plans.views import (
    ResourcePlanAllocationGridView,
    ResourcePlanConflictsView,
    ResourcePlanDetailView,
    ResourcePlanListView,
    ResourcePlanPlaceholderLeavesView,
    ResourcePlanSnapshotAllocationsView,
    ResourcePlanSnapshotsView,
    ResourcePlanUtilisationView,
    ResourcePlanVersionDetailView,
)

urlpatterns = [
    path("resource-plans/", ResourcePlanListView.as_view(), name="resource-plans-list"),
    path(
        "resource-plans/<str:code>/",
        ResourcePlanDetailView.as_view(),
        name="resource-plans-detail",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/",
        ResourcePlanVersionDetailView.as_view(),
        name="resource-plans-versions-detail",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/grid/",
        ResourcePlanAllocationGridView.as_view(),
        name="resource-plans-versions-grid",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/conflicts/",
        ResourcePlanConflictsView.as_view(),
        name="resource-plans-versions-conflicts",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/placeholder-leaves/",
        ResourcePlanPlaceholderLeavesView.as_view(),
        name="resource-plans-versions-placeholder-leaves",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/utilisation/",
        ResourcePlanUtilisationView.as_view(),
        name="resource-plans-versions-utilisation",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/snapshots/",
        ResourcePlanSnapshotsView.as_view(),
        name="resource-plans-versions-snapshots",
    ),
    path(
        "resource-plans/<str:code>/versions/<version_code:version>/snapshots/<str:snapshot_code>/allocations/",
        ResourcePlanSnapshotAllocationsView.as_view(),
        name="resource-plans-versions-snapshots-allocations",
    ),
]
