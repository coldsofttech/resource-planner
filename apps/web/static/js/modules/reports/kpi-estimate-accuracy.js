"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import { apiFetch, formatCurrency } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

// ---- Shared state ----
let currentData = null;
let tabsInitialized = false;

// Ordered best -> worst, plus the "Exception" outlier. Mirrors the backend's
// `_BANDS` ordering in `apps.reports.reports.kpi_estimate_accuracy`.
const BAND_COLORS = {
  gt90: "#16a34a",
  gt80: "#4ade80",
  in_range: "#eab308",
  gt70: "#f97316",
  gt60: "#f87171",
  gt50: "#ef4444",
  lt50: "#b91c1c",
  exception: "#8b5cf6",
  no_estimate: "#9ca3af",
};

// Collapsed to the four semantic badge colors the design system provides.
const BAND_BADGE_CLASS = {
  gt90: "rp-badge-success",
  gt80: "rp-badge-success",
  in_range: "rp-badge-warning",
  gt70: "rp-badge-warning",
  gt60: "rp-badge-danger",
  gt50: "rp-badge-danger",
  lt50: "rp-badge-danger",
  exception: "rp-badge-purple",
  no_estimate: "rp-badge-neutral",
};

// ---- Row renderer ----

window.renderKpiEeaRow = function renderKpiEeaRow(row) {
  const badgeClass = BAND_BADGE_CLASS[row.band_key] || "rp-badge-neutral";
  const accuracy =
    row.accuracy_pct !== null && row.accuracy_pct !== undefined ? `${esc(row.accuracy_pct)}%` : "—";
  return `
    <td>${esc(row.programme)}</td>
    <td class="fw-medium">${esc(row.project)}</td>
    <td>${esc(row.team)}</td>
    <td>${esc(row.collaborators_display)}</td>
    <td class="rp-mono">${formatCurrency(row.estimate_value)}</td>
    <td class="rp-mono">${formatCurrency(row.estimate_value_with_contingency)}</td>
    <td class="rp-mono">${formatCurrency(row.total_cost_till_date)}</td>
    <td><span class="rp-badge">${esc(row.tshirt_size)}</span></td>
    <td>${accuracy}</td>
    <td><span class="rp-badge ${badgeClass}">${esc(row.band)}</span></td>
    <td>${row.comment ? esc(row.comment) : "—"}</td>
  `;
};

// ---- Data tab ----

function renderDataTab() {
  const table = document.getElementById("rp-kpi-eea-table");
  if (!table || !currentData) return;
  table.rows = currentData.rows;
}

// ---- Chart tab ----

function buildBandChartData(counts, bandLabels, bandOrder) {
  const keys = bandOrder.filter((key) => counts[key]);
  return {
    labels: keys.map((key) => bandLabels[key] || key),
    values: keys.map((key) => counts[key]),
    colors: keys.map((key) => BAND_COLORS[key] || "#9ca3af"),
  };
}

function renderChartTab() {
  const container = document.getElementById("rp-kpi-eea-chart-container");
  if (!container || !currentData) return;

  container.innerHTML = `
    <div class="row g-3">
      <div class="col-12 col-md-6">
        <pie-chart id="rp-kpi-eea-chart-xs-s" title="XS / S Projects"></pie-chart>
      </div>
      <div class="col-12 col-md-6">
        <pie-chart id="rp-kpi-eea-chart-m-plus" title="M / L / XL Projects"></pie-chart>
      </div>
    </div>
  `;

  const { band_labels: bandLabels, band_order: bandOrder, charts } = currentData;
  const xsSChart = document.getElementById("rp-kpi-eea-chart-xs-s");
  if (xsSChart) xsSChart.data = buildBandChartData(charts.xs_s, bandLabels, bandOrder);

  const mPlusChart = document.getElementById("rp-kpi-eea-chart-m-plus");
  if (mPlusChart) mPlusChart.data = buildBandChartData(charts.m_plus, bandLabels, bandOrder);
}

// ---- Tabs ----

function buildTabsMarkup() {
  return `
    <tab-panel id="rp-kpi-eea-tabs">
      <tab-items>
        <tab-item id="data" active>
          <tab-header title="Data" icon="bi-table"></tab-header>
          <tab-content>
            <data-table
              id="rp-kpi-eea-table"
              row-template="renderKpiEeaRow"
              empty-message="No projects found."
            >
              <table-columns>
                <table-column label="Programme" key="programme" sortable></table-column>
                <table-column label="Project" key="project" sortable></table-column>
                <table-column label="Team" key="team"></table-column>
                <table-column label="Collaborators" key="collaborators_display"></table-column>
                <table-column label="Estimate Value" key="estimate_value" numeric></table-column>
                <table-column label="Est. with Contingency" key="estimate_value_with_contingency" numeric></table-column>
                <table-column label="Total Cost till Date" key="total_cost_till_date" numeric></table-column>
                <table-column label="T-Shirt Size" key="tshirt_size"></table-column>
                <table-column label="% Accuracy" key="accuracy_pct" numeric sortable></table-column>
                <table-column label="Band" key="band"></table-column>
                <table-column label="Comment" key="comment"></table-column>
              </table-columns>
            </data-table>
          </tab-content>
        </tab-item>
        <tab-item id="chart">
          <tab-header title="Chart" icon="bi-pie-chart-fill"></tab-header>
          <tab-content>
            <div id="rp-kpi-eea-chart-container"></div>
          </tab-content>
        </tab-item>
      </tab-items>
    </tab-panel>
  `;
}

function initTabs() {
  const container = document.getElementById("rp-kpi-eea-tabs-container");
  if (!container) return;

  container.innerHTML = buildTabsMarkup();
  tabsInitialized = true;

  renderDataTab();
  renderChartTab();
}

// ---- Filter helpers ----

function buildQuery() {
  const fyField = document.getElementById("rp-kpi-eea-fy");
  const monthField = document.getElementById("rp-kpi-eea-month");
  return { fy: fyField?.value ?? "", month: monthField?.value ?? "" };
}

function validateFilters() {
  const fyField = document.getElementById("rp-kpi-eea-fy");
  const monthField = document.getElementById("rp-kpi-eea-month");
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
  const { href, method } = API_URLS.reports.kpiEstimateAccuracyData();

  const loadBtn = document.getElementById("rp-kpi-eea-load-btn");
  loadBtn?.setAttribute("disabled", "");

  document.getElementById("rp-kpi-eea-hint-panel")?.setAttribute("hidden", "");
  document.getElementById("rp-kpi-eea-results")?.setAttribute("hidden", "");
  document.getElementById("rp-kpi-eea-export-btn")?.setAttribute("hidden", "");

  try {
    const res = await apiFetch(`${href}?${params.toString()}`, { method });
    const data = res?.data ?? {};
    currentData = data;

    if (!data.rows || !data.rows.length) {
      document.getElementById("rp-kpi-eea-hint-panel")?.removeAttribute("hidden");
      return;
    }

    if (!tabsInitialized) initTabs();
    else {
      renderDataTab();
      renderChartTab();
    }

    document.getElementById("rp-kpi-eea-results")?.removeAttribute("hidden");
    document.getElementById("rp-kpi-eea-export-btn")?.removeAttribute("hidden");
  } catch (err) {
    const msg =
      err?.data?.error?.message ??
      "Failed to load the KPI Report - Estimate % Accuracy. Please try again.";
    toast({ type: "error", title: "Error", message: msg });
  } finally {
    loadBtn?.removeAttribute("disabled");
  }
}

// ---- Export ----

function initExport() {
  const exportBtn = document.getElementById("rp-kpi-eea-export-btn");
  const exportView = document.getElementById("rp-kpi-eea-export-view");
  if (!exportBtn || !exportView) return;

  exportView.setAttribute("specs-url", API_URLS.reports.kpiEstimateAccuracyExportSpecs().href);

  exportBtn.addEventListener("click", () => {
    const query = buildQuery();
    const params = new URLSearchParams(query);
    const baseHref = API_URLS.reports.kpiEstimateAccuracyExport().href;
    exportView.setAttribute("export-url", `${baseHref}?${params.toString()}`);
    exportView.show();
  });
}

// ---- Bootstrap ----

document.addEventListener("DOMContentLoaded", () => {
  const fyField = document.getElementById("rp-kpi-eea-fy");
  const monthField = document.getElementById("rp-kpi-eea-month");
  if (!fyField || !monthField) return;

  setBreadcrumbs([
    { label: "Reports" },
    { label: "Standard Reports", href: UI_URLS.reports.standardList() },
    { label: "KPI Report - Estimate % Accuracy" },
  ]);

  fyField.addEventListener("change", () => {
    const fyCode = fyField.value;
    if (fyCode) monthField.setAttribute("fy-code", fyCode);
    else monthField.removeAttribute("fy-code");
    monthField.value = "";
  });

  document.getElementById("rp-kpi-eea-load-btn")?.addEventListener("click", loadReport);

  document.getElementById("rp-kpi-eea-config-btn")?.addEventListener("click", () => {
    window.location.href = UI_URLS.reports.standardKpiEstimateAccuracyConfig();
  });

  initExport();
});
