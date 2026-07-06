"use strict";

import { esc } from "../../components/utils.js";
import { apiFetch, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

// ---- Shared state ----
let planCode = "";
let versionNumber = 0;
let allocationSets = [];
let currentAllocationSetCode = null;
let currentAllocationSetStatus = null;
let discoveredTeams = [];
let enginePolling = false;

const CATEGORY_DEFS = [
  {
    key: "capacity",
    icon: "bi-speedometer2",
    iconColor: "info",
    title: "Capacity",
    subtitle: "Net capacity (working − holidays − leave − placeholder) per sprint",
    requiresAllocationSet: false,
  },
  {
    key: "absences",
    icon: "bi-calendar-minus-fill",
    iconColor: "warning",
    title: "Absences",
    subtitle: "Total absence per sprint with breakdown by type",
    requiresAllocationSet: false,
  },
  {
    key: "allocated_capacity",
    icon: "bi-bar-chart-fill",
    iconColor: "danger",
    title: "Allocated Capacity",
    subtitle: "Engineer allocated days vs net capacity per sprint",
    requiresAllocationSet: true,
  },
  {
    key: "allocations",
    icon: "bi-diagram-3-fill",
    iconColor: "success",
    title: "Allocations",
    subtitle: "Days allocated per engineer per sprint by programme, project, and phase",
    requiresAllocationSet: true,
  },
];

// ---- Utility functions ----

function formatDays(value) {
  const num = Number(value);
  return `${(Number.isFinite(num) ? num : 0).toFixed(2)}d`;
}

function capacityBucketClass(days) {
  const n = Number(days);
  if (n >= 10) return "rp-cap-hi";
  if (n > 8) return "rp-cap-good";
  if (n > 5) return "rp-cap-mid";
  if (n > 3) return "rp-cap-low";
  if (n > 0) return "rp-cap-crit";
  return "rp-cap-zero";
}

function priorityRowClass(priority) {
  if (priority === "very_high") return "rp-grid-priority-very_high";
  if (priority === "high") return "rp-grid-priority-high";
  if (priority === "medium") return "rp-grid-priority-medium";
  return "";
}

const CONFIDENCE_LABELS = { low: "L", medium: "M", high: "H", very_high: "VH" };

function confidenceBadge(confidence) {
  if (!confidence) return "";
  const label = CONFIDENCE_LABELS[confidence] || confidence;
  return `<span class="rp-grid-confidence-dot rp-grid-confidence-${esc(confidence)}"></span>${esc(label)}`;
}

function sprintHeaderCells(sprints) {
  return sprints
    .map((s) => `<th class="rp-grid-cell">${esc("Sprint " + s.sprint_number)}</th>`)
    .join("");
}

function teamNames(names) {
  return Array.isArray(names) && names.length ? esc(names.join(", ")) : "";
}

function allocationSetLabel(row) {
  const num = String(row.code || "")
    .split("-")
    .pop();
  return `Set #${num} — ${row.status_display || row.status}`;
}

// ---- Row template (collapsed) ----

window.renderGridCategoryRow = function renderGridCategoryRow(row) {
  return `
    <td>
      <div class="rp-grid-category">
        <icon-field icon="${esc(row.icon)}" color="${esc(row.iconColor)}"></icon-field>
        <span class="rp-grid-category-title">${esc(row.title)}</span>
        <span class="rp-grid-category-subtitle">${esc(row.subtitle)}</span>
      </div>
    </td>
  `;
};

// ---- Detail template (expanded) ----

window.renderGridCategoryDetail = function renderGridCategoryDetail(row) {
  if (row.requiresAllocationSet && !currentAllocationSetCode) {
    return `<p class="small mb-0" style="color:var(--rp-text-muted)">Run the engine to generate allocation data before viewing this section.</p>`;
  }
  if (row.error) {
    return `<p class="small mb-0 text-danger">${esc(row.error)}</p>`;
  }
  if (!row.data) {
    return `<p class="small mb-0" style="color:var(--rp-text-muted)">No data available.</p>`;
  }
  if (row.key === "capacity") return renderCapacityDetail(row.data);
  if (row.key === "absences") return renderAbsencesDetail(row.data);
  if (row.key === "allocated_capacity") return renderAllocatedCapacityDetail(row.data);
  if (row.key === "allocations") return renderAllocationsDetail(row.data);
  return "";
};

function renderCapacityDetail(data) {
  const sprints = data.sprints || [];
  const members = data.members || [];
  if (!members.length) {
    return `<p class="small mb-0" style="color:var(--rp-text-muted)">No members found.</p>`;
  }
  const rows = members
    .map((m) => {
      const cells = m.cells
        .map(
          (c) =>
            `<td class="rp-grid-cell ${capacityBucketClass(c.net_capacity)}">${esc(formatDays(c.net_capacity))}</td>`,
        )
        .join("");
      return `<tr><td>${esc(m.member_name)}</td><td>${teamNames(m.team_names)}</td>${cells}</tr>`;
    })
    .join("");
  return `
    <div style="overflow-x:auto">
      <table class="rp-grid-detail-table">
        <thead><tr><th>Member</th><th>Team</th>${sprintHeaderCells(sprints)}</tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function absenceBreakdownHtml(cell) {
  const parts = [];
  if (Number(cell.holiday_days) > 0) {
    parts.push(
      `<icon-field icon="bi-cup-hot-fill" size="xs" class="rp-grid-absence-icon-holidays"></icon-field> ${esc(cell.holiday_days)}`,
    );
  }
  if (Number(cell.leave_days) > 0) {
    parts.push(
      `<icon-field icon="bi-person-x-fill" size="xs" class="rp-grid-absence-icon-leave"></icon-field> ${esc(cell.leave_days)}`,
    );
  }
  if (Number(cell.placeholder_leave_days) > 0) {
    parts.push(
      `<icon-field icon="bi-bookmark-fill" size="xs" class="rp-grid-absence-icon-placeholder"></icon-field> ${esc(cell.placeholder_leave_days)}`,
    );
  }
  return parts.length
    ? `<div class="d-flex gap-2 justify-content-end mt-1 small">${parts.join("")}</div>`
    : "";
}

function renderAbsencesDetail(data) {
  const sprints = data.sprints || [];
  const members = data.members || [];
  if (!members.length) {
    return `<p class="small mb-0" style="color:var(--rp-text-muted)">No members found.</p>`;
  }
  const rows = members
    .map((m) => {
      const cells = m.cells
        .map((c) => `<td class="rp-grid-cell">${esc(c.total_days)}${absenceBreakdownHtml(c)}</td>`)
        .join("");
      return `<tr><td>${esc(m.member_name)}</td><td>${teamNames(m.team_names)}</td>${cells}</tr>`;
    })
    .join("");
  return `
    <div style="overflow-x:auto">
      <table class="rp-grid-detail-table">
        <thead><tr><th>Member</th><th>Team</th>${sprintHeaderCells(sprints)}</tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function renderAllocatedCapacityDetail(data) {
  const sprints = data.sprints || [];
  const members = data.members || [];
  if (!members.length) {
    return `<p class="small mb-0" style="color:var(--rp-text-muted)">No members found.</p>`;
  }
  const editable = currentAllocationSetStatus === "draft";
  const rows = members
    .map((m) => {
      const cells = m.cells
        .map((c) => {
          const remaining = Number(c.net_capacity) - Number(c.allocated_days);
          const cls = capacityBucketClass(remaining);
          const zeroCapacity = Number(c.net_capacity) <= 0 && Number(c.allocated_days) <= 0;
          const display = zeroCapacity
            ? `<span class="rp-grid-empty-cell">—</span>`
            : esc(formatDays(c.allocated_days));
          return `<td class="rp-grid-cell ${zeroCapacity ? "" : cls}">${display}</td>`;
        })
        .join("");
      return `<tr><td>${esc(m.member_name)}</td><td>${teamNames(m.team_names)}</td>${cells}</tr>`;
    })
    .join("");
  const editHint = editable
    ? `<p class="small mb-2" style="color:var(--rp-text-muted)">This allocation set is a draft — use the Allocations section below to edit day overrides.</p>`
    : "";
  return `
    ${editHint}
    <div style="overflow-x:auto">
      <table class="rp-grid-detail-table">
        <thead><tr><th>Member</th><th>Team</th>${sprintHeaderCells(sprints)}</tr></thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

function renderAllocationsDetail(data) {
  const sprints = data.sprints || [];
  const results = data.results || [];
  if (!results.length) {
    return `<p class="small mb-0" style="color:var(--rp-text-muted)">No allocations found.</p>`;
  }
  const editable = currentAllocationSetStatus === "draft";
  const rows = results
    .map((r) => {
      const rowClass = priorityRowClass(r.priority);
      const phaseCell = r.phase_name
        ? `${esc(r.phase_name)} ${confidenceBadge(r.confidence)}`
        : `<span class="rp-grid-empty-cell">—</span>`;
      const memberLabel = r.is_placeholder
        ? `${esc(r.member_name)} <span class="rp-badge rp-badge-soft">Placeholder</span>`
        : esc(r.member_name);
      const cells = r.cells
        .map((c) => {
          const editAttr =
            editable && c.allocation_code
              ? ` data-rp-grid-editable data-days="${esc(c.days)}" data-allocation-code="${esc(c.allocation_code)}"`
              : "";
          return `<td class="rp-grid-cell"${editAttr}>${esc(formatDays(c.days))}</td>`;
        })
        .join("");
      return `
        <tr class="${esc(rowClass)}">
          <td>${esc(r.programme_name || "")}</td>
          <td>${esc(r.project_name || "")}</td>
          <td>${teamNames([r.team_name])}</td>
          <td>${memberLabel}</td>
          <td>${phaseCell}</td>
          ${cells}
        </tr>
      `;
    })
    .join("");
  return `
    <div style="overflow-x:auto">
      <table class="rp-grid-detail-table">
        <thead>
          <tr>
            <th>Programme</th><th>Project</th><th>Team</th><th>Member</th><th>Phase</th>
            ${sprintHeaderCells(sprints)}
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}

// ---- Data fetching per tab ----

async function fetchGridDataForTeam(teamCode) {
  const capacityUrl = API_URLS.resourcePlans.gridCapacity(planCode, versionNumber);
  const absencesUrl = API_URLS.resourcePlans.gridAbsences(planCode, versionNumber);
  const teamParam = teamCode ? `?team=${encodeURIComponent(teamCode)}` : "";

  const categories = CATEGORY_DEFS.map((def) => ({ ...def }));

  const [capacityResult, absencesResult] = await Promise.all([
    apiFetch(`${capacityUrl.href}${teamParam}`, { method: capacityUrl.method }),
    apiFetch(`${absencesUrl.href}${teamParam}`, { method: absencesUrl.method }),
  ]);
  categories[0].data = capacityResult?.data ?? null;
  categories[1].data = absencesResult?.data ?? null;

  if (currentAllocationSetCode) {
    const allocParam = `${teamParam ? teamParam + "&" : "?"}allocation_set=${encodeURIComponent(currentAllocationSetCode)}`;
    const allocatedCapacityUrl = API_URLS.resourcePlans.gridAllocatedCapacity(
      planCode,
      versionNumber,
    );
    const allocationsUrl = API_URLS.resourcePlans.gridAllocations(planCode, versionNumber);
    try {
      const [allocatedCapacityResult, allocationsResult] = await Promise.all([
        apiFetch(`${allocatedCapacityUrl.href}${allocParam}`, {
          method: allocatedCapacityUrl.method,
        }),
        apiFetch(`${allocationsUrl.href}${allocParam}`, { method: allocationsUrl.method }),
      ]);
      categories[2].data = allocatedCapacityResult?.data ?? null;
      categories[3].data = allocationsResult?.data ?? null;
    } catch (err) {
      const msg = err?.data?.error?.message ?? "Failed to load allocation data.";
      categories[2].error = msg;
      categories[3].error = msg;
    }
  }

  return { categories, capacityData: categories[0].data };
}

function extractTeamsFromCapacity(capacityData) {
  const teamMap = new Map();
  for (const member of capacityData?.members ?? []) {
    const codes = member.team_codes || [];
    const names = member.team_names || [];
    codes.forEach((code, idx) => {
      if (!teamMap.has(code)) teamMap.set(code, names[idx] || code);
    });
  }
  return Array.from(teamMap.entries()).map(([code, name]) => ({ code, name }));
}

async function loadTabData(teamCode, tableId) {
  const table = document.getElementById(tableId);
  if (!table) return;

  try {
    const { categories } = await fetchGridDataForTeam(teamCode);
    table.rows = categories;
  } catch (err) {
    const msg = err?.data?.error?.message ?? "Failed to load the allocation grid.";
    toast({ type: "error", title: "Error", message: msg });
  }
}

// ---- Tabs ----

function buildGridTableMarkup(tableId) {
  return `
    <data-table id="${tableId}" expandable row-template="renderGridCategoryRow" detail-template="renderGridCategoryDetail">
      <table-columns>
        <table-column label="" key="title"></table-column>
      </table-columns>
    </data-table>
  `;
}

let tabsInitialized = false;

/** First load — fetches "All Teams" data (to discover the team list), then
 * builds the full tab set in one shot with that data already attached, since
 * <tab-panel> only parses its <tab-item> children once on connect (there is
 * no supported way to add a tab to an already-rendered panel). */
async function initializeGrid() {
  const container = document.getElementById("rp-grid-tabs-container");
  if (!container) return;

  let initial;
  try {
    initial = await fetchGridDataForTeam(null);
  } catch (err) {
    const msg = err?.data?.error?.message ?? "Failed to load the allocation grid.";
    container.innerHTML = `<p class="text-danger">${esc(msg)}</p>`;
    return;
  }

  discoveredTeams = extractTeamsFromCapacity(initial.capacityData);

  const tabItemsHtml = [
    `
      <tab-item id="all" active>
        <tab-header title="All Teams" icon="bi-people-fill"></tab-header>
        <tab-content>${buildGridTableMarkup("rp-grid-table-all")}</tab-content>
      </tab-item>
    `,
    ...discoveredTeams.map(
      (team) => `
      <tab-item id="team-${esc(team.code)}">
        <tab-header title="${esc(team.name)}" icon="bi-diagram-2"></tab-header>
        <tab-content>${buildGridTableMarkup(`rp-grid-table-team-${esc(team.code)}`)}</tab-content>
      </tab-item>
    `,
    ),
  ].join("");

  container.innerHTML = `
    <tab-panel id="rp-grid-tabs">
      <tab-items>${tabItemsHtml}</tab-items>
    </tab-panel>
  `;
  tabsInitialized = true;

  const allTable = document.getElementById("rp-grid-table-all");
  if (allTable) allTable.rows = initial.categories;

  const loadedTabs = new Set(["all"]);
  const panel = document.getElementById("rp-grid-tabs");
  panel?.addEventListener("rp:tab-change", (e) => {
    const tabId = e.detail.tab;
    if (loadedTabs.has(tabId)) return;
    loadedTabs.add(tabId);
    const teamCode = tabId.replace(/^team-/, "");
    loadTabData(teamCode, `rp-grid-table-team-${teamCode}`);
  });
}

async function refreshAllLoadedTabs() {
  if (!tabsInitialized) return;
  if (document.getElementById("rp-grid-table-all")) {
    await loadTabData(null, "rp-grid-table-all");
  }
  for (const team of discoveredTeams) {
    const tableId = `rp-grid-table-team-${team.code}`;
    if (document.getElementById(tableId)) {
      await loadTabData(team.code, tableId);
    }
  }
}

// ---- Allocation override editing ----

function initOverrideEditing() {
  document.addEventListener("click", async (e) => {
    const cell = e.target.closest("td[data-rp-grid-editable]");
    if (!cell || cell.querySelector("input")) return;
    if (!currentAllocationSetCode) return;

    const originalDays = cell.getAttribute("data-days") || "0";
    const allocationCode = cell.getAttribute("data-allocation-code");

    cell.innerHTML = `
      <div class="d-flex align-items-center gap-1">
        <input type="number" step="0.5" min="0" class="form-control form-control-sm" style="width:80px" value="${esc(originalDays)}">
        <button type="button" class="btn btn-sm btn-link p-0" data-rp-save title="Save"><i class="bi bi-check-lg"></i></button>
        <button type="button" class="btn btn-sm btn-link p-0" data-rp-cancel title="Cancel"><i class="bi bi-x-lg"></i></button>
      </div>
    `;

    const input = cell.querySelector("input");
    input?.focus();
    input?.select();

    cell.querySelector("[data-rp-cancel]")?.addEventListener("click", () => {
      cell.innerHTML = esc(formatDays(originalDays));
    });

    cell.querySelector("[data-rp-save]")?.addEventListener("click", async () => {
      if (!allocationCode) {
        toast({
          type: "error",
          title: "Error",
          message: "Unable to identify this allocation row.",
        });
        return;
      }
      const value = input?.value ?? "";
      try {
        const { href, method } = API_URLS.resourcePlans.allocationOverride(
          planCode,
          versionNumber,
          currentAllocationSetCode,
          allocationCode,
        );
        await apiFetch(href, {
          method,
          body: JSON.stringify({ override_days: value === "" ? null : value, notes: "" }),
        });
        toast({ type: "success", title: "Updated", message: "Allocation override saved." });
        await refreshAllLoadedTabs();
      } catch (err) {
        const msg = err?.data?.error?.message ?? "Failed to save the override. Please try again.";
        toast({ type: "error", title: "Error", message: msg });
        cell.innerHTML = esc(formatDays(originalDays));
      }
    });
  });
}

// ---- Allocation Set dropdown ----

function renderAllocationSetHint() {
  const hint = document.getElementById("rp-grid-allocation-set-hint");
  const activateBtn = document.getElementById("rp-grid-activate-set-btn");
  if (!hint) return;

  hint.hidden = false;
  hint.className = "rp-grid-allocation-set-hint";

  if (currentAllocationSetStatus === "draft") {
    hint.hidden = true;
    if (activateBtn) activateBtn.hidden = false;
  } else if (currentAllocationSetStatus === "active") {
    hint.classList.add("is-active");
    hint.innerHTML = `<icon-field icon="bi-lock-fill"></icon-field> <strong>Active allocation set.</strong> Cells are read-only. Run the engine to create a new draft set for editing.`;
    if (activateBtn) activateBtn.hidden = true;
  } else if (currentAllocationSetStatus === "superseded") {
    hint.classList.add("is-superseded");
    hint.innerHTML = `<icon-field icon="bi-archive-fill"></icon-field> <strong>Superseded allocation set.</strong> This set has been replaced by a newer run. Cells are read-only.`;
    if (activateBtn) activateBtn.hidden = true;
  } else {
    hint.hidden = true;
    if (activateBtn) activateBtn.hidden = true;
  }
}

async function initAllocationSetDropdown() {
  const container = document.getElementById("rp-grid-allocation-set-container");
  if (!container) return;

  try {
    const { href, method } = API_URLS.resourcePlans.allocationSetsList(planCode, versionNumber);
    const res = await apiFetch(href, { method });
    allocationSets = res?.data ?? [];
  } catch {
    allocationSets = [];
  }

  if (!allocationSets.length) {
    container.innerHTML = `<span class="text-muted">No allocation sets yet — run the engine</span>`;
    currentAllocationSetCode = null;
    currentAllocationSetStatus = null;
    renderAllocationSetHint();
    return;
  }

  const selected = allocationSets[0];
  currentAllocationSetCode = selected.code;
  currentAllocationSetStatus = selected.status;

  // <dropdown-field> only parses its <values-list> children once, at its
  // own connectedCallback — rebuilding the whole element (rather than
  // mutating an already-connected instance's innerHTML) is required every
  // time the option list changes (new engine run, activation, etc.).
  const optionsHtml = allocationSets
    .map((s) => `<value value="${esc(s.code)}">${esc(allocationSetLabel(s))}</value>`)
    .join("");
  container.innerHTML = `
    <dropdown-field id="rp-grid-allocation-set" name="allocation_set" value="${esc(selected.code)}">
      <values-list>${optionsHtml}</values-list>
    </dropdown-field>
  `;

  renderAllocationSetHint();

  document.getElementById("rp-grid-allocation-set")?.addEventListener("change", async (e) => {
    const code = e.target.value;
    const match = allocationSets.find((s) => s.code === code);
    currentAllocationSetCode = match ? match.code : null;
    currentAllocationSetStatus = match ? match.status : null;
    renderAllocationSetHint();
    await refreshAllLoadedTabs();
  });
}

function initActivateButton() {
  const activateBtn = document.getElementById("rp-grid-activate-set-btn");
  activateBtn?.addEventListener("click", async () => {
    if (!currentAllocationSetCode) return;
    const snap = snapshotButton(activateBtn);
    setBusyButton(activateBtn, "Activating…");
    try {
      const { href, method } = API_URLS.resourcePlans.allocationSetActivate(
        planCode,
        versionNumber,
        currentAllocationSetCode,
      );
      await apiFetch(href, { method });
      restoreButton(activateBtn, snap);
      toast({ type: "success", title: "Activated", message: "The allocation set is now active." });
      await initAllocationSetDropdown();
      await refreshAllLoadedTabs();
    } catch (err) {
      restoreButton(activateBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to activate the allocation set.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ---- Utilisation navigation ----

function initUtilisationButton() {
  const utilisationBtn = document.getElementById("rp-grid-utilisation-btn");
  utilisationBtn?.addEventListener("click", () => {
    const base = UI_URLS.resourcePlans.versionUtilisation(planCode, versionNumber);
    window.location.href = currentAllocationSetCode
      ? `${base}?allocation_set=${encodeURIComponent(currentAllocationSetCode)}`
      : base;
  });
}

// ---- Conflicts navigation ----

function initConflictsButton() {
  const conflictsBtn = document.getElementById("rp-grid-conflicts-btn");
  conflictsBtn?.addEventListener("click", () => {
    const base = UI_URLS.resourcePlans.versionConflicts(planCode, versionNumber);
    window.location.href = currentAllocationSetCode
      ? `${base}?allocation_set=${encodeURIComponent(currentAllocationSetCode)}`
      : base;
  });
}

// ---- Placeholder Leaves navigation ----

function initPlaceholderLeavesButton() {
  const placeholderLeavesBtn = document.getElementById("rp-grid-placeholder-leaves-btn");
  placeholderLeavesBtn?.addEventListener("click", () => {
    window.location.href = UI_URLS.resourcePlans.versionPlaceholderLeaves(planCode, versionNumber);
  });
}

// ---- Snapshots navigation ----

function initSnapshotsButton() {
  const snapshotsBtn = document.getElementById("rp-grid-snapshots-btn");
  snapshotsBtn?.addEventListener("click", () => {
    window.location.href = UI_URLS.resourcePlans.versionSnapshots(planCode, versionNumber);
  });
}

// ---- Engine job run + poll ----

const ENGINE_JOB_STATUS_LABELS = {
  pending: "Pending",
  running: "Running",
  complete: "Complete",
  failed: "Failed",
};

function engineJobStatusBadgeClass(status) {
  if (status === "complete") return "rp-badge rp-badge-soft rp-badge-success";
  if (status === "failed") return "rp-badge rp-badge-soft rp-badge-danger";
  if (status === "running") return "rp-badge rp-badge-soft rp-badge-warning";
  return "rp-badge rp-badge-soft";
}

function renderGridEngineJobProgress(job) {
  const pill = document.getElementById("rp-grid-engine-job-status-pill");
  const statusText = document.getElementById("rp-grid-engine-job-status-text");
  const progressBar = document.getElementById("rp-grid-engine-job-progress-bar");
  const errorSummary = document.getElementById("rp-grid-engine-job-error-summary");
  const errorsContainer = document.getElementById("rp-grid-engine-job-errors");

  if (pill) {
    pill.className = engineJobStatusBadgeClass(job.status);
    pill.textContent = (
      job.status_display ||
      ENGINE_JOB_STATUS_LABELS[job.status] ||
      job.status
    ).toUpperCase();
  }
  if (statusText) statusText.textContent = job.status_display || job.status;
  if (progressBar) progressBar.setAttribute("percent", String(job.progress_percentage ?? 0));

  const errors = Array.isArray(job.error_log) ? job.error_log : [];
  if (errorSummary) {
    errorSummary.hidden = errors.length === 0;
    errorSummary.textContent = errors.length
      ? `${errors.length} error${errors.length === 1 ? "" : "s"}`
      : "";
  }
  if (errorsContainer) {
    errorsContainer.innerHTML = errors.length
      ? `<strong class="text-danger">Errors</strong>` +
        errors
          .map(
            (err) =>
              `<div class="rp-card p-2 mt-2"><div>${esc(String(err.message || ""))}</div></div>`,
          )
          .join("")
      : "";
  }
}

async function pollGridEngineJob(jobCode) {
  enginePolling = true;
  while (enginePolling) {
    try {
      const { href, method } = API_URLS.resourcePlans.engineJobDetail(
        planCode,
        versionNumber,
        jobCode,
      );
      const res = await apiFetch(href, { method });
      const job = res?.data;
      if (job) renderGridEngineJobProgress(job);
      if (job && (job.status === "complete" || job.status === "failed")) {
        enginePolling = false;
        if (job.status === "complete") {
          await initAllocationSetDropdown();
          await refreshAllLoadedTabs();
        }
        break;
      }
    } catch {
      enginePolling = false;
      break;
    }
    if (enginePolling) await new Promise((resolve) => setTimeout(resolve, 5000));
  }
}

function initGridEngineJobDrawer() {
  const runEngineBtn = document.getElementById("rp-grid-run-engine-btn");
  const drawer = document.getElementById("rp-grid-engine-job-drawer");
  const formView = document.getElementById("rp-grid-engine-job-form-view");
  const progressView = document.getElementById("rp-grid-engine-job-progress-view");
  const submitBtn = document.getElementById("rp-grid-engine-job-run-btn");
  if (!drawer || !formView || !progressView || !submitBtn) return;

  runEngineBtn?.addEventListener("click", () => {
    enginePolling = false;
    const modeField = document.getElementById("rp-grid-engine-job-mode");
    const includeCurrentSprintField = document.getElementById(
      "rp-grid-engine-job-include-current-sprint",
    );
    // radio-group-field only exposes a read-only `value` getter — the
    // checked option must be set on the underlying <input> directly.
    const validateInput = modeField?.querySelector('input[value="validate"]');
    if (validateInput) validateInput.checked = true;
    if (includeCurrentSprintField) includeCurrentSprintField.checked = false;
    formView.hidden = false;
    progressView.hidden = true;
    drawer.show();
  });

  submitBtn.addEventListener("click", async () => {
    const modeField = document.getElementById("rp-grid-engine-job-mode");
    const includeCurrentSprintField = document.getElementById(
      "rp-grid-engine-job-include-current-sprint",
    );
    const mode = modeField?.value || "validate";

    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Running…");

    try {
      const { href, method } = API_URLS.resourcePlans.engineJobsCreate(planCode, versionNumber);
      const res = await apiFetch(href, {
        method,
        body: JSON.stringify({
          mode,
          include_current_sprint: includeCurrentSprintField?.checked === true,
        }),
      });
      restoreButton(submitBtn, snap);

      const job = res?.data;
      formView.hidden = true;
      progressView.hidden = false;
      if (job) {
        renderGridEngineJobProgress(job);
        if (job.status !== "complete" && job.status !== "failed") {
          pollGridEngineJob(job.code);
        } else if (job.status === "complete") {
          await initAllocationSetDropdown();
          await refreshAllLoadedTabs();
        }
      }
      toast({
        type: "success",
        title: "Engine started",
        message: "The engine job has started running.",
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to start the engine. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ---- Bootstrap ----

document.addEventListener("DOMContentLoaded", () => {
  const planCodeField = document.getElementById("rp-grid-plan-code");
  const versionField = document.getElementById("rp-grid-version-number");
  if (!planCodeField || !versionField) return;

  planCode = planCodeField.value;
  versionNumber = parseInt(versionField.value, 10);

  initGridEngineJobDrawer();
  initOverrideEditing();
  initActivateButton();
  initConflictsButton();
  initPlaceholderLeavesButton();
  initUtilisationButton();
  initSnapshotsButton();

  initAllocationSetDropdown().then(() => {
    initializeGrid();
  });
});
