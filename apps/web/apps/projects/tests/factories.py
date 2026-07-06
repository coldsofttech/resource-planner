from datetime import date

from apps.comments.models import Comment
from apps.contacts.models import Contact
from apps.financial_years.constants import FinancialYearStatus
from apps.financial_years.models import FinancialYear
from apps.projects import selectors as project_selectors
from apps.projects.constants import (
    ContactRole,
    ProjectBudgetAction,
    ProjectEstimateAction,
    ProjectEstimateStatus,
)
from apps.projects.models import (
    Programme,
    Project,
    ProjectAttachment,
    ProjectBudget,
    ProjectBudgetStatusHistory,
    ProjectCode,
    ProjectCodeHistory,
    ProjectCollaborator,
    ProjectComment,
    ProjectContact,
    ProjectEstimate,
    ProjectEstimateStatusHistory,
    ProjectLink,
    ProjectSprintActual,
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


def make_project_link(
    project: Project | None = None,
    title: str = "Test Link",
    url: str = "https://example.com",
    **overrides,
) -> ProjectLink:
    if project is None:
        project = make_project()
    return ProjectLink.objects.create(
        project=project, title=title, url=url, **overrides
    )


def make_project_attachment(
    project: Project | None = None,
    file_name: str = "test.pdf",
    content_type: str = "application/pdf",
    file_size: int = 1024,
    file_path: str = "file:///tmp/test.pdf",
    **overrides,
) -> ProjectAttachment:
    if project is None:
        project = make_project()
    return ProjectAttachment.objects.create(
        project=project,
        file_name=file_name,
        content_type=content_type,
        file_size=file_size,
        file_path=file_path,
        **overrides,
    )


def make_financial_year(
    start_date: date = date(2024, 4, 1),
    end_date: date = date(2025, 3, 31),
    status: str = FinancialYearStatus.FUTURE,  # type: ignore[assignment]
    is_active: bool = True,
    **overrides,
) -> FinancialYear:
    return FinancialYear.objects.create(
        start_date=start_date,
        end_date=end_date,
        status=status,
        is_active=is_active,
        **overrides,
    )


def make_budget(
    project: Project | None = None,
    financial_year: FinancialYear | None = None,
    allocated_budget: float = 10000,
    **overrides,
) -> ProjectBudget:
    if project is None:
        project = make_project()
    if financial_year is None:
        financial_year = make_financial_year()
    return ProjectBudget.objects.create(
        project=project,
        financial_year=financial_year,
        allocated_budget=allocated_budget,
        **overrides,
    )


def make_budget_history(
    budget: ProjectBudget | None = None,
    action: str = ProjectBudgetAction.CREATED,  # type: ignore[assignment]
    new_allocated_budget: float = 10000,
    **overrides,
) -> ProjectBudgetStatusHistory:
    if budget is None:
        budget = make_budget()
    return ProjectBudgetStatusHistory.objects.create(
        budget=budget,
        action=action,
        new_allocated_budget=new_allocated_budget,
        **overrides,
    )


def make_contact(
    name: str = "Test Contact",
    email: str = "contact@example.com",
    **overrides,
) -> Contact:
    return Contact.objects.create(name=name, email=email, **overrides)


def make_project_contact(
    project: Project | None = None,
    contact: Contact | None = None,
    role: str = ContactRole.PROJECT,  # type: ignore[assignment]
    **overrides,
) -> ProjectContact:
    if project is None:
        project = make_project()
    if contact is None:
        contact = make_contact()
    return ProjectContact.objects.create(
        project=project, contact=contact, role=role, **overrides
    )


def make_project_comment(
    project: Project | None = None,
    comment_text: str = "Test comment.",
    **overrides,
) -> ProjectComment:
    if project is None:
        project = make_project()
    comment = Comment.objects.create(comment=comment_text)
    return ProjectComment.objects.create(project=project, comment=comment, **overrides)


def make_project_sprint_actual(
    project: Project | None = None,
    sprint=None,
    total_days: float = 5,
    total_cost: float = 5000,
    **overrides,
) -> ProjectSprintActual:
    if project is None:
        project = make_project()
    if sprint is None:
        from apps.sprints.tests.factories import make_sprint

        sprint = make_sprint()
    return ProjectSprintActual.objects.create(
        project=project,
        sprint=sprint,
        total_days=total_days,
        total_cost=total_cost,
        **overrides,
    )


def make_csv_file(content: str, name: str = "programmes.csv"):
    class FakeFile:
        def __init__(self, text: str, filename: str) -> None:
            self.name = filename
            self._data = text.encode("utf-8")
            self.size = len(self._data)

        def read(self) -> bytes:
            return self._data

    return FakeFile(content, name)
