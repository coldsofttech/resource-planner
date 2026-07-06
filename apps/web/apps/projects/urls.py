from django.urls import path

from apps.projects.views import (
    CreateDemandView,
    OnboardingPortalView,
    OnboardingReviewView,
    ProgrammesListView,
    ProjectDetailView,
    ProjectFinanceView,
    ProjectSizesConfigView,
    ProjectsListView,
    ProjectStatusesListView,
    ProjectTypesListView,
)

urlpatterns = [
    path("onboarding/", OnboardingPortalView.as_view(), name="onboarding-portal"),
    path("demands/", OnboardingReviewView.as_view(), name="demands"),
    path("demands/new/", CreateDemandView.as_view(), name="demands-create"),
    path("projects/", ProjectsListView.as_view(), name="projects-list"),
    path(
        "projects/sizes/", ProjectSizesConfigView.as_view(), name="project-sizes-config"
    ),
    path("projects/types/", ProjectTypesListView.as_view(), name="project-types-list"),
    path(
        "projects/statuses/",
        ProjectStatusesListView.as_view(),
        name="project-statuses-list",
    ),
    # Finance (burn tracker) — must precede projects/<str:code>/ catch-all
    path("projects/finance/", ProjectFinanceView.as_view(), name="projects-finance"),
    path("projects/<str:code>/", ProjectDetailView.as_view(), name="project-detail"),
    path("programmes/", ProgrammesListView.as_view(), name="programmes-list"),
]
