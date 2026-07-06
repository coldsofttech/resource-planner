from __future__ import annotations

from .actuals import ProjectActualsViewSet
from .attachment import ProjectAttachmentViewSet
from .budget import ProjectBudgetViewSet
from .burn_tracker import BurnTrackerViewSet
from .comment import ProjectCommentViewSet
from .contact import ProjectContactViewSet
from .demand_attachments import DemandAttachmentViewSet
from .demands import DemandsViewSet
from .estimate import ProjectEstimateViewSet
from .follower import ProjectFollowerViewSet
from .label import ProjectLabelViewSet
from .link import ProjectLinkViewSet
from .onboarding import OnboardingViewSet
from .onboarding_attachments import OnboardingAttachmentUploadViewSet
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
    "BurnTrackerViewSet",
    "DemandAttachmentViewSet",
    "DemandsViewSet",
    "OnboardingViewSet",
    "OnboardingAttachmentUploadViewSet",
    "ProjectActualsViewSet",
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
    "ProjectAttachmentViewSet",
    "ProjectCommentViewSet",
    "ProjectContactViewSet",
    "ProjectLinkViewSet",
    "ProjectEstimateViewSet",
    "ProjectBudgetViewSet",
]
