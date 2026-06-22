from django.urls import path

from apps.projects.api_views import (
    ProgrammeViewSet,
    ProjectAttachmentViewSet,
    ProjectBudgetViewSet,
    ProjectCommentViewSet,
    ProjectContactViewSet,
    ProjectEstimateViewSet,
    ProjectFollowerViewSet,
    ProjectLabelViewSet,
    ProjectLinkViewSet,
    ProjectSizeConfigViewSet,
    ProjectStatusViewSet,
    ProjectSubStatusFlatOptionsViewSet,
    ProjectSubStatusGlobalViewSet,
    ProjectSubStatusViewSet,
    ProjectTagViewSet,
    ProjectTypeViewSet,
    ProjectViewSet,
)

urlpatterns = [
    path(
        "programmes/",
        ProgrammeViewSet.as_view({"get": "list", "post": "create"}),
        name="programmes-list",
    ),
    path(
        "programmes/stats/",
        ProgrammeViewSet.as_view({"get": "statistics"}),
        name="programmes-stats",
    ),
    path(
        "programmes/options/",
        ProgrammeViewSet.as_view({"get": "options"}),
        name="programmes-options",
    ),
    path(
        "programmes/import/specs/",
        ProgrammeViewSet.as_view({"get": "import_specs"}),
        name="programmes-import-specs",
    ),
    path(
        "programmes/import/sample/",
        ProgrammeViewSet.as_view({"get": "import_sample"}),
        name="programmes-import-sample",
    ),
    path(
        "programmes/import/",
        ProgrammeViewSet.as_view({"post": "import_bulk"}),
        name="programmes-import",
    ),
    path(
        "programmes/export/specs/",
        ProgrammeViewSet.as_view({"get": "export_specs"}),
        name="programmes-export-specs",
    ),
    path(
        "programmes/export/",
        ProgrammeViewSet.as_view({"get": "export"}),
        name="programmes-export",
    ),
    path(
        "programmes/<str:code>/",
        ProgrammeViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="programmes-detail",
    ),
    path(
        "programmes/<str:code>/activate/",
        ProgrammeViewSet.as_view({"post": "activate"}),
        name="programmes-activate",
    ),
    path(
        "programmes/<str:code>/deactivate/",
        ProgrammeViewSet.as_view({"post": "deactivate"}),
        name="programmes-deactivate",
    ),
    path(
        "projects/sizes/",
        ProjectSizeConfigViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update"}
        ),
        name="project-sizes-config",
    ),
    path(
        "projects/types/",
        ProjectTypeViewSet.as_view({"get": "list", "post": "create"}),
        name="project-types-list",
    ),
    path(
        "projects/types/stats/",
        ProjectTypeViewSet.as_view({"get": "statistics"}),
        name="project-types-stats",
    ),
    path(
        "projects/types/options/",
        ProjectTypeViewSet.as_view({"get": "options"}),
        name="project-types-options",
    ),
    path(
        "projects/types/import/specs/",
        ProjectTypeViewSet.as_view({"get": "import_specs"}),
        name="project-types-import-specs",
    ),
    path(
        "projects/types/import/sample/",
        ProjectTypeViewSet.as_view({"get": "import_sample"}),
        name="project-types-import-sample",
    ),
    path(
        "projects/types/import/",
        ProjectTypeViewSet.as_view({"post": "import_bulk"}),
        name="project-types-import",
    ),
    path(
        "projects/types/export/specs/",
        ProjectTypeViewSet.as_view({"get": "export_specs"}),
        name="project-types-export-specs",
    ),
    path(
        "projects/types/export/",
        ProjectTypeViewSet.as_view({"get": "export"}),
        name="project-types-export",
    ),
    path(
        "projects/types/<str:code>/",
        ProjectTypeViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="project-types-detail",
    ),
    path(
        "projects/types/<str:code>/activate/",
        ProjectTypeViewSet.as_view({"post": "activate"}),
        name="project-types-activate",
    ),
    path(
        "projects/types/<str:code>/deactivate/",
        ProjectTypeViewSet.as_view({"post": "deactivate"}),
        name="project-types-deactivate",
    ),
    path(
        "projects/statuses/",
        ProjectStatusViewSet.as_view({"get": "list"}),
        name="project-statuses-list",
    ),
    path(
        "projects/statuses/stats/",
        ProjectStatusViewSet.as_view({"get": "statistics"}),
        name="project-statuses-stats",
    ),
    path(
        "projects/statuses/options/",
        ProjectStatusViewSet.as_view({"get": "options"}),
        name="project-statuses-options",
    ),
    path(
        "projects/statuses/export/specs/",
        ProjectStatusViewSet.as_view({"get": "export_specs"}),
        name="project-statuses-export-specs",
    ),
    path(
        "projects/statuses/export/",
        ProjectStatusViewSet.as_view({"get": "export"}),
        name="project-statuses-export",
    ),
    path(
        "projects/statuses/<str:code>/",
        ProjectStatusViewSet.as_view({"get": "retrieve"}),
        name="project-statuses-detail",
    ),
    # Sub-status nested routes
    path(
        "projects/statuses/<str:status_code>/substatus/",
        ProjectSubStatusViewSet.as_view({"get": "list", "post": "create"}),
        name="project-sub-statuses-list",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/stats/",
        ProjectSubStatusViewSet.as_view({"get": "statistics"}),
        name="project-sub-statuses-stats",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/options/",
        ProjectSubStatusViewSet.as_view({"get": "options"}),
        name="project-sub-statuses-options",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/reorder/",
        ProjectSubStatusViewSet.as_view({"post": "reorder"}),
        name="project-sub-statuses-reorder",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/import/specs/",
        ProjectSubStatusViewSet.as_view({"get": "import_specs"}),
        name="project-sub-statuses-import-specs",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/import/sample/",
        ProjectSubStatusViewSet.as_view({"get": "import_sample"}),
        name="project-sub-statuses-import-sample",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/import/",
        ProjectSubStatusViewSet.as_view({"post": "import_bulk"}),
        name="project-sub-statuses-import",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/export/specs/",
        ProjectSubStatusViewSet.as_view({"get": "export_specs"}),
        name="project-sub-statuses-export-specs",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/export/",
        ProjectSubStatusViewSet.as_view({"get": "export"}),
        name="project-sub-statuses-export",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/<str:code>/",
        ProjectSubStatusViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="project-sub-statuses-detail",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/<str:code>/activate/",
        ProjectSubStatusViewSet.as_view({"post": "activate"}),
        name="project-sub-statuses-activate",
    ),
    path(
        "projects/statuses/<str:status_code>/substatus/<str:code>/deactivate/",
        ProjectSubStatusViewSet.as_view({"post": "deactivate"}),
        name="project-sub-statuses-deactivate",
    ),
    # Flat options endpoint (for project-substatus-field without status context)
    path(
        "projects/sub-statuses/options/",
        ProjectSubStatusFlatOptionsViewSet.as_view({"get": "options"}),
        name="project-sub-statuses-flat-options",
    ),
    # Global sub-status import/export (main_status_code as CSV column)
    path(
        "projects/sub-statuses/import/specs/",
        ProjectSubStatusGlobalViewSet.as_view({"get": "import_specs"}),
        name="project-sub-statuses-global-import-specs",
    ),
    path(
        "projects/sub-statuses/import/sample/",
        ProjectSubStatusGlobalViewSet.as_view({"get": "import_sample"}),
        name="project-sub-statuses-global-import-sample",
    ),
    path(
        "projects/sub-statuses/import/",
        ProjectSubStatusGlobalViewSet.as_view({"post": "import_bulk"}),
        name="project-sub-statuses-global-import",
    ),
    path(
        "projects/sub-statuses/export/specs/",
        ProjectSubStatusGlobalViewSet.as_view({"get": "export_specs"}),
        name="project-sub-statuses-global-export-specs",
    ),
    path(
        "projects/sub-statuses/export/",
        ProjectSubStatusGlobalViewSet.as_view({"get": "export"}),
        name="project-sub-statuses-global-export",
    ),
    # Project routes
    path(
        "projects/",
        ProjectViewSet.as_view({"get": "list", "post": "create"}),
        name="projects-list",
    ),
    path(
        "projects/stats/",
        ProjectViewSet.as_view({"get": "statistics"}),
        name="projects-stats",
    ),
    path(
        "projects/options/",
        ProjectViewSet.as_view({"get": "options"}),
        name="projects-options",
    ),
    path(
        "projects/import/specs/",
        ProjectViewSet.as_view({"get": "import_specs"}),
        name="projects-import-specs",
    ),
    path(
        "projects/import/sample/",
        ProjectViewSet.as_view({"get": "import_sample"}),
        name="projects-import-sample",
    ),
    path(
        "projects/import/",
        ProjectViewSet.as_view({"post": "import_bulk"}),
        name="projects-import",
    ),
    path(
        "projects/export/specs/",
        ProjectViewSet.as_view({"get": "export_specs"}),
        name="projects-export-specs",
    ),
    path(
        "projects/export/",
        ProjectViewSet.as_view({"get": "export"}),
        name="projects-export",
    ),
    path(
        "projects/<str:code>/",
        ProjectViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="projects-detail",
    ),
    path(
        "projects/<str:code>/activate/",
        ProjectViewSet.as_view({"post": "activate"}),
        name="projects-activate",
    ),
    path(
        "projects/<str:code>/deactivate/",
        ProjectViewSet.as_view({"post": "deactivate"}),
        name="projects-deactivate",
    ),
    path(
        "projects/<str:code>/collaborators/",
        ProjectViewSet.as_view({"get": "collaborators", "post": "collaborators"}),
        name="projects-collaborators",
    ),
    path(
        "projects/<str:code>/collaborators/<str:team_code>/",
        ProjectViewSet.as_view({"delete": "remove_collaborator"}),
        name="projects-collaborators-remove",
    ),
    # Project label nested routes
    path(
        "projects/<str:code>/labels/",
        ProjectLabelViewSet.as_view({"get": "list", "post": "create"}),
        name="project-labels-list",
    ),
    path(
        "projects/<str:code>/labels/suggest/",
        ProjectLabelViewSet.as_view({"get": "suggest"}),
        name="project-labels-suggest",
    ),
    path(
        "projects/<str:code>/labels/<str:label_code>/",
        ProjectLabelViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="project-labels-detail",
    ),
    path(
        "projects/<str:code>/labels/<str:label_code>/set-default/",
        ProjectLabelViewSet.as_view({"post": "set_default"}),
        name="project-labels-set-default",
    ),
    # Project tag nested routes
    path(
        "projects/<str:code>/tags/",
        ProjectTagViewSet.as_view({"get": "list", "post": "create"}),
        name="project-tags-list",
    ),
    path(
        "projects/<str:code>/tags/<str:tag_code>/",
        ProjectTagViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="project-tags-detail",
    ),
    # Project follower nested routes
    path(
        "projects/<str:code>/followers/",
        ProjectFollowerViewSet.as_view({"get": "list", "post": "create"}),
        name="project-followers-list",
    ),
    path(
        "projects/<str:code>/followers/<str:follower_code>/",
        ProjectFollowerViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="project-followers-detail",
    ),
    # Project estimate nested routes
    path(
        "projects/<str:code>/estimates/",
        ProjectEstimateViewSet.as_view({"get": "list", "post": "create"}),
        name="project-estimates-list",
    ),
    path(
        "projects/<str:code>/estimates/export/specs/",
        ProjectEstimateViewSet.as_view({"get": "export_specs"}),
        name="project-estimates-export-specs",
    ),
    path(
        "projects/<str:code>/estimates/export/",
        ProjectEstimateViewSet.as_view({"get": "export"}),
        name="project-estimates-export",
    ),
    path(
        "projects/<str:code>/estimates/<str:estimate_code>/",
        ProjectEstimateViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="project-estimates-detail",
    ),
    path(
        "projects/<str:code>/estimates/<str:estimate_code>/activate/",
        ProjectEstimateViewSet.as_view({"post": "activate"}),
        name="project-estimates-activate",
    ),
    path(
        "projects/<str:code>/estimates/<str:estimate_code>/deactivate/",
        ProjectEstimateViewSet.as_view({"post": "deactivate"}),
        name="project-estimates-deactivate",
    ),
    path(
        "projects/<str:code>/estimates/<str:estimate_code>/history/",
        ProjectEstimateViewSet.as_view({"get": "history"}),
        name="project-estimates-history",
    ),
    # Project link nested routes
    path(
        "projects/<str:code>/links/",
        ProjectLinkViewSet.as_view({"get": "list", "post": "create"}),
        name="project-links-list",
    ),
    path(
        "projects/<str:code>/links/<str:link_code>/",
        ProjectLinkViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="project-links-detail",
    ),
    # Project budget nested routes
    path(
        "projects/<str:code>/budgets/",
        ProjectBudgetViewSet.as_view({"get": "list", "post": "create"}),
        name="project-budgets-list",
    ),
    path(
        "projects/<str:code>/budgets/export/specs/",
        ProjectBudgetViewSet.as_view({"get": "export_specs"}),
        name="project-budgets-export-specs",
    ),
    path(
        "projects/<str:code>/budgets/export/",
        ProjectBudgetViewSet.as_view({"get": "export"}),
        name="project-budgets-export",
    ),
    path(
        "projects/<str:code>/budgets/lifetime/",
        ProjectBudgetViewSet.as_view({"get": "lifetime"}),
        name="project-budgets-lifetime",
    ),
    path(
        "projects/<str:code>/budgets/<str:budget_code>/",
        ProjectBudgetViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="project-budgets-detail",
    ),
    path(
        "projects/<str:code>/budgets/<str:budget_code>/history/",
        ProjectBudgetViewSet.as_view({"get": "history"}),
        name="project-budgets-history",
    ),
    path(
        "projects/labels/options/",
        ProjectLabelViewSet.as_view({"get": "options"}),
        name="project-labels-options-global",
    ),
    path(
        "projects/<str:code>/comments/",
        ProjectCommentViewSet.as_view({"get": "list", "post": "create"}),
        name="project-comments-list",
    ),
    path(
        "projects/<str:code>/comments/<str:comment_code>/",
        ProjectCommentViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="project-comments-detail",
    ),
    path(
        "projects/<str:code>/comments/<str:comment_code>/pin/",
        ProjectCommentViewSet.as_view({"post": "pin"}),
        name="project-comments-pin",
    ),
    path(
        "projects/<str:code>/comments/<str:comment_code>/unpin/",
        ProjectCommentViewSet.as_view({"post": "unpin"}),
        name="project-comments-unpin",
    ),
    path(
        "projects/<str:code>/contacts/",
        ProjectContactViewSet.as_view({"get": "list", "post": "create"}),
        name="project-contacts-list",
    ),
    path(
        "projects/<str:code>/contacts/<str:contact_code>/",
        ProjectContactViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="project-contacts-detail",
    ),
    path(
        "projects/<str:code>/attachments/",
        ProjectAttachmentViewSet.as_view({"get": "list", "post": "create"}),
        name="project-attachments-list",
    ),
    path(
        "projects/<str:code>/attachments/<str:attachment_code>/",
        ProjectAttachmentViewSet.as_view({"delete": "destroy"}),
        name="project-attachments-detail",
    ),
    path(
        "projects/<str:code>/attachments/<str:attachment_code>/download/",
        ProjectAttachmentViewSet.as_view({"get": "download"}),
        name="project-attachments-download",
    ),
]
