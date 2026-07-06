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
let tabsInitialized = false;
let activeTab = "teams";

// ---- Utility functions ----

function allocationSetLabel(row) {
  const num = String(row.code || "")
    .split("-")
    .pop();
  return `Set #${num} — ${row.status_display || row.status}`;
}

function num(value) {
  const n = Number(value);
  return Number.isFinite(n) ? n : 0;
}

function formatCurrency(value) {
  return `£${num(value).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`;
}

function classifyCell(cell) {
  const allocated = num(cell.allocated_days);
  if (cell.util_pct === null || cell.util_pct === undefined) {
    if (allocated > 0) {
      return { display: `${allocated.toFixed(1)}d`, bucket: null, is_over: false };
    }
    return { display: "—", bucket: "none", is_over: false };
  }
  const utilPct = num(cell.util_pct);
  const display = `${Math.round(utilPct)}%`;
  if (utilPct > 100) return { display, bucket: "over", is_over: true };
  if (utilPct >= 90) return { display, bucket: "excellent", is_over: false };
  if (utilPct >= 50) return { display, bucket: "healthy", is_over: false };
  if (utilPct > 0) return { display, bucket: "ramp", is_over: false };
  return { display, bucket: "none", is_over: false };
}

function sprintLabels(sprints) {
  return sprints.map((s) => `Sprint ${s.sprint_number}`);
}

function buildChartData(sprints, chartCells) {
  return {
    labels: sprintLabels(sprints),
    axisLeftLabel: "Days",
    axisRightLabel: "Util%",
    bars: [
      {
        label: "Net Capacity",
        data: chartCells.map((c) => num(c.net_capacity)),
        color: "#6366f1",
      },
      {
        label: "Allocated",
        data: chartCells.map((c) => num(c.allocated_days)),
        color: "#f59e0b",
      },
    ],
    lines: [
      {
        label: "Util%",
        data: chartCells.map((c) => (c.util_pct === null ? null : num(c.util_pct))),
        color: "#10b981",
        axis: "y1",
        max: 140,
      },
    ],
  };
}

function buildProgrammeChartData(sprints, cells) {
  return {
    labels: sprintLabels(sprints),
    axisLeftLabel: "£",
    bars: [
      {
        label: "Forecast Cost (£)",
        data: cells.map((c) => num(c.forecast_cost)),
        color: "#6366f1",
      },
    ],
    lines: [
      {
        label: "Budget Baseline (£)",
        data: cells.map((c) => num(c.budget_baseline)),
        color: "#ef4444",
        dashed: true,
      },
      {
        label: "Cumulative (£)",
        data: cells.map((c) => num(c.cumulative_cost)),
        color: "#10b981",
      },
    ],
  };
}

// ---- Row renderers ----

window.renderUtilisationSummaryRow = function renderUtilisationSummaryRow(row) {
  const sublabelHTML = row.sublabel
    ? `<div class="small" style="color:var(--rp-text-muted)">${esc(row.sublabel)}</div>`
    : "";
  return `
    <td>
      <div class="fw-medium">${esc(row.label)}</div>
      ${sublabelHTML}
    </td>
    <td>${esc(row.total_net_capacity)}d</td>
    <td>${esc(row.total_allocated)}d</td>
    <td>${esc(row.avg_util_pct)}%</td>
    <td class="text-danger text-end fw-medium">${esc(row.sprints_over)}</td>
  `;
};

// ---- Filter state helpers ----

function getRow1Filters() {
  const teamField = document.getElementById("rp-utilisation-team");
  const employmentTypeField = document.getElementById("rp-utilisation-employment-type");
  const includePlaceholdersField = document.getElementById("rp-utilisation-include-placeholders");
  return {
    team: teamField?.value || "",
    employmentType: employmentTypeField?.value || "",
    includePlaceholders: includePlaceholdersField?.checked === true,
  };
}

// ---- Data fetching ----

async function fetchTeamsData() {
  if (!currentAllocationSetCode) return null;
  const { team, includePlaceholders } = getRow1Filters();
  const { href, method } = API_URLS.resourcePlans.utilisationTeams(planCode, versionNumber);
  const params = new URLSearchParams({ allocation_set: currentAllocationSetCode });
  if (team) params.set("team", team);
  if (includePlaceholders) params.set("include_placeholders", "true");
  const res = await apiFetch(`${href}?${params.toString()}`, { method });
  return res?.data ?? null;
}

async function fetchMembersData() {
  if (!currentAllocationSetCode) return null;
  const { team, employmentType } = getRow1Filters();
  const memberField = document.getElementById("rp-utilisation-member");
  const projectField = document.getElementById("rp-utilisation-project");
  const { href, method } = API_URLS.resourcePlans.utilisationMembers(planCode, versionNumber);
  const params = new URLSearchParams({ allocation_set: currentAllocationSetCode });
  if (team) params.set("team", team);
  if (employmentType) params.set("employment_type", employmentType);
  if (memberField?.value) params.set("member", memberField.value);
  if (projectField?.value) params.set("project", projectField.value);
  const res = await apiFetch(`${href}?${params.toString()}`, { method });
  return res?.data ?? null;
}

// ---- Render: Teams tab ----

async function loadTeamsTab() {
  const chartContainer = document.getElementById("rp-utilisation-teams-chart");
  const table = document.getElementById("rp-utilisation-teams-table");
  if (!chartContainer || !table) return;

  if (!currentAllocationSetCode) {
    chartContainer.innerHTML = `<p class="text-muted">No allocation sets yet — run the engine from the Allocation Grid page first.</p>`;
    table.rows = [];
    return;
  }

  try {
    const data = await fetchTeamsData();
    if (!data) return;

    chartContainer.innerHTML = `<bar-chart id="rp-utilisation-teams-bar-chart" title="Team Utilisation — Net Capacity vs Allocated"></bar-chart>`;
    const chartEl = document.getElementById("rp-utilisation-teams-bar-chart");
    if (chartEl) chartEl.data = buildChartData(data.sprints, data.chart_cells);

    table.rows = data.teams.map((t) => ({
      label: t.team_name,
      sublabel: "",
      total_net_capacity: t.total_net_capacity,
      total_allocated: t.total_allocated,
      avg_util_pct: t.avg_util_pct,
      sprints_over: t.sprints_over,
    }));
  } catch (err) {
    const msg = err?.data?.error?.message ?? "Failed to load team utilisation.";
    toast({ type: "error", title: "Error", message: msg });
  }
}

// ---- Render: Members tab ----

function getMembersGraphType() {
  const field = document.getElementById("rp-utilisation-members-graph-type");
  return field?.value || "bar";
}

async function loadMembersTab() {
  const chartContainer = document.getElementById("rp-utilisation-members-chart");
  const table = document.getElementById("rp-utilisation-members-table");
  if (!chartContainer || !table) return;

  if (!currentAllocationSetCode) {
    chartContainer.innerHTML = `<p class="text-muted">No allocation sets yet — run the engine from the Allocation Grid page first.</p>`;
    table.rows = [];
    return;
  }

  try {
    const data = await fetchMembersData();
    if (!data) return;

    if (getMembersGraphType() === "heatmap") {
      chartContainer.innerHTML = `<heatmap-chart id="rp-utilisation-members-heatmap-chart" title="Member Utilisation Heatmap"></heatmap-chart>`;
      const heatmapEl = document.getElementById("rp-utilisation-members-heatmap-chart");
      if (heatmapEl) {
        heatmapEl.data = {
          sprints: data.sprints,
          rows: data.members.map((m) => ({
            label: m.member_name,
            sublabel: m.team_names.join(", "),
            cells: m.cells.map((c) => classifyCell(c)),
          })),
        };
      }
    } else {
      chartContainer.innerHTML = `<bar-chart id="rp-utilisation-members-bar-chart" title="Member Utilisation — Per Sprint"></bar-chart>`;
      const chartEl = document.getElementById("rp-utilisation-members-bar-chart");
      if (chartEl) chartEl.data = buildChartData(data.sprints, data.chart_cells);
    }

    table.rows = data.members.map((m) => ({
      label: m.member_name,
      sublabel: m.team_names.join(", "),
      total_net_capacity: m.total_net_capacity,
      total_allocated: m.total_allocated,
      avg_util_pct: m.avg_util_pct,
      sprints_over: m.sprints_over,
    }));
  } catch (err) {
    const msg = err?.data?.error?.message ?? "Failed to load member utilisation.";
    toast({ type: "error", title: "Error", message: msg });
  }
}

// ---- Render: Programmes tab ----

async function fetchProgrammesData() {
  const programmeField = document.getElementById("rp-utilisation-programme");
  const { href, method } = API_URLS.resourcePlans.utilisationProgrammes(planCode, versionNumber);
  const params = new URLSearchParams();
  if (programmeField?.value) params.set("programme", programmeField.value);
  const qs = params.toString();
  const res = await apiFetch(qs ? `${href}?${qs}` : href, { method });
  return res?.data ?? null;
}

async function loadProgrammesTab() {
  const container = document.getElementById("rp-utilisation-programmes-charts");
  if (!container) return;

  try {
    const data = await fetchProgrammesData();
    if (!data) return;

    if (!data.programmes.length) {
      container.innerHTML = `<p class="text-muted">No programmes configured on this version's projects.</p>`;
      return;
    }

    container.innerHTML = data.programmes
      .map(
        (p, idx) =>
          `<bar-chart id="rp-utilisation-programme-chart-${idx}" class="mb-3"></bar-chart>`,
      )
      .join("");

    data.programmes.forEach((p, idx) => {
      const chartEl = document.getElementById(`rp-utilisation-programme-chart-${idx}`);
      if (!chartEl) return;
      chartEl.setAttribute("title", p.programme_name);
      const chartData = buildProgrammeChartData(data.sprints, p.cells);
      chartData.meta = `Budget: ${formatCurrency(p.total_budget)}    Forecast: ${formatCurrency(p.total_forecast)}`;
      chartEl.data = chartData;
    });
  } catch (err) {
    const msg = err?.data?.error?.message ?? "Failed to load programme utilisation.";
    toast({ type: "error", title: "Error", message: msg });
  }
}

// ---- Refresh coordination ----

async function refreshActiveTab() {
  if (activeTab === "teams") await loadTeamsTab();
  else if (activeTab === "members") await loadMembersTab();
  else if (activeTab === "programmes") await loadProgrammesTab();
}

// ---- Tabs ----

function buildSummaryTableMarkup(tableId, labelColumnTitle) {
  return `
    <data-table id="${tableId}" row-template="renderUtilisationSummaryRow" empty-message="No data found.">
      <table-columns>
        <table-column label="${esc(labelColumnTitle)}" key="label"></table-column>
        <table-column label="Total Net Cap." key="total_net_capacity" numeric></table-column>
        <table-column label="Total Allocated" key="total_allocated" numeric></table-column>
        <table-column label="Avg Util%" key="avg_util_pct" numeric></table-column>
        <table-column label="Sprints Over" key="sprints_over" numeric></table-column>
      </table-columns>
    </data-table>
  `;
}

function buildTabsMarkup() {
  return `
    <tab-panel id="rp-utilisation-tabs">
      <tab-items>
        <tab-item id="teams" active>
          <tab-header title="Teams" icon="bi-people-fill"></tab-header>
          <tab-content>
            <div id="rp-utilisation-teams-chart" class="mb-3"></div>
            <section-panel>
              <panel-title>Team Summary</panel-title>
              <panel-body>${buildSummaryTableMarkup("rp-utilisation-teams-table", "Team")}</panel-body>
            </section-panel>
          </tab-content>
        </tab-item>
        <tab-item id="members">
          <tab-header title="Members" icon="bi-person-fill"></tab-header>
          <tab-content>
            <div class="row g-3 align-items-end mb-3">
              <div class="col-auto">
                <radio-group-field id="rp-utilisation-members-graph-type" label="Graph Type">
                  <option-field value="bar" label="Bar" checked></option-field>
                  <option-field value="heatmap" label="Heatmap"></option-field>
                </radio-group-field>
              </div>
              <div class="col-auto">
                <member-field id="rp-utilisation-member" name="member" allow-all show-label></member-field>
              </div>
              <div class="col-auto">
                <project-field id="rp-utilisation-project" name="project" allow-all show-label></project-field>
              </div>
            </div>
            <div id="rp-utilisation-members-chart" class="mb-3"></div>
            <section-panel>
              <panel-title>Member Summary</panel-title>
              <panel-body>${buildSummaryTableMarkup("rp-utilisation-members-table", "Member")}</panel-body>
            </section-panel>
          </tab-content>
        </tab-item>
        <tab-item id="programmes">
          <tab-header title="Programmes" icon="bi-diagram-3-fill"></tab-header>
          <tab-content>
            <div class="row g-3 align-items-end mb-3">
              <div class="col-auto">
                <programme-field id="rp-utilisation-programme" name="programme" allow-all show-label></programme-field>
              </div>
            </div>
            <div id="rp-utilisation-programmes-charts"></div>
          </tab-content>
        </tab-item>
      </tab-items>
    </tab-panel>
  `;
}

function initTabs() {
  const container = document.getElementById("rp-utilisation-tabs-container");
  if (!container) return;

  container.innerHTML = buildTabsMarkup();
  tabsInitialized = true;

  const panel = document.getElementById("rp-utilisation-tabs");
  panel?.addEventListener("rp:tab-change", async (e) => {
    activeTab = e.detail.tab;
    await refreshActiveTab();
  });

  document
    .getElementById("rp-utilisation-members-graph-type")
    ?.addEventListener("change", () => loadMembersTab());
  document
    .getElementById("rp-utilisation-member")
    ?.addEventListener("change", () => loadMembersTab());
  document
    .getElementById("rp-utilisation-project")
    ?.addEventListener("change", () => loadMembersTab());
  document
    .getElementById("rp-utilisation-programme")
    ?.addEventListener("change", () => loadProgrammesTab());

  loadTeamsTab();
}

// ---- Allocation Set dropdown ----

async function initAllocationSetDropdown() {
  const container = document.getElementById("rp-utilisation-allocation-set-container");
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
    if (!tabsInitialized) initTabs();
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
    <dropdown-field id="rp-utilisation-allocation-set" name="allocation_set" value="${esc(selected.code)}">
      <values-list>${optionsHtml}</values-list>
    </dropdown-field>
  `;

  document
    .getElementById("rp-utilisation-allocation-set")
    ?.addEventListener("change", async (e) => {
      const code = e.target.value;
      const match = allocationSets.find((s) => s.code === code);
      currentAllocationSetCode = match ? match.code : null;
      await refreshActiveTab();
    });

  if (!tabsInitialized) initTabs();
  else await refreshActiveTab();
}

function initRow1Filters() {
  document
    .getElementById("rp-utilisation-team")
    ?.addEventListener("change", () => refreshActiveTab());
  document
    .getElementById("rp-utilisation-employment-type")
    ?.addEventListener("change", () => refreshActiveTab());
  document.getElementById("rp-utilisation-include-placeholders")?.addEventListener("change", () => {
    if (activeTab === "teams") loadTeamsTab();
  });
}

// ---- Bootstrap ----

document.addEventListener("DOMContentLoaded", () => {
  const planCodeField = document.getElementById("rp-utilisation-plan-code");
  const versionField = document.getElementById("rp-utilisation-version-number");
  if (!planCodeField || !versionField) return;

  planCode = planCodeField.value;
  versionNumber = parseInt(versionField.value, 10);

  initRow1Filters();
  initAllocationSetDropdown();
});
