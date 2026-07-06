"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import { apiFetch } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

// ---- Shared state ----
let currentData = null;
let viewMode = "all";
let tabsInitialized = false;

// ---- Utility functions ----

function num(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function rowClass(type) {
  return type === "total" || type === "risk" ? "fw-bold" : "";
}

function cellClass(row, value) {
  if (row.type === "risk" && value !== null && value !== undefined) {
    return num(value) < 0 ? "text-danger" : "text-success";
  }
  return "";
}

function formatCellValue(row, value) {
  if (value === null || value === undefined || value === "") {
    return `<span class="rp-grid-empty-cell">—</span>`;
  }
  return row.type === "percent" ? `${esc(value)}%` : esc(value);
}

// ---- Rows table (shared by "All Teams" and each "By Team" accordion) ----

function buildRowsTableMarkup(rows, months, monthLabels) {
  const headerCells = months.map((m) => `<th>${esc(monthLabels[m] || m)}</th>`).join("");
  const bodyRows = rows
    .map((row) => {
      const cells = months
        .map((m) => {
          const value = row.values[m];
          return `<td class="rp-grid-cell ${cellClass(row, value)}">${formatCellValue(row, value)}</td>`;
        })
        .join("");
      return `<tr class="${rowClass(row.type)}"><td>${esc(row.label)}</td>${cells}</tr>`;
    })
    .join("");

  return `
    <div style="overflow-x:auto">
      <table class="rp-grid-detail-table">
        <thead><tr><th>Category</th>${headerCells}</tr></thead>
        <tbody>${bodyRows}</tbody>
      </table>
    </div>
  `;
}

// ---- Data tab ----

function renderDataTab() {
  const container = document.getElementById("rp-dvc-data-container");
  if (!container || !currentData) return;

  if (viewMode === "all") {
    container.innerHTML = buildRowsTableMarkup(
      currentData.overall.rows,
      currentData.months,
      currentData.month_labels,
    );
    return;
  }

  if (!currentData.teams.length) {
    container.innerHTML = `<p class="small mb-0" style="color:var(--rp-text-muted)">No teams found for this plan version.</p>`;
    return;
  }

  container.innerHTML = currentData.teams
    .map(
      (block, idx) => `
        <accordion-panel label="${esc(block.team.name)}" icon="bi-people" group="rp-dvc-teams"${idx === 0 ? " open" : ""}>
          <accordion-body><div id="rp-dvc-team-body-${idx}"></div></accordion-body>
        </accordion-panel>
      `,
    )
    .join("");

  currentData.teams.forEach((block, idx) => {
    const body = document.getElementById(`rp-dvc-team-body-${idx}`);
    if (body) {
      body.innerHTML = buildRowsTableMarkup(
        block.rows,
        currentData.months,
        currentData.month_labels,
      );
    }
  });
}

// ---- Chart tab — always "All Teams", per #231 ----

function buildChartData(rows, months, monthLabels) {
  const demandRow = rows.find((r) => r.key === "total_demand");
  const capacityRow = rows.find((r) => r.key === "total_capacity");
  return {
    labels: months.map((m) => monthLabels[m] || m),
    axisLeftLabel: "FTE",
    bars: [
      {
        label: "Total Demand (FTE)",
        data: months.map((m) => num(demandRow?.values[m])),
        color: "#6366f1",
      },
      {
        label: "Total Capacity (FTE)",
        data: months.map((m) => num(capacityRow?.values[m])),
        color: "#10b981",
      },
    ],
  };
}

function renderChartTab() {
  const container = document.getElementById("rp-dvc-chart-container");
  if (!container || !currentData) return;

  container.innerHTML = `<bar-chart id="rp-dvc-bar-chart" title="Demand vs. Capacity — All Teams"></bar-chart>`;
  const chartEl = document.getElementById("rp-dvc-bar-chart");
  if (chartEl) {
    chartEl.data = buildChartData(
      currentData.overall.rows,
      currentData.months,
      currentData.month_labels,
    );
  }
}

// ---- Tabs ----

function buildTabsMarkup() {
  return `
    <tab-panel id="rp-dvc-tabs">
      <tab-items>
        <tab-item id="data" active>
          <tab-header title="Data" icon="bi-table"></tab-header>
          <tab-content>
            <div class="row g-3 align-items-end mb-3">
              <div class="col-auto">
                <dropdown-field id="rp-dvc-view-mode" name="view_mode" label="View" value="all">
                  <values-list>
                    <value value="all">All Teams</value>
                    <value value="by_team">By Team</value>
                  </values-list>
                </dropdown-field>
              </div>
            </div>
            <div id="rp-dvc-data-container"></div>
          </tab-content>
        </tab-item>
        <tab-item id="chart">
          <tab-header title="Chart" icon="bi-bar-chart-fill"></tab-header>
          <tab-content>
            <div id="rp-dvc-chart-container"></div>
          </tab-content>
        </tab-item>
      </tab-items>
    </tab-panel>
  `;
}

function initTabs() {
  const container = document.getElementById("rp-dvc-tabs-container");
  if (!container) return;

  container.innerHTML = buildTabsMarkup();
  tabsInitialized = true;

  document.getElementById("rp-dvc-view-mode")?.addEventListener("change", (e) => {
    viewMode = e.target.value || "all";
    renderDataTab();
  });

  renderDataTab();
  renderChartTab();
}

// ---- Filter helpers ----

function buildQuery() {
  const planField = document.getElementById("rp-dvc-plan");
  const versionField = document.getElementById("rp-dvc-version");
  const teamField = document.getElementById("rp-dvc-team");
  const empTypeField = document.getElementById("rp-dvc-emp-type");
  const query = { plan: planField?.value ?? "", version: versionField?.value ?? "" };
  if (teamField?.value) query.team = teamField.value;
  if (empTypeField?.value) query.employment_type = empTypeField.value;
  return query;
}

function validateFilters() {
  const planField = document.getElementById("rp-dvc-plan");
  const versionField = document.getElementById("rp-dvc-version");
  planField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
  versionField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
  return (
    !planField?.querySelector("[data-rp-error]:not([hidden])") &&
    !versionField?.querySelector("[data-rp-error]:not([hidden])")
  );
}

// ---- Load report ----

async function loadReport() {
  if (!validateFilters()) return;

  const query = buildQuery();
  const params = new URLSearchParams(query);
  const { href, method } = API_URLS.reports.demandVsCapacityData();

  const loadBtn = document.getElementById("rp-dvc-load-btn");
  loadBtn?.setAttribute("disabled", "");

  document.getElementById("rp-dvc-hint-panel")?.setAttribute("hidden", "");
  document.getElementById("rp-dvc-results")?.setAttribute("hidden", "");
  document.getElementById("rp-dvc-export-btn")?.setAttribute("hidden", "");

  try {
    const res = await apiFetch(`${href}?${params.toString()}`, { method });
    const data = res?.data ?? {};
    currentData = data;

    if (!data.has_allocation_set) {
      document.getElementById("rp-dvc-hint-panel")?.removeAttribute("hidden");
      return;
    }

    if (!tabsInitialized) initTabs();
    else {
      renderDataTab();
      renderChartTab();
    }

    document.getElementById("rp-dvc-results")?.removeAttribute("hidden");
    document.getElementById("rp-dvc-export-btn")?.removeAttribute("hidden");
  } catch (err) {
    const msg =
      err?.data?.error?.message ??
      "Failed to load the Demand vs. Capacity report. Please try again.";
    toast({ type: "error", title: "Error", message: msg });
  } finally {
    loadBtn?.removeAttribute("disabled");
  }
}

// ---- Export ----

function initExport() {
  const exportBtn = document.getElementById("rp-dvc-export-btn");
  const exportView = document.getElementById("rp-dvc-export-view");
  if (!exportBtn || !exportView) return;

  exportView.setAttribute("specs-url", API_URLS.reports.demandVsCapacityExportSpecs().href);

  exportBtn.addEventListener("click", () => {
    const query = buildQuery();
    const params = new URLSearchParams(query);
    const baseHref = API_URLS.reports.demandVsCapacityExport().href;
    exportView.setAttribute("export-url", `${baseHref}?${params.toString()}`);
    exportView.show();
  });
}

// ---- Bootstrap ----

document.addEventListener("DOMContentLoaded", () => {
  const planField = document.getElementById("rp-dvc-plan");
  const versionField = document.getElementById("rp-dvc-version");
  if (!planField || !versionField) return;

  setBreadcrumbs([
    { label: "Reports" },
    { label: "Standard Reports", href: UI_URLS.reports.standardList() },
    { label: "Demand vs. Capacity" },
  ]);

  planField.addEventListener("change", () => {
    const planCode = planField.value;
    if (planCode) versionField.setAttribute("plan-code", planCode);
    else versionField.removeAttribute("plan-code");
    versionField.value = "";
  });

  document.getElementById("rp-dvc-load-btn")?.addEventListener("click", loadReport);

  document.getElementById("rp-dvc-config-btn")?.addEventListener("click", () => {
    window.location.href = UI_URLS.reports.standardDemandVsCapacityConfig();
  });

  initExport();
});
