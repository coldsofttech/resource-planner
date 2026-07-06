from apps.projects.models import Project
from apps.reports.models import KPIEstimateAccuracyConfig, Report


def make_report(
    slug: str = "test-report",
    name: str = "Test Report",
    description: str = "",
    category: str = "",
    icon: str = "bi-bar-chart",
    sort_order: int = 0,
    is_active: bool = True,
    **overrides,
) -> Report:
    return Report.objects.create(
        slug=slug,
        name=name,
        description=description,
        category=category,
        icon=icon,
        sort_order=sort_order,
        is_active=is_active,
        **overrides,
    )


def make_kpi_estimate_accuracy_config(
    project: Project | None = None,
    month: str = "2025-04",
    comment: str = "Delayed due to scope change.",
    **overrides,
) -> KPIEstimateAccuracyConfig:
    if project is None:
        from apps.projects.tests.factories import make_project

        project = make_project()
    return KPIEstimateAccuracyConfig.objects.create(
        project=project, month=month, comment=comment, **overrides
    )
