from django.db.models import Count, Q, QuerySet

from apps.projects.models import (
    Project,
    ProjectCollaborator,
    ProjectStatusHistory,
)


def get_all_projects() -> QuerySet[Project]:
    return (
        Project.objects.select_related(
            "project_type",
            "programme",
            "status",
            "sub_status",
            "assigned_team",
            "created_by",
            "updated_by",
        )
        .prefetch_related("collaborators__team")
        .all()
    )


def get_project_by_code(code: str) -> Project | None:
    try:
        return (
            Project.objects.select_related(
                "project_type",
                "programme",
                "status",
                "sub_status",
                "assigned_team",
                "created_by",
                "updated_by",
            )
            .prefetch_related("collaborators__team", "codes", "labels")
            .get(code=code)
        )
    except Project.DoesNotExist:
        return None


def project_name_exists(name: str, exclude_pk: int | None = None) -> bool:
    qs = Project.objects.filter(name__iexact=name)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()


def get_project_options(programme_code: str | None = None) -> QuerySet[Project]:
    qs = (
        Project.objects.filter(is_active=True)
        .only("code", "name", "display_name")
        .order_by("name")
    )
    if programme_code:
        qs = qs.filter(programme__code=programme_code)
    return qs


def get_project_stats() -> dict:
    return Project.objects.aggregate(
        total=Count("id"),
        active=Count("id", filter=Q(is_active=True)),
        inactive=Count("id", filter=Q(is_active=False)),
    )


def get_project_collaborator(
    project: Project, team_code: str
) -> ProjectCollaborator | None:
    try:
        return ProjectCollaborator.objects.select_related("team").get(
            project=project, team__code=team_code
        )
    except ProjectCollaborator.DoesNotExist:
        return None


def get_project_status_history(project: Project) -> QuerySet[ProjectStatusHistory]:
    return (
        ProjectStatusHistory.objects.select_related(
            "previous_status",
            "new_status",
            "previous_sub_status",
            "new_sub_status",
            "changed_by",
        )
        .filter(project=project)
        .order_by("-changed_on")
    )
