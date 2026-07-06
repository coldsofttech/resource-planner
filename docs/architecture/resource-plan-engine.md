# Resource Plan Engine

This document maps a reference implementation (from
`coldsofttech/resourceplanner_old`, `dev` branch —
`apps/resource_plans/engine.py` and `apps/resource_plans/models.py`/
`services.py`) onto this project's actual `apps.resource_plans` models
(built across #171-#180), so that the real `ResourcePlanEngine` can be
implemented from a reviewed, gap-aware design rather than a blind port.

**Nothing in this document has been implemented yet.** It originated from
GH #180 (readiness models) and #181 (this design review). The actual
engine, its services, and any model changes it requires are tracked as
separate follow-up issues (linked at the bottom).

---

## What the reference does, at a glance

`run_engine(job_id)` is a background-thread orchestrator: it loads an
`EngineJob`, and executes 7 steps in order — Validate Configuration →
Override Placeholder Leaves → Generate Placeholder Leaves → Sync Capacity
Snapshot → Build Dependency Graph → Compute Allocations → Detect Conflicts
— logging each step's start/end/duration, updating the job's
`current_step`/`progress_percentage` live, and writing an audit entry at
the end. If the job's mode is **Validate Only**, the engine stops after
Step 1 and never runs Steps 2-7.

---

## Model/field name mapping (reference → ours)

| Reference                                             | Ours                                                | Notes                                                      |
| ----------------------------------------------------- | --------------------------------------------------- | ---------------------------------------------------------- |
| `PlanEngineJob`                                       | `EngineJob`                                         | direct rename                                              |
| `ResourcePlanVersion`                                 | `PlanVersion`                                       | direct rename                                              |
| `ResourcePlanVersionProject`                          | `PlanVersionProject`                                | direct rename                                              |
| `ResourcePlanVersionProjectTeam`                      | `PlanVersionTeam`                                   | direct rename                                              |
| `PlanPhase`                                           | `PlanPhase`                                         | same name                                                  |
| `PlanAssignment`                                      | `PlanAssignment`                                    | same name (`team_member` → `member`)                       |
| `ResourcePlanAllocationSet`                           | `AllocationSet`                                     | direct rename                                              |
| `ResourcePlanAllocation`                              | `Allocation`                                        | direct rename                                              |
| `ResourcePlanMemberCapacity`                          | `MemberCapacity`                                    | direct rename                                              |
| `ResourcePlanPlaceholderEngineer`                     | `PlaceholderEngineer`                               | direct rename                                              |
| `Conflict`                                            | `Conflict`                                          | same name                                                  |
| `ManpowerRequest`                                     | `ManpowerRequest`                                   | same name                                                  |
| `PlaceholderEngineer` (hire, Phase 10)                | `EngineerHirePlaceholder`                           | reference overloads one model for two concepts — see below |
| `PlaceholderEngineerAbsence`                          | `EngineerHirePlaceholderAbsence`                    | direct rename                                              |
| `SprintCapacity` (`apps.sprint_capacity`)             | `apps.sprints.models.Capacity`                      | already exists, no gap                                     |
| `LeaveDay` (`apps.member_leaves`)                     | `apps.leaves.models.LeaveDayEntry`                  | already exists, no gap                                     |
| `AuditLogService.write(...)`                          | `AuditService.log_create/log_update/log_delete/...` | 8 named methods instead of 1 generic — map per call site   |
| `ResourcePlanScope.financial_year` (via `plan_group`) | `Plan.financial_year` (direct FK)                   | simpler in ours — no scope indirection needed              |

### The one real naming collision

The reference uses **the same model name, `PlaceholderEngineer`, for two
different concepts**:

1. An unnamed "slot" auto-created during allocation compute when
   `auto_assign=True` and no real team member is available (reference:
   `ResourcePlanPlaceholderEngineer`, created inline in
   `AllocationEngineService.run()` with names like `"Auto #3"`).
2. A deliberately-created "we're hiring for this" placeholder from
   `PlaceholderEngineerService.create_from_manpower_request()`, with
   `manpower_request`, `onboard_sprint`, `engine_suggested_sprint`,
   `replaces_by`/`replaced_at` — a full hiring-workflow record.

**Our #180 models already correctly split these into two separate models**
— `PlaceholderEngineer` (concept 1: version/team/phase/slot_number, no
hiring fields) and `EngineerHirePlaceholder` (concept 2: version/
sequence_number/manpower_request/onboard_sprint/replaced_by, no phase/team-
slot fields). This is cleaner than the reference. Any future
implementation should keep this split and be precise about which one each
step creates (auto-assign fallback → `PlaceholderEngineer`; manpower-
request hire action → `EngineerHirePlaceholder`).

---

## Field-level discrepancies vs. the reference

Diffed field-by-field against the reference `models.py` (1,023 lines, 27
model classes). These are concrete nullability/`on_delete` differences
worth a deliberate decision each — not all need to change, some of ours
may be the right call, but they should be reviewed rather than silently
inherited:

| Field                                           | Reference                          | Ours                      | Comment                                                                                                                                                                                                                              |
| ----------------------------------------------- | ---------------------------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `Allocation.programme`                          | nullable (`null=True, blank=True`) | required, `PROTECT`       | Reference allows an allocation with no programme. Check whether `Project.programme` is itself nullable — if so, ours may over-constrain.                                                                                             |
| `Allocation.phase`                              | nullable, `SET_NULL`               | required, `CASCADE`       | Reference preserves allocation history if the phase is later deleted; ours wipes it. Needs a deliberate decision.                                                                                                                    |
| `AllocationSet.engine_job`                      | nullable, `PROTECT`                | required, `PROTECT`       | Reference allows a manually-created allocation set with no originating job. Probably fine as required for us (no manual-creation path planned), but flagging.                                                                        |
| `Conflict.engine_job`                           | nullable, **`CASCADE`**            | required, **`PROTECT`**   | Reference cascades conflicts away when their engine job is deleted — consistent with conflicts being fully regenerated every run. Ours protecting the job from deletion may be unnecessarily strict for disposable/regenerable data. |
| `ManpowerRequest.conflict`                      | required, **`CASCADE`**            | required, **`PROTECT`**   | Same "disposable vs. protected" question as above.                                                                                                                                                                                   |
| `ManpowerRequest.phase`                         | nullable, `SET_NULL`               | required, `CASCADE`       | Reference allows a team-level manpower request not tied to one specific phase.                                                                                                                                                       |
| `EngineerHirePlaceholder.onboard_sprint`        | nullable                           | required, `PROTECT`       | Reference allows "we're hiring but haven't picked a start sprint yet." Ours forces it at creation.                                                                                                                                   |
| `EngineerHirePlaceholderAbsence.effective_days` | has this `@property`               | **missing entirely**      | Straightforward gap — we added the equivalent property on `Allocation` but not here, even though the field shape (`days`/`override_days`) is identical.                                                                              |
| `PlanPhasePause.is_beyond_fy`                   | stored `BooleanField`, recomputed  | doesn't exist             | Same pattern as `is_split_incomplete` — a stored, recomputed flag, not a live `@property`.                                                                                                                                           |
| `PlanEngineJob.error_log`                       | `TextField` (plain string)         | `JSONField(default=list)` | Ours is more structured — an intentional improvement, not a gap.                                                                                                                                                                     |
| `PlanEngineJob.duration_seconds`                | seconds                            | `duration_milliseconds`   | Ours is finer-grained — intentional improvement.                                                                                                                                                                                     |

---

## Gaps: fields/logic the reference assumes but we don't have yet

1. **`PlanVersionProject.is_team_budget_mismatch`** (+ sibling flags
   `is_over_threshold`/`is_under_threshold`/`is_percent_incomplete`) —
   stored, recomputed booleans maintained by a helper every time a
   `PlanVersionTeam` row changes. Does not exist on our model at all.
   Needs a migration + a maintenance hook called from
   `PlanVersionTeamService.create/update/delete` (not just the engine).
2. **`PlanPhase.is_split_incomplete` real logic** — the field already
   exists (added in #171, always `False` today). Reference logic: for
   `split_mode == PERCENT`, sum `assignments.split_value` and flag
   incomplete if it doesn't sum to 100 (±0.01 tolerance) — directly
   portable, just needs wiring into `PlanAssignmentService.create/update/delete`.
   For `DAYS`/`EQUAL`/`AUTO` split modes the reference has no analogous
   check — an open design question for the implementation issue.
3. **`PlanPhasePause.is_beyond_fy`** — doesn't exist in any form yet. A
   stored, recomputed `BooleanField` (see table above), computed via a
   5-hop FK traversal (`pause` → `phase` → `plan_project_team` →
   `plan_project` → `version` → `plan.financial_year`) compared against
   `resume_sprint.financial_year` — worth denormalizing or accepting the
   join cost.
4. **A day-rate / budget↔days conversion** — needed if
   `is_team_budget_mismatch` must compare `allocation_days`/`allocated_days`
   sums against a currency-denominated `basis_amount`. The reference uses
   a _global_ `SPRINT_POINT_PRICE` configuration value for this; our
   `apps.configurations` app likely has (or should have) the equivalent.
5. **Predecessor-phase same-version guarantee** — only enforced by UI
   convention, not a DB constraint, on both the reference and ours. Worth
   re-flagging since the dependency graph step depends on it.
6. **No unique constraint on `PlanAssignment(phase, member)`** — allocation
   compute assumes at most one row per phase per (member or auto-assign)
   slot in the way it iterates `phase.assignments.all()`.

---

## The 7 steps, mapped onto our models

### Step 1 — Validate Configuration

Iterate `PlanVersionProject` → `PlanVersionTeam` (`.teams.all()`) →
`PlanPhase` (`.phases.all()`), **sequentially, project by project** (never
bulk-query everything and cross-reference in memory — walk one
`PlanVersionProject` to completion before moving to the next). For each
level:

- No projects on the version at all → error.
- A project with no teams → error, skip its phases.
- A project flagged `is_team_budget_mismatch` (gap #1) → warning.
- A team with no phases → error, skip.
- A phase flagged `is_split_incomplete` → error.
- Each phase's pauses: flag `is_beyond_fy` (gap #3) → warning.
- After all phases are collected: run cycle detection over
  `PlanPhaseDependency` (`phase` → `predecessor_phase` edges) using a
  white/grey/black DFS — pure graph logic, no model gaps, fully portable.

If `job.mode == EngineJobMode.VALIDATE`: persist `validation_result`
(`error_count`, `warning_count`, `errors`, `warnings`), mark the job
`Complete`, write the audit entry, **stop — Steps 2-7 do not run**. Today's
stub already completes the job after this point but never populates real
findings — that's exactly what the implementation issue needs to change.

### Step 2 — Override Placeholder Leaves

Only runs when `job.remove_overrides` is set (currently a stored-but-unused
placeholder field on `EngineJob`). When set: delete all `PlaceholderLeave`
rows for the version (both auto and manual), then clear
`PlanVersion.has_leave_overrides` back to `False`. When not set: the step is
recorded as **skipped**, not completed or failed — proposed as a 5th
step-result state (today only Pending/Running/Complete/Failed exist).

### Step 3 — Generate Placeholder Leaves

For every member across every team assigned anywhere in the version:
entitlement = `UserProfile.default_holidays` minus confirmed `Leave`/
`LeaveDayEntry` days already used/booked within the plan's financial year
(`Plan.financial_year`). Remaining entitlement is spread across the
**second half of the FY's sprints** (front-loaded certainty, back-half
placeholder buffer), only over sprints still in the future (respecting
`include_current_sprint`), capped per-sprint by that member's
`Capacity.net_capacity`, rounded to 0.5-day increments, with leftover
redistributed to any sprint still under its cap. Auto-generated rows
(`is_auto=True`) are cleared and regenerated every run; manual overrides
(`is_auto=False`) are preserved unless Step 2 just cleared everything.

### Step 4 — Sync Capacity Snapshot

**Simpler than it first appears**: our codebase already has
`apps.sprints.models.Capacity` and
`apps.sprints.engine.capacity.SprintCapacityEngine`, which compute
`working_days`/`holiday_days`/`leave_days`/`net_capacity` per member per
sprint from `Holiday`, `LeaveDayEntry`, and `UserProfile` location/join/
leave dates. This step doesn't need to compute raw capacity at all — it
only reads `Capacity`, subtracts that sprint's `PlaceholderLeave.days`
(floored at 0), and materializes into `resource_plans.MemberCapacity` via
delete-then-bulk-create (full resync per version).

### Step 5 — Build Dependency Graph

In the reference this "step" doesn't persist anything on its own — it's
Kahn's topological sort with priority/confidence/`dates_strict`/end-sprint/
display-order tie-breaking, computed in-memory and fed directly into
Step 6. It should still be a **distinct, timed step in `steps_log`**
(matching the existing `EngineJobStepName.BUILD_DEPENDENCY_GRAPH` choice)
even though its output isn't a persisted model — it's meaningfully
separate, CPU-bound work worth its own timing entry.

### Step 6 — Compute Allocations

The most complex step. For each phase, in topological order, sequentially
by project:

- Determine the phase's active sprint window (earliest start from
  dependency lag, clamped to `start_sprint`/`end_sprint`/version min-sprint,
  with paused sprint ranges from `PlanPhasePause.pause_from` →
  `resume_sprint` excluded).
- Determine total effort for the phase (`PlanPhase.days_effort` if set,
  else `PlanVersionTeam.allocated_days / phase_count` as a fallback split).
- For each `PlanAssignment` on the phase (or a synthetic auto-assign
  placeholder if none exist): compute this assignment's share of the
  phase's effort (`split_value` for Percent/Days mode, equal share
  otherwise), then distribute those days across the phase's active sprints
  using the ramp pattern (flat, ramp up/down, up-down, up-steady,
  steady-down, stepped, or segment-driven curves from `PlanPhaseSegment`),
  capped per-sprint by `max_days_per_sprint` and by the member's remaining
  `MemberCapacity.net_capacity` for that sprint. Named (non-auto)
  assignments allocate to the named `member`; auto-assign ones pick the
  team member with the lowest existing load, or — if no real team member
  is available — create/reuse a `PlaceholderEngineer` "slot" for that team
  (reusing a slot only when its already-used sprints don't overlap the new
  phase's sprints, to avoid double-booking one placeholder slot across two
  concurrent phases).
- Persist one `Allocation` row per (assignment, sprint) pair, including
  explicit 0-day rows for active sprints that received no allocation (so a
  future editing UI has a full grid to render, not gaps).

### Step 7 — Detect Conflicts

Delete any existing `Conflict` rows for the `AllocationSet` (a fresh
detection pass every run), then check, in this order:

1. **`CAPACITY_EXCEEDED`** (Error) — any member/sprint where allocated
   days exceed `MemberCapacity.net_capacity`.
2. **`THRESHOLD_BREACH`** (Warning) — per project, compare total allocated
   days (respecting any `Allocation.override_days`) against required days
   (sum of team `allocated_days`, falling back to `days_required`), flag if
   the percentage difference exceeds `PlanVersion.threshold_percentage`.
3. **`TIMELINE_BREACH`** (Error) — any phase with assignments configured
   but zero `Allocation` rows produced (its sprint window fully expired or
   fully paused).
4. **`UNRESOLVABLE_GAP`** (Error) — any `PlaceholderEngineer` slot that
   received allocation (auto-assign found no real member), grouped by
   `(team, slot_number)` into one `Conflict` + one auto-created
   `ManpowerRequest` per slot, suggesting the earliest sprint that slot's
   work was needed.

**The reference itself only implements 4 of our 7 `ConflictType` choices.**
`COMPETING_PRIORITY`, `BUDGET_EXCEEDED`, and `DEPENDENCY_VIOLATED` exist in
both enums but have no detection logic anywhere in the reference — they're
reserved values with resolution-type mappings already defined but no code
path that ever creates one. Recommendation: leave them undetected
initially, matching the reference's own scope, and treat as a known future
gap.

**Resolution-type-per-conflict-type mapping** (fully portable, no gaps):

```
CAPACITY_EXCEEDED    → Deprioritised | Engineer Swapped | Team Changed | Manpower Raised | Rebalanced | Dismissed
THRESHOLD_BREACH     → Rebalanced | Deprioritised | Dismissed
UNRESOLVABLE_GAP      → Manpower Raised | Rebalanced | Dismissed
COMPETING_PRIORITY    → Deprioritised | Rebalanced | Dismissed
TIMELINE_BREACH       → Timeline Shifted | Manpower Raised | Dismissed
BUDGET_EXCEEDED       → Deprioritised | Rebalanced | Dismissed
DEPENDENCY_VIOLATED   → Timeline Shifted | Dismissed
```

---

## Suggested additional steps beyond the original 7

1. **A "Skipped" step-result state** — `EngineJobStepName`/`steps_log`
   currently only distinguish Complete/Failed; Step 2 is conditionally a
   no-op and deserves a distinct visible state.
2. **A pre-flight "Resolve Financial Year Scope" micro-step** — every
   downstream step (3/4/6) needs `Plan.financial_year` and its sprint list
   resolved once; doing this explicitly as its own tiny logged step would
   surface a clear, actionable error ("Plan has no financial year
   configured") before failing confusingly deep inside Step 3/4.
3. **A "Refresh Threshold Conflicts" lightweight re-check**, separate from
   the full Step 7 — the reference has a standalone
   `refresh_threshold_for_alloc_set()` used after a manual
   `Allocation.override_days` edit, so a full engine re-run isn't required
   just to re-evaluate budget thresholds. Not a new _engine run_ step so
   much as a note for whoever builds `Allocation` editing: call this
   lightweight recheck, not a full re-run.

---

## Follow-up implementation issues

Tracked separately (created after this document was reviewed):

- Model changes (gaps + field-level discrepancies above)
- `PlaceholderLeaveService` (Steps 2-3)
- `CapacitySnapshotService` (Step 4)
- `DependencyGraphService` + `RampDistributionService` (Step 5, and the
  ramp-distribution helper used by Step 6)
- `AllocationEngineService` (Step 6)
- `ConflictDetectionService` + `ConflictResolutionService` +
  `ManpowerRequestService` (Step 7 + resolution + manpower lifecycle)
- `PlaceholderEngineerService` + `PlaceholderEngineerAbsenceService`
  (hire-placeholder workflow triggered by `ManpowerRequest.hire()`)
- `ResourcePlanEngine` orchestrator (ties the above together, replacing
  today's stub in `EngineJobService.create()`)
