"use strict";

import { esc } from "../../components/utils.js";
import { apiFetch } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS } from "../main/urls.js";

// ---- Shared state ----
let planCode = "";
let versionNumber = 0;
let allocationSets = [];
let currentAllocationSetCode = null;
let pendingConflict = null;
let pendingManpowerRequest = null;

const SEVERITY_OPTIONS = [
  { value: "0", label: "Error" },
  { value: "1", label: "Warning" },
  { value: "2", label: "Info" },
];

const CONFLICT_TYPE_OPTIONS = [
  { value: "capacity_exceeded", label: "Capacity Exceeded" },
  { value: "competing_priority", label: "Competing Priority" },
  { value: "timeline_breach", label: "Timeline Breach" },
  { value: "budget_exceeded", label: "Budget Exceeded" },
  { value: "dependency_violated", label: "Dependency Violated" },
  { value: "unresolvable_gap", label: "Unresolvable Gap" },
  { value: "threshold_breach", label: "Threshold Breach" },
];

const CONFLICT_STATUS_OPTIONS = [
  { value: "open", label: "Open" },
  { value: "resolved", label: "Resolved" },
  { value: "dismissed", label: "Dismissed" },
];

const MANPOWER_STATUS_OPTIONS = [
  { value: "open", label: "Open" },
  { value: "hiring", label: "Hiring" },
  { value: "rebalanced", label: "Rebalanced" },
  { value: "dismissed", label: "Dismissed" },
];

// ---- Utility functions ----

function allocationSetLabel(row) {
  const num = String(row.code || "")
    .split("-")
    .pop();
  return `Set #${num} — ${row.status_display || row.status}`;
}

function severityBadgeClass(severity) {
  if (Number(severity) === 0) return "rp-badge rp-badge-soft rp-badge-danger";
  if (Number(severity) === 1) return "rp-badge rp-badge-soft rp-badge-warning";
  return "rp-badge rp-badge-soft";
}

function statusBadgeClass(status) {
  if (status === "resolved" || status === "hiring" || status === "rebalanced") {
    return "rp-badge rp-badge-soft rp-badge-success";
  }
  if (status === "dismissed") return "rp-badge rp-badge-soft";
  return "rp-badge rp-badge-soft rp-badge-info";
}

function dash(value) {
  return value ? esc(value) : `<span class="rp-grid-empty-cell">—</span>`;
}

// ---- Row templates ----

window.renderConflictRow = function renderConflictRow(row) {
  return `
    <td>${esc(row.conflict_type_display)}</td>
    <td><span class="${severityBadgeClass(row.severity)}">${esc(row.severity_display)}</span></td>
    <td><span class="${statusBadgeClass(row.status)}">${esc(row.status_display)}</span></td>
    <td>${dash(row.affected_project_name)}</td>
    <td>${dash(row.affected_phase_name)}</td>
    <td>${dash(row.affected_member_name)}</td>
    <td>${dash(row.affected_sprint_name)}</td>
    <td>${dash(row.affected_team_name)}</td>
    <td>${dash(row.description)}</td>
  `;
};

window.renderManpowerRequestRow = function renderManpowerRequestRow(row) {
  return `
    <td>${esc(row.team_name)}</td>
    <td>${dash(row.phase_name)}</td>
    <td>${esc(row.sprints_needed)}</td>
    <td>${esc(Number(row.days_needed).toFixed(2))}d</td>
    <td><span class="${statusBadgeClass(row.status)}">${esc(row.status_display)}</span></td>
  `;
};

// ---- Tabs ----

function buildFilterPanelMarkup(kind) {
  if (kind === "conflicts") {
    const typeOptions = CONFLICT_TYPE_OPTIONS.map(
      (o) => `<value value="${esc(o.value)}">${esc(o.label)}</value>`,
    ).join("");
    const severityOptions = SEVERITY_OPTIONS.map(
      (o) => `<value value="${esc(o.value)}">${esc(o.label)}</value>`,
    ).join("");
    const statusOptions = CONFLICT_STATUS_OPTIONS.map(
      (o) => `<value value="${esc(o.value)}">${esc(o.label)}</value>`,
    ).join("");
    return `
      <filter-panel>
        <search-field name="search" placeholder="Search description…"></search-field>
        <dropdown-field name="type" label="Type" col="col-md-3">
          <values-list><value value="">All Types</value>${typeOptions}</values-list>
        </dropdown-field>
        <dropdown-field name="severity" label="Severity" col="col-md-2">
          <values-list><value value="">All Severities</value>${severityOptions}</values-list>
        </dropdown-field>
        <dropdown-field name="status" label="Status" col="col-md-2">
          <values-list><value value="">All Statuses</value>${statusOptions}</values-list>
        </dropdown-field>
      </filter-panel>
    `;
  }
  const statusOptions = MANPOWER_STATUS_OPTIONS.map(
    (o) => `<value value="${esc(o.value)}">${esc(o.label)}</value>`,
  ).join("");
  return `
    <filter-panel>
      <dropdown-field name="status" label="Status" col="col-md-3">
        <values-list><value value="">All Statuses</value>${statusOptions}</values-list>
      </dropdown-field>
    </filter-panel>
  `;
}

function buildConflictsTableMarkup(url) {
  const resolveAction = document.getElementById("rp-conflict-resolve-modal")
    ? `<table-action icon="bi-check2-circle" label="Resolve" event="rp:conflict:resolve" hidden-key="is_finalized"></table-action>`
    : "";
  return `
    <list-view show-active-filters>
      ${buildFilterPanelMarkup("conflicts")}
      <data-table id="rp-conflicts-table" url="${esc(url)}" paginated row-template="renderConflictRow" empty-message="No conflicts found.">
        <table-columns>
          <table-column label="Type" key="conflict_type_display"></table-column>
          <table-column label="Severity" key="severity_display"></table-column>
          <table-column label="Status" key="status_display"></table-column>
          <table-column label="Project" key="affected_project_name"></table-column>
          <table-column label="Phase" key="affected_phase_name"></table-column>
          <table-column label="Member" key="affected_member_name"></table-column>
          <table-column label="Sprint" key="affected_sprint_name"></table-column>
          <table-column label="Team" key="affected_team_name"></table-column>
          <table-column label="Description" key="description"></table-column>
        </table-columns>
        <table-actions>${resolveAction}</table-actions>
      </data-table>
    </list-view>
  `;
}

function buildManpowerRequestsTableMarkup(url) {
  const hireAction = document.getElementById("rp-manpower-hire-modal")
    ? `<table-action icon="bi-person-plus-fill" label="Hire" event="rp:manpower-request:hire" hidden-key="is_finalized"></table-action>`
    : "";
  const rebalanceAction = document.getElementById("rp-manpower-rebalance-modal")
    ? `<table-action icon="bi-arrow-left-right" label="Rebalance" event="rp:manpower-request:rebalance" hidden-key="is_finalized"></table-action>`
    : "";
  const dismissAction = document.getElementById("rp-manpower-dismiss-modal")
    ? `<table-action icon="bi-x-circle" label="Dismiss" event="rp:manpower-request:dismiss" danger hidden-key="is_finalized"></table-action>`
    : "";
  return `
    <list-view show-active-filters>
      ${buildFilterPanelMarkup("manpower")}
      <data-table id="rp-manpower-requests-table" url="${esc(url)}" paginated row-template="renderManpowerRequestRow" empty-message="No manpower requests found.">
        <table-columns>
          <table-column label="Team" key="team_name"></table-column>
          <table-column label="Phase" key="phase_name"></table-column>
          <table-column label="Sprints Needed" key="sprints_needed" numeric></table-column>
          <table-column label="Days Needed" key="days_needed" numeric></table-column>
          <table-column label="Status" key="status_display"></table-column>
        </table-columns>
        <table-actions>${hireAction}${rebalanceAction}${dismissAction}</table-actions>
      </data-table>
    </list-view>
  `;
}

function buildTabsMarkup() {
  const conflictsUrl = API_URLS.resourcePlans.conflictsList(
    planCode,
    versionNumber,
    currentAllocationSetCode,
  ).href;
  const manpowerUrl = API_URLS.resourcePlans.manpowerRequestsList(
    planCode,
    versionNumber,
    currentAllocationSetCode,
  ).href;

  return `
    <tab-panel id="rp-conflicts-tabs">
      <tab-items>
        <tab-item id="conflicts" active>
          <tab-header title="Conflicts" icon="bi-exclamation-triangle"></tab-header>
          <tab-content>${buildConflictsTableMarkup(conflictsUrl)}</tab-content>
        </tab-item>
        <tab-item id="manpower-requests">
          <tab-header title="Manpower Requests" icon="bi-people"></tab-header>
          <tab-content>${buildManpowerRequestsTableMarkup(manpowerUrl)}</tab-content>
        </tab-item>
      </tab-items>
    </tab-panel>
  `;
}

function renderTabs() {
  const container = document.getElementById("rp-conflicts-tabs-container");
  if (!container) return;

  if (!currentAllocationSetCode) {
    container.innerHTML = `<p class="text-muted">No allocation sets yet — run the engine from the Allocation Grid page first.</p>`;
    return;
  }

  container.innerHTML = buildTabsMarkup();
  initResolveHandler();
  initManpowerRequestHandlers();
}

// ---- Allocation Set dropdown ----

async function initAllocationSetDropdown() {
  const container = document.getElementById("rp-conflicts-allocation-set-container");
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
    renderTabs();
    return;
  }

  const requested = new URLSearchParams(window.location.search).get("allocation_set");
  const preselected = requested && allocationSets.find((s) => s.code === requested);
  const selected = preselected || allocationSets[0];
  currentAllocationSetCode = selected.code;

  const optionsHtml = allocationSets
    .map((s) => `<value value="${esc(s.code)}">${esc(allocationSetLabel(s))}</value>`)
    .join("");
  container.innerHTML = `
    <dropdown-field id="rp-conflicts-allocation-set" name="allocation_set" value="${esc(selected.code)}">
      <values-list>${optionsHtml}</values-list>
    </dropdown-field>
  `;

  document.getElementById("rp-conflicts-allocation-set")?.addEventListener("change", (e) => {
    const code = e.target.value;
    const match = allocationSets.find((s) => s.code === code);
    currentAllocationSetCode = match ? match.code : null;
    renderTabs();
  });

  renderTabs();
}

// ---- Resolve modal ----

function initResolveHandler() {
  const table = document.getElementById("rp-conflicts-table");
  const modal = document.getElementById("rp-conflict-resolve-modal");
  if (!table || !modal) return;

  table.addEventListener("rp:conflict:resolve", (e) => {
    pendingConflict = e.detail.row;
    const optionsContainer = document.getElementById("rp-conflict-resolve-options-container");
    const notesField = document.getElementById("rp-conflict-resolve-notes");
    if (notesField) notesField.value = "";

    const allowed = pendingConflict.allowed_resolutions || [];
    const optionsHtml = allowed
      .map(
        (o, idx) =>
          `<option-field value="${esc(o.value)}" label="${esc(o.label)}" ${idx === 0 ? "checked" : ""}></option-field>`,
      )
      .join("");
    // radio-group-field only parses its <option-field> children once on
    // connect — rebuild the element fresh each time the allowed resolution
    // set changes for a new conflict.
    if (optionsContainer) {
      optionsContainer.innerHTML = `
        <radio-group-field id="rp-conflict-resolve-type" name="resolution_type" label="Resolution" col="col-12">
          ${optionsHtml}
        </radio-group-field>
      `;
    }
    modal.show();
    // show() sets the `open` attribute, which triggers FormModal's own
    // attributeChangedCallback → _render() and resets the title back to
    // its static `title` attribute — setTitle() must run after show().
    modal.setTitle(`Resolve: ${pendingConflict.conflict_type_display}`);
  });

  modal.addEventListener("rp:primary", async () => {
    if (!pendingConflict || !currentAllocationSetCode) return;
    const typeField = document.getElementById("rp-conflict-resolve-type");
    const notesField = document.getElementById("rp-conflict-resolve-notes");
    const resolutionType = typeField?.value || "";
    if (!resolutionType) return;

    try {
      const { href, method } = API_URLS.resourcePlans.conflictResolve(
        planCode,
        versionNumber,
        currentAllocationSetCode,
        pendingConflict.code,
      );
      await apiFetch(href, {
        method,
        body: JSON.stringify({
          resolution_type: resolutionType,
          notes: notesField?.value || "",
        }),
      });
      modal.hide();
      table.refresh();
      toast({ type: "success", title: "Resolved", message: "The conflict has been resolved." });
      pendingConflict = null;
    } catch (err) {
      const msg = err?.data?.error?.message ?? "Failed to resolve the conflict. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ---- Manpower request modals ----

function initManpowerRequestHandlers() {
  const table = document.getElementById("rp-manpower-requests-table");
  if (!table) return;

  const hireModal = document.getElementById("rp-manpower-hire-modal");
  const rebalanceModal = document.getElementById("rp-manpower-rebalance-modal");
  const dismissModal = document.getElementById("rp-manpower-dismiss-modal");

  hireModal?.addEventListener("rp:primary", async () => {
    if (!pendingManpowerRequest || !currentAllocationSetCode) return;
    try {
      const { href, method } = API_URLS.resourcePlans.manpowerRequestHire(
        planCode,
        versionNumber,
        currentAllocationSetCode,
        pendingManpowerRequest.code,
      );
      await apiFetch(href, { method, body: JSON.stringify({}) });
      hireModal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Hire started",
        message: "A hire placeholder has been created.",
      });
      pendingManpowerRequest = null;
    } catch (err) {
      const msg = err?.data?.error?.message ?? "Failed to hire against this request.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });

  rebalanceModal?.addEventListener("rp:primary", async () => {
    if (!pendingManpowerRequest || !currentAllocationSetCode) return;
    const notesField = document.getElementById("rp-manpower-rebalance-notes");
    try {
      const { href, method } = API_URLS.resourcePlans.manpowerRequestRebalance(
        planCode,
        versionNumber,
        currentAllocationSetCode,
        pendingManpowerRequest.code,
      );
      await apiFetch(href, {
        method,
        body: JSON.stringify({ notes: notesField?.value || "" }),
      });
      rebalanceModal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Rebalanced",
        message: "The manpower request has been rebalanced.",
      });
      pendingManpowerRequest = null;
    } catch (err) {
      const msg = err?.data?.error?.message ?? "Failed to rebalance this request.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });

  dismissModal?.addEventListener("rp:primary", async () => {
    if (!pendingManpowerRequest || !currentAllocationSetCode) return;
    const notesField = document.getElementById("rp-manpower-dismiss-notes");
    try {
      const { href, method } = API_URLS.resourcePlans.manpowerRequestDismiss(
        planCode,
        versionNumber,
        currentAllocationSetCode,
        pendingManpowerRequest.code,
      );
      await apiFetch(href, {
        method,
        body: JSON.stringify({ notes: notesField?.value || "" }),
      });
      dismissModal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Dismissed",
        message: "The manpower request has been dismissed.",
      });
      pendingManpowerRequest = null;
    } catch (err) {
      const msg = err?.data?.error?.message ?? "Failed to dismiss this request.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });

  table.addEventListener("rp:manpower-request:hire", (e) => {
    pendingManpowerRequest = e.detail.row;
    hireModal?.show();
  });

  table.addEventListener("rp:manpower-request:rebalance", (e) => {
    pendingManpowerRequest = e.detail.row;
    const notesField = document.getElementById("rp-manpower-rebalance-notes");
    if (notesField) notesField.value = "";
    rebalanceModal?.show();
  });

  table.addEventListener("rp:manpower-request:dismiss", (e) => {
    pendingManpowerRequest = e.detail.row;
    const notesField = document.getElementById("rp-manpower-dismiss-notes");
    if (notesField) notesField.value = "";
    dismissModal?.show();
  });
}

// ---- Bootstrap ----

document.addEventListener("DOMContentLoaded", () => {
  const planCodeField = document.getElementById("rp-conflicts-plan-code");
  const versionField = document.getElementById("rp-conflicts-version-number");
  if (!planCodeField || !versionField) return;

  planCode = planCodeField.value;
  versionNumber = parseInt(versionField.value, 10);

  initAllocationSetDropdown();
});
