from apps.financial_years.models import FinancialYear
from apps.projects.models import Project
from apps.resource_plans.constants import (
    AllocationType,
    AssignmentType,
    Basis,
    DependencyType,
    EngineJobMode,
    PlanType,
)
from apps.resource_plans.models import (
    EngineJob,
    Plan,
    PlanAssignment,
    PlanPhase,
    PlanPhaseDependency,
    PlanVersion,
    PlanVersionProject,
    PlanVersionTeam,
)
from apps.teams.models import Team
from apps.users.models import User


def make_plan(
    name: str = "Test Plan",
    plan_type: str = str(PlanType.PROJECT),
    financial_year: FinancialYear | None = None,
    is_active: bool = True,
    **overrides,
) -> Plan:
    if financial_year is None:
        from apps.financial_years.tests.factories import make_financial_year

        financial_year = make_financial_year()
    return Plan.objects.create(
        name=name,
        plan_type=plan_type,
        financial_year=financial_year,
        is_active=is_active,
        **overrides,
    )


def make_plan_version(
    plan: Plan | None = None,
    version: int = 1,
    **overrides,
) -> PlanVersion:
    if plan is None:
        plan = make_plan()
    return PlanVersion.objects.create(plan=plan, version=version, **overrides)


def make_plan_version_project(
    version: PlanVersion | None = None,
    project: Project | None = None,
    basis: str = str(Basis.BUDGET),
    **overrides,
) -> PlanVersionProject:
    if version is None:
        version = make_plan_version()
    if project is None:
        from apps.projects.tests.factories import make_project

        project = make_project()
    return PlanVersionProject.objects.create(
        version=version, project=project, basis=basis, **overrides
    )


def make_plan_version_team(
    plan_project: PlanVersionProject | None = None,
    team: Team | None = None,
    allocation_type: str = str(AllocationType.BUDGET),
    **overrides,
) -> PlanVersionTeam:
    if plan_project is None:
        plan_project = make_plan_version_project()
    if team is None:
        from apps.teams.tests.factories import make_team

        team = make_team()
    return PlanVersionTeam.objects.create(
        plan_project=plan_project,
        team=team,
        allocation_type=allocation_type,
        **overrides,
    )


def make_plan_phase(
    plan_project_team: PlanVersionTeam | None = None,
    name: str = "Test Phase",
    sequence_order: int = 1,
    **overrides,
) -> PlanPhase:
    if plan_project_team is None:
        plan_project_team = make_plan_version_team()
    return PlanPhase.objects.create(
        plan_project_team=plan_project_team,
        name=name,
        sequence_order=sequence_order,
        **overrides,
    )


def make_plan_phase_dependency(
    phase: PlanPhase,
    predecessor_phase: PlanPhase,
    dependency_type: str = str(DependencyType.FINISH_TO_START),
    lag_sprints: int = 0,
    **overrides,
) -> PlanPhaseDependency:
    return PlanPhaseDependency.objects.create(
        phase=phase,
        predecessor_phase=predecessor_phase,
        dependency_type=dependency_type,
        lag_sprints=lag_sprints,
        **overrides,
    )


def make_plan_assignment(
    phase: PlanPhase,
    member: User,
    assignment_type: str = str(AssignmentType.ENGINEER),
    auto_assign: bool = False,
    **overrides,
) -> PlanAssignment:
    return PlanAssignment.objects.create(
        phase=phase,
        member=member,
        assignment_type=assignment_type,
        auto_assign=auto_assign,
        **overrides,
    )


def make_engine_job(
    plan: Plan | None = None,
    version: PlanVersion | None = None,
    mode: str = str(EngineJobMode.FULL),
    **overrides,
) -> EngineJob:
    if version is None:
        version = make_plan_version(plan=plan)
    if plan is None:
        plan = version.plan
    return EngineJob.objects.create(plan=plan, version=version, mode=mode, **overrides)
