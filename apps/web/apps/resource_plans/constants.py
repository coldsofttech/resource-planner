from django.db import models


class PlanType(models.TextChoices):
    FINANCIAL_YEAR = "financial_year", "Financial Year"
    PROGRAMME = "programme", "Programme"
    PROJECT = "project", "Project"
    TEAM = "team", "Team"


class VersionStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    LOCKED = "locked", "Locked"
    EXPIRED = "expired", "Expired"
    SUPERSEDED = "superseded", "Superseded"


class Basis(models.TextChoices):
    BUDGET = "budget", "Budget"
    ESTIMATE = "estimate", "Estimate"
    CUSTOM = "custom", "Custom"


class Priority(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    VERY_HIGH = "very_high", "Very High"


class Confidence(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"
    VERY_HIGH = "very_high", "Very High"


class AllocationType(models.TextChoices):
    PERCENT = "percent", "% of Basis Amount"
    DAYS = "days", "Days"
    BUDGET = "budget", "Budget"


class RampPattern(models.TextChoices):
    FLAT = "flat", "Flat"
    RAMP_UP = "ramp_up", "Ramp Up"
    RAMP_DOWN = "ramp_down", "Ramp Down"
    RAMP_UP_DOWN = "ramp_up_down", "Ramp Up Down"
    RAMP_UP_STEADY = "ramp_up_steady", "Ramp Up Steady"
    STEADY_DOWN = "steady_down", "Steady Down"
    STEPPED = "stepped", "Stepped"
    CUSTOM = "custom", "Custom"


class SplitMode(models.TextChoices):
    PERCENT = "percent", "Percent"
    DAYS = "days", "Days"
    EQUAL = "equal", "Equal"
    AUTO = "auto", "Auto"


class SegmentType(models.TextChoices):
    RAMP = "ramp", "Ramp"
    FLAT = "flat", "Flat"


class Progression(models.TextChoices):
    LINEAR = "linear", "Linear"
    EXPONENTIAL = "exponential", "Exponential"
    LOGARITHMIC = "logarithmic", "Logarithmic"
    STEPPED = "stepped", "Stepped"
    FLAT = "flat", "Flat"


class DependencyType(models.TextChoices):
    START_TO_START = "start_to_start", "Start to Start"
    FINISH_TO_START = "finish_to_start", "Finish to Start"
    FINISH_TO_FINISH = "finish_to_finish", "Finish to Finish"
    START_TO_FINISH = "start_to_finish", "Start to Finish"


class PauseInputMode(models.TextChoices):
    SPRINT = "sprint", "Sprint"
    COUNT = "count", "Count"


class AssignmentType(models.TextChoices):
    ENGINEER = "engineer", "Engineer"
    ARCHITECT = "architect", "Architect"
    ADHOC = "adhoc", "Adhoc"
    INTERIM = "interim", "Interim"


class BudgetReleaseEntryType(models.TextChoices):
    SPRINT = "sprint", "Sprint"
    MONTH = "month", "Month"


class EngineJobStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    COMPLETE = "complete", "Complete"
    FAILED = "failed", "Failed"
    # Step-level only (EngineJobStep.status) — a conditional step (e.g.
    # Override Placeholder Leaves) that did not run this pass.
    SKIPPED = "skipped", "Skipped"


class SnapshotStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    IN_PROGRESS = "in_progress", "In Progress"
    COMPLETE = "complete", "Complete"
    FAILED = "failed", "Failed"


class EngineJobMode(models.TextChoices):
    VALIDATE = "validate", "Validate"
    FULL = "full", "Full"


class EngineJobStepName(models.TextChoices):
    VALIDATE_CONFIGURATION = "validate_configuration", "Validate Configuration"
    OVERRIDE_PLACEHOLDER_LEAVES = (
        "override_placeholder_leaves",
        "Override Placeholder Leaves",
    )
    GENERATE_PLACEHOLDER_LEAVES = (
        "generate_placeholder_leaves",
        "Generate Placeholder Leaves",
    )
    SYNC_CAPACITY_SNAPSHOT = "sync_capacity_snapshot", "Sync Capacity Snapshot"
    BUILD_DEPENDENCY_GRAPH = "build_dependency_graph", "Build Dependency Graph"
    COMPUTE_ALLOCATIONS = "compute_allocations", "Compute Allocations"
    DETECT_CONFLICTS = "detect_conflicts", "Detect Conflicts"


class AllocationSetStatus(models.TextChoices):
    DRAFT = "draft", "Draft"
    ACTIVE = "active", "Active"
    SUPERSEDED = "superseded", "Superseded"


class ConflictType(models.TextChoices):
    CAPACITY_EXCEEDED = "capacity_exceeded", "Capacity Exceeded"
    COMPETING_PRIORITY = "competing_priority", "Competing Priority"
    TIMELINE_BREACH = "timeline_breach", "Timeline Breach"
    BUDGET_EXCEEDED = "budget_exceeded", "Budget Exceeded"
    DEPENDENCY_VIOLATED = "dependency_violated", "Dependency Violated"
    UNRESOLVABLE_GAP = "unresolvable_gap", "Unresolvable Gap"
    THRESHOLD_BREACH = "threshold_breach", "Threshold Breach"


class ConflictSeverity(models.IntegerChoices):
    ERROR = 0, "Error"
    WARNING = 1, "Warning"
    INFO = 2, "Info"


class ConflictStatus(models.TextChoices):
    OPEN = "open", "Open"
    RESOLVED = "resolved", "Resolved"
    DISMISSED = "dismissed", "Dismissed"


class ConflictResolutionType(models.TextChoices):
    DEPRIORITISED = "deprioritised", "Deprioritised"
    TIMELINE_SHIFTED = "timeline_shifted", "Timeline Shifted"
    ENGINEER_SWAPPED = "engineer_swapped", "Engineer Swapped"
    TEAM_CHANGED = "team_changed", "Team Changed"
    MANPOWER_RAISED = "manpower_raised", "Manpower Raised"
    REBALANCED = "rebalanced", "Rebalanced"
    DISMISSED = "dismissed", "Dismissed"


class ManpowerRequestStatus(models.TextChoices):
    OPEN = "open", "Open"
    HIRING = "hiring", "Hiring"
    REBALANCED = "rebalanced", "Rebalanced"
    DISMISSED = "dismissed", "Dismissed"


# Allowed ConflictResolutionType values per ConflictType — enforced by
# ConflictResolutionService.resolve(). COMPETING_PRIORITY, BUDGET_EXCEEDED,
# and DEPENDENCY_VIOLATED have no detection logic yet (see
# docs/architecture/resource-plan-engine.md) but their resolution mappings
# are defined here so the service is ready when detection lands.
CONFLICT_RESOLUTION_OPTIONS: dict[str, tuple[str, ...]] = {
    str(ConflictType.CAPACITY_EXCEEDED): (
        str(ConflictResolutionType.DEPRIORITISED),
        str(ConflictResolutionType.ENGINEER_SWAPPED),
        str(ConflictResolutionType.TEAM_CHANGED),
        str(ConflictResolutionType.MANPOWER_RAISED),
        str(ConflictResolutionType.REBALANCED),
        str(ConflictResolutionType.DISMISSED),
    ),
    str(ConflictType.THRESHOLD_BREACH): (
        str(ConflictResolutionType.REBALANCED),
        str(ConflictResolutionType.DEPRIORITISED),
        str(ConflictResolutionType.DISMISSED),
    ),
    str(ConflictType.UNRESOLVABLE_GAP): (
        str(ConflictResolutionType.MANPOWER_RAISED),
        str(ConflictResolutionType.REBALANCED),
        str(ConflictResolutionType.DISMISSED),
    ),
    str(ConflictType.COMPETING_PRIORITY): (
        str(ConflictResolutionType.DEPRIORITISED),
        str(ConflictResolutionType.REBALANCED),
        str(ConflictResolutionType.DISMISSED),
    ),
    str(ConflictType.TIMELINE_BREACH): (
        str(ConflictResolutionType.TIMELINE_SHIFTED),
        str(ConflictResolutionType.MANPOWER_RAISED),
        str(ConflictResolutionType.DISMISSED),
    ),
    str(ConflictType.BUDGET_EXCEEDED): (
        str(ConflictResolutionType.DEPRIORITISED),
        str(ConflictResolutionType.REBALANCED),
        str(ConflictResolutionType.DISMISSED),
    ),
    str(ConflictType.DEPENDENCY_VIOLATED): (
        str(ConflictResolutionType.TIMELINE_SHIFTED),
        str(ConflictResolutionType.DISMISSED),
    ),
}
