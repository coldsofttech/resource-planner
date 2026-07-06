from django.urls import path

from apps.recharges.api_views import (
    ProjectTypeMappingViewSet,
    RechargeEmailViewSet,
    RechargeProjectGroupViewSet,
    RechargeTypeViewSet,
    RechargeViewSet,
)

urlpatterns = [
    # Project Groups
    path(
        "recharges/project-groups/",
        RechargeProjectGroupViewSet.as_view({"get": "list", "post": "create"}),
        name="recharge-project-groups-list",
    ),
    path(
        "recharges/project-groups/stats/",
        RechargeProjectGroupViewSet.as_view({"get": "statistics"}),
        name="recharge-project-groups-stats",
    ),
    path(
        "recharges/project-groups/<str:code>/",
        RechargeProjectGroupViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="recharge-project-groups-detail",
    ),
    # Recharges
    path(
        "recharges/",
        RechargeViewSet.as_view({"get": "list"}),
        name="recharges-list",
    ),
    path(
        "recharges/summary/",
        RechargeViewSet.as_view({"get": "summary"}),
        name="recharges-summary",
    ),
    path(
        "recharges/<str:code>/details/",
        RechargeViewSet.as_view({"get": "details"}),
        name="recharges-details",
    ),
    path(
        "recharges/<str:code>/jira/",
        RechargeViewSet.as_view({"get": "jira"}),
        name="recharges-jira",
    ),
    path(
        "recharges/types/",
        RechargeTypeViewSet.as_view({"get": "list", "post": "create"}),
        name="recharge-types-list",
    ),
    path(
        "recharges/types/stats/",
        RechargeTypeViewSet.as_view({"get": "statistics"}),
        name="recharge-types-stats",
    ),
    path(
        "recharges/types/options/",
        RechargeTypeViewSet.as_view({"get": "options"}),
        name="recharge-types-options",
    ),
    path(
        "recharges/types/import/specs/",
        RechargeTypeViewSet.as_view({"get": "import_specs"}),
        name="recharge-types-import-specs",
    ),
    path(
        "recharges/types/import/sample/",
        RechargeTypeViewSet.as_view({"get": "import_sample"}),
        name="recharge-types-import-sample",
    ),
    path(
        "recharges/types/import/",
        RechargeTypeViewSet.as_view({"post": "import_bulk"}),
        name="recharge-types-import",
    ),
    path(
        "recharges/types/export/specs/",
        RechargeTypeViewSet.as_view({"get": "export_specs"}),
        name="recharge-types-export-specs",
    ),
    path(
        "recharges/types/export/",
        RechargeTypeViewSet.as_view({"get": "export"}),
        name="recharge-types-export",
    ),
    path(
        "recharges/types/<str:code>/",
        RechargeTypeViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="recharge-types-detail",
    ),
    path(
        "recharges/types/<str:code>/activate/",
        RechargeTypeViewSet.as_view({"post": "activate"}),
        name="recharge-types-activate",
    ),
    path(
        "recharges/types/<str:code>/deactivate/",
        RechargeTypeViewSet.as_view({"post": "deactivate"}),
        name="recharge-types-deactivate",
    ),
    # Email Review
    path(
        "recharges/email-review/",
        RechargeEmailViewSet.as_view({"get": "list"}),
        name="recharge-email-review-list",
    ),
    path(
        "recharges/email-review/trigger/",
        RechargeEmailViewSet.as_view({"post": "trigger_all"}),
        name="recharge-email-review-trigger",
    ),
    path(
        "recharges/email-review/<str:code>/resend/",
        RechargeEmailViewSet.as_view({"post": "resend"}),
        name="recharge-email-review-resend",
    ),
    # ProjectTypeMapping nested routes
    path(
        "recharges/types/<str:recharge_type_code>/mappings/",
        ProjectTypeMappingViewSet.as_view({"get": "list", "post": "create"}),
        name="project-type-mappings-list",
    ),
    path(
        "recharges/types/<str:recharge_type_code>/mappings/import/specs/",
        ProjectTypeMappingViewSet.as_view({"get": "import_specs"}),
        name="project-type-mappings-import-specs",
    ),
    path(
        "recharges/types/<str:recharge_type_code>/mappings/import/sample/",
        ProjectTypeMappingViewSet.as_view({"get": "import_sample"}),
        name="project-type-mappings-import-sample",
    ),
    path(
        "recharges/types/<str:recharge_type_code>/mappings/import/",
        ProjectTypeMappingViewSet.as_view({"post": "import_bulk"}),
        name="project-type-mappings-import",
    ),
    path(
        "recharges/types/<str:recharge_type_code>/mappings/export/specs/",
        ProjectTypeMappingViewSet.as_view({"get": "export_specs"}),
        name="project-type-mappings-export-specs",
    ),
    path(
        "recharges/types/<str:recharge_type_code>/mappings/export/",
        ProjectTypeMappingViewSet.as_view({"get": "export"}),
        name="project-type-mappings-export",
    ),
    path(
        "recharges/types/<str:recharge_type_code>/mappings/<int:pk>/",
        ProjectTypeMappingViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="project-type-mappings-detail",
    ),
]
