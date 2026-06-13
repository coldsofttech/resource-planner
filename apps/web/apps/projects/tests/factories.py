from apps.projects import selectors as project_selectors
from apps.projects.models import Programme, ProjectStatus, ProjectSubStatus, ProjectType


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


def make_csv_file(content: str, name: str = "programmes.csv"):
    class FakeFile:
        def __init__(self, text: str, filename: str) -> None:
            self.name = filename
            self._data = text.encode("utf-8")
            self.size = len(self._data)

        def read(self) -> bytes:
            return self._data

    return FakeFile(content, name)
