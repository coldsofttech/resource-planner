"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import { apiFetch, formatCurrency } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

// ---- Shared state ----
let currentData = null;

// ---- Row / detail renderers ----

window.renderMfrRow = function renderMfrRow(row) {
  return `
    <td class="rp-mono">${esc(row.project_code)}</td>
    <td class="rp-mono">${esc(row.total_days)}</td>
    <td class="rp-mono">${formatCurrency(row.total_cost)}</td>
  `;
};

window.renderMfrDetail = function renderMfrDetail(row) {
  return `
    <div class="row g-3">
      <div class="col-6 col-md-3">
        <div class="small" style="color:var(--rp-text-muted)">Programme</div>
        <div>${esc(row.programme)}</div>
      </div>
      <div class="col-6 col-md-3">
        <div class="small" style="color:var(--rp-text-muted)">Project</div>
        <div>${esc(row.project)}</div>
      </div>
      <div class="col-6 col-md-3">
        <div class="small" style="color:var(--rp-text-muted)">Total Days</div>
        <div class="rp-mono">${esc(row.total_days)}</div>
      </div>
      <div class="col-6 col-md-3">
        <div class="small" style="color:var(--rp-text-muted)">Total Cost</div>
        <div class="rp-mono">${formatCurrency(row.total_cost)}</div>
      </div>
    </div>
  `;
};

// ---- Sprint badges ----

function buildSprintBadges(sprints) {
  if (!sprints.length) return "";
  return sprints
    .map((sprint) => {
      const badgeClass = sprint.has_actuals ? "rp-badge-success" : "rp-badge-warning";
      const icon = sprint.has_actuals ? "bi-check-circle-fill" : "bi-exclamation-triangle-fill";
      const suffix = sprint.has_actuals ? "Actuals Confirmed" : "Actuals Missing";
      return `<span class="rp-badge ${badgeClass}"><i class="bi ${icon} me-1"></i>${esc(sprint.name)} — ${suffix}</span>`;
    })
    .join("");
}

function renderSprintBadges(containerId, sprints) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = buildSprintBadges(sprints);
}

// ---- Results ----

function renderResults(data) {
  document.getElementById("rp-mfr-total-projects").textContent = String(data.totals.project_count);
  document.getElementById("rp-mfr-total-days").textContent = data.totals.total_days;
  document.getElementById("rp-mfr-total-cost").textContent = formatCurrency(data.totals.total_cost);
  document.getElementById("rp-mfr-grand-total-days").textContent = data.totals.total_days;
  document.getElementById("rp-mfr-grand-total-cost").textContent = formatCurrency(
    data.totals.total_cost,
  );

  renderSprintBadges("rp-mfr-sprint-badges", data.sprints);

  const table = document.getElementById("rp-mfr-table");
  if (table) table.rows = data.rows;
}

// ---- Filter helpers ----

function buildQuery() {
  const fyField = document.getElementById("rp-mfr-fy");
  const monthField = document.getElementById("rp-mfr-month");
  return { fy: fyField?.value ?? "", month: monthField?.value ?? "" };
}

function validateFilters() {
  const fyField = document.getElementById("rp-mfr-fy");
  const monthField = document.getElementById("rp-mfr-month");
  fyField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
  monthField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
  return (
    !fyField?.querySelector("[data-rp-error]:not([hidden])") &&
    !monthField?.querySelector("[data-rp-error]:not([hidden])")
  );
}

// ---- Load report ----

async function loadReport() {
  if (!validateFilters()) return;

  const query = buildQuery();
  const params = new URLSearchParams(query);
  const { href, method } = API_URLS.reports.monthlyFinanceReportData();

  const loadBtn = document.getElementById("rp-mfr-load-btn");
  loadBtn?.setAttribute("disabled", "");

  document.getElementById("rp-mfr-hint-panel")?.setAttribute("hidden", "");
  document.getElementById("rp-mfr-results")?.setAttribute("hidden", "");
  document.getElementById("rp-mfr-export-btn")?.setAttribute("hidden", "");

  try {
    const res = await apiFetch(`${href}?${params.toString()}`, { method });
    const data = res?.data ?? {};
    currentData = data;

    if (!data.sprints || !data.sprints.length) {
      document.getElementById("rp-mfr-hint-text").textContent =
        `No sprints were found for ${data.month_label ?? "the selected month"}.`;
      document.getElementById("rp-mfr-hint-sprints").innerHTML = "";
      document.getElementById("rp-mfr-hint-panel")?.removeAttribute("hidden");
      return;
    }

    if (!data.is_complete) {
      document.getElementById("rp-mfr-hint-text").textContent =
        "Actuals are not confirmed yet for every sprint in this month. The report becomes available once all sprints below have confirmed actuals.";
      renderSprintBadges("rp-mfr-hint-sprints", data.sprints);
      document.getElementById("rp-mfr-hint-panel")?.removeAttribute("hidden");
      return;
    }

    renderResults(data);
    document.getElementById("rp-mfr-results")?.removeAttribute("hidden");
    document.getElementById("rp-mfr-export-btn")?.removeAttribute("hidden");
  } catch (err) {
    const msg =
      err?.data?.error?.message ?? "Failed to load the Monthly Finance Report. Please try again.";
    toast({ type: "error", title: "Error", message: msg });
  } finally {
    loadBtn?.removeAttribute("disabled");
  }
}

// ---- Export ----

function initExport() {
  const exportBtn = document.getElementById("rp-mfr-export-btn");
  const exportView = document.getElementById("rp-mfr-export-view");
  if (!exportBtn || !exportView) return;

  exportView.setAttribute("specs-url", API_URLS.reports.monthlyFinanceReportExportSpecs().href);

  exportBtn.addEventListener("click", () => {
    if (!currentData) return;
    const query = buildQuery();
    const params = new URLSearchParams(query);
    const baseHref = API_URLS.reports.monthlyFinanceReportExport().href;
    exportView.setAttribute("export-url", `${baseHref}?${params.toString()}`);
    exportView.show();
  });
}

// ---- Bootstrap ----

document.addEventListener("DOMContentLoaded", () => {
  const fyField = document.getElementById("rp-mfr-fy");
  const monthField = document.getElementById("rp-mfr-month");
  if (!fyField || !monthField) return;

  setBreadcrumbs([
    { label: "Reports" },
    { label: "Standard Reports", href: UI_URLS.reports.standardList() },
    { label: "Monthly Finance Report" },
  ]);

  fyField.addEventListener("change", () => {
    const fyCode = fyField.value;
    if (fyCode) monthField.setAttribute("fy-code", fyCode);
    else monthField.removeAttribute("fy-code");
    monthField.value = "";
  });

  document.getElementById("rp-mfr-load-btn")?.addEventListener("click", loadReport);

  initExport();
});
