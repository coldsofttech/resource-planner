from apps.projects.models import ProjectType
from apps.recharges.models import ProjectTypeMapping, RechargeType


def make_recharge_type(
    name: str = "BAU",
    description: str = "",
    is_active: bool = True,
    **overrides,
) -> RechargeType:
    return RechargeType.objects.create(
        name=name,
        description=description,
        is_active=is_active,
        **overrides,
    )


def make_project_type_mapping(
    recharge_type: RechargeType,
    project_type: ProjectType,
    **overrides,
) -> ProjectTypeMapping:
    return ProjectTypeMapping.objects.create(
        recharge_type=recharge_type,
        project_type=project_type,
        **overrides,
    )


class FakeCsvFile:
    def __init__(self, content: str, name: str = "recharges.csv") -> None:
        self.name = name
        self._data = content.encode("utf-8")
        self.size = len(self._data)

    def read(self) -> bytes:
        return self._data
