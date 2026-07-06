"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import { apiFetch } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

// ---- Shared state ----
let currentData = null;
let dataView = "all";
let chartView = "label";
let tabsInitialized = false;

const DIMENSION_LABELS = {
  label: "Label",
  project: "Project",
  programme: "Programme",
  team: "Team",
  engineer: "Engineer",
  finance_type: "Finance Type",
};

// ---- Utility functions ----

function num(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function fmtDays(value) {
  return `${num(value).toFixed(2)}d`;
}

function buildDiffRows(rows, dimensionKey) {
  return rows
    .map((row) => {
      const forecast = num(row.forecast_days);
      const actual = num(row.actual_days);
      const variance = actual - forecast;
      if (variance === 0) return null;
      const cells = { ...row, forecast_days: fmtDays(forecast), actual_days: fmtDays(actual) };
      if (dimensionKey) cells[dimensionKey] = row[dimensionKey];
      return { type: variance > 0 ? "add" : "del", cells };
    })
    .filter(Boolean);
}

function buildChartData(rows, dimensionKey) {
  return {
    labels: rows.map((r) => r[dimensionKey]),
    axisLeftLabel: "Days",
    bars: [
      {
        label: "Forecast (Days)",
        data: rows.map((r) => num(r.forecast_days)),
        color: "#6366f1",
      },
      {
        label: "Actuals (Days)",
        data: rows.map((r) => num(r.actual_days)),
        color: "#10b981",
      },
    ],
  };
}

// ---- Filter helpers ----

function buildQuery() {
  const sprintField = document.getElementById("rp-sfva-sprint");
  const teamField = document.getElementById("rp-sfva-team");
  const query = { sprint: sprintField?.value ?? "" };
  if (teamField?.value) query.team = teamField.value;
  return query;
}

function validateFilters() {
  const fyField = document.getElementById("rp-sfva-fy");
  const sprintField = document.getElementById("rp-sfva-sprint");
  fyField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
  sprintField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
  return (
    !fyField?.querySelector("[data-rp-error]:not([hidden])") &&
    !sprintField?.querySelector("[data-rp-error]:not([hidden])")
  );
}

// ---- Data tab ----

function renderDataTab() {
  const diffEl = document.getElementById("rp-sfva-diff");
  if (!diffEl || !currentData) return;

  if (dataView === "all") {
    diffEl.columns = [
      { key: "team", label: "Team" },
      { key: "engineer", label: "Engineer" },
      { key: "label", label: "Label" },
      { key: "project", label: "Project" },
      { key: "programme", label: "Programme" },
      { key: "finance_type", label: "Finance Type" },
      { key: "forecast_days", label: "Forecast (Days)" },
      { key: "actual_days", label: "Actuals (Days)" },
    ];
    diffEl.data = { rows: buildDiffRows(currentData.all_rows, null) };
    return;
  }

  diffEl.columns = [
    { key: dataView, label: DIMENSION_LABELS[dataView] },
    { key: "forecast_days", label: "Forecast (Days)" },
    { key: "actual_days", label: "Actuals (Days)" },
  ];
  diffEl.data = { rows: buildDiffRows(currentData.grouped[dataView] ?? [], dataView) };
}

// ---- Chart tab ----

function renderChartTab() {
  const container = document.getElementById("rp-sfva-chart-container");
  if (!container || !currentData) return;

  container.innerHTML = `<bar-chart id="rp-sfva-bar-chart" title="Forecast vs. Actuals — ${esc(DIMENSION_LABELS[chartView])}"></bar-chart>`;
  const chartEl = document.getElementById("rp-sfva-bar-chart");
  if (chartEl) chartEl.data = buildChartData(currentData.grouped[chartView] ?? [], chartView);
}

// ---- Tabs ----

function buildTabsMarkup() {
  return `
    <tab-panel id="rp-sfva-tabs">
      <tab-items>
        <tab-item id="data" active>
          <tab-header title="Data" icon="bi-table"></tab-header>
          <tab-content>
            <div class="row g-3 align-items-end mb-3">
              <div class="col-auto">
                <dropdown-field id="rp-sfva-data-view" name="data_view" label="View" value="all">
                  <values-list>
                    <value value="all">All</value>
                    <value value="label">By Label</value>
                    <value value="project">By Project</value>
                    <value value="programme">By Programme</value>
                    <value value="team">By Team</value>
                    <value value="engineer">By Engineer</value>
                    <value value="finance_type">By Finance/Recharge Type</value>
                  </values-list>
                </dropdown-field>
              </div>
              <div class="col-auto d-flex gap-3 small" style="color:var(--rp-text-muted)">
                <span><span class="rp-diff-legend-swatch add">+</span> Actuals higher than Forecast</span>
                <span><span class="rp-diff-legend-swatch del">-</span> Actuals lower than Forecast</span>
              </div>
            </div>
            <diff-compare id="rp-sfva-diff"></diff-compare>
          </tab-content>
        </tab-item>
        <tab-item id="chart">
          <tab-header title="Chart" icon="bi-bar-chart-fill"></tab-header>
          <tab-content>
            <div class="row g-3 align-items-end mb-3">
              <div class="col-auto">
                <dropdown-field id="rp-sfva-chart-view" name="chart_view" label="View" value="label">
                  <values-list>
                    <value value="label">By Label</value>
                    <value value="project">By Project</value>
                    <value value="programme">By Programme</value>
                    <value value="team">By Team</value>
                    <value value="engineer">By Engineer</value>
                    <value value="finance_type">By Finance/Recharge Type</value>
                  </values-list>
                </dropdown-field>
              </div>
            </div>
            <div id="rp-sfva-chart-container"></div>
          </tab-content>
        </tab-item>
      </tab-items>
    </tab-panel>
  `;
}

function initTabs() {
  const container = document.getElementById("rp-sfva-tabs-container");
  if (!container) return;

  container.innerHTML = buildTabsMarkup();
  tabsInitialized = true;

  document.getElementById("rp-sfva-data-view")?.addEventListener("change", (e) => {
    dataView = e.target.value || "all";
    renderDataTab();
  });
  document.getElementById("rp-sfva-chart-view")?.addEventListener("change", (e) => {
    chartView = e.target.value || "label";
    renderChartTab();
  });

  renderDataTab();
  renderChartTab();
}

// ---- Stat cards ----

function renderStatCards(totals) {
  const forecastEl = document.getElementById("rp-sfva-total-forecast");
  const actualEl = document.getElementById("rp-sfva-total-actual");
  const varianceEl = document.getElementById("rp-sfva-total-variance");
  if (forecastEl) forecastEl.textContent = fmtDays(totals.forecast_days);
  if (actualEl) actualEl.textContent = fmtDays(totals.actual_days);
  if (varianceEl) {
    const variance = num(totals.variance_days);
    varianceEl.textContent = `${variance > 0 ? "+" : ""}${fmtDays(variance)}`;
    varianceEl.style.color =
      variance > 0 ? "var(--rp-success)" : variance < 0 ? "var(--rp-danger)" : "";
  }
}

// ---- Load report ----

async function loadReport() {
  if (!validateFilters()) return;

  const query = buildQuery();
  const params = new URLSearchParams(query);
  const { href, method } = API_URLS.reports.sprintForecastVsActualsData();

  const loadBtn = document.getElementById("rp-sfva-load-btn");
  loadBtn?.setAttribute("disabled", "");

  document.getElementById("rp-sfva-hint-panel")?.setAttribute("hidden", "");
  document.getElementById("rp-sfva-results")?.setAttribute("hidden", "");
  document.getElementById("rp-sfva-export-btn")?.setAttribute("hidden", "");

  try {
    const res = await apiFetch(`${href}?${params.toString()}`, { method });
    const data = res?.data ?? {};
    currentData = data;

    if (!data.has_forecast && !data.has_actuals) {
      const teamField = document.getElementById("rp-sfva-team");
      const suffixEl = document.getElementById("rp-sfva-hint-team-suffix");
      if (suffixEl) {
        const teamLabel =
          teamField?.querySelector(".rp-input")?.selectedOptions?.[0]?.textContent ?? "";
        suffixEl.textContent = teamField?.value ? ` for team "${teamLabel}"` : "";
      }
      document.getElementById("rp-sfva-hint-panel")?.removeAttribute("hidden");
      return;
    }

    renderStatCards(data.totals);

    const noActualsBanner = document.getElementById("rp-sfva-no-actuals-banner");
    if (noActualsBanner) {
      if (data.has_forecast && !data.has_actuals) noActualsBanner.setAttribute("open", "");
      else noActualsBanner.removeAttribute("open");
    }

    if (!tabsInitialized) initTabs();
    else {
      renderDataTab();
      renderChartTab();
    }

    document.getElementById("rp-sfva-results")?.removeAttribute("hidden");
    document.getElementById("rp-sfva-export-btn")?.removeAttribute("hidden");
  } catch (err) {
    const msg =
      err?.data?.error?.message ??
      "Failed to load the Sprint Forecast vs. Actuals report. Please try again.";
    toast({ type: "error", title: "Error", message: msg });
  } finally {
    loadBtn?.removeAttribute("disabled");
  }
}

// ---- Export ----

function initExport() {
  const exportBtn = document.getElementById("rp-sfva-export-btn");
  const exportView = document.getElementById("rp-sfva-export-view");
  if (!exportBtn || !exportView) return;

  exportView.setAttribute("specs-url", API_URLS.reports.sprintForecastVsActualsExportSpecs().href);

  exportBtn.addEventListener("click", () => {
    const query = buildQuery();
    const params = new URLSearchParams(query);
    const baseHref = API_URLS.reports.sprintForecastVsActualsExport().href;
    exportView.setAttribute("export-url", `${baseHref}?${params.toString()}`);
    exportView.show();
  });
}

// ---- Bootstrap ----

document.addEventListener("DOMContentLoaded", () => {
  const fyField = document.getElementById("rp-sfva-fy");
  const sprintField = document.getElementById("rp-sfva-sprint");
  if (!fyField || !sprintField) return;

  setBreadcrumbs([
    { label: "Reports" },
    { label: "Standard Reports", href: UI_URLS.reports.standardList() },
    { label: "Sprint Forecast vs. Actuals" },
  ]);

  fyField.addEventListener("change", () => {
    const fy = fyField.value;
    if (fy) sprintField.setAttribute("fy-code", fy);
    else sprintField.removeAttribute("fy-code");
    sprintField.value = "";
  });

  document.getElementById("rp-sfva-load-btn")?.addEventListener("click", loadReport);

  initExport();
});
