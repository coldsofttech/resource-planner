from __future__ import annotations

import logging
import threading
from typing import Any, Callable

from django.db import close_old_connections
from django.utils import timezone

from apps.audit.services import AuditService
from apps.core.exceptions import ValidationException
from apps.resource_plans import selectors
from apps.resource_plans.constants import (
    EngineJobMode,
    EngineJobStatus,
    EngineJobStepName,
)
from apps.resource_plans.models import (
    AllocationSet,
    EngineJob,
    EngineJobStep,
    PlanPhase,
    PlanVersion,
    PlanVersionProject,
)
from apps.resource_plans.selectors import phase as phase_selectors
from apps.resource_plans.selectors import version_team as version_team_selectors
from apps.resource_plans.services.allocation_engine import AllocationEngineService
from apps.resource_plans.services.capacity_snapshot import CapacitySnapshotService
from apps.resource_plans.services.conflict_detection import ConflictDetectionService
from apps.resource_plans.services.dependency_graph import DependencyGraphService
from apps.resource_plans.services.placeholder_leave import PlaceholderLeaveService

logger = logging.getLogger(__name__)


class ResourcePlanEngine:
    """Orchestrates the 7-step resource plan engine run for a single EngineJob
    (Validate Configuration → Override Placeholder Leaves → Generate
    Placeholder Leaves → Sync Capacity Snapshot → Build Dependency Graph →
    Compute Allocations → Detect Conflicts). See
    docs/architecture/resource-plan-engine.md.

    Runs on a background thread (run_in_background()) so a slow allocation
    compute never holds the request/response cycle open — the caller must
    launch it from `transaction.on_commit()` so the thread's own DB
    connection can already see the EngineJob row.
    """

    _STEP_NAMES: list[str] = [str(name) for name in EngineJobStepName.values]
    _TOTAL_STEPS = len(_STEP_NAMES)

    # ------------------------------------------------------------------ #
    # Entry points
    # ------------------------------------------------------------------ #

    @classmethod
    def run_in_background(cls, job_id: int) -> None:
        threading.Thread(target=cls.run, args=(job_id,), daemon=True).start()

    @classmethod
    def run(cls, job_id: int) -> None:
        close_old_connections()
        try:
            job = EngineJob.objects.select_related(
                "plan", "version", "version__plan__financial_year", "created_by"
            ).get(id=job_id)
        except EngineJob.DoesNotExist:
            logger.error("EngineJob id=%s not found for engine run.", job_id)
            return

        try:
            cls()._run_job(job)
        finally:
            close_old_connections()

    # ------------------------------------------------------------------ #
    # Orchestration
    # ------------------------------------------------------------------ #

    def _run_job(self, job: EngineJob) -> None:
        steps_log: list[dict] = []
        validation_result: dict = {}
        try:
            errors, warnings, phases, proj_by_phase_id = self._log_step(
                job,
                steps_log,
                str(EngineJobStepName.VALIDATE_CONFIGURATION),
                lambda: self._validate_configuration(job.version),
            )
            validation_result = {
                "error_count": len(errors),
                "warning_count": len(warnings),
                "errors": errors,
                "warnings": warnings,
            }

            if job.mode == EngineJobMode.VALIDATE:
                self._finish(
                    job, steps_log=steps_log, validation_result=validation_result
                )
                self._audit_result(job, allocation_set=None, conflict_count=0)
                return

            if job.remove_overrides:
                self._log_step(
                    job,
                    steps_log,
                    str(EngineJobStepName.OVERRIDE_PLACEHOLDER_LEAVES),
                    lambda: PlaceholderLeaveService().clear_overrides_for_version(
                        job.version
                    ),
                )
            else:
                self._log_skipped_step(
                    job, steps_log, str(EngineJobStepName.OVERRIDE_PLACEHOLDER_LEAVES)
                )

            self._log_step(
                job,
                steps_log,
                str(EngineJobStepName.GENERATE_PLACEHOLDER_LEAVES),
                lambda: PlaceholderLeaveService().generate_for_version(
                    job.version, job.include_current_sprint, job.remove_overrides
                ),
            )

            self._log_step(
                job,
                steps_log,
                str(EngineJobStepName.SYNC_CAPACITY_SNAPSHOT),
                lambda: CapacitySnapshotService().sync_for_version(job.version),
            )

            # Kahn's sort is re-derived inside AllocationEngineService.run()
            # itself (it needs the ordered phase list to drive Step 6's
            # iteration) — this entry exists purely to give the graph-build
            # phase its own timed slot in steps_log, per the design doc;
            # nothing is persisted here.
            self._log_step(
                job,
                steps_log,
                str(EngineJobStepName.BUILD_DEPENDENCY_GRAPH),
                lambda: None,
            )

            allocation_set = self._log_step(
                job,
                steps_log,
                str(EngineJobStepName.COMPUTE_ALLOCATIONS),
                lambda: AllocationEngineService().run(job),
            )

            conflicts = self._log_step(
                job,
                steps_log,
                str(EngineJobStepName.DETECT_CONFLICTS),
                lambda: ConflictDetectionService().detect_and_persist(
                    job.version, allocation_set, job
                ),
            )

            self._finish(job, steps_log=steps_log, validation_result=validation_result)
            self._audit_result(
                job, allocation_set=allocation_set, conflict_count=len(conflicts)
            )
        except Exception as exc:
            logger.exception("Resource plan engine run failed for job %s", job.code)
            self._fail(job, steps_log, validation_result, exc)

    # ------------------------------------------------------------------ #
    # Step 1 — Validate Configuration
    # ------------------------------------------------------------------ #

    @staticmethod
    def _validate_configuration(
        version: PlanVersion,
    ) -> tuple[list[str], list[str], list[PlanPhase], dict[int, PlanVersionProject]]:
        errors: list[str] = []
        warnings: list[str] = []
        phases: list[PlanPhase] = []
        proj_by_phase_id: dict[int, PlanVersionProject] = {}

        # Walked project-by-project, never bulk-queried and cross-referenced
        # in memory, per #181's instruction.
        plan_projects = list(selectors.get_configured_projects(version))
        if not plan_projects:
            errors.append("No projects are configured for this plan version.")

        for plan_project in plan_projects:
            if plan_project.is_team_budget_mismatch:
                warnings.append(
                    f"{plan_project.project} — team allocation does not match "
                    "the required budget/days within the configured threshold."
                )

            teams = list(
                version_team_selectors.get_teams_for_plan_project(plan_project)
            )
            if not teams:
                errors.append(f"{plan_project.project} has no teams configured.")
                continue

            for plan_version_team in teams:
                team_phases = list(
                    phase_selectors.get_phases_for_plan_project_team(plan_version_team)
                )
                if not team_phases:
                    errors.append(
                        f"{plan_version_team.team} on {plan_project.project} has "
                        "no phases configured."
                    )
                    continue

                for phase in team_phases:
                    if phase.is_split_incomplete:
                        errors.append(f"{phase} split percentages do not sum to 100%.")
                    for pause in selectors.get_pauses_for_phase(phase):
                        if pause.is_beyond_fy:
                            warnings.append(
                                f"A pause on {phase} resumes beyond the plan's "
                                "financial year."
                            )
                    phases.append(phase)
                    proj_by_phase_id[phase.id] = plan_project

        try:
            DependencyGraphService.topological_sort(phases, proj_by_phase_id)
        except ValidationException as exc:
            errors.append(str(exc))

        return errors, warnings, phases, proj_by_phase_id

    # ------------------------------------------------------------------ #
    # Per-step logging
    # ------------------------------------------------------------------ #

    def _log_step(
        self,
        job: EngineJob,
        steps_log: list[dict],
        step_name: str,
        func: Callable[[], Any],
    ) -> Any:
        order = self._STEP_NAMES.index(step_name) + 1
        started_at = timezone.now()
        step = EngineJobStep.objects.create(
            job=job,
            step_order=order,
            name=step_name,
            status=EngineJobStatus.RUNNING,
            started_at=started_at,
        )
        job.current_step = step_name
        job.progress_percentage = int((order - 1) / self._TOTAL_STEPS * 100)
        job.save(update_fields=["current_step", "progress_percentage"])

        try:
            result = func()
        except Exception:
            self._close_step(step, steps_log, started_at, str(EngineJobStatus.FAILED))
            raise

        self._close_step(step, steps_log, started_at, str(EngineJobStatus.COMPLETE))
        job.current_step = step_name
        job.progress_percentage = int(order / self._TOTAL_STEPS * 100)
        job.save(update_fields=["current_step", "progress_percentage"])
        return result

    @staticmethod
    def _close_step(
        step: EngineJobStep, steps_log: list[dict], started_at, status: str
    ) -> None:
        completed_at = timezone.now()
        duration_ms = int((completed_at - started_at).total_seconds() * 1000)
        step.status = status
        step.completed_at = completed_at
        step.duration_milliseconds = duration_ms
        step.save(update_fields=["status", "completed_at", "duration_milliseconds"])
        steps_log.append(
            {
                "step": step.name,
                "status": status,
                "duration_milliseconds": duration_ms,
            }
        )

    def _log_skipped_step(
        self, job: EngineJob, steps_log: list[dict], step_name: str
    ) -> None:
        order = self._STEP_NAMES.index(step_name) + 1
        now = timezone.now()
        EngineJobStep.objects.create(
            job=job,
            step_order=order,
            name=step_name,
            status=EngineJobStatus.SKIPPED,
            started_at=now,
            completed_at=now,
            duration_milliseconds=0,
        )
        steps_log.append(
            {
                "step": step_name,
                "status": str(EngineJobStatus.SKIPPED),
                "duration_milliseconds": 0,
            }
        )
        job.current_step = step_name
        job.progress_percentage = int(order / self._TOTAL_STEPS * 100)
        job.save(update_fields=["current_step", "progress_percentage"])

    # ------------------------------------------------------------------ #
    # Finalization
    # ------------------------------------------------------------------ #

    @staticmethod
    def _finish(
        job: EngineJob, *, steps_log: list[dict], validation_result: dict
    ) -> None:
        job.status = EngineJobStatus.COMPLETE
        job.completed_at = timezone.now()
        job.duration_milliseconds = int(
            (job.completed_at - job.started_at).total_seconds() * 1000
        )
        job.progress_percentage = 100
        job.steps_log = steps_log
        job.validation_result = validation_result
        job.save(
            update_fields=[
                "status",
                "completed_at",
                "duration_milliseconds",
                "progress_percentage",
                "steps_log",
                "validation_result",
            ]
        )

    @staticmethod
    def _fail(
        job: EngineJob,
        steps_log: list[dict],
        validation_result: dict,
        exc: Exception,
    ) -> None:
        now = timezone.now()
        job.status = EngineJobStatus.FAILED
        job.completed_at = now
        job.duration_milliseconds = int((now - job.started_at).total_seconds() * 1000)
        job.steps_log = steps_log
        if validation_result:
            job.validation_result = validation_result
        job.error_log = [
            *job.error_log,
            {"message": str(exc), "occurred_at": now.isoformat()},
        ]
        job.save(
            update_fields=[
                "status",
                "completed_at",
                "duration_milliseconds",
                "steps_log",
                "validation_result",
                "error_log",
            ]
        )

        AuditService.log_update(
            module="resource_plans",
            resource_type="engine_job",
            resource_code=f"{job.plan.code}-{job.code}",
            before={"status": str(EngineJobStatus.RUNNING)},
            after={"status": str(EngineJobStatus.FAILED), "error": str(exc)},
            actor=job.created_by,
        )

    @staticmethod
    def _audit_result(
        job: EngineJob,
        *,
        allocation_set: AllocationSet | None,
        conflict_count: int,
    ) -> None:
        phases_allocated = (
            allocation_set.allocations.values("phase_id").distinct().count()
            if allocation_set is not None
            else 0
        )
        AuditService.log_update(
            module="resource_plans",
            resource_type="engine_job",
            resource_code=f"{job.plan.code}-{job.code}",
            before={"status": str(EngineJobStatus.RUNNING)},
            after={
                "status": str(EngineJobStatus.COMPLETE),
                "mode": job.mode,
                "phases_allocated": phases_allocated,
                "conflicts_raised": conflict_count,
                "allocation_set_code": (
                    allocation_set.code if allocation_set is not None else None
                ),
            },
            actor=job.created_by,
        )
