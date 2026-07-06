"use strict";

import { esc } from "../../components/utils.js";
import {
  apiFetch,
  formatCurrency,
  formatDateTime,
  snapshotButton,
  setBusyButton,
  restoreButton,
} from "../utils/utils.js";
import { isRequired, isValidMonth } from "../utils/validators.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

let planCode = "";
let versionNumber = "";
let financialYearCode = "";
let pendingRow = null;
let pendingConfigRow = null;
let pendingBudgetReleaseProjectRow = null;
let pendingBudgetReleaseRow = null;
let pendingBudgetReleaseLockedType = null;
let pendingDeleteBudgetReleaseRow = null;
let pendingDeleteEngineJobRow = null;
let enginePolling = false;

function readPhasePermissions() {
  const el = document.getElementById("rp-phase-permissions");
  if (!el) return { can_add: false, can_change: false, can_delete: false };
  try {
    return JSON.parse(el.textContent);
  } catch {
    return { can_add: false, can_change: false, can_delete: false };
  }
}

const phasePermissions = readPhasePermissions();

function readSegmentPermissions() {
  const el = document.getElementById("rp-segment-permissions");
  if (!el) return { can_view: false, can_add: false, can_delete: false };
  try {
    return JSON.parse(el.textContent);
  } catch {
    return { can_view: false, can_add: false, can_delete: false };
  }
}

const segmentPermissions = readSegmentPermissions();

function readDependencyPermissions() {
  const el = document.getElementById("rp-dependency-permissions");
  if (!el) return { can_view: false, can_add: false, can_change: false, can_delete: false };
  try {
    return JSON.parse(el.textContent);
  } catch {
    return { can_view: false, can_add: false, can_change: false, can_delete: false };
  }
}

const dependencyPermissions = readDependencyPermissions();

function readPausePermissions() {
  const el = document.getElementById("rp-pause-permissions");
  if (!el) return { can_view: false, can_add: false, can_change: false, can_delete: false };
  try {
    return JSON.parse(el.textContent);
  } catch {
    return { can_view: false, can_add: false, can_change: false, can_delete: false };
  }
}

const pausePermissions = readPausePermissions();

function readAssignmentPermissions() {
  const el = document.getElementById("rp-assignment-permissions");
  if (!el) return { can_view: false, can_add: false, can_change: false, can_delete: false };
  try {
    return JSON.parse(el.textContent);
  } catch {
    return { can_view: false, can_add: false, can_change: false, can_delete: false };
  }
}

const assignmentPermissions = readAssignmentPermissions();

const setView = (id, val) => {
  const el = document.getElementById(id);
  if (el) el.value = val ?? "—";
};

const showView = (id, val) => {
  const el = document.getElementById(id);
  if (!el) return;
  el.value = val;
  el.removeAttribute("hidden");
};

function initVersionDetailPage() {
  const planCodeInput = document.getElementById("rp-version-detail-plan-code");
  const versionInput = document.getElementById("rp-version-detail-version-number");
  if (!planCodeInput || !versionInput) return null;

  planCode = planCodeInput.value;
  versionNumber = versionInput.value;
  if (!planCode || !versionNumber) return null;

  const { href } = API_URLS.resourcePlans.versionDetail(planCode, versionNumber);
  return apiFetch(href, { method: "GET" })
    .then((res) => {
      const data = res?.data;
      if (!data) return;

      document.title = `v${data.version} — ${data.plan_name} — Resource Plans`;

      const titleEl = document.getElementById("rp-resource-plan-version-detail-title");
      if (titleEl) titleEl.textContent = `${data.plan_name} — v${data.version}`;

      setView("rp-version-detail-plan", `${data.plan_name} (${data.plan_code})`);
      setView("rp-version-detail-version", `v${data.version}`);

      const statusEl = document.getElementById("rp-version-detail-status");
      if (statusEl) {
        const badgeCls =
          data.status === "active"
            ? "rp-badge rp-badge-soft rp-badge-success"
            : data.status === "locked"
              ? "rp-badge rp-badge-soft rp-badge-warning"
              : "rp-badge rp-badge-soft";
        statusEl.setAttribute("badge", badgeCls);
        statusEl.value = data.status_display;
      }

      setView("rp-version-detail-threshold", `${data.threshold_percentage}%`);
      setView(
        "rp-version-detail-sprint-point-price",
        data.sprint_point_price != null ? formatCurrency(data.sprint_point_price) : "—",
      );

      if (data.cloned_from_version) {
        showView("rp-version-detail-cloned-from", `v${data.cloned_from_version}`);
      }

      if (data.financial_year_code) {
        financialYearCode = data.financial_year_code;
        const startSprintField = document.getElementById("rp-edit-version-project-start-sprint");
        const endSprintField = document.getElementById("rp-edit-version-project-end-sprint");
        if (startSprintField) startSprintField.setAttribute("fy-code", data.financial_year_code);
        if (endSprintField) endSprintField.setAttribute("fy-code", data.financial_year_code);
        const phaseStartSprintField = document.getElementById("rp-phase-start-sprint");
        const phaseEndSprintField = document.getElementById("rp-phase-end-sprint");
        if (phaseStartSprintField)
          phaseStartSprintField.setAttribute("fy-code", data.financial_year_code);
        if (phaseEndSprintField)
          phaseEndSprintField.setAttribute("fy-code", data.financial_year_code);
      }

      setView(
        "rp-version-detail-created-at",
        data.created_at ? new Date(data.created_at).toLocaleString() : "—",
      );
      setView(
        "rp-version-detail-created-by",
        data.created_by?.display_name || data.created_by?.email || "—",
      );
      setView(
        "rp-version-detail-updated-at",
        data.updated_at ? new Date(data.updated_at).toLocaleString() : "—",
      );
      setView(
        "rp-version-detail-updated-by",
        data.updated_by?.display_name || data.updated_by?.email || "—",
      );
    })
    .catch(() => {
      toast({
        type: "error",
        title: "Error",
        message: "Failed to load resource plan version details.",
      });
    });
}

// ── Unmapped Projects table ──────────────────────────────────────────────────

window.renderUnmappedProjectRow = function renderUnmappedProjectRow(row) {
  const meta = [row.code, row.programme_name].filter(Boolean).join(" · ");
  return `
    <td>
      <div class="fw-medium">${esc(row.display_name || row.name)}</div>
      <div style="color:var(--rp-text-muted);font-size:12px">${esc(meta)}</div>
    </td>
  `;
};

function initUnmappedProjectsTable() {
  const table = document.getElementById("rp-resource-plan-version-projects-table");
  if (!table) return null;

  const baseUrl = API_URLS.resourcePlans.versionProjectsUnmapped(planCode, versionNumber).href;
  table.setAttribute("url", baseUrl);

  const panel = document.getElementById("rp-resource-plan-version-projects-filters");
  if (panel) {
    panel.addEventListener("rp:filter:change", (e) => {
      const qs = e.detail.params.toString();
      table.setAttribute("url", qs ? `${baseUrl}?${qs}` : baseUrl);
    });
  }

  return table;
}

// ── Add Project drawer ───────────────────────────────────────────────────────

function setStaticHint(id, type, message) {
  const hint = document.getElementById(id);
  if (!hint) return;
  hint.setAttribute("type", type);
  hint._content = esc(message);
  if (typeof hint._render === "function") hint._render();
}

function setBudgetHint(type, message) {
  setStaticHint("rp-new-version-project-budget-hint", type, message);
}

function setEstimateHint(type, message) {
  const hint = document.getElementById("rp-new-version-project-estimate-hint");
  if (!hint) return;
  if (!message) {
    hint.hidden = true;
    return;
  }
  setStaticHint("rp-new-version-project-estimate-hint", type, message);
  hint.hidden = false;
}

function showBasisSection(basis) {
  const budgetHint = document.getElementById("rp-new-version-project-budget-hint");
  const estimateField = document.getElementById("rp-new-version-project-estimate");
  const amountField = document.getElementById("rp-new-version-project-amount");
  if (budgetHint) budgetHint.hidden = basis !== "budget";
  if (estimateField) estimateField.hidden = basis !== "estimate";
  if (amountField) amountField.hidden = basis !== "custom";
  if (basis !== "estimate") setEstimateHint("info", "");
}

async function loadBudgetHint(projectCode) {
  setBudgetHint("info", "Checking for a configured budget...");
  try {
    const { href, method } = API_URLS.resourcePlans.versionProjectBudget(planCode, versionNumber);
    const res = await apiFetch(`${href}?project=${encodeURIComponent(projectCode)}`, {
      method,
    });
    const budget = res?.data;
    if (!budget) {
      setBudgetHint(
        "warning",
        "No budget is configured for this project in the plan's financial year.",
      );
      return;
    }
    setBudgetHint(
      "success",
      `Budget available: ${formatCurrency(budget.actual_budget)} (${budget.financial_year_display}).`,
    );
  } catch {
    setBudgetHint("warning", "Could not load budget information for this project.");
  }
}

function resetAddProjectForm() {
  const basisField = document.getElementById("rp-new-version-project-basis");
  const estimateField = document.getElementById("rp-new-version-project-estimate");
  const amountField = document.getElementById("rp-new-version-project-amount");
  const priorityField = document.getElementById("rp-new-version-project-priority");
  const confidenceField = document.getElementById("rp-new-version-project-confidence");

  if (basisField) basisField.value = "";
  if (estimateField) estimateField.value = "";
  if (amountField) amountField.value = "";
  if (priorityField) priorityField.value = "";
  if (confidenceField) confidenceField.value = "";
  setEstimateHint("info", "");
  showBasisSection("");
}

function openAddProjectDrawer(row) {
  const drawer = document.getElementById("rp-resource-plan-version-project-create-drawer");
  if (!drawer) return;

  pendingRow = row;
  resetAddProjectForm();

  const estimateField = document.getElementById("rp-new-version-project-estimate");
  if (estimateField) estimateField.setAttribute("project-code", row.code);

  drawer.show();
}

function initCreateProjectDrawer(table) {
  const drawer = document.getElementById("rp-resource-plan-version-project-create-drawer");
  if (!drawer) return;

  if (table) {
    table.addEventListener("rp:version-project:add", (e) => openAddProjectDrawer(e.detail.row));
  }

  const basisField = document.getElementById("rp-new-version-project-basis");
  if (basisField) {
    basisField.addEventListener("change", (e) => {
      const basis = e.target.value;
      showBasisSection(basis);
      if (basis === "budget" && pendingRow) loadBudgetHint(pendingRow.code);
    });
  }

  const estimateField = document.getElementById("rp-new-version-project-estimate");
  if (estimateField) {
    estimateField.addEventListener("change", (e) => {
      const code = e.target.value;
      if (!code) {
        setEstimateHint("info", "");
        return;
      }
      const totalCost = estimateField.getEstimateTotalCost?.(code);
      setEstimateHint(
        "success",
        totalCost != null ? `Estimate value: ${formatCurrency(totalCost)}` : "",
      );
    });
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow) return;

    const basisField2 = document.getElementById("rp-new-version-project-basis");
    const estimateField = document.getElementById("rp-new-version-project-estimate");
    const amountField = document.getElementById("rp-new-version-project-amount");
    const priorityField = document.getElementById("rp-new-version-project-priority");
    const confidenceField = document.getElementById("rp-new-version-project-confidence");

    const basis = basisField2?.value || "";
    if (!basis) {
      toast({ type: "warning", title: "Basis required", message: "Please select a basis." });
      return;
    }

    const payload = {
      project_code: pendingRow.code,
      basis,
      priority_override: priorityField?.value || null,
      confidence_override: confidenceField?.value || null,
    };
    if (basis === "estimate") payload.estimate_code = estimateField?.value || "";
    if (basis === "custom") payload.basis_amount = amountField?.value || "";

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Adding…");

    try {
      const { href, method } = API_URLS.resourcePlans.versionProjectCreate(planCode, versionNumber);
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table?.refresh();
      toast({
        type: "success",
        title: "Project added",
        message: `"${pendingRow.name}" has been added to this version.`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to add project. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ── Configured Projects table ────────────────────────────────────────────────

const BADGE_LABELS = { low: "Low", medium: "Medium", high: "High", very_high: "Very High" };

function priorityBadge(value) {
  if (!value) return `<span style="color:var(--rp-text-muted)">—</span>`;
  const cls =
    value === "high" || value === "very_high"
      ? "rp-badge rp-badge-soft rp-badge-danger"
      : value === "medium"
        ? "rp-badge rp-badge-soft rp-badge-warning"
        : "rp-badge rp-badge-soft rp-badge-info";
  return `<span class="${cls}">${BADGE_LABELS[value] ?? esc(value)}</span>`;
}

function confidenceBadge(value) {
  if (!value) return `<span style="color:var(--rp-text-muted)">—</span>`;
  const cls =
    value === "high" || value === "very_high"
      ? "rp-badge rp-badge-soft rp-badge-danger"
      : value === "medium"
        ? "rp-badge rp-badge-soft rp-badge-warning"
        : "rp-badge rp-badge-soft rp-badge-info";
  return `<span class="${cls}">${BADGE_LABELS[value] ?? esc(value)}</span>`;
}

function basisBadge(row) {
  const cls =
    row.basis === "budget"
      ? "rp-badge rp-badge-soft rp-badge-info"
      : row.basis === "estimate"
        ? "rp-badge rp-badge-soft rp-badge-warning"
        : "rp-badge rp-badge-soft";
  return `<span class="${cls}">${esc(row.basis_display || row.basis)}</span>`;
}

window.renderConfiguredProjectRow = function renderConfiguredProjectRow(row) {
  return `
    <td><identicon-field name="${esc(row.project_name)}" variant="geometric" no-border></identicon-field></td>
    <td>
      <div class="fw-medium">${esc(row.project_name)}</div>
      <div style="color:var(--rp-text-muted);font-size:12px">${esc(row.project_code)}</div>
    </td>
    <td>${esc(row.programme_name || "—")}</td>
    <td>${basisBadge(row)}</td>
    <td class="rp-td-num">${esc(formatCurrency(row.basis_amount))}</td>
    <td class="rp-td-num">${esc(String(row.days_required))}</td>
    <td>${priorityBadge(row.effective_priority)}</td>
    <td>${confidenceBadge(row.effective_confidence)}</td>
  `;
};

function initConfiguredProjectsTable() {
  const table = document.getElementById("rp-resource-plan-version-configured-projects-table");
  if (!table) return null;

  const baseUrl = API_URLS.resourcePlans.versionProjectsList(planCode, versionNumber).href;
  table.setAttribute("url", baseUrl);

  const panel = document.getElementById("rp-resource-plan-version-configured-projects-filters");
  if (panel) {
    panel.addEventListener("rp:filter:change", (e) => {
      const qs = e.detail.params.toString();
      table.setAttribute("url", qs ? `${baseUrl}?${qs}` : baseUrl);
    });
  }

  return table;
}

function initConfiguredProjectActionModals(table) {
  if (!table) return;

  const resyncModal = document.getElementById("rp-resource-plan-version-project-resync-modal");
  const deleteModal = document.getElementById("rp-resource-plan-version-project-delete-modal");
  let actionRow = null;

  table.addEventListener("rp:resource-plan-version-project:resync", (e) => {
    actionRow = e.detail.row;
    if (!resyncModal) return;
    resyncModal.setAttribute("title", `Resync "${actionRow.project_name}"?`);
    resyncModal.setAttribute(
      "body",
      "This will update the basis amount and recalculate days required from the latest budget/estimate value.",
    );
    resyncModal.show();
  });

  table.addEventListener("rp:resource-plan-version-project:delete", (e) => {
    actionRow = e.detail.row;
    if (!deleteModal) return;
    deleteModal.setAttribute("title", `Delete "${actionRow.project_name}"?`);
    deleteModal.setAttribute(
      "body",
      "This will remove the project from this resource plan version. This action cannot be undone.",
    );
    deleteModal.setAttribute("confirm-value", actionRow.project_name);
    deleteModal.show();
  });

  resyncModal?.addEventListener("rp:confirm", async () => {
    if (!actionRow) return;
    try {
      const { href, method } = API_URLS.resourcePlans.versionProjectResync(
        planCode,
        versionNumber,
        actionRow.code,
      );
      await apiFetch(href, { method });
      resyncModal.hide();
      toast({
        type: "success",
        title: "Project resynced",
        message: `"${actionRow.project_name}" has been resynced.`,
      });
      actionRow = null;
      table.refresh?.();
    } catch (err) {
      const msg = err?.data?.error?.message ?? "Failed to resync project. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });

  deleteModal?.addEventListener("rp:delete", async () => {
    if (!actionRow) return;
    const deleteBtn = deleteModal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");
    try {
      const { href, method } = API_URLS.resourcePlans.versionProjectDelete(
        planCode,
        versionNumber,
        actionRow.code,
      );
      await apiFetch(href, { method });
      deleteModal.hide();
      toast({
        type: "success",
        title: "Project removed",
        message: `"${actionRow.project_name}" has been removed from this version.`,
      });
      actionRow = null;
      table.refresh?.();
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete project. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ── Edit Project drawer (Config tab) ─────────────────────────────────────────

function setEditBudgetHint(type, message) {
  setStaticHint("rp-edit-version-project-budget-hint", type, message);
}

function setEditEstimateHint(type, message) {
  const hint = document.getElementById("rp-edit-version-project-estimate-hint");
  if (!hint) return;
  if (!message) {
    hint.hidden = true;
    return;
  }
  setStaticHint("rp-edit-version-project-estimate-hint", type, message);
  hint.hidden = false;
}

function showEditBasisSection(basis) {
  const budgetHint = document.getElementById("rp-edit-version-project-budget-hint");
  const estimateField = document.getElementById("rp-edit-version-project-estimate");
  const amountField = document.getElementById("rp-edit-version-project-amount");
  if (budgetHint) budgetHint.hidden = basis !== "budget";
  if (estimateField) estimateField.hidden = basis !== "estimate";
  if (amountField) amountField.hidden = basis !== "custom";
  if (basis !== "estimate") setEditEstimateHint("info", "");
}

async function loadEditBudgetHint(projectCode) {
  setEditBudgetHint("info", "Checking for a configured budget...");
  try {
    const { href, method } = API_URLS.resourcePlans.versionProjectBudget(planCode, versionNumber);
    const res = await apiFetch(`${href}?project=${encodeURIComponent(projectCode)}`, {
      method,
    });
    const budget = res?.data;
    if (!budget) {
      setEditBudgetHint(
        "warning",
        "No budget is configured for this project in the plan's financial year.",
      );
      return;
    }
    setEditBudgetHint(
      "success",
      `Budget available: ${formatCurrency(budget.actual_budget)} (${budget.financial_year_display}).`,
    );
  } catch {
    setEditBudgetHint("warning", "Could not load budget information for this project.");
  }
}

function setEditDrawerSyncedAt(text) {
  const drawer = document.getElementById("rp-resource-plan-version-project-edit-drawer");
  const metaEl = drawer?.querySelector(".rp-rdrawer-foot-meta");
  if (metaEl) metaEl.textContent = text;
}

function resetEditProjectForm() {
  const basisField = document.getElementById("rp-edit-version-project-basis");
  const estimateField = document.getElementById("rp-edit-version-project-estimate");
  const amountField = document.getElementById("rp-edit-version-project-amount");
  const priorityField = document.getElementById("rp-edit-version-project-priority");
  const confidenceField = document.getElementById("rp-edit-version-project-confidence");
  const startSprintField = document.getElementById("rp-edit-version-project-start-sprint");
  const endSprintField = document.getElementById("rp-edit-version-project-end-sprint");
  const datesStrictField = document.getElementById("rp-edit-version-project-dates-strict");

  if (basisField) basisField.value = "";
  if (estimateField) estimateField.value = "";
  if (amountField) amountField.value = "";
  if (priorityField) priorityField.value = "";
  if (confidenceField) confidenceField.value = "";
  if (startSprintField) startSprintField.value = "";
  if (endSprintField) endSprintField.value = "";
  if (datesStrictField) datesStrictField.checked = false;
  setEditEstimateHint("info", "");
  showEditBasisSection("");
  setEditDrawerSyncedAt("");
}

async function openEditProjectDrawer(row) {
  const drawer = document.getElementById("rp-resource-plan-version-project-edit-drawer");
  if (!drawer) return;

  pendingConfigRow = row;
  resetEditProjectForm();

  const estimateField = document.getElementById("rp-edit-version-project-estimate");
  if (estimateField) estimateField.setAttribute("project-code", row.project_code);

  drawer.show();

  const basisField = document.getElementById("rp-edit-version-project-basis");
  const amountField = document.getElementById("rp-edit-version-project-amount");
  const priorityField = document.getElementById("rp-edit-version-project-priority");
  const confidenceField = document.getElementById("rp-edit-version-project-confidence");
  const startSprintField = document.getElementById("rp-edit-version-project-start-sprint");
  const endSprintField = document.getElementById("rp-edit-version-project-end-sprint");
  const datesStrictField = document.getElementById("rp-edit-version-project-dates-strict");

  try {
    const { href, method } = API_URLS.resourcePlans.versionProjectConfigGet(
      planCode,
      versionNumber,
      row.code,
    );
    const res = await apiFetch(href, { method });
    const data = res?.data;
    if (!data || pendingConfigRow?.code !== row.code) return;

    if (basisField) basisField.value = data.basis;
    showEditBasisSection(data.basis);

    if (data.basis === "estimate") {
      if (estimateField) estimateField.value = data.estimate_code || "";
      const totalCost = estimateField?.getEstimateTotalCost?.(data.estimate_code);
      setEditEstimateHint(
        "success",
        totalCost != null ? `Estimate value: ${formatCurrency(totalCost)}` : "",
      );
    } else if (data.basis === "budget") {
      loadEditBudgetHint(data.project_code);
    } else if (amountField) {
      amountField.value = data.basis_amount ?? "";
    }

    setEditDrawerSyncedAt(
      data.basis_synced_at
        ? `Synced ${new Date(data.basis_synced_at).toLocaleString()}`
        : "Not yet synced",
    );
    if (priorityField) priorityField.value = data.priority_override || "";
    if (confidenceField) confidenceField.value = data.confidence_override || "";
    if (startSprintField) startSprintField.value = data.start_sprint_code || "";
    if (endSprintField) endSprintField.value = data.end_sprint_code || "";
    if (datesStrictField) datesStrictField.checked = !!data.dates_strict;
  } catch {
    toast({
      type: "error",
      title: "Error",
      message: "Failed to load project configuration.",
    });
  }
}

function initEditProjectDrawer(table) {
  const drawer = document.getElementById("rp-resource-plan-version-project-edit-drawer");
  if (!drawer || !table) return;

  table.addEventListener("rp:resource-plan-version-project:config", (e) => {
    openEditProjectDrawer(e.detail.row);
  });

  const basisField = document.getElementById("rp-edit-version-project-basis");
  if (basisField) {
    basisField.addEventListener("change", (e) => {
      const basis = e.target.value;
      showEditBasisSection(basis);
      if (basis === "budget" && pendingConfigRow) loadEditBudgetHint(pendingConfigRow.project_code);
    });
  }

  const estimateField = document.getElementById("rp-edit-version-project-estimate");
  if (estimateField) {
    estimateField.addEventListener("change", (e) => {
      const code = e.target.value;
      if (!code) {
        setEditEstimateHint("info", "");
        return;
      }
      const totalCost = estimateField.getEstimateTotalCost?.(code);
      setEditEstimateHint(
        "success",
        totalCost != null ? `Estimate value: ${formatCurrency(totalCost)}` : "",
      );
    });
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingConfigRow) return;

    const basisField2 = document.getElementById("rp-edit-version-project-basis");
    const estimateField2 = document.getElementById("rp-edit-version-project-estimate");
    const amountField = document.getElementById("rp-edit-version-project-amount");
    const priorityField = document.getElementById("rp-edit-version-project-priority");
    const confidenceField = document.getElementById("rp-edit-version-project-confidence");
    const startSprintField = document.getElementById("rp-edit-version-project-start-sprint");
    const endSprintField = document.getElementById("rp-edit-version-project-end-sprint");
    const datesStrictField = document.getElementById("rp-edit-version-project-dates-strict");

    const basis = basisField2?.value || "";
    if (!basis) {
      toast({ type: "warning", title: "Basis required", message: "Please select a basis." });
      return;
    }

    const payload = {
      basis,
      priority_override: priorityField?.value || null,
      confidence_override: confidenceField?.value || null,
      start_sprint_code: startSprintField?.value || null,
      end_sprint_code: endSprintField?.value || null,
      dates_strict: datesStrictField?.checked === true,
    };
    if (basis === "estimate") payload.estimate_code = estimateField2?.value || "";
    if (basis === "custom") payload.basis_amount = amountField?.value || "";

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    try {
      const { href, method } = API_URLS.resourcePlans.versionProjectConfigUpdate(
        planCode,
        versionNumber,
        pendingConfigRow.code,
      );
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh?.();
      toast({
        type: "success",
        title: "Configuration saved",
        message: `"${pendingConfigRow.project_name}" configuration has been updated.`,
      });
      pendingConfigRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to save configuration. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ── Teams Assignment drawer (Configured Projects) ───────────────────────────

let pendingTeamsProjectRow = null; // configured-project row whose teams drawer is open
let pendingDeleteTeamRow = null; // team row pending delete confirmation

const ALLOCATION_TYPE_LABELS = { percent: "% of Basis Amount", days: "Days", budget: "Budget" };

function allocationValueLabel(type) {
  if (type === "percent") return "Allocation %";
  if (type === "budget") return "Allocation Budget (£)";
  return "Allocation Days";
}

function allocationValueOf(team) {
  if (team.allocation_type === "percent") return team.allocation_percentage;
  if (team.allocation_type === "budget") return team.allocation_budget;
  return team.allocation_days;
}

function resetAddTeamForm() {
  const teamField = document.getElementById("rp-new-version-team-team");
  const typeField = document.getElementById("rp-new-version-team-allocation-type");
  const valueField = document.getElementById("rp-new-version-team-value");
  const orderField = document.getElementById("rp-new-version-team-order");
  if (teamField) teamField.value = "";
  if (typeField) typeField.value = "";
  if (valueField) valueField.value = "";
  if (orderField) orderField.value = "1";
}

function updateTeamsSummary(teams) {
  const summaryEl = document.getElementById("rp-version-teams-summary");
  if (!summaryEl || !pendingTeamsProjectRow) return;

  const totalAllocated = teams.reduce((sum, t) => sum + Number(t.allocated_days || 0), 0);
  const daysRequired = Number(pendingTeamsProjectRow.days_required || 0);
  const matches = Math.abs(totalAllocated - daysRequired) < 0.005;
  const badgeCls = matches
    ? "rp-badge rp-badge-soft rp-badge-success"
    : "rp-badge rp-badge-soft rp-badge-warning";

  summaryEl.innerHTML = `${esc(String(teams.length))} team${teams.length === 1 ? "" : "s"} · <span class="${badgeCls}">${esc(totalAllocated.toFixed(2))} / ${esc(daysRequired.toFixed(2))} days allocated</span>`;
}

const RAMP_PATTERN_LABELS = {
  flat: "Flat",
  ramp_up: "Ramp Up",
  ramp_down: "Ramp Down",
  ramp_up_down: "Ramp Up Down",
  ramp_up_steady: "Ramp Up Steady",
  steady_down: "Steady Down",
  stepped: "Stepped",
  custom: "Custom",
};

window.renderPhaseRow = function renderPhaseRow(row) {
  const sprintRange =
    row.start_sprint_name && row.end_sprint_name
      ? `${esc(row.start_sprint_name)} → ${esc(row.end_sprint_name)}`
      : "—";
  const maxDays = row.max_days_per_sprint != null ? esc(String(row.max_days_per_sprint)) : "—";
  return `
    <td>${esc(row.name)}</td>
    <td>${sprintRange}</td>
    <td class="rp-td-num">${esc(String(row.sequence_order))}</td>
    <td>${esc(row.ramp_pattern_display || RAMP_PATTERN_LABELS[row.ramp_pattern] || row.ramp_pattern)}</td>
    <td class="rp-td-num">${maxDays}</td>
    <td class="rp-td-num">${esc(String(row.days_effort))}</td>
  `;
};

function buildPhasesTable(team) {
  const table = document.createElement("data-table");
  table.id = `rp-phases-table-${team.code}`;
  table.dataset.teamCode = team.code;
  table.setAttribute("row-template", "renderPhaseRow");
  table.setAttribute("empty-message", "No phases added yet.");
  table.setAttribute(
    "url",
    API_URLS.resourcePlans.versionProjectTeamPhasesList(
      planCode,
      versionNumber,
      pendingTeamsProjectRow.code,
      team.code,
    ).href,
  );

  const cols = document.createElement("table-columns");
  [
    ["Name", "name"],
    ["Sprints", "start_sprint_name"],
    ["Order", "sequence_order", true],
    ["Ramp Pattern", "ramp_pattern"],
    ["Max Days/Sprint", "max_days_per_sprint", true],
    ["Days Effort", "days_effort", true],
  ].forEach(([label, key, numeric]) => {
    const col = document.createElement("table-column");
    col.setAttribute("label", label);
    col.setAttribute("key", key);
    if (numeric) col.setAttribute("numeric", "");
    cols.appendChild(col);
  });
  table.appendChild(cols);

  const actions = document.createElement("table-actions");
  if (segmentPermissions.can_view) {
    const segmentsAction = document.createElement("table-action");
    segmentsAction.setAttribute("icon", "bi-bar-chart-steps");
    segmentsAction.setAttribute("label", "Segments");
    segmentsAction.setAttribute("event", "rp:phase:segments");
    actions.appendChild(segmentsAction);
  }
  if (dependencyPermissions.can_view) {
    const dependenciesAction = document.createElement("table-action");
    dependenciesAction.setAttribute("icon", "bi-diagram-2");
    dependenciesAction.setAttribute("label", "Dependencies");
    dependenciesAction.setAttribute("event", "rp:phase:dependencies");
    actions.appendChild(dependenciesAction);
  }
  if (pausePermissions.can_view) {
    const pausesAction = document.createElement("table-action");
    pausesAction.setAttribute("icon", "bi-pause-circle");
    pausesAction.setAttribute("label", "Pauses");
    pausesAction.setAttribute("event", "rp:phase:pauses");
    actions.appendChild(pausesAction);
  }
  if (assignmentPermissions.can_view) {
    const assignmentsAction = document.createElement("table-action");
    assignmentsAction.setAttribute("icon", "bi-person-check");
    assignmentsAction.setAttribute("label", "Assignments");
    assignmentsAction.setAttribute("event", "rp:phase:assignments");
    actions.appendChild(assignmentsAction);
  }
  if (phasePermissions.can_change) {
    const editAction = document.createElement("table-action");
    editAction.setAttribute("icon", "bi-pencil");
    editAction.setAttribute("label", "Edit");
    editAction.setAttribute("event", "rp:phase:edit");
    actions.appendChild(editAction);
  }
  if (phasePermissions.can_delete) {
    const deleteAction = document.createElement("table-action");
    deleteAction.setAttribute("icon", "bi-trash");
    deleteAction.setAttribute("label", "Delete");
    deleteAction.setAttribute("event", "rp:phase:delete");
    deleteAction.setAttribute("danger", "");
    actions.appendChild(deleteAction);
  }
  table.appendChild(actions);

  const wrapper = document.createElement("div");
  wrapper.className = "mt-3";

  const header = document.createElement("div");
  header.className = "d-flex align-items-center justify-content-between mb-2";
  const title = document.createElement("span");
  title.className = "fw-medium small";
  title.textContent = "Phases";
  header.appendChild(title);
  if (phasePermissions.can_add) {
    const addBtn = document.createElement("link-field");
    addBtn.setAttribute("href", "#");
    addBtn.setAttribute("icon", "bi-plus-lg");
    addBtn.setAttribute("variant", "icon-btn");
    addBtn.setAttribute("label", "Add phase");
    addBtn.setAttribute("title", "Add phase");
    addBtn.dataset.phaseAddBtn = team.code;
    header.appendChild(addBtn);
  }
  wrapper.appendChild(header);
  wrapper.appendChild(table);
  return wrapper;
}

function buildTeamViewBlock(team) {
  const view = document.createElement("div");
  view.className = "rp-team-view";
  const rows = [
    ["Allocation Type", ALLOCATION_TYPE_LABELS[team.allocation_type] || team.allocation_type],
    [allocationValueLabel(team.allocation_type), allocationValueOf(team)],
    ["Allocated Days", team.allocated_days],
  ];
  view.innerHTML = rows
    .map(
      ([label, value]) =>
        `<div class="d-flex justify-content-between py-1"><span style="color:var(--rp-text-muted)">${esc(label)}</span><span class="fw-medium">${esc(String(value ?? "—"))}</span></div>`,
    )
    .join("");
  return view;
}

function buildTeamEditBlock(team) {
  const edit = document.createElement("div");
  edit.className = "rp-team-edit";
  edit.hidden = true;

  const row = document.createElement("div");
  row.className = "row g-3";

  const typeField = document.createElement("dropdown-field");
  typeField.id = `rp-team-edit-type-${team.code}`;
  typeField.setAttribute("col", "col-12");
  typeField.setAttribute("label", "Allocation Type");
  typeField.setAttribute("show-label", "");
  typeField.setAttribute("required", "");
  const valuesList = document.createElement("values-list");
  [
    ["percent", "% of Basis Amount"],
    ["days", "Days"],
    ["budget", "Budget"],
  ].forEach(([val, label]) => {
    const opt = document.createElement("value");
    opt.setAttribute("value", val);
    opt.textContent = label;
    valuesList.appendChild(opt);
  });
  typeField.appendChild(valuesList);

  const valueField = document.createElement("decimal-field");
  valueField.id = `rp-team-edit-value-${team.code}`;
  valueField.setAttribute("col", "col-6");
  valueField.setAttribute("label", "Value");
  valueField.setAttribute("min", "0");
  valueField.setAttribute("required", "");

  const orderField = document.createElement("number-field");
  orderField.id = `rp-team-edit-order-${team.code}`;
  orderField.setAttribute("col", "col-6");
  orderField.setAttribute("label", "Order");
  orderField.setAttribute("min", "1");

  row.appendChild(typeField);
  row.appendChild(valueField);
  row.appendChild(orderField);
  edit.appendChild(row);

  // Custom elements need a tick to connect before their value setter is reliable.
  requestAnimationFrame(() => {
    typeField.value = team.allocation_type;
    valueField.value = String(allocationValueOf(team) ?? "");
    orderField.value = String(team.sequence_order ?? 1);
  });

  return edit;
}

function buildTeamAccordion(team) {
  const panel = document.createElement("accordion-panel");
  panel.setAttribute("group", "rp-version-teams");
  panel.dataset.teamCode = team.code;

  const header = document.createElement("accordion-header");
  const wrapper = document.createElement("div");
  wrapper.className = "d-flex align-items-center justify-content-between w-100 pe-2";

  const left = document.createElement("div");
  left.className = "d-flex align-items-center gap-2";
  const avatar = document.createElement("identicon-field");
  avatar.setAttribute("name", team.team_name);
  avatar.setAttribute("variant", "monogram");
  avatar.setAttribute("size", "md");
  const nameEl = document.createElement("span");
  nameEl.className = "fw-medium";
  nameEl.textContent = team.team_name;
  left.appendChild(avatar);
  left.appendChild(nameEl);

  const right = document.createElement("div");
  right.className = "d-flex align-items-center gap-2";

  const editBtn = document.createElement("link-field");
  editBtn.setAttribute("href", "#");
  editBtn.setAttribute("icon", "bi-pencil");
  editBtn.setAttribute("variant", "icon-btn");
  editBtn.setAttribute("label", "Edit team allocation");
  editBtn.setAttribute("title", "Edit team allocation");
  editBtn.dataset.teamEditBtn = team.code;

  const deleteBtn = document.createElement("link-field");
  deleteBtn.setAttribute("href", "#");
  deleteBtn.setAttribute("icon", "bi-trash");
  deleteBtn.setAttribute("icon-color", "danger");
  deleteBtn.setAttribute("variant", "icon-btn");
  deleteBtn.setAttribute("label", "Delete team");
  deleteBtn.setAttribute("title", "Delete team");
  deleteBtn.dataset.teamDeleteBtn = team.code;

  right.appendChild(editBtn);
  right.appendChild(deleteBtn);

  wrapper.appendChild(left);
  wrapper.appendChild(right);
  header.appendChild(wrapper);

  const body = document.createElement("accordion-body");
  body.appendChild(buildTeamViewBlock(team));
  body.appendChild(buildTeamEditBlock(team));
  body.appendChild(buildPhasesTable(team));

  panel.appendChild(header);
  panel.appendChild(body);
  return panel;
}

function renderTeamsList(teams) {
  const container = document.getElementById("rp-version-teams-container");
  if (!container) return;

  updateTeamsSummary(teams);

  if (!teams.length) {
    container.innerHTML = `
      <div class="rp-empty-state">
        <span class="rp-empty-icon bi bi-people"></span>
        <p class="rp-empty-title">No teams assigned yet.</p>
      </div>`;
    return;
  }

  container.innerHTML = "";
  teams.forEach((team, i) => {
    const panel = buildTeamAccordion(team);
    if (i > 0) panel.classList.add("mt-2");
    container.appendChild(panel);
  });
}

async function loadTeams() {
  const container = document.getElementById("rp-version-teams-container");
  if (!container || !pendingTeamsProjectRow) return;
  try {
    const { href, method } = API_URLS.resourcePlans.versionProjectTeamsList(
      planCode,
      versionNumber,
      pendingTeamsProjectRow.code,
    );
    const res = await apiFetch(href, { method });
    renderTeamsList(res?.data ?? []);
  } catch {
    container.innerHTML = `
      <div class="rp-empty-state">
        <span class="rp-empty-icon bi bi-exclamation-circle" style="color:var(--rp-danger)"></span>
        <p class="rp-empty-title">Failed to load teams. Refresh and try again.</p>
      </div>`;
  }
}

function openTeamsDrawer(row) {
  const drawer = document.getElementById("rp-resource-plan-version-teams-drawer");
  if (!drawer) return;

  pendingTeamsProjectRow = row;
  resetAddTeamForm();
  const form = document.getElementById("rp-version-team-add-form");
  if (form) form.hidden = true;

  drawer.show();
  loadTeams();
}

function initAddTeamForm() {
  const addBtn = document.getElementById("rp-version-teams-add-btn");
  const form = document.getElementById("rp-version-team-add-form");
  const cancelBtn = document.getElementById("rp-version-team-add-cancel-btn");
  const submitBtn = document.getElementById("rp-version-team-add-submit-btn");
  if (!addBtn || !form) return;

  addBtn.addEventListener("click", () => {
    const wasHidden = form.hidden;
    if (wasHidden) resetAddTeamForm();
    form.hidden = !wasHidden;
  });

  cancelBtn?.addEventListener("click", () => {
    form.hidden = true;
  });

  submitBtn?.addEventListener("click", async () => {
    if (!pendingTeamsProjectRow) return;

    const teamField = document.getElementById("rp-new-version-team-team");
    const typeField = document.getElementById("rp-new-version-team-allocation-type");
    const valueField = document.getElementById("rp-new-version-team-value");
    const orderField = document.getElementById("rp-new-version-team-order");

    const teamCode = teamField?.value || "";
    const allocationType = typeField?.value || "";
    const value = valueField?.value || "";

    if (!teamCode || !allocationType || value === "") {
      toast({
        type: "warning",
        title: "Missing details",
        message: "Please fill in team, allocation type, and value.",
      });
      return;
    }

    const payload = {
      team_code: teamCode,
      allocation_type: allocationType,
      value,
      sequence_order: parseInt(orderField?.value || "1", 10) || 1,
    };

    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Adding…");

    try {
      const { href, method } = API_URLS.resourcePlans.versionProjectTeamCreate(
        planCode,
        versionNumber,
        pendingTeamsProjectRow.code,
      );
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      form.hidden = true;
      await loadTeams();
      toast({
        type: "success",
        title: "Team added",
        message: "The team has been assigned to this project.",
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to add team. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initTeamRowActions() {
  const container = document.getElementById("rp-version-teams-container");
  const deleteModal = document.getElementById("rp-resource-plan-version-team-delete-modal");

  container?.addEventListener("click", async (e) => {
    const editBtn = e.target.closest("[data-team-edit-btn]");
    if (editBtn) {
      e.preventDefault();
      const teamCode = editBtn.getAttribute("data-team-edit-btn");
      const panel = container.querySelector(
        `accordion-panel[data-team-code="${CSS.escape(teamCode)}"]`,
      );
      const viewBlock = panel?.querySelector(".rp-team-view");
      const editBlock = panel?.querySelector(".rp-team-edit");
      const icon = editBtn.querySelector(".bi");
      if (!panel || !viewBlock || !editBlock) return;

      const isEditing = !editBlock.hidden;
      if (!isEditing) {
        viewBlock.hidden = true;
        editBlock.hidden = false;
        icon?.classList.replace("bi-pencil", "bi-check-lg");
        return;
      }

      const typeField = editBlock.querySelector(`#rp-team-edit-type-${CSS.escape(teamCode)}`);
      const valueField = editBlock.querySelector(`#rp-team-edit-value-${CSS.escape(teamCode)}`);
      const orderField = editBlock.querySelector(`#rp-team-edit-order-${CSS.escape(teamCode)}`);
      const payload = {
        allocation_type: typeField?.value || "",
        value: valueField?.value || "",
        sequence_order: parseInt(orderField?.value || "1", 10) || 1,
      };
      if (!payload.allocation_type || payload.value === "") {
        toast({
          type: "warning",
          title: "Missing details",
          message: "Please fill in allocation type and value.",
        });
        return;
      }

      try {
        const { href, method } = API_URLS.resourcePlans.versionProjectTeamUpdate(
          planCode,
          versionNumber,
          pendingTeamsProjectRow.code,
          teamCode,
        );
        await apiFetch(href, { method, body: JSON.stringify(payload) });
        toast({
          type: "success",
          title: "Allocation saved",
          message: "Team allocation has been updated.",
        });
        await loadTeams();
      } catch (err) {
        const msg = err?.data?.error?.message ?? "Failed to save allocation. Please try again.";
        toast({ type: "error", title: "Error", message: msg });
      }
      return;
    }

    const deleteBtn = e.target.closest("[data-team-delete-btn]");
    if (deleteBtn) {
      e.preventDefault();
      const teamCode = deleteBtn.getAttribute("data-team-delete-btn");
      const panel = container.querySelector(
        `accordion-panel[data-team-code="${CSS.escape(teamCode)}"]`,
      );
      const nameEl = panel?.querySelector(".fw-medium");
      pendingDeleteTeamRow = { code: teamCode, name: nameEl?.textContent || "this team" };
      if (!deleteModal) return;
      deleteModal.setAttribute("title", `Remove "${pendingDeleteTeamRow.name}"?`);
      deleteModal.setAttribute("body", "This will remove the team's allocation from this project.");
      deleteModal.setAttribute("confirm-value", pendingDeleteTeamRow.name);
      deleteModal.show();
    }
  });

  deleteModal?.addEventListener("rp:delete", async () => {
    if (!pendingDeleteTeamRow || !pendingTeamsProjectRow) return;
    const deleteConfirmBtn = deleteModal.querySelector("[data-delete-modal]");
    deleteConfirmBtn?.setAttribute("disabled", "");
    try {
      const { href, method } = API_URLS.resourcePlans.versionProjectTeamDelete(
        planCode,
        versionNumber,
        pendingTeamsProjectRow.code,
        pendingDeleteTeamRow.code,
      );
      await apiFetch(href, { method });
      deleteModal.hide();
      toast({
        type: "success",
        title: "Team removed",
        message: `"${pendingDeleteTeamRow.name}" has been removed from this project.`,
      });
      pendingDeleteTeamRow = null;
      await loadTeams();
    } catch (err) {
      deleteConfirmBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to remove team. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ── Phases (per team, inside the Teams drawer) ──────────────────────────────

let pendingPhaseTeamCode = null;
let pendingPhaseRow = null; // null = create mode, set = edit mode
let pendingDeletePhaseRow = null; // { teamCode, code, name }

function phasesTableFor(teamCode) {
  return document.getElementById(`rp-phases-table-${teamCode}`);
}

function resetPhaseForm() {
  const nameField = document.getElementById("rp-phase-name");
  const startSprintField = document.getElementById("rp-phase-start-sprint");
  const endSprintField = document.getElementById("rp-phase-end-sprint");
  const maxDaysField = document.getElementById("rp-phase-max-days-per-sprint");
  const orderField = document.getElementById("rp-phase-sequence-order");
  const rampField = document.getElementById("rp-phase-ramp-pattern");
  const splitField = document.getElementById("rp-phase-split-mode");
  const multiEngineersField = document.getElementById("rp-phase-allow-multiple-engineers");
  const notesField = document.getElementById("rp-phase-notes");

  if (nameField) nameField.value = "";
  if (startSprintField) startSprintField.value = "";
  if (endSprintField) endSprintField.value = "";
  if (maxDaysField) maxDaysField.value = "";
  if (orderField) orderField.value = "1";
  if (rampField) rampField.value = "flat";
  if (splitField) splitField.value = "auto";
  if (multiEngineersField) multiEngineersField.checked = false;
  if (notesField) notesField.value = "";
}

function fillPhaseForm(row) {
  const nameField = document.getElementById("rp-phase-name");
  const startSprintField = document.getElementById("rp-phase-start-sprint");
  const endSprintField = document.getElementById("rp-phase-end-sprint");
  const maxDaysField = document.getElementById("rp-phase-max-days-per-sprint");
  const orderField = document.getElementById("rp-phase-sequence-order");
  const rampField = document.getElementById("rp-phase-ramp-pattern");
  const splitField = document.getElementById("rp-phase-split-mode");
  const multiEngineersField = document.getElementById("rp-phase-allow-multiple-engineers");
  const notesField = document.getElementById("rp-phase-notes");

  if (nameField) nameField.value = row.name;
  if (startSprintField) startSprintField.value = row.start_sprint_code || "";
  if (endSprintField) endSprintField.value = row.end_sprint_code || "";
  if (maxDaysField) {
    maxDaysField.value = row.max_days_per_sprint != null ? String(row.max_days_per_sprint) : "";
  }
  if (orderField) orderField.value = String(row.sequence_order);
  if (rampField) rampField.value = row.ramp_pattern;
  if (splitField) splitField.value = row.split_mode;
  if (multiEngineersField) multiEngineersField.checked = !!row.allow_multiple_engineers;
  if (notesField) notesField.value = row.notes || "";
}

function openPhaseDrawer(teamCode, row = null) {
  const drawer = document.getElementById("rp-resource-plan-phase-drawer");
  if (!drawer) return;

  pendingPhaseTeamCode = teamCode;
  pendingPhaseRow = row;

  resetPhaseForm();
  if (row) fillPhaseForm(row);

  if (financialYearCode) {
    const startSprintField = document.getElementById("rp-phase-start-sprint");
    const endSprintField = document.getElementById("rp-phase-end-sprint");
    if (startSprintField) startSprintField.setAttribute("fy-code", financialYearCode);
    if (endSprintField) endSprintField.setAttribute("fy-code", financialYearCode);
  }

  drawer.setTitle?.(row ? "Edit Phase" : "Add Phase");
  drawer.show();
}

function initPhasesContainerEvents() {
  const container = document.getElementById("rp-version-teams-container");
  if (!container) return;

  container.addEventListener("click", (e) => {
    const addBtn = e.target.closest("[data-phase-add-btn]");
    if (!addBtn) return;
    e.preventDefault();
    openPhaseDrawer(addBtn.getAttribute("data-phase-add-btn"));
  });

  container.addEventListener("rp:phase:segments", (e) => {
    const table = e.target.closest("data-table");
    const teamCode = table?.dataset.teamCode;
    if (teamCode) openSegmentsDrawer(teamCode, e.detail.row);
  });

  container.addEventListener("rp:phase:dependencies", (e) => {
    const table = e.target.closest("data-table");
    const teamCode = table?.dataset.teamCode;
    if (teamCode) openDependenciesDrawer(teamCode, e.detail.row);
  });

  container.addEventListener("rp:phase:pauses", (e) => {
    const table = e.target.closest("data-table");
    const teamCode = table?.dataset.teamCode;
    if (teamCode) openPausesDrawer(teamCode, e.detail.row);
  });

  container.addEventListener("rp:phase:assignments", (e) => {
    const table = e.target.closest("data-table");
    const teamCode = table?.dataset.teamCode;
    if (teamCode) openAssignmentsDrawer(teamCode, e.detail.row);
  });

  container.addEventListener("rp:phase:edit", (e) => {
    const table = e.target.closest("data-table");
    const teamCode = table?.dataset.teamCode;
    if (teamCode) openPhaseDrawer(teamCode, e.detail.row);
  });

  container.addEventListener("rp:phase:delete", (e) => {
    const table = e.target.closest("data-table");
    const teamCode = table?.dataset.teamCode;
    if (!teamCode) return;

    const deleteModal = document.getElementById("rp-resource-plan-phase-delete-modal");
    if (!deleteModal) return;

    pendingDeletePhaseRow = { teamCode, code: e.detail.row.code, name: e.detail.row.name };
    deleteModal.setAttribute("title", `Delete "${pendingDeletePhaseRow.name}"?`);
    deleteModal.setAttribute(
      "body",
      "This will permanently remove this phase from the team's allocation.",
    );
    deleteModal.setAttribute("confirm-value", pendingDeletePhaseRow.name);
    deleteModal.show();
  });
}

function initPhaseDrawer() {
  const drawer = document.getElementById("rp-resource-plan-phase-drawer");
  if (!drawer) return;

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingPhaseTeamCode || !pendingTeamsProjectRow) return;

    const nameField = document.getElementById("rp-phase-name");
    const startSprintField = document.getElementById("rp-phase-start-sprint");
    const endSprintField = document.getElementById("rp-phase-end-sprint");
    const maxDaysField = document.getElementById("rp-phase-max-days-per-sprint");
    const orderField = document.getElementById("rp-phase-sequence-order");
    const rampField = document.getElementById("rp-phase-ramp-pattern");
    const splitField = document.getElementById("rp-phase-split-mode");
    const multiEngineersField = document.getElementById("rp-phase-allow-multiple-engineers");
    const notesField = document.getElementById("rp-phase-notes");

    const name = nameField?.value?.trim() || "";
    const startSprintCode = startSprintField?.value || "";
    const endSprintCode = endSprintField?.value || "";
    const maxDaysPerSprint = maxDaysField?.value || "";

    if (!name) {
      toast({
        type: "warning",
        title: "Missing details",
        message: "Please fill in a name.",
      });
      return;
    }

    const payload = {
      name,
      start_sprint_code: startSprintCode || null,
      end_sprint_code: endSprintCode || null,
      max_days_per_sprint: maxDaysPerSprint !== "" ? maxDaysPerSprint : null,
      sequence_order: parseInt(orderField?.value || "1", 10) || 1,
      ramp_pattern: rampField?.value || "flat",
      split_mode: splitField?.value || "auto",
      allow_multiple_engineers: multiEngineersField?.checked === true,
      notes: notesField?.value || "",
    };

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    try {
      const teamCode = pendingPhaseTeamCode;
      if (pendingPhaseRow) {
        const { href, method } = API_URLS.resourcePlans.versionProjectTeamPhaseUpdate(
          planCode,
          versionNumber,
          pendingTeamsProjectRow.code,
          teamCode,
          pendingPhaseRow.code,
        );
        await apiFetch(href, { method, body: JSON.stringify(payload) });
      } else {
        const { href, method } = API_URLS.resourcePlans.versionProjectTeamPhaseCreate(
          planCode,
          versionNumber,
          pendingTeamsProjectRow.code,
          teamCode,
        );
        await apiFetch(href, { method, body: JSON.stringify(payload) });
      }
      restoreButton(submitBtn, snap);
      drawer.hide();
      phasesTableFor(teamCode)?.refresh();
      toast({
        type: "success",
        title: pendingPhaseRow ? "Phase updated" : "Phase added",
        message: pendingPhaseRow
          ? `"${name}" has been updated.`
          : `"${name}" has been added to this team.`,
      });
      pendingPhaseTeamCode = null;
      pendingPhaseRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to save phase. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initPhaseDeleteModal() {
  const deleteModal = document.getElementById("rp-resource-plan-phase-delete-modal");
  if (!deleteModal) return;

  deleteModal.addEventListener("rp:delete", async () => {
    if (!pendingDeletePhaseRow || !pendingTeamsProjectRow) return;
    const deleteConfirmBtn = deleteModal.querySelector("[data-delete-modal]");
    deleteConfirmBtn?.setAttribute("disabled", "");
    try {
      const { href, method } = API_URLS.resourcePlans.versionProjectTeamPhaseDelete(
        planCode,
        versionNumber,
        pendingTeamsProjectRow.code,
        pendingDeletePhaseRow.teamCode,
        pendingDeletePhaseRow.code,
      );
      await apiFetch(href, { method });
      deleteModal.hide();
      toast({
        type: "success",
        title: "Phase removed",
        message: `"${pendingDeletePhaseRow.name}" has been removed.`,
      });
      phasesTableFor(pendingDeletePhaseRow.teamCode)?.refresh();
      pendingDeletePhaseRow = null;
    } catch (err) {
      deleteConfirmBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to remove phase. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ── Segments (per phase, opened from the Phases table) ──────────────────────

let pendingSegmentsTeamCode = null;
let pendingSegmentsPhaseRow = null;
let pendingDeleteSegmentRow = null; // { code, label }

window.renderSegmentRow = function renderSegmentRow(row) {
  return `
    <td class="rp-td-num">${esc(String(row.segment_order))}</td>
    <td>${esc(row.segment_type_display || row.segment_type)}</td>
    <td class="rp-td-num">${esc(String(row.start_percentage))}</td>
    <td class="rp-td-num">${esc(String(row.end_percentage))}</td>
    <td>${esc(row.progression_display || row.progression)}</td>
    <td class="rp-td-num">${esc(String(row.duration))}</td>
    <td class="rp-td-num">${esc(row.step_count != null ? String(row.step_count) : "—")}</td>
  `;
};

function resetAddSegmentForm() {
  const typeField = document.getElementById("rp-new-segment-type");
  const progressionField = document.getElementById("rp-new-segment-progression");
  const startPctField = document.getElementById("rp-new-segment-start-pct");
  const endPctField = document.getElementById("rp-new-segment-end-pct");
  const durationField = document.getElementById("rp-new-segment-duration");
  const stepCountField = document.getElementById("rp-new-segment-step-count");

  if (typeField) typeField.value = "";
  if (progressionField) progressionField.value = "linear";
  if (startPctField) startPctField.value = "";
  if (endPctField) endPctField.value = "";
  if (durationField) durationField.value = "";
  if (stepCountField) {
    stepCountField.value = "";
    stepCountField.hidden = true;
  }
}

function openSegmentsDrawer(teamCode, phaseRow) {
  const drawer = document.getElementById("rp-resource-plan-phase-segments-drawer");
  const table = document.getElementById("rp-phase-segments-table");
  if (!drawer || !table || !pendingTeamsProjectRow) return;

  pendingSegmentsTeamCode = teamCode;
  pendingSegmentsPhaseRow = phaseRow;

  const form = document.getElementById("rp-segment-add-form");
  if (form) form.hidden = true;
  resetAddSegmentForm();

  const { href } = API_URLS.resourcePlans.versionProjectTeamPhaseSegmentsList(
    planCode,
    versionNumber,
    pendingTeamsProjectRow.code,
    teamCode,
    phaseRow.code,
  );
  table.setAttribute("url", href);

  drawer.setTitle?.(`Segments — ${phaseRow.name}`);
  drawer.show();
  table.refresh?.();
}

function initAddSegmentForm() {
  const addBtn = document.getElementById("rp-segments-add-btn");
  const form = document.getElementById("rp-segment-add-form");
  const cancelBtn = document.getElementById("rp-segment-add-cancel-btn");
  const submitBtn = document.getElementById("rp-segment-add-submit-btn");
  const progressionField = document.getElementById("rp-new-segment-progression");
  const stepCountField = document.getElementById("rp-new-segment-step-count");
  if (!addBtn || !form) return;

  addBtn.addEventListener("click", () => {
    const wasHidden = form.hidden;
    if (wasHidden) resetAddSegmentForm();
    form.hidden = !wasHidden;
  });

  cancelBtn?.addEventListener("click", () => {
    form.hidden = true;
  });

  progressionField?.addEventListener("change", (e) => {
    if (stepCountField) stepCountField.hidden = e.target.value !== "stepped";
  });

  submitBtn?.addEventListener("click", async () => {
    if (!pendingSegmentsTeamCode || !pendingSegmentsPhaseRow || !pendingTeamsProjectRow) return;

    const typeField = document.getElementById("rp-new-segment-type");
    const startPctField = document.getElementById("rp-new-segment-start-pct");
    const endPctField = document.getElementById("rp-new-segment-end-pct");
    const durationField = document.getElementById("rp-new-segment-duration");

    const segmentType = typeField?.value || "";
    const startPct = startPctField?.value || "";
    const endPct = endPctField?.value || "";
    const duration = durationField?.value || "";

    if (!segmentType || startPct === "" || endPct === "" || duration === "") {
      toast({
        type: "warning",
        title: "Missing details",
        message: "Please fill in segment type, start/end %, and duration.",
      });
      return;
    }

    const payload = {
      segment_type: segmentType,
      start_percentage: startPct,
      end_percentage: endPct,
      progression: progressionField?.value || "linear",
      duration: parseInt(duration, 10),
      step_count:
        stepCountField && !stepCountField.hidden && stepCountField.value !== ""
          ? parseInt(stepCountField.value, 10)
          : null,
    };

    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Adding…");

    try {
      const { href, method } = API_URLS.resourcePlans.versionProjectTeamPhaseSegmentCreate(
        planCode,
        versionNumber,
        pendingTeamsProjectRow.code,
        pendingSegmentsTeamCode,
        pendingSegmentsPhaseRow.code,
      );
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      form.hidden = true;
      document.getElementById("rp-phase-segments-table")?.refresh();
      toast({
        type: "success",
        title: "Segment added",
        message: "The segment has been added to this phase.",
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to add segment. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initSegmentRowActions() {
  const table = document.getElementById("rp-phase-segments-table");
  const deleteModal = document.getElementById("rp-resource-plan-phase-segment-delete-modal");
  if (!table) return;

  table.addEventListener("rp:segment:delete", (e) => {
    if (!deleteModal) return;
    const row = e.detail.row;
    pendingDeleteSegmentRow = { code: row.code, label: `Segment ${row.segment_order}` };
    deleteModal.setAttribute("title", `Delete "${pendingDeleteSegmentRow.label}"?`);
    deleteModal.setAttribute("body", "This will permanently remove this segment from the phase.");
    deleteModal.setAttribute("confirm-value", pendingDeleteSegmentRow.label);
    deleteModal.show();
  });

  deleteModal?.addEventListener("rp:delete", async () => {
    if (
      !pendingDeleteSegmentRow ||
      !pendingSegmentsTeamCode ||
      !pendingSegmentsPhaseRow ||
      !pendingTeamsProjectRow
    )
      return;
    const deleteConfirmBtn = deleteModal.querySelector("[data-delete-modal]");
    deleteConfirmBtn?.setAttribute("disabled", "");
    try {
      const { href, method } = API_URLS.resourcePlans.versionProjectTeamPhaseSegmentDelete(
        planCode,
        versionNumber,
        pendingTeamsProjectRow.code,
        pendingSegmentsTeamCode,
        pendingSegmentsPhaseRow.code,
        pendingDeleteSegmentRow.code,
      );
      await apiFetch(href, { method });
      deleteModal.hide();
      toast({
        type: "success",
        title: "Segment removed",
        message: `"${pendingDeleteSegmentRow.label}" has been removed.`,
      });
      pendingDeleteSegmentRow = null;
      table.refresh?.();
    } catch (err) {
      deleteConfirmBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to remove segment. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initSuggestAndPreviewRampButtons() {
  const suggestBtn = document.getElementById("rp-segments-suggest-btn");
  const previewBtn = document.getElementById("rp-segments-preview-ramp-btn");

  suggestBtn?.addEventListener("click", () => {
    toast({
      type: "info",
      title: "Coming soon",
      message: "Suggesting segments isn't available yet.",
    });
  });

  previewBtn?.addEventListener("click", () => {
    toast({
      type: "info",
      title: "Coming soon",
      message: "Previewing the ramp graph isn't available yet.",
    });
  });
}

// ── Dependencies (per phase, opened from the Phases table) ──────────────────

let pendingDependenciesTeamCode = null;
let pendingDependenciesPhaseRow = null;
let pendingDependencyRow = null; // null = create mode, set = edit mode
let pendingDeleteDependencyRow = null; // { code, label }

const DEPENDENCY_TYPE_LABELS = {
  start_to_start: "Start to Start",
  finish_to_start: "Finish to Start",
  finish_to_finish: "Finish to Finish",
  start_to_finish: "Start to Finish",
};

window.renderDependencyRow = function renderDependencyRow(row) {
  return `
    <td>${esc(row.predecessor_phase_name)}</td>
    <td>${esc(row.predecessor_project_name)}</td>
    <td>${esc(row.predecessor_team_name)}</td>
    <td>${esc(row.dependency_type_display || DEPENDENCY_TYPE_LABELS[row.dependency_type] || row.dependency_type)}</td>
    <td class="rp-td-num">${esc(String(row.lag_sprints))}</td>
  `;
};

function resetDependencyForm() {
  const predecessorField = document.getElementById("rp-dependency-predecessor");
  const typeField = document.getElementById("rp-dependency-type");
  const lagField = document.getElementById("rp-dependency-lag-sprints");

  if (predecessorField) predecessorField.value = "";
  if (typeField) typeField.value = "";
  if (lagField) lagField.value = "0";
}

async function fillDependencyForm(row) {
  const predecessorField = document.getElementById("rp-dependency-predecessor");
  const typeField = document.getElementById("rp-dependency-type");
  const lagField = document.getElementById("rp-dependency-lag-sprints");

  if (typeField) typeField.value = row.dependency_type;
  if (lagField) lagField.value = String(row.lag_sprints);
  if (predecessorField) predecessorField.value = row.predecessor_phase_code;
}

async function openDependencyForm(row = null) {
  const form = document.getElementById("rp-dependency-form");
  const submitBtn = document.getElementById("rp-dependency-form-submit-btn");
  const predecessorField = document.getElementById("rp-dependency-predecessor");
  if (!form || !pendingDependenciesTeamCode || !pendingDependenciesPhaseRow) return;

  pendingDependencyRow = row;
  resetDependencyForm();
  form.hidden = false;
  submitBtn?.setAttribute("label", row ? "Save" : "Add");

  if (predecessorField?.setScope) {
    await predecessorField.setScope({
      planCode,
      version: versionNumber,
      projectVersionCode: pendingTeamsProjectRow.code,
      teamVersionCode: pendingDependenciesTeamCode,
      phaseVersionCode: pendingDependenciesPhaseRow.code,
    });
  }

  if (row) await fillDependencyForm(row);
}

function openDependenciesDrawer(teamCode, phaseRow) {
  const drawer = document.getElementById("rp-resource-plan-phase-dependencies-drawer");
  const table = document.getElementById("rp-phase-dependencies-table");
  if (!drawer || !table || !pendingTeamsProjectRow) return;

  pendingDependenciesTeamCode = teamCode;
  pendingDependenciesPhaseRow = phaseRow;

  const form = document.getElementById("rp-dependency-form");
  if (form) form.hidden = true;
  resetDependencyForm();

  const { href } = API_URLS.resourcePlans.versionProjectTeamPhaseDependenciesList(
    planCode,
    versionNumber,
    pendingTeamsProjectRow.code,
    teamCode,
    phaseRow.code,
  );
  table.setAttribute("url", href);

  drawer.setTitle?.(`Dependencies — ${phaseRow.name}`);
  drawer.show();
  table.refresh?.();
}

function initDependencyForm() {
  const addBtn = document.getElementById("rp-dependencies-add-btn");
  const form = document.getElementById("rp-dependency-form");
  const cancelBtn = document.getElementById("rp-dependency-form-cancel-btn");
  const submitBtn = document.getElementById("rp-dependency-form-submit-btn");
  if (!addBtn || !form) return;

  addBtn.addEventListener("click", () => {
    if (form.hidden) {
      openDependencyForm(null);
    } else {
      form.hidden = true;
    }
  });

  cancelBtn?.addEventListener("click", () => {
    form.hidden = true;
  });

  submitBtn?.addEventListener("click", async () => {
    if (!pendingDependenciesTeamCode || !pendingDependenciesPhaseRow || !pendingTeamsProjectRow)
      return;

    const predecessorField = document.getElementById("rp-dependency-predecessor");
    const typeField = document.getElementById("rp-dependency-type");
    const lagField = document.getElementById("rp-dependency-lag-sprints");

    const predecessorCode = predecessorField?.value || "";
    const dependencyType = typeField?.value || "";
    const lagSprints = parseInt(lagField?.value || "0", 10) || 0;

    if (!predecessorCode || !dependencyType) {
      toast({
        type: "warning",
        title: "Missing details",
        message: "Please select a predecessor phase and a dependency type.",
      });
      return;
    }

    const payload = {
      predecessor_phase_code: predecessorCode,
      dependency_type: dependencyType,
      lag_sprints: lagSprints,
    };

    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, pendingDependencyRow ? "Saving…" : "Adding…");

    try {
      if (pendingDependencyRow) {
        const { href, method } = API_URLS.resourcePlans.versionProjectTeamPhaseDependencyUpdate(
          planCode,
          versionNumber,
          pendingTeamsProjectRow.code,
          pendingDependenciesTeamCode,
          pendingDependenciesPhaseRow.code,
          pendingDependencyRow.code,
        );
        await apiFetch(href, { method, body: JSON.stringify(payload) });
      } else {
        const { href, method } = API_URLS.resourcePlans.versionProjectTeamPhaseDependencyCreate(
          planCode,
          versionNumber,
          pendingTeamsProjectRow.code,
          pendingDependenciesTeamCode,
          pendingDependenciesPhaseRow.code,
        );
        await apiFetch(href, { method, body: JSON.stringify(payload) });
      }
      restoreButton(submitBtn, snap, { label: pendingDependencyRow ? "Save" : "Add" });
      form.hidden = true;
      document.getElementById("rp-phase-dependencies-table")?.refresh();
      toast({
        type: "success",
        title: pendingDependencyRow ? "Dependency updated" : "Dependency added",
        message: pendingDependencyRow
          ? "The dependency has been updated."
          : "The dependency has been added to this phase.",
      });
      pendingDependencyRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap, { label: pendingDependencyRow ? "Save" : "Add" });
      const msg = err?.data?.error?.message ?? "Failed to save dependency. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initDependencyRowActions() {
  const table = document.getElementById("rp-phase-dependencies-table");
  const deleteModal = document.getElementById("rp-resource-plan-phase-dependency-delete-modal");
  if (!table) return;

  table.addEventListener("rp:dependency:edit", (e) => {
    openDependencyForm(e.detail.row);
  });

  table.addEventListener("rp:dependency:delete", (e) => {
    if (!deleteModal) return;
    const row = e.detail.row;
    pendingDeleteDependencyRow = { code: row.code, label: row.predecessor_phase_name };
    deleteModal.setAttribute(
      "title",
      `Delete dependency on "${pendingDeleteDependencyRow.label}"?`,
    );
    deleteModal.setAttribute(
      "body",
      "This will permanently remove this dependency from the phase.",
    );
    deleteModal.setAttribute("confirm-value", pendingDeleteDependencyRow.label);
    deleteModal.show();
  });

  deleteModal?.addEventListener("rp:delete", async () => {
    if (
      !pendingDeleteDependencyRow ||
      !pendingDependenciesTeamCode ||
      !pendingDependenciesPhaseRow ||
      !pendingTeamsProjectRow
    )
      return;
    const deleteConfirmBtn = deleteModal.querySelector("[data-delete-modal]");
    deleteConfirmBtn?.setAttribute("disabled", "");
    try {
      const { href, method } = API_URLS.resourcePlans.versionProjectTeamPhaseDependencyDelete(
        planCode,
        versionNumber,
        pendingTeamsProjectRow.code,
        pendingDependenciesTeamCode,
        pendingDependenciesPhaseRow.code,
        pendingDeleteDependencyRow.code,
      );
      await apiFetch(href, { method });
      deleteModal.hide();
      toast({
        type: "success",
        title: "Dependency removed",
        message: `The dependency on "${pendingDeleteDependencyRow.label}" has been removed.`,
      });
      pendingDeleteDependencyRow = null;
      table.refresh?.();
    } catch (err) {
      deleteConfirmBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to remove dependency. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ── Pauses (per phase, opened from the Phases table) ────────────────────────

let pendingPausesTeamCode = null;
let pendingPausesPhaseRow = null;
let pendingPauseRow = null; // null = create mode, set = edit mode
let pendingDeletePauseRow = null; // { code, label }

const PAUSE_INPUT_MODE_LABELS = { sprint: "Sprint", count: "Count" };

window.renderPauseRow = function renderPauseRow(row) {
  return `
    <td>${esc(row.pause_from_name)}</td>
    <td>${esc(row.input_mode_display || PAUSE_INPUT_MODE_LABELS[row.input_mode] || row.input_mode)}</td>
    <td>${esc(row.resume_sprint_name)}</td>
    <td>${esc(row.notes || "—")}</td>
  `;
};

function showPauseModeFields(inputMode) {
  const untilField = document.getElementById("rp-pause-until-sprint");
  const countField = document.getElementById("rp-pause-sprint-count");
  if (untilField) untilField.hidden = inputMode !== "sprint";
  if (countField) countField.hidden = inputMode !== "count";
}

function resetPauseForm() {
  const fromField = document.getElementById("rp-pause-from");
  const modeField = document.getElementById("rp-pause-input-mode");
  const untilField = document.getElementById("rp-pause-until-sprint");
  const countField = document.getElementById("rp-pause-sprint-count");
  const notesField = document.getElementById("rp-pause-notes");

  if (fromField) fromField.value = "";
  if (modeField) modeField.value = "";
  if (untilField) untilField.value = "";
  if (countField) countField.value = "";
  if (notesField) notesField.value = "";
  showPauseModeFields("");
}

function fillPauseForm(row) {
  const fromField = document.getElementById("rp-pause-from");
  const modeField = document.getElementById("rp-pause-input-mode");
  const untilField = document.getElementById("rp-pause-until-sprint");
  const countField = document.getElementById("rp-pause-sprint-count");
  const notesField = document.getElementById("rp-pause-notes");

  if (fromField) fromField.value = row.pause_from_code;
  if (modeField) modeField.value = row.input_mode;
  showPauseModeFields(row.input_mode);
  if (untilField) untilField.value = row.pause_until_sprint_code || "";
  if (countField)
    countField.value = row.pause_sprint_count != null ? String(row.pause_sprint_count) : "";
  if (notesField) notesField.value = row.notes || "";
}

function openPauseForm(row = null) {
  const form = document.getElementById("rp-pause-form");
  const submitBtn = document.getElementById("rp-pause-form-submit-btn");
  const fromField = document.getElementById("rp-pause-from");
  const untilField = document.getElementById("rp-pause-until-sprint");
  if (!form) return;

  pendingPauseRow = row;
  resetPauseForm();
  form.hidden = false;
  submitBtn?.setAttribute("label", row ? "Save" : "Add");

  if (financialYearCode) {
    if (fromField) fromField.setAttribute("fy-code", financialYearCode);
    if (untilField) untilField.setAttribute("fy-code", financialYearCode);
  }

  if (row) fillPauseForm(row);
}

function openPausesDrawer(teamCode, phaseRow) {
  const drawer = document.getElementById("rp-resource-plan-phase-pauses-drawer");
  const table = document.getElementById("rp-phase-pauses-table");
  if (!drawer || !table || !pendingTeamsProjectRow) return;

  pendingPausesTeamCode = teamCode;
  pendingPausesPhaseRow = phaseRow;

  const form = document.getElementById("rp-pause-form");
  if (form) form.hidden = true;
  resetPauseForm();

  const { href } = API_URLS.resourcePlans.versionProjectTeamPhasePausesList(
    planCode,
    versionNumber,
    pendingTeamsProjectRow.code,
    teamCode,
    phaseRow.code,
  );
  table.setAttribute("url", href);

  drawer.setTitle?.(`Pauses — ${phaseRow.name}`);
  drawer.show();
  table.refresh?.();
}

function initPauseForm() {
  const addBtn = document.getElementById("rp-pauses-add-btn");
  const form = document.getElementById("rp-pause-form");
  const cancelBtn = document.getElementById("rp-pause-form-cancel-btn");
  const submitBtn = document.getElementById("rp-pause-form-submit-btn");
  const modeField = document.getElementById("rp-pause-input-mode");
  if (!addBtn || !form) return;

  addBtn.addEventListener("click", () => {
    if (form.hidden) {
      openPauseForm(null);
    } else {
      form.hidden = true;
    }
  });

  cancelBtn?.addEventListener("click", () => {
    form.hidden = true;
  });

  modeField?.addEventListener("change", (e) => {
    showPauseModeFields(e.target.value);
  });

  submitBtn?.addEventListener("click", async () => {
    if (!pendingPausesTeamCode || !pendingPausesPhaseRow || !pendingTeamsProjectRow) return;

    const fromField = document.getElementById("rp-pause-from");
    const untilField = document.getElementById("rp-pause-until-sprint");
    const countField = document.getElementById("rp-pause-sprint-count");
    const notesField = document.getElementById("rp-pause-notes");

    const pauseFromCode = fromField?.value || "";
    const inputMode = modeField?.value || "";
    const pauseUntilCode = untilField?.value || "";
    const pauseCount = countField?.value || "";

    if (!pauseFromCode || !inputMode) {
      toast({
        type: "warning",
        title: "Missing details",
        message: "Please select a pause-from sprint and an input mode.",
      });
      return;
    }
    if (inputMode === "sprint" && !pauseUntilCode) {
      toast({
        type: "warning",
        title: "Missing details",
        message: "Please select a pause-until sprint.",
      });
      return;
    }
    if (inputMode === "count" && pauseCount === "") {
      toast({
        type: "warning",
        title: "Missing details",
        message: "Please enter a pause sprint count.",
      });
      return;
    }

    const payload = {
      pause_from_code: pauseFromCode,
      input_mode: inputMode,
      pause_until_sprint_code: inputMode === "sprint" ? pauseUntilCode : null,
      pause_sprint_count: inputMode === "count" ? parseInt(pauseCount, 10) : null,
      notes: notesField?.value || "",
    };

    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, pendingPauseRow ? "Saving…" : "Adding…");

    try {
      if (pendingPauseRow) {
        const { href, method } = API_URLS.resourcePlans.versionProjectTeamPhasePauseUpdate(
          planCode,
          versionNumber,
          pendingTeamsProjectRow.code,
          pendingPausesTeamCode,
          pendingPausesPhaseRow.code,
          pendingPauseRow.code,
        );
        await apiFetch(href, { method, body: JSON.stringify(payload) });
      } else {
        const { href, method } = API_URLS.resourcePlans.versionProjectTeamPhasePauseCreate(
          planCode,
          versionNumber,
          pendingTeamsProjectRow.code,
          pendingPausesTeamCode,
          pendingPausesPhaseRow.code,
        );
        await apiFetch(href, { method, body: JSON.stringify(payload) });
      }
      restoreButton(submitBtn, snap, { label: pendingPauseRow ? "Save" : "Add" });
      form.hidden = true;
      document.getElementById("rp-phase-pauses-table")?.refresh();
      toast({
        type: "success",
        title: pendingPauseRow ? "Pause updated" : "Pause added",
        message: pendingPauseRow
          ? "The pause has been updated."
          : "The pause has been added to this phase.",
      });
      pendingPauseRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap, { label: pendingPauseRow ? "Save" : "Add" });
      const msg = err?.data?.error?.message ?? "Failed to save pause. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initPauseRowActions() {
  const table = document.getElementById("rp-phase-pauses-table");
  const deleteModal = document.getElementById("rp-resource-plan-phase-pause-delete-modal");
  if (!table) return;

  table.addEventListener("rp:pause:edit", (e) => {
    openPauseForm(e.detail.row);
  });

  table.addEventListener("rp:pause:delete", (e) => {
    if (!deleteModal) return;
    const row = e.detail.row;
    pendingDeletePauseRow = { code: row.code, label: `Pause from ${row.pause_from_name}` };
    deleteModal.setAttribute("title", `Delete "${pendingDeletePauseRow.label}"?`);
    deleteModal.setAttribute("body", "This will permanently remove this pause from the phase.");
    deleteModal.setAttribute("confirm-value", pendingDeletePauseRow.label);
    deleteModal.show();
  });

  deleteModal?.addEventListener("rp:delete", async () => {
    if (
      !pendingDeletePauseRow ||
      !pendingPausesTeamCode ||
      !pendingPausesPhaseRow ||
      !pendingTeamsProjectRow
    )
      return;
    const deleteConfirmBtn = deleteModal.querySelector("[data-delete-modal]");
    deleteConfirmBtn?.setAttribute("disabled", "");
    try {
      const { href, method } = API_URLS.resourcePlans.versionProjectTeamPhasePauseDelete(
        planCode,
        versionNumber,
        pendingTeamsProjectRow.code,
        pendingPausesTeamCode,
        pendingPausesPhaseRow.code,
        pendingDeletePauseRow.code,
      );
      await apiFetch(href, { method });
      deleteModal.hide();
      toast({
        type: "success",
        title: "Pause removed",
        message: `"${pendingDeletePauseRow.label}" has been removed.`,
      });
      pendingDeletePauseRow = null;
      table.refresh?.();
    } catch (err) {
      deleteConfirmBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to remove pause. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ── Assignments (per phase, opened from the Phases table) ───────────────────

let pendingAssignmentsTeamCode = null;
let pendingAssignmentsPhaseRow = null;
let pendingAssignmentRow = null; // null = create mode, set = edit mode
let pendingDeleteAssignmentRow = null; // { code, label }

const ASSIGNMENT_TYPE_LABELS = {
  engineer: "Engineer",
  architect: "Architect",
  adhoc: "Adhoc",
  interim: "Interim",
};

function yesNoBadge(value) {
  const cls = value ? "rp-badge rp-badge-soft rp-badge-success" : "rp-badge rp-badge-soft";
  return `<span class="${cls}">${value ? "Yes" : "No"}</span>`;
}

window.renderAssignmentRow = function renderAssignmentRow(row) {
  return `
    <td>${esc(row.member_name)}</td>
    <td>${esc(row.assignment_type_display || ASSIGNMENT_TYPE_LABELS[row.assignment_type] || row.assignment_type)}</td>
    <td class="rp-td-num">${esc(row.split_value != null ? String(row.split_value) : "—")}</td>
    <td>${yesNoBadge(row.includes_in_budget)}</td>
    <td>${esc(row.notes || "—")}</td>
  `;
};

function showAssignmentTypeFields(assignmentType, splitMode) {
  const replacesField = document.getElementById("rp-assignment-replaces-member");
  const interimCountField = document.getElementById("rp-assignment-interim-sprint-count");
  const splitValueField = document.getElementById("rp-assignment-split-value");

  const isInterim = assignmentType === "interim";
  if (replacesField) replacesField.hidden = !isInterim;
  if (interimCountField) interimCountField.hidden = !isInterim;
  if (splitValueField) splitValueField.hidden = !["percent", "days"].includes(splitMode);
}

function resetAssignmentForm() {
  const memberField = document.getElementById("rp-assignment-member");
  const typeField = document.getElementById("rp-assignment-type");
  const replacesField = document.getElementById("rp-assignment-replaces-member");
  const interimCountField = document.getElementById("rp-assignment-interim-sprint-count");
  const splitValueField = document.getElementById("rp-assignment-split-value");
  const notesField = document.getElementById("rp-assignment-notes");

  if (memberField) memberField.value = "";
  if (typeField) typeField.value = "";
  if (replacesField) replacesField.value = "";
  if (interimCountField) interimCountField.value = "";
  if (splitValueField) splitValueField.value = "";
  if (notesField) notesField.value = "";
  showAssignmentTypeFields("", pendingAssignmentsPhaseRow?.split_mode);
}

function fillAssignmentForm(row) {
  const memberField = document.getElementById("rp-assignment-member");
  const typeField = document.getElementById("rp-assignment-type");
  const replacesField = document.getElementById("rp-assignment-replaces-member");
  const interimCountField = document.getElementById("rp-assignment-interim-sprint-count");
  const splitValueField = document.getElementById("rp-assignment-split-value");
  const notesField = document.getElementById("rp-assignment-notes");

  if (memberField) memberField.value = row.member_code;
  if (typeField) typeField.value = row.assignment_type;
  showAssignmentTypeFields(row.assignment_type, pendingAssignmentsPhaseRow?.split_mode);
  if (replacesField) replacesField.value = row.replaces_member_code || "";
  if (interimCountField)
    interimCountField.value =
      row.interim_sprint_count != null ? String(row.interim_sprint_count) : "";
  if (splitValueField)
    splitValueField.value = row.split_value != null ? String(row.split_value) : "";
  if (notesField) notesField.value = row.notes || "";
}

function openAssignmentForm(row = null) {
  const form = document.getElementById("rp-assignment-form");
  const submitBtn = document.getElementById("rp-assignment-form-submit-btn");
  if (!form) return;

  pendingAssignmentRow = row;
  resetAssignmentForm();
  form.hidden = false;
  submitBtn?.setAttribute("label", row ? "Save" : "Add");

  if (row) fillAssignmentForm(row);
}

function openAssignmentsDrawer(teamCode, phaseRow) {
  const drawer = document.getElementById("rp-resource-plan-assignments-drawer");
  const table = document.getElementById("rp-phase-assignments-table");
  if (!drawer || !table || !pendingTeamsProjectRow) return;

  pendingAssignmentsTeamCode = teamCode;
  pendingAssignmentsPhaseRow = phaseRow;

  const form = document.getElementById("rp-assignment-form");
  if (form) form.hidden = true;
  resetAssignmentForm();

  const { href } = API_URLS.resourcePlans.versionProjectTeamPhaseAssignmentsList(
    planCode,
    versionNumber,
    pendingTeamsProjectRow.code,
    teamCode,
    phaseRow.code,
  );
  table.setAttribute("url", href);

  drawer.setTitle?.(`Assignments — ${phaseRow.name}`);
  drawer.show();
  table.refresh?.();
}

function initAssignmentForm() {
  const addBtn = document.getElementById("rp-assignments-add-btn");
  const form = document.getElementById("rp-assignment-form");
  const cancelBtn = document.getElementById("rp-assignment-form-cancel-btn");
  const submitBtn = document.getElementById("rp-assignment-form-submit-btn");
  const typeField = document.getElementById("rp-assignment-type");
  if (!addBtn || !form) return;

  addBtn.addEventListener("click", () => {
    if (form.hidden) {
      openAssignmentForm(null);
    } else {
      form.hidden = true;
    }
  });

  cancelBtn?.addEventListener("click", () => {
    form.hidden = true;
  });

  typeField?.addEventListener("change", (e) => {
    showAssignmentTypeFields(e.target.value, pendingAssignmentsPhaseRow?.split_mode);
  });

  submitBtn?.addEventListener("click", async () => {
    if (!pendingAssignmentsTeamCode || !pendingAssignmentsPhaseRow || !pendingTeamsProjectRow)
      return;

    const memberField = document.getElementById("rp-assignment-member");
    const replacesField = document.getElementById("rp-assignment-replaces-member");
    const interimCountField = document.getElementById("rp-assignment-interim-sprint-count");
    const splitValueField = document.getElementById("rp-assignment-split-value");
    const notesField = document.getElementById("rp-assignment-notes");

    const memberCode = memberField?.value || "";
    const assignmentType = typeField?.value || "";
    const replacesCode = replacesField?.value || "";
    const interimCount = interimCountField?.value || "";

    if (!memberCode || !assignmentType) {
      toast({
        type: "warning",
        title: "Missing details",
        message: "Please select a member and an assignment type.",
      });
      return;
    }
    if (assignmentType === "interim" && (!replacesCode || interimCount === "")) {
      toast({
        type: "warning",
        title: "Missing details",
        message: "Interim assignments require a member to replace and a sprint count.",
      });
      return;
    }

    const payload = {
      member_code: memberCode,
      auto_assign: pendingAssignmentRow ? pendingAssignmentRow.auto_assign : false,
      assignment_type: assignmentType,
      replaces_member_code: assignmentType === "interim" ? replacesCode : null,
      interim_sprint_count: assignmentType === "interim" ? parseInt(interimCount, 10) : null,
      split_value:
        splitValueField && !splitValueField.hidden && splitValueField.value !== ""
          ? splitValueField.value
          : null,
      notes: notesField?.value || "",
    };

    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, pendingAssignmentRow ? "Saving…" : "Adding…");

    try {
      if (pendingAssignmentRow) {
        const { href, method } = API_URLS.resourcePlans.versionProjectTeamPhaseAssignmentUpdate(
          planCode,
          versionNumber,
          pendingTeamsProjectRow.code,
          pendingAssignmentsTeamCode,
          pendingAssignmentsPhaseRow.code,
          pendingAssignmentRow.code,
        );
        await apiFetch(href, { method, body: JSON.stringify(payload) });
      } else {
        const { href, method } = API_URLS.resourcePlans.versionProjectTeamPhaseAssignmentCreate(
          planCode,
          versionNumber,
          pendingTeamsProjectRow.code,
          pendingAssignmentsTeamCode,
          pendingAssignmentsPhaseRow.code,
        );
        await apiFetch(href, { method, body: JSON.stringify(payload) });
      }
      restoreButton(submitBtn, snap, { label: pendingAssignmentRow ? "Save" : "Add" });
      form.hidden = true;
      document.getElementById("rp-phase-assignments-table")?.refresh();
      toast({
        type: "success",
        title: pendingAssignmentRow ? "Assignment updated" : "Assignment added",
        message: pendingAssignmentRow
          ? "The assignment has been updated."
          : "The assignment has been added to this phase.",
      });
      pendingAssignmentRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap, { label: pendingAssignmentRow ? "Save" : "Add" });
      const msg = err?.data?.error?.message ?? "Failed to save assignment. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initAssignmentRowActions() {
  const table = document.getElementById("rp-phase-assignments-table");
  const deleteModal = document.getElementById("rp-resource-plan-assignment-delete-modal");
  if (!table) return;

  table.addEventListener("rp:assignment:edit", (e) => {
    openAssignmentForm(e.detail.row);
  });

  table.addEventListener("rp:assignment:delete", (e) => {
    if (!deleteModal) return;
    const row = e.detail.row;
    pendingDeleteAssignmentRow = { code: row.code, label: row.member_name };
    deleteModal.setAttribute(
      "title",
      `Delete assignment for "${pendingDeleteAssignmentRow.label}"?`,
    );
    deleteModal.setAttribute(
      "body",
      "This will permanently remove this assignment from the phase.",
    );
    deleteModal.setAttribute("confirm-value", pendingDeleteAssignmentRow.label);
    deleteModal.show();
  });

  deleteModal?.addEventListener("rp:delete", async () => {
    if (
      !pendingDeleteAssignmentRow ||
      !pendingAssignmentsTeamCode ||
      !pendingAssignmentsPhaseRow ||
      !pendingTeamsProjectRow
    )
      return;
    const deleteConfirmBtn = deleteModal.querySelector("[data-delete-modal]");
    deleteConfirmBtn?.setAttribute("disabled", "");
    try {
      const { href, method } = API_URLS.resourcePlans.versionProjectTeamPhaseAssignmentDelete(
        planCode,
        versionNumber,
        pendingTeamsProjectRow.code,
        pendingAssignmentsTeamCode,
        pendingAssignmentsPhaseRow.code,
        pendingDeleteAssignmentRow.code,
      );
      await apiFetch(href, { method });
      deleteModal.hide();
      toast({
        type: "success",
        title: "Assignment removed",
        message: `The assignment for "${pendingDeleteAssignmentRow.label}" has been removed.`,
      });
      pendingDeleteAssignmentRow = null;
      table.refresh?.();
    } catch (err) {
      deleteConfirmBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to remove assignment. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

window.renderBudgetReleaseRow = function renderBudgetReleaseRow(row) {
  const releaseLabel = row.entry_type === "sprint" ? row.sprint_name : row.month;
  return `
    <td>${esc(releaseLabel || "—")}</td>
    <td class="rp-td-num">${esc(formatCurrency(row.amount))}</td>
    <td>${esc(row.notes || "—")}</td>
  `;
};

function showBudgetReleaseTypeFields(entryType) {
  const sprintField = document.getElementById("rp-budget-release-sprint");
  const monthField = document.getElementById("rp-budget-release-month");
  if (sprintField) sprintField.hidden = entryType !== "sprint";
  if (monthField) monthField.hidden = entryType !== "month";
}

function updateReleaseTypeLockUI(lockedType) {
  const typeField = document.getElementById("rp-budget-release-type");
  const lockedHint = document.getElementById("rp-budget-release-type-locked-hint");
  if (!typeField) return;

  if (lockedType) {
    typeField.value = lockedType;
    typeField.setAttribute("disabled", "");
    if (lockedHint) lockedHint.hidden = false;
  } else {
    typeField.removeAttribute("disabled");
    if (lockedHint) lockedHint.hidden = true;
  }
  showBudgetReleaseTypeFields(lockedType || typeField.value || "");
}

function resetBudgetReleaseForm() {
  const sprintField = document.getElementById("rp-budget-release-sprint");
  const monthField = document.getElementById("rp-budget-release-month");
  const amountField = document.getElementById("rp-budget-release-amount");
  const notesField = document.getElementById("rp-budget-release-notes");

  if (sprintField) sprintField.value = "";
  if (monthField) monthField.value = "";
  if (amountField) amountField.value = "";
  if (notesField) notesField.value = "";
  updateReleaseTypeLockUI(pendingBudgetReleaseLockedType);
}

function fillBudgetReleaseForm(row) {
  const typeField = document.getElementById("rp-budget-release-type");
  const sprintField = document.getElementById("rp-budget-release-sprint");
  const monthField = document.getElementById("rp-budget-release-month");
  const amountField = document.getElementById("rp-budget-release-amount");
  const notesField = document.getElementById("rp-budget-release-notes");
  const lockedHint = document.getElementById("rp-budget-release-type-locked-hint");

  if (typeField) {
    typeField.value = row.entry_type;
    typeField.setAttribute("disabled", "");
  }
  if (lockedHint) lockedHint.hidden = false;
  showBudgetReleaseTypeFields(row.entry_type);
  if (sprintField) sprintField.value = row.sprint_code || "";
  if (monthField) monthField.value = row.month || "";
  if (amountField) amountField.value = row.amount != null ? String(row.amount) : "";
  if (notesField) notesField.value = row.notes || "";
}

function openBudgetReleaseForm(row = null) {
  const form = document.getElementById("rp-budget-release-form");
  const submitBtn = document.getElementById("rp-budget-release-form-submit-btn");
  if (!form) return;

  pendingBudgetReleaseRow = row;
  resetBudgetReleaseForm();
  form.hidden = false;
  submitBtn?.setAttribute("label", row ? "Save" : "Add");

  if (row) fillBudgetReleaseForm(row);
}

function openBudgetReleasesDrawer(projectRow) {
  const drawer = document.getElementById("rp-resource-plan-version-project-budget-releases-drawer");
  const table = document.getElementById("rp-project-budget-releases-table");
  if (!drawer || !table) return;

  pendingBudgetReleaseProjectRow = projectRow;
  pendingBudgetReleaseLockedType = null;

  const form = document.getElementById("rp-budget-release-form");
  if (form) form.hidden = true;
  resetBudgetReleaseForm();

  const { href } = API_URLS.resourcePlans.versionProjectBudgetReleasesList(
    planCode,
    versionNumber,
    projectRow.code,
  );
  table.setAttribute("url", href);

  drawer.setTitle?.(`Budget Release — ${projectRow.project_name}`);
  drawer.show();
  table.refresh?.();
}

function initBudgetReleaseForm() {
  const addBtn = document.getElementById("rp-budget-releases-add-btn");
  const form = document.getElementById("rp-budget-release-form");
  const cancelBtn = document.getElementById("rp-budget-release-form-cancel-btn");
  const submitBtn = document.getElementById("rp-budget-release-form-submit-btn");
  const typeField = document.getElementById("rp-budget-release-type");
  if (!addBtn || !form) return;

  addBtn.addEventListener("click", () => {
    if (form.hidden) {
      openBudgetReleaseForm(null);
    } else {
      form.hidden = true;
    }
  });

  cancelBtn?.addEventListener("click", () => {
    form.hidden = true;
  });

  typeField?.addEventListener("change", (e) => {
    showBudgetReleaseTypeFields(e.target.value);
  });

  submitBtn?.addEventListener("click", async () => {
    if (!pendingBudgetReleaseProjectRow) return;

    const sprintField = document.getElementById("rp-budget-release-sprint");
    const monthField = document.getElementById("rp-budget-release-month");
    const amountField = document.getElementById("rp-budget-release-amount");
    const notesField = document.getElementById("rp-budget-release-notes");

    const entryType = typeField?.value || "";
    const sprintCode = sprintField?.value || "";
    const month = monthField?.value || "";
    const amount = amountField?.value || "";

    if (!entryType) {
      toast({
        type: "warning",
        title: "Missing details",
        message: "Please select a release type.",
      });
      return;
    }
    if (entryType === "sprint" && !sprintCode) {
      toast({ type: "warning", title: "Missing details", message: "Please select a sprint." });
      return;
    }
    if (entryType === "month") {
      if (!isRequired(month)) {
        toast({ type: "warning", title: "Missing details", message: "Please enter a month." });
        return;
      }
      if (!isValidMonth(month)) {
        toast({
          type: "warning",
          title: "Invalid month",
          message: "Month must be in YYYY-MM format.",
        });
        return;
      }
    }
    if (!isRequired(amount)) {
      toast({
        type: "warning",
        title: "Missing details",
        message: "Please enter a release amount.",
      });
      return;
    }

    const payload = {
      sprint_code: entryType === "sprint" ? sprintCode : null,
      month: entryType === "month" ? month : null,
      amount,
      notes: notesField?.value || "",
    };
    if (!pendingBudgetReleaseRow) payload.entry_type = entryType;

    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, pendingBudgetReleaseRow ? "Saving…" : "Adding…");

    try {
      if (pendingBudgetReleaseRow) {
        const { href, method } = API_URLS.resourcePlans.versionProjectBudgetReleasesUpdate(
          planCode,
          versionNumber,
          pendingBudgetReleaseProjectRow.code,
          pendingBudgetReleaseRow.code,
        );
        await apiFetch(href, { method, body: JSON.stringify(payload) });
      } else {
        const { href, method } = API_URLS.resourcePlans.versionProjectBudgetReleasesCreate(
          planCode,
          versionNumber,
          pendingBudgetReleaseProjectRow.code,
        );
        await apiFetch(href, { method, body: JSON.stringify(payload) });
      }
      restoreButton(submitBtn, snap, { label: pendingBudgetReleaseRow ? "Save" : "Add" });
      form.hidden = true;
      document.getElementById("rp-project-budget-releases-table")?.refresh();
      toast({
        type: "success",
        title: pendingBudgetReleaseRow ? "Release updated" : "Release added",
        message: pendingBudgetReleaseRow
          ? "The budget release has been updated."
          : "The budget release has been added to this project.",
      });
      pendingBudgetReleaseRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap, { label: pendingBudgetReleaseRow ? "Save" : "Add" });
      const msg = err?.data?.error?.message ?? "Failed to save budget release. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initBudgetReleaseRowActions() {
  const table = document.getElementById("rp-project-budget-releases-table");
  const deleteModal = document.getElementById(
    "rp-resource-plan-version-project-budget-release-delete-modal",
  );
  if (!table) return;

  table.addEventListener("rp:budget-release:edit", (e) => {
    openBudgetReleaseForm(e.detail.row);
  });

  table.addEventListener("rp:budget-release:delete", (e) => {
    if (!deleteModal) return;
    const row = e.detail.row;
    const label = row.entry_type === "sprint" ? row.sprint_name : row.month;
    pendingDeleteBudgetReleaseRow = { code: row.code, label };
    deleteModal.setAttribute("title", `Delete release "${label}"?`);
    deleteModal.setAttribute(
      "body",
      "This will permanently remove this budget release from the project.",
    );
    deleteModal.setAttribute("confirm-value", label);
    deleteModal.show();
  });

  deleteModal?.addEventListener("rp:delete", async () => {
    if (!pendingDeleteBudgetReleaseRow || !pendingBudgetReleaseProjectRow) return;
    const deleteConfirmBtn = deleteModal.querySelector("[data-delete-modal]");
    deleteConfirmBtn?.setAttribute("disabled", "");
    try {
      const { href, method } = API_URLS.resourcePlans.versionProjectBudgetReleasesDelete(
        planCode,
        versionNumber,
        pendingBudgetReleaseProjectRow.code,
        pendingDeleteBudgetReleaseRow.code,
      );
      await apiFetch(href, { method });
      deleteModal.hide();
      toast({
        type: "success",
        title: "Budget release removed",
        message: `The release "${pendingDeleteBudgetReleaseRow.label}" has been removed.`,
      });
      pendingDeleteBudgetReleaseRow = null;
      table.refresh?.();
    } catch (err) {
      deleteConfirmBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to remove budget release. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initBudgetReleasesDrawer(table) {
  const drawer = document.getElementById("rp-resource-plan-version-project-budget-releases-drawer");
  if (!drawer || !table) return;

  table.addEventListener("rp:resource-plan-version-project:budget-releases", (e) =>
    openBudgetReleasesDrawer(e.detail.row),
  );

  const releasesTable = document.getElementById("rp-project-budget-releases-table");
  releasesTable?.addEventListener("rp:data:loaded", (e) => {
    pendingBudgetReleaseLockedType = (e.detail.rows || [])[0]?.entry_type ?? null;
    updateReleaseTypeLockUI(pendingBudgetReleaseLockedType);
  });

  initBudgetReleaseForm();
  initBudgetReleaseRowActions();
}

function initTeamsDrawer(table) {
  const drawer = document.getElementById("rp-resource-plan-version-teams-drawer");
  if (!drawer || !table) return;

  table.addEventListener("rp:resource-plan-version-project:teams", (e) =>
    openTeamsDrawer(e.detail.row),
  );

  initAddTeamForm();
  initTeamRowActions();
  initPhasesContainerEvents();
  initPhaseDrawer();
  initPhaseDeleteModal();
  initAddSegmentForm();
  initSegmentRowActions();
  initSuggestAndPreviewRampButtons();
  initDependencyForm();
  initDependencyRowActions();
  initPauseForm();
  initPauseRowActions();
  initAssignmentForm();
  initAssignmentRowActions();
}

const ENGINE_JOB_MODE_LABELS = { validate: "Validate", full: "Full" };
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

window.renderEngineJobRow = function renderEngineJobRow(row) {
  const errorCount = Array.isArray(row.error_log) ? row.error_log.length : 0;
  const resultSummary =
    row.status !== "complete" && row.status !== "failed"
      ? "—"
      : errorCount > 0
        ? `${errorCount} error${errorCount === 1 ? "" : "s"}`
        : "Success";
  return `
    <td>${esc(row.mode_display || ENGINE_JOB_MODE_LABELS[row.mode] || row.mode)}</td>
    <td><span class="${engineJobStatusBadgeClass(row.status)}">${esc(row.status_display || ENGINE_JOB_STATUS_LABELS[row.status] || row.status)}</span></td>
    <td>v${esc(String(row.version_number))}</td>
    <td>${esc(formatDateTime(row.initiated_at))}</td>
    <td class="rp-td-num">${row.duration_milliseconds != null ? esc(String(row.duration_milliseconds)) + " ms" : "—"}</td>
    <td>${esc(resultSummary)}</td>
  `;
};

window.renderEngineJobSteps = function renderEngineJobSteps(row) {
  const steps = Array.isArray(row.steps) ? row.steps : [];
  if (!steps.length) {
    return `<strong>Steps</strong><p class="small mb-0" style="color:var(--rp-text-muted)">No step data available.</p>`;
  }
  const items = steps
    .map(
      (s) => `
        <li>
          <span class="fw-medium">${esc(s.name_display || s.name)}</span>
          <span style="color:var(--rp-text-muted)">
            — started ${esc(formatDateTime(s.started_at))},
            ${s.duration_milliseconds != null ? esc(String(s.duration_milliseconds)) + " ms" : "—"}
          </span>
        </li>
      `,
    )
    .join("");
  return `<strong>Steps</strong><ul class="mb-0 ps-3">${items}</ul>`;
};

function initEngineJobsTable() {
  const table = document.getElementById("rp-engine-jobs-table");
  if (!table) return null;

  const baseUrl = API_URLS.resourcePlans.engineJobsList(planCode, versionNumber).href;
  table.setAttribute("url", baseUrl);

  const panel = document.getElementById("rp-engine-jobs-filters");
  if (panel) {
    panel.addEventListener("rp:filter:change", (e) => {
      const qs = e.detail.params.toString();
      table.setAttribute("url", qs ? `${baseUrl}?${qs}` : baseUrl);
    });
  }

  return table;
}

function initEngineJobRowActions(table) {
  if (!table) return;
  const deleteModal = document.getElementById("rp-engine-job-delete-modal");

  table.addEventListener("rp:engine-job:view", (e) => {
    openEngineJobDrawer({ mode: "view", job: e.detail.row });
  });

  table.addEventListener("rp:engine-job:delete", (e) => {
    if (!deleteModal) return;
    const row = e.detail.row;
    pendingDeleteEngineJobRow = row;
    deleteModal.setAttribute(
      "title",
      `Delete this ${ENGINE_JOB_MODE_LABELS[row.mode] || row.mode} job?`,
    );
    deleteModal.setAttribute(
      "body",
      "This will permanently remove this engine job from the history.",
    );
    deleteModal.setAttribute("confirm-value", row.code || "delete");
    deleteModal.show();
  });

  deleteModal?.addEventListener("rp:delete", async () => {
    if (!pendingDeleteEngineJobRow) return;
    const deleteConfirmBtn = deleteModal.querySelector("[data-delete-modal]");
    deleteConfirmBtn?.setAttribute("disabled", "");
    try {
      const { href, method } = API_URLS.resourcePlans.engineJobDelete(
        planCode,
        versionNumber,
        pendingDeleteEngineJobRow.code,
      );
      await apiFetch(href, { method });
      deleteModal.hide();
      toast({
        type: "success",
        title: "Engine job removed",
        message: "The engine job has been removed from the history.",
      });
      pendingDeleteEngineJobRow = null;
      table.refresh?.();
    } catch (err) {
      deleteConfirmBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to remove engine job. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function renderEngineJobProgress(job) {
  const pill = document.getElementById("rp-engine-job-status-pill");
  const statusText = document.getElementById("rp-engine-job-status-text");
  const progressBar = document.getElementById("rp-engine-job-progress-bar");
  const errorSummary = document.getElementById("rp-engine-job-error-summary");
  const errorsContainer = document.getElementById("rp-engine-job-errors");

  if (pill) {
    pill.className = engineJobStatusBadgeClass(job.status);
    pill.textContent = (
      job.status_display ||
      ENGINE_JOB_STATUS_LABELS[job.status] ||
      job.status
    ).toUpperCase();
  }
  if (statusText) {
    statusText.textContent = job.current_step
      ? job.status_display || job.status
      : job.status_display || job.status;
  }
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
            (err) => `
              <div class="rp-card p-2 mt-2">
                <span class="rp-badge rp-badge-soft">${esc(String(err.scope || ""))}</span>
                <div>${esc(String(err.message || ""))}</div>
                ${err.context ? `<div class="small" style="color:var(--rp-text-muted)">${esc(String(err.context))}</div>` : ""}
              </div>
            `,
          )
          .join("")
      : "";
  }
}

function openEngineJobDrawer({ mode, job }) {
  const drawer = document.getElementById("rp-engine-job-drawer");
  const formView = document.getElementById("rp-engine-job-form-view");
  const progressView = document.getElementById("rp-engine-job-progress-view");
  if (!drawer || !formView || !progressView) return;

  enginePolling = false;

  if (mode === "form") {
    const modeField = document.getElementById("rp-engine-job-mode");
    const includeCurrentSprintField = document.getElementById(
      "rp-engine-job-include-current-sprint",
    );
    // radio-group-field only exposes a read-only `value` getter — the
    // checked option must be set on the underlying <input> directly.
    const validateInput = modeField?.querySelector('input[value="validate"]');
    if (validateInput) validateInput.checked = true;
    if (includeCurrentSprintField) includeCurrentSprintField.checked = false;
    formView.hidden = false;
    progressView.hidden = true;
  } else {
    formView.hidden = true;
    progressView.hidden = false;
    if (job) renderEngineJobProgress(job);
  }

  drawer.show();
}

async function pollEngineJob(jobCode) {
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
      if (job) renderEngineJobProgress(job);
      if (job && (job.status === "complete" || job.status === "failed")) {
        enginePolling = false;
        break;
      }
    } catch {
      enginePolling = false;
      break;
    }
    if (enginePolling) await new Promise((resolve) => setTimeout(resolve, 5000));
  }
}

function initEngineJobRunButton() {
  const runEngineBtn = document.getElementById("rp-run-engine-btn");
  runEngineBtn?.addEventListener("click", () => {
    openEngineJobDrawer({ mode: "form" });
  });
}

function initAllocationGridButton() {
  const gridBtn = document.getElementById("rp-allocation-grid-btn");
  gridBtn?.addEventListener("click", () => {
    window.location.href = UI_URLS.resourcePlans.versionGrid(planCode, versionNumber);
  });
}

function initEngineJobForm() {
  const submitBtn = document.getElementById("rp-engine-job-run-btn");
  const formView = document.getElementById("rp-engine-job-form-view");
  const progressView = document.getElementById("rp-engine-job-progress-view");
  if (!submitBtn) return;

  submitBtn.addEventListener("click", async () => {
    const modeField = document.getElementById("rp-engine-job-mode");
    const includeCurrentSprintField = document.getElementById(
      "rp-engine-job-include-current-sprint",
    );
    const mode = modeField?.value || "validate";

    const payload = {
      mode,
      include_current_sprint: includeCurrentSprintField?.checked === true,
    };

    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Running…");

    try {
      const { href, method } = API_URLS.resourcePlans.engineJobsCreate(planCode, versionNumber);
      const res = await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);

      const job = res?.data;
      if (formView) formView.hidden = true;
      if (progressView) progressView.hidden = false;
      if (job) {
        renderEngineJobProgress(job);
        if (job.status !== "complete" && job.status !== "failed") {
          pollEngineJob(job.code);
        }
      }
      document.getElementById("rp-engine-jobs-table")?.refresh();
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

document.addEventListener("DOMContentLoaded", () => {
  const result = initVersionDetailPage();
  if (!result) return;
  result.then(() => {
    const table = initUnmappedProjectsTable();
    initCreateProjectDrawer(table);

    const configuredTable = initConfiguredProjectsTable();
    initConfiguredProjectActionModals(configuredTable);
    initEditProjectDrawer(configuredTable);
    initBudgetReleasesDrawer(configuredTable);
    initTeamsDrawer(configuredTable);

    const engineJobsTable = initEngineJobsTable();
    initEngineJobRowActions(engineJobsTable);
    initEngineJobRunButton();
    initEngineJobForm();
    initAllocationGridButton();
  });
});
