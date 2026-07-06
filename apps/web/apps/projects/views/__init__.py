from apps.projects.views.finance import ProjectFinanceView
from apps.projects.views.onboarding import (
    CreateDemandView,
    OnboardingPortalView,
    OnboardingReviewView,
)
from apps.projects.views.programme import ProgrammesListView
from apps.projects.views.project import ProjectDetailView, ProjectsListView
from apps.projects.views.project_size_config import ProjectSizesConfigView
from apps.projects.views.project_status import ProjectStatusesListView
from apps.projects.views.project_type import ProjectTypesListView

__all__ = [
    "CreateDemandView",
    "ProjectFinanceView",
    "OnboardingPortalView",
    "OnboardingReviewView",
    "ProgrammesListView",
    "ProjectDetailView",
    "ProjectsListView",
    "ProjectSizesConfigView",
    "ProjectStatusesListView",
    "ProjectTypesListView",
]
