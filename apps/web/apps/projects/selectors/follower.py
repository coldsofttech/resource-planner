from django.db.models import QuerySet

from apps.projects.models import Project, ProjectFollower


def get_all_project_followers(project: Project) -> QuerySet[ProjectFollower]:
    return (
        ProjectFollower.objects.select_related(
            "user", "user__profile", "created_by", "updated_by"
        )
        .filter(project=project)
        .order_by("user__last_name", "user__first_name")
    )


def get_project_follower_by_code(code: str) -> ProjectFollower | None:
    try:
        return ProjectFollower.objects.select_related(
            "project", "user", "user__profile", "created_by", "updated_by"
        ).get(code=code)
    except ProjectFollower.DoesNotExist:
        return None


def project_follower_exists(
    project: Project, user, exclude_pk: int | None = None
) -> bool:
    qs = ProjectFollower.objects.filter(project=project, user=user)
    if exclude_pk is not None:
        qs = qs.exclude(pk=exclude_pk)
    return qs.exists()
