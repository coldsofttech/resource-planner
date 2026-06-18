from __future__ import annotations

from .budget import ProjectBudgetViewSet
from .estimate import ProjectEstimateViewSet
from .follower import ProjectFollowerViewSet
from .label import ProjectLabelViewSet
from .link import ProjectLinkViewSet
from .programme import ProgrammeViewSet
from .project import ProjectViewSet
from .project_size_config import ProjectSizeConfigViewSet
from .project_status import (
    ProjectStatusViewSet,
    ProjectSubStatusFlatOptionsViewSet,
    ProjectSubStatusGlobalViewSet,
    ProjectSubStatusViewSet,
)
from .project_type import ProjectTypeViewSet
from .tag import ProjectTagViewSet

__all__ = [
    "ProjectSizeConfigViewSet",
    "ProgrammeViewSet",
    "ProjectTypeViewSet",
    "ProjectStatusViewSet",
    "ProjectSubStatusViewSet",
    "ProjectSubStatusFlatOptionsViewSet",
    "ProjectSubStatusGlobalViewSet",
    "ProjectViewSet",
    "ProjectLabelViewSet",
    "ProjectTagViewSet",
    "ProjectFollowerViewSet",
    "ProjectLinkViewSet",
    "ProjectEstimateViewSet",
    "ProjectBudgetViewSet",
]
