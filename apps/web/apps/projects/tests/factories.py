from apps.projects import selectors as project_selectors
from apps.projects.constants import ProjectEstimateAction, ProjectEstimateStatus
from apps.projects.models import (
    Programme,
    Project,
    ProjectCode,
    ProjectCodeHistory,
    ProjectCollaborator,
    ProjectEstimate,
    ProjectEstimateStatusHistory,
    ProjectStatus,
    ProjectStatusHistory,
    ProjectSubStatus,
    ProjectTag,
    ProjectType,
)
from apps.tags.models import Tag


def make_project_type(
    name: str = "Test Type",
    description: str = "",
    is_active: bool = True,
    is_protected: bool = False,
    **overrides,
) -> ProjectType:
    return ProjectType.objects.create(
        name=name,
        description=description,
        is_active=is_active,
        is_protected=is_protected,
        **overrides,
    )


def make_programme(
    name: str = "Test Programme",
    description: str = "",
    is_active: bool = True,
    is_protected: bool = False,
    **overrides,
) -> Programme:
    return Programme.objects.create(
        name=name,
        description=description,
        is_active=is_active,
        is_protected=is_protected,
        **overrides,
    )


def make_project_status(
    name: str = "Test Status",
    is_active: bool = True,
    **overrides,
) -> ProjectStatus:
    return ProjectStatus.objects.create(name=name, is_active=is_active, **overrides)


def make_project_substatus(
    name: str = "Test Sub Status",
    status: ProjectStatus | None = None,
    order: int | None = None,
    is_active: bool = True,
    **overrides,
) -> ProjectSubStatus:
    if status is None:
        status = make_project_status("Default Status")
    if order is None:
        order = project_selectors.get_project_sub_status_max_order(status) + 1
    return ProjectSubStatus.objects.create(
        name=name,
        main_status=status,
        order=order,
        is_active=is_active,
        **overrides,
    )


def make_project(
    name: str = "Test Project",
    project_type: ProjectType | None = None,
    status: ProjectStatus | None = None,
    programme: Programme | None = None,
    is_active: bool = True,
    **overrides,
) -> Project:
    if project_type is None:
        project_type = make_project_type(f"Type for {name}")
    if status is None:
        status = make_project_status(f"Status for {name}")
    return Project.objects.create(
        name=name,
        project_type=project_type,
        status=status,
        programme=programme,
        is_active=is_active,
        **overrides,
    )


def make_project_collaborator(
    project: Project,
    team,
) -> ProjectCollaborator:
    return ProjectCollaborator.objects.create(project=project, team=team)


def make_project_status_history(
    project: Project | None = None,
    new_status: ProjectStatus | None = None,
    previous_status: ProjectStatus | None = None,
    **overrides,
) -> ProjectStatusHistory:
    if new_status is None:
        new_status = make_project_status("New Status")
    if project is None:
        project = make_project(status=new_status)
    return ProjectStatusHistory.objects.create(
        project=project,
        new_status=new_status,
        previous_status=previous_status,
        **overrides,
    )


def make_project_code(
    project: Project | None = None,
    value: str = "JIRA-001",
    note: str = "",
    **overrides,
) -> ProjectCode:
    if project is None:
        project = make_project()
    return ProjectCode.objects.create(
        project=project,
        value=value,
        note=note,
        **overrides,
    )


def make_project_code_history(
    project: Project | None = None,
    previous_code: ProjectCode | None = None,
    new_code: ProjectCode | None = None,
    **overrides,
) -> ProjectCodeHistory:
    if project is None:
        project = make_project()
    return ProjectCodeHistory.objects.create(
        project=project,
        previous_code=previous_code,
        new_code=new_code,
        **overrides,
    )


def make_estimate(
    project: Project | None = None,
    version: int = 1,
    status: str = ProjectEstimateStatus.DRAFT,  # type: ignore[assignment]
    estimate_days: float = 10,
    day_rate: int = 1000,
    contingency_percentage: float = 0,
    **overrides,
) -> ProjectEstimate:
    if project is None:
        project = make_project()
    return ProjectEstimate.objects.create(
        project=project,
        version=version,
        status=status,
        estimate_days=estimate_days,
        day_rate=day_rate,
        contingency_percentage=contingency_percentage,
        **overrides,
    )


def make_estimate_history(
    estimate: ProjectEstimate | None = None,
    action: str = ProjectEstimateAction.CREATED,  # type: ignore[assignment]
    previous_status: str | None = None,
    new_status: str = ProjectEstimateStatus.DRAFT,  # type: ignore[assignment]
    note: str = "",
    **overrides,
) -> ProjectEstimateStatusHistory:
    if estimate is None:
        estimate = make_estimate()
    return ProjectEstimateStatusHistory.objects.create(
        estimate=estimate,
        action=action,
        previous_status=previous_status,
        new_status=new_status,
        note=note,
        **overrides,
    )


def make_tag(name: str = "#test", **overrides) -> Tag:
    return Tag.objects.create(name=name, **overrides)


def make_project_tag(
    project: Project | None = None,
    tag: Tag | None = None,
    **overrides,
) -> ProjectTag:
    if project is None:
        project = make_project()
    if tag is None:
        tag = make_tag()
    return ProjectTag.objects.create(project=project, tag=tag, **overrides)


def make_csv_file(content: str, name: str = "programmes.csv"):
    class FakeFile:
        def __init__(self, text: str, filename: str) -> None:
            self.name = filename
            self._data = text.encode("utf-8")
            self.size = len(self._data)

        def read(self) -> bytes:
            return self._data

    return FakeFile(content, name)
