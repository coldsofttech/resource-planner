"use strict";

import { esc } from "../../components/utils.js";
import {
  apiFetch,
  formatCurrency,
  snapshotButton,
  setBusyButton,
  restoreButton,
} from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS } from "../main/urls.js";

// ---------------------------------------------------------------------------
// Shared state
// ---------------------------------------------------------------------------
let pendingRow = null;
let currentFyCode = null;
let currentSprintColumns = []; // [{name, sprint_number}]
const sprintColumnsCache = {}; // fyCode → [{name, sprint_number}]

// ---------------------------------------------------------------------------
// Utility helpers
// ---------------------------------------------------------------------------
function fmtCurrency(value) {
  if (value == null) return "—";
  return formatCurrency(value);
}

function riskRowClass(risk) {
  if (risk === "warning") return "table-warning";
  if (risk === "at_risk") return "table-danger";
  return "";
}

function riskBadge(risk) {
  if (risk === "warning")
    return ` <span class="rp-badge rp-badge-soft rp-badge-warning">Warning</span>`;
  if (risk === "at_risk")
    return ` <span class="rp-badge rp-badge-soft rp-badge-danger">At Risk</span>`;
  return "";
}

function labelBadges(labels) {
  if (!labels || !labels.length) return "—";
  const badges = labels
    .map(
      (lbl) =>
        `<span class="rp-badge ${lbl.is_default ? "rp-badge-success" : "rp-badge-soft rp-badge-info"}">${esc(lbl.label)}</span>`,
    )
    .join("");
  return `<span class="d-flex flex-wrap gap-1">${badges}</span>`;
}

function teamBadges(assignedTeamName, collaborators) {
  const badges = [];
  if (assignedTeamName) {
    badges.push(`<span class="rp-badge rp-badge-success">${esc(assignedTeamName)}</span>`);
  }
  for (const name of collaborators ?? []) {
    badges.push(`<span class="rp-badge rp-badge-soft rp-badge-info">${esc(name)}</span>`);
  }
  if (!badges.length) return "—";
  return `<span class="d-flex flex-wrap gap-1">${badges.join("")}</span>`;
}

// ---------------------------------------------------------------------------
// Row renderer
// ---------------------------------------------------------------------------
window.renderBurnTrackerRow = function renderBurnTrackerRow(row) {
  const programme = row.programme_name ? esc(row.programme_name) : "—";
  const project = esc(row.project_name || "") + riskBadge(row.risk);
  const fy = esc(row.financial_year || "");
  const labels = labelBadges(row.labels);
  const code = row.project_code_value ? `<code>${esc(row.project_code_value)}</code>` : "—";
  const teams = teamBadges(row.assigned_team_name, row.collaborators);
  const estimate = fmtCurrency(row.estimate_cost);
  const estimateConting = fmtCurrency(row.estimate_cost_with_contingency);
  const total = fmtCurrency(row.total_cost_to_date);
  const remaining = fmtCurrency(row.remaining_cost);
  const prevFy = row.ignore_prev_fy_actuals ? "—" : fmtCurrency(row.prev_fy_actuals);

  // One <td> per sprint column in the current FY
  const sprintCells = currentSprintColumns
    .map((sprint) => {
      const cost = row.sprint_costs?.[sprint.name];
      return `<td class="text-end">${fmtCurrency(cost)}</td>`;
    })
    .join("");

  return (
    `<td>${programme}</td>` +
    `<td>${project}</td>` +
    `<td>${fy}</td>` +
    `<td>${labels}</td>` +
    `<td>${code}</td>` +
    `<td>${teams}</td>` +
    `<td class="text-end">${estimate}</td>` +
    `<td class="text-end">${estimateConting}</td>` +
    `<td class="text-end">${total}</td>` +
    `<td class="text-end">${remaining}</td>` +
    `<td class="text-end">${prevFy}</td>` +
    sprintCells
  );
};

// ---------------------------------------------------------------------------
// Risk row highlighting (applied after each table render)
// ---------------------------------------------------------------------------
function applyRiskRowClasses(table) {
  if (!table || !table.rows) return;
  table.querySelectorAll("tr[data-rp-row]").forEach((tr) => {
    const idx = parseInt(tr.getAttribute("data-rp-row"), 10);
    const row = table.rows[idx];
    if (!row) return;
    tr.classList.remove("table-warning", "table-danger");
    const cls = riskRowClass(row.risk);
    if (cls) tr.classList.add(cls);
  });
}

// ---------------------------------------------------------------------------
// Dynamic sprint column management
// ---------------------------------------------------------------------------
function updateSprintColumns(table, sprintColumns) {
  currentSprintColumns = sprintColumns;

  // Snapshot the fixed base columns on first call so FY switches restore cleanly.
  if (!table._baseColumns) {
    table._baseColumns = [...(table._columns ?? [])];
  }

  table._columns = [
    ...table._baseColumns,
    ...sprintColumns.map((sprint) => ({
      label: sprint.name,
      key: "",
      sortable: false,
      numeric: true,
      mono: false,
      width: "",
      hideMobile: true,
    })),
  ];

  // Rebuild only the header row — avoids a full _render() which clears the tbody.
  const theadRow = table.querySelector("thead tr");
  if (theadRow) {
    theadRow.innerHTML = table._buildTheadCells();
  }
}

async function ensureSprintColumns(table, fyCode) {
  if (sprintColumnsCache[fyCode]) {
    updateSprintColumns(table, sprintColumnsCache[fyCode]);
    return;
  }
  const { href } = API_URLS.burnTracker.list();
  try {
    const resp = await apiFetch(`${href}?fy=${encodeURIComponent(fyCode)}&page_size=1`);
    const cols = resp?.data?.sprint_columns ?? [];
    sprintColumnsCache[fyCode] = cols;
    updateSprintColumns(table, cols);
  } catch {
    // Column discovery failed; table still loads without sprint columns
  }
}

// ---------------------------------------------------------------------------
// Config drawer
// ---------------------------------------------------------------------------
function openConfigDrawer(row) {
  const drawer = document.getElementById("rp-burn-tracker-config-drawer");
  if (!drawer) return;
  pendingRow = row;

  const ignoreRisk = drawer.querySelector("#rp-bt-config-ignore-risk");
  const ignorePrev = drawer.querySelector("#rp-bt-config-ignore-prev-fy");
  const notes = drawer.querySelector("#rp-bt-config-notes");

  if (ignoreRisk) ignoreRisk.checked = false;
  if (ignorePrev) ignorePrev.checked = false;
  if (notes) notes.setAttribute("value", "");

  // Load full config from API
  const { href } = API_URLS.projectActuals.config(row.project_code);
  apiFetch(href, { method: "GET" })
    .then((data) => {
      const cfg = data?.data ?? {};
      if (ignoreRisk) ignoreRisk.checked = !!cfg.ignore_risk;
      if (ignorePrev) ignorePrev.checked = !!cfg.ignore_prev_fy_actuals;
      if (notes) notes.setAttribute("value", cfg.notes || "");
    })
    .catch(() => {});

  drawer.show();
}

function initConfigDrawer(table) {
  const drawer = document.getElementById("rp-burn-tracker-config-drawer");
  if (!drawer) return;

  table.addEventListener("rp:burn-tracker:config", (e) => openConfigDrawer(e.detail.row));

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow) return;
    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const ignoreRisk = drawer.querySelector("#rp-bt-config-ignore-risk");
    const ignorePrev = drawer.querySelector("#rp-bt-config-ignore-prev-fy");
    const notesEl = drawer.querySelector("#rp-bt-config-notes");

    const payload = {
      ignore_risk: ignoreRisk?.checked ?? false,
      ignore_prev_fy_actuals: ignorePrev?.checked ?? false,
      notes: notesEl?.value || "",
    };

    const { href, method } = API_URLS.projectActuals.updateConfig(pendingRow.project_code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap, { label: "Saved", suffixIcon: "bi-check-circle-fill" });
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Config saved",
        message: `Actuals config updated for "${pendingRow.project_name}".`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to save config. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ---------------------------------------------------------------------------
// Mark done drawer
// ---------------------------------------------------------------------------
function initDoneDrawer(table) {
  const drawer = document.getElementById("rp-burn-tracker-done-drawer");
  if (!drawer) return;

  let doneRow = null;

  table.addEventListener("rp:burn-tracker:done", (e) => {
    doneRow = e.detail.row;
    const desc = drawer.querySelector("#rp-bt-done-description");
    const sprintField = drawer.querySelector("#rp-bt-done-sprint");
    if (desc) {
      desc.textContent = `Select the sprint in which "${doneRow.project_name}" was completed. The project will be marked as Completed and deactivated.`;
    }
    if (sprintField) {
      sprintField.setAttribute("value", "");
      if (currentFyCode) sprintField.setAttribute("fy-code", currentFyCode);
    }
    drawer.show();
  });

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!doneRow) return;
    const sprintField = drawer.querySelector("#rp-bt-done-sprint");
    const sprintCode = sprintField?.value || "";
    if (!sprintCode) {
      sprintField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
      return;
    }
    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const { href, method } = API_URLS.burnTracker.markDone(doneRow.project_code);
    try {
      await apiFetch(href, { method, body: JSON.stringify({ sprint_code: sprintCode }) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Project marked as done",
        message: `"${doneRow.project_name}" has been marked as Completed.`,
      });
      doneRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to mark project as done. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ---------------------------------------------------------------------------
// Table action dispatch
// ---------------------------------------------------------------------------
function initActions(table) {
  table.addEventListener("rp:burn-tracker:config", (e) => openConfigDrawer(e.detail.row));
}

// ---------------------------------------------------------------------------
// FY picker + filter panel + Show button
// ---------------------------------------------------------------------------
function buildQueryString(fyCode) {
  const search = document.getElementById("rp-burn-tracker-search")?.value || "";
  const programme = document.getElementById("rp-burn-tracker-programme")?.value || "";
  const team = document.getElementById("rp-burn-tracker-team")?.value || "";
  const status = document.getElementById("rp-burn-tracker-status")?.value || "";
  const risk = document.getElementById("rp-burn-tracker-risk")?.value || "";

  const params = new URLSearchParams();
  params.set("fy", fyCode);
  if (search) params.set("search", search);
  if (programme) params.set("programme", programme);
  if (team) params.set("team", team);
  if (status) params.set("status", status);
  if (risk) params.set("risk", risk);
  return params.toString();
}

function loadTable(table, fyCode) {
  const { href } = API_URLS.burnTracker.list();
  const qs = buildQueryString(fyCode);
  table.setAttribute("url", `${href}?${qs}`);
  table.refresh();
}

function initFinancePage(table) {
  const fyPicker = document.getElementById("rp-burn-tracker-fy");
  const showBtn = document.getElementById("rp-burn-tracker-show-btn");
  const content = document.getElementById("rp-burn-tracker-content");
  const filterPanel = document.getElementById("rp-burn-tracker-filter-panel");

  if (!fyPicker || !showBtn || !content) return;

  async function onShow() {
    const fyCode = fyPicker.value || fyPicker.getAttribute("value");
    if (!fyCode) {
      toast({
        type: "warning",
        title: "Select a year",
        message: "Please select a financial year first.",
      });
      return;
    }
    const fyChanged = fyCode !== currentFyCode;
    currentFyCode = fyCode;
    content.removeAttribute("hidden");

    if (fyChanged) {
      await ensureSprintColumns(table, fyCode);
    }
    loadTable(table, fyCode);
  }

  showBtn.addEventListener("click", onShow);
  fyPicker.addEventListener("change", () => {
    if (currentFyCode) onShow();
  });

  // Filter changes re-load the table if a FY is already selected
  if (filterPanel) {
    filterPanel.addEventListener("rp:filter:change", () => {
      if (currentFyCode) loadTable(table, currentFyCode);
    });
    filterPanel.addEventListener("rp:search", () => {
      if (currentFyCode) loadTable(table, currentFyCode);
    });
  }

  // Apply risk row classes after each render
  table.addEventListener("rp:rendered", () => applyRiskRowClasses(table));
}

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-burn-tracker-table");
  if (!table) return;

  initFinancePage(table);
  initActions(table);
  initConfigDrawer(table);
  initDoneDrawer(table);
});
