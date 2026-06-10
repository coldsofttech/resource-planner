from django.urls import path

from apps.skills.api_views import SkillViewSet

urlpatterns = [
    path(
        "skills/",
        SkillViewSet.as_view({"get": "list", "post": "create"}),
        name="skills-list",
    ),
    path(
        "skills/stats/",
        SkillViewSet.as_view({"get": "statistics"}),
        name="skills-stats",
    ),
    # Options — must precede skills/<code>/ to avoid <code> matching "options"
    path(
        "skills/options/",
        SkillViewSet.as_view({"get": "options"}),
        name="skills-options",
    ),
    # Import — must precede skills/<code>/ to avoid <code> matching "import"
    path(
        "skills/import/specs/",
        SkillViewSet.as_view({"get": "import_specs"}),
        name="skills-import-specs",
    ),
    path(
        "skills/import/sample/",
        SkillViewSet.as_view({"get": "import_sample"}),
        name="skills-import-sample",
    ),
    path(
        "skills/import/",
        SkillViewSet.as_view({"post": "import_bulk"}),
        name="skills-import",
    ),
    # Export — specs must precede export/ to avoid prefix clash
    path(
        "skills/export/specs/",
        SkillViewSet.as_view({"get": "export_specs"}),
        name="skills-export-specs",
    ),
    path(
        "skills/export/",
        SkillViewSet.as_view({"get": "export"}),
        name="skills-export",
    ),
    path(
        "skills/<str:code>/",
        SkillViewSet.as_view(
            {"get": "retrieve", "patch": "partial_update", "delete": "destroy"}
        ),
        name="skills-detail",
    ),
    path(
        "skills/<str:code>/activate/",
        SkillViewSet.as_view({"post": "activate"}),
        name="skills-activate",
    ),
    path(
        "skills/<str:code>/deactivate/",
        SkillViewSet.as_view({"post": "deactivate"}),
        name="skills-deactivate",
    ),
    path(
        "skills/<str:code>/members/",
        SkillViewSet.as_view({"get": "members"}),
        name="skills-members",
    ),
]
