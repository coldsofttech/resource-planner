"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import { apiFetch, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

const FILTER_OPERATORS = [
  { value: "eq", label: "Equals" },
  { value: "neq", label: "Not Equals" },
  { value: "gt", label: "Greater Than" },
  { value: "gte", label: "Greater Than or Equal" },
  { value: "lt", label: "Less Than" },
  { value: "lte", label: "Less Than or Equal" },
  { value: "contains", label: "Contains" },
  { value: "starts_with", label: "Starts With" },
  { value: "ends_with", label: "Ends With" },
  { value: "is_null", label: "Is Empty" },
  { value: "is_not_null", label: "Is Not Empty" },
  { value: "in", label: "Is Any Of (comma-separated)" },
  { value: "not_in", label: "Is Not Any Of (comma-separated)" },
];

const AGGREGATIONS = [
  { value: "count", label: "Count" },
  { value: "count_distinct", label: "Count Distinct" },
  { value: "sum", label: "Sum" },
  { value: "avg", label: "Average" },
  { value: "min", label: "Minimum" },
  { value: "max", label: "Maximum" },
];

const CHART_VISUALIZATIONS = ["bar", "line", "pie"];
const CHART_COLORS = [
  "#6366f1",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#14b8a6",
  "#f472b6",
  "#0ea5e9",
];

// ---- Shared state ----
let state = {
  code: null,
  name: "Custom Report",
  dataSource: "",
  visualization: "table",
  config: { fields: [], filters: [], values: [], axis: "", legend: "" },
  canEdit: true,
};
let dataSourcesByKey = {};
let lastResult = null;
let currentColumns = [];

// ---- Cell formatting + row renderer ----

function formatCellValue(value) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  if (typeof value === "number") return value.toLocaleString();
  return String(value);
}

window.renderCustomReportResultRow = function renderCustomReportResultRow(row) {
  return currentColumns.map((c) => `<td>${esc(formatCellValue(row[c.key]))}</td>`).join("");
};

// ---- Result rendering ----

function renderResult(result) {
  const container = document.getElementById("rp-crb-result-container");
  if (!container || !result) return;

  if (result.type === "table") {
    currentColumns = result.columns;
    const columnsHTML = result.columns
      .map((c) => `<table-column label="${esc(c.label)}" key="${esc(c.key)}"></table-column>`)
      .join("");
    container.innerHTML = `
      <data-table id="rp-crb-result-table" row-template="renderCustomReportResultRow" empty-message="No rows found.">
        <table-columns>${columnsHTML}</table-columns>
      </data-table>
      ${result.truncated ? `<div class="small mt-2" style="color:var(--rp-text-muted)">Showing the first ${result.row_count} rows — results were truncated.</div>` : ""}
    `;
    const table = document.getElementById("rp-crb-result-table");
    if (table) table.rows = result.rows;
    return;
  }

  if (result.type === "card") {
    container.innerHTML = `
      <div class="row g-3">
        ${result.cards
          .map(
            (c) => `
          <section-panel col="col-12 col-md-4">
            <panel-title>${esc(c.label)}</panel-title>
            <panel-body><div class="fw-bold fs-4 mb-0">${esc(formatCellValue(c.value))}</div></panel-body>
          </section-panel>`,
          )
          .join("")}
      </div>
    `;
    return;
  }

  if (result.type === "pie") {
    container.innerHTML = `<pie-chart id="rp-crb-result-pie"></pie-chart>`;
    const chart = document.getElementById("rp-crb-result-pie");
    if (chart) {
      chart.data = {
        labels: result.labels,
        values: result.values,
        colors: result.labels.map((_, i) => CHART_COLORS[i % CHART_COLORS.length]),
      };
    }
    return;
  }

  if (result.type === "chart") {
    container.innerHTML = `<bar-chart id="rp-crb-result-chart"></bar-chart>`;
    const chart = document.getElementById("rp-crb-result-chart");
    if (!chart) return;
    const seriesData = result.series.map((s, i) => ({
      label: s.label,
      data: s.data,
      color: CHART_COLORS[i % CHART_COLORS.length],
    }));
    chart.data =
      result.visualization === "line"
        ? { labels: result.labels, axisLeftLabel: "Value", lines: seriesData }
        : { labels: result.labels, axisLeftLabel: "Value", bars: seriesData };
  }
}

// ---- Config form reading ----

function readConfigFromForm() {
  const fieldsGroup = document.getElementById("rp-crb-fields-group");
  const fields = fieldsGroup?.value ? fieldsGroup.value.split(",").filter(Boolean) : [];

  const filters = [...document.querySelectorAll("[data-filter-row]")]
    .map((row) => {
      const fieldKey = row.querySelector(".rp-crb-filter-field")?.value ?? "";
      const operator = row.querySelector(".rp-crb-filter-operator")?.value ?? "";
      const rawValue =
        row.querySelector(".rp-crb-filter-value")?.querySelector(".rp-input")?.value ?? "";
      let value = rawValue;
      if (operator === "in" || operator === "not_in") {
        value = rawValue
          .split(",")
          .map((v) => v.trim())
          .filter(Boolean);
      }
      return { field: fieldKey, operator, value };
    })
    .filter((f) => f.field && f.operator);

  const values = [...document.querySelectorAll("[data-value-row]")]
    .map((row) => ({
      field: row.querySelector(".rp-crb-value-field")?.value ?? "",
      aggregation: row.querySelector(".rp-crb-value-aggregation")?.value ?? "",
    }))
    .filter((v) => v.field && v.aggregation);

  const axis = document.getElementById("rp-crb-axis")?.value ?? "";
  const legend = document.getElementById("rp-crb-legend")?.value ?? "";

  return { fields, filters, values, axis, legend };
}

// ---- Filters tab ----

function addFilterRow(prefill) {
  const container = document.getElementById("rp-crb-filters-rows");
  const ds = dataSourcesByKey[state.dataSource];
  if (!container || !ds) return;

  const filterableFields = ds.fields.filter((f) => f.filterable);
  const row = document.createElement("div");
  row.className = "row g-2 align-items-end mb-2";
  row.setAttribute("data-filter-row", "");
  row.innerHTML = `
    <div class="col-12 col-md-4">
      <dropdown-field class="rp-crb-filter-field" show-label label="Field" placeholder="Select field…">
        <values-list>${filterableFields
          .map(
            (f) =>
              `<value value="${esc(f.key)}"${prefill?.field === f.key ? " selected" : ""}>${esc(f.label)}</value>`,
          )
          .join("")}</values-list>
      </dropdown-field>
    </div>
    <div class="col-12 col-md-3">
      <dropdown-field class="rp-crb-filter-operator" show-label label="Operator">
        <values-list>${FILTER_OPERATORS.map(
          (o) =>
            `<value value="${o.value}"${prefill?.operator === o.value ? " selected" : ""}>${esc(o.label)}</value>`,
        ).join("")}</values-list>
      </dropdown-field>
    </div>
    <div class="col-12 col-md-4">
      <text-field class="rp-crb-filter-value" show-label label="Value" placeholder="Value"></text-field>
    </div>
    <div class="col-12 col-md-1">
      <muted-button class="rp-crb-filter-remove" label="Remove" prefix-icon="bi-trash3"></muted-button>
    </div>
  `;
  container.appendChild(row);

  if (prefill?.value !== undefined) {
    const valueInput = row.querySelector(".rp-crb-filter-value")?.querySelector(".rp-input");
    if (valueInput) {
      valueInput.value = Array.isArray(prefill.value)
        ? prefill.value.join(", ")
        : (prefill.value ?? "");
    }
  }

  row.querySelector(".rp-crb-filter-remove")?.addEventListener("click", () => row.remove());
}

// ---- Values tab ----

function updateValuesAddButtonState() {
  const btn = document.getElementById("rp-crb-values-add-btn");
  const container = document.getElementById("rp-crb-values-rows");
  if (!btn || !container) return;
  const isChart = CHART_VISUALIZATIONS.includes(state.visualization);
  btn.toggleAttribute("hidden", isChart && container.children.length >= 1);
}

function addValueRow(prefill) {
  const container = document.getElementById("rp-crb-values-rows");
  const ds = dataSourcesByKey[state.dataSource];
  if (!container || !ds) return;

  const isChart = CHART_VISUALIZATIONS.includes(state.visualization);
  if (isChart && container.children.length >= 1) return;

  const row = document.createElement("div");
  row.className = "row g-2 align-items-end mb-2";
  row.setAttribute("data-value-row", "");
  row.innerHTML = `
    <div class="col-12 col-md-5">
      <dropdown-field class="rp-crb-value-field" show-label label="Field" placeholder="Select field…">
        <values-list>${ds.fields
          .map(
            (f) =>
              `<value value="${esc(f.key)}"${prefill?.field === f.key ? " selected" : ""}>${esc(f.label)}</value>`,
          )
          .join("")}</values-list>
      </dropdown-field>
    </div>
    <div class="col-12 col-md-5">
      <dropdown-field class="rp-crb-value-aggregation" show-label label="Aggregation">
        <values-list>${AGGREGATIONS.map(
          (a) =>
            `<value value="${a.value}"${prefill?.aggregation === a.value ? " selected" : ""}>${esc(a.label)}</value>`,
        ).join("")}</values-list>
      </dropdown-field>
    </div>
    <div class="col-12 col-md-2">
      <muted-button class="rp-crb-value-remove" label="Remove" prefix-icon="bi-trash3"></muted-button>
    </div>
  `;
  container.appendChild(row);
  row.querySelector(".rp-crb-value-remove")?.addEventListener("click", () => {
    row.remove();
    updateValuesAddButtonState();
  });
  updateValuesAddButtonState();
}

// ---- Fields tab ----

function renderFieldsTab(ds) {
  const container = document.getElementById("rp-crb-fields-container");
  if (!container) return;
  const checkedSet = new Set(state.config.fields || []);
  container.innerHTML = `
    <checkbox-group-field id="rp-crb-fields-group" label="Columns to include">
      ${ds.fields
        .map(
          (f) =>
            `<option-field value="${esc(f.key)}" label="${esc(f.label)}"${checkedSet.has(f.key) ? " checked" : ""}></option-field>`,
        )
        .join("")}
    </checkbox-group-field>
  `;
}

// ---- Axis / Legend tab ----

function renderAxisTab(ds) {
  const container = document.getElementById("rp-crb-axis-container");
  if (!container) return;
  const groupable = ds.fields.filter((f) => f.groupable);
  const showLegend = state.visualization !== "pie";
  container.innerHTML = `
    <div class="row g-3">
      <dropdown-field id="rp-crb-axis" col="col-12 col-md-6" show-label label="Axis / Dimension" placeholder="Select field…">
        <values-list>${groupable
          .map(
            (f) =>
              `<value value="${esc(f.key)}"${state.config.axis === f.key ? " selected" : ""}>${esc(f.label)}</value>`,
          )
          .join("")}</values-list>
      </dropdown-field>
      ${
        showLegend
          ? `<dropdown-field id="rp-crb-legend" col="col-12 col-md-6" show-label label="Legend (optional)" placeholder="None">
        <values-list>
          <value value="">None</value>
          ${groupable
            .map(
              (f) =>
                `<value value="${esc(f.key)}"${state.config.legend === f.key ? " selected" : ""}>${esc(f.label)}</value>`,
            )
            .join("")}
        </values-list>
      </dropdown-field>`
          : ""
      }
    </div>
  `;
}

// ---- Config panel ----

function buildTabsMarkup(visualization) {
  const showAxis = CHART_VISUALIZATIONS.includes(visualization);
  return `
    <tab-panel id="rp-crb-tabs">
      <tab-items>
        <tab-item id="fields" active>
          <tab-header title="Fields" icon="bi-list-check"></tab-header>
          <tab-content><div id="rp-crb-fields-container"></div></tab-content>
        </tab-item>
        <tab-item id="filters">
          <tab-header title="Filters" icon="bi-funnel"></tab-header>
          <tab-content>
            <div id="rp-crb-filters-rows"></div>
            <secondary-button id="rp-crb-filters-add-btn" label="Add filter" prefix-icon="bi-plus-lg" size="sm"></secondary-button>
          </tab-content>
        </tab-item>
        <tab-item id="values">
          <tab-header title="Values" icon="bi-calculator"></tab-header>
          <tab-content>
            <div id="rp-crb-values-rows"></div>
            <secondary-button id="rp-crb-values-add-btn" label="Add value" prefix-icon="bi-plus-lg" size="sm"></secondary-button>
          </tab-content>
        </tab-item>
        ${
          showAxis
            ? `<tab-item id="axis">
          <tab-header title="Axis / Legend" icon="bi-graph-up"></tab-header>
          <tab-content><div id="rp-crb-axis-container"></div></tab-content>
        </tab-item>`
            : ""
        }
      </tab-items>
    </tab-panel>
  `;
}

function renderConfigPanel() {
  const ds = dataSourcesByKey[state.dataSource];
  const panel = document.getElementById("rp-crb-config-panel");
  const emptyPanel = document.getElementById("rp-crb-empty-panel");

  if (!ds) {
    panel?.setAttribute("hidden", "");
    emptyPanel?.removeAttribute("hidden");
    return;
  }
  emptyPanel?.setAttribute("hidden", "");
  panel?.removeAttribute("hidden");

  const container = document.getElementById("rp-crb-tabs-container");
  if (!container) return;
  container.innerHTML = buildTabsMarkup(state.visualization);

  renderFieldsTab(ds);
  document
    .getElementById("rp-crb-filters-add-btn")
    ?.addEventListener("click", () => addFilterRow());
  document.getElementById("rp-crb-values-add-btn")?.addEventListener("click", () => addValueRow());

  (state.config.filters || []).forEach((f) => addFilterRow(f));
  (state.config.values || []).forEach((v) => addValueRow(v));

  if (CHART_VISUALIZATIONS.includes(state.visualization)) {
    renderAxisTab(ds);
  }
  updateValuesAddButtonState();
}

// ---- Data source / visualization change handling ----

function bindDataSourceChange(field) {
  field.addEventListener("change", () => {
    state.dataSource = field.value;
    state.config = { fields: [], filters: [], values: [], axis: "", legend: "" };
    renderConfigPanel();
  });
}

function bindVisualizationChange(field) {
  field.addEventListener("change", () => {
    if (state.dataSource) state.config = readConfigFromForm();
    state.visualization = field.value;
    if (CHART_VISUALIZATIONS.includes(state.visualization) && state.config.values.length > 1) {
      state.config.values = state.config.values.slice(0, 1);
    }
    renderConfigPanel();
  });
}

// ---- Data sources ----

async function loadDataSources() {
  const { href, method } = API_URLS.reports.customDataSources();
  const res = await apiFetch(href, { method });
  const sources = res?.data ?? [];
  dataSourcesByKey = Object.fromEntries(sources.map((s) => [s.key, s]));

  const old = document.getElementById("rp-crb-datasource");
  if (!old) return;

  const valuesListHTML = `<values-list>${sources
    .map(
      (s) =>
        `<value value="${esc(s.key)}"${s.key === state.dataSource ? " selected" : ""}>${esc(s.label)}</value>`,
    )
    .join("")}</values-list>`;

  const wrapper = document.createElement("div");
  wrapper.innerHTML = `<dropdown-field id="rp-crb-datasource" col="col-12 col-md-4" label="Data Source" show-label required placeholder="Select a data source…">${valuesListHTML}</dropdown-field>`;
  const fresh = wrapper.firstElementChild;
  old.replaceWith(fresh);
  fresh.value = state.dataSource;
  bindDataSourceChange(fresh);

  if (!state.canEdit) fresh.setAttribute("disabled", "");
}

// ---- Report load / save / execute ----

async function loadReport(code) {
  const { href, method } = API_URLS.reports.customDetail(code);
  const res = await apiFetch(href, { method });
  const data = res?.data ?? {};

  state.name = data.name ?? "Custom Report";
  state.dataSource = data.data_source || "";
  state.visualization = data.visualization || "table";
  state.config = data.config || { fields: [], filters: [], values: [], axis: "", legend: "" };
  state.canEdit = !data.is_readonly;

  const titleEl = document.getElementById("rp-crb-title");
  if (titleEl) titleEl.textContent = state.name;

  setBreadcrumbs([
    { label: "Reports" },
    { label: "Custom Reports", href: UI_URLS.reports.customList() },
    { label: state.name },
  ]);

  const vizField = document.getElementById("rp-crb-visualization");
  if (vizField) vizField.value = state.visualization;
}

function applyReadonlyMode() {
  if (state.canEdit) return;
  document.getElementById("rp-crb-save-btn")?.setAttribute("hidden", "");
  document.getElementById("rp-crb-share-btn")?.setAttribute("hidden", "");
  document.getElementById("rp-crb-preview-btn")?.setAttribute("hidden", "");
  document.getElementById("rp-crb-visualization")?.setAttribute("disabled", "");
}

function updateExportButtonVisibility() {
  const btn = document.getElementById("rp-crb-export-btn");
  if (!btn) return;
  const canExport = state.visualization === "table" && !!lastResult;
  btn.toggleAttribute("hidden", !canExport);
}

async function executeSavedAndRender() {
  if (!state.dataSource) return;
  try {
    const { href, method } = API_URLS.reports.customExecute(state.code);
    const res = await apiFetch(href, { method, body: JSON.stringify({}) });
    lastResult = res?.data;
    renderResult(lastResult);
    document.getElementById("rp-crb-results")?.removeAttribute("hidden");
    updateExportButtonVisibility();
  } catch {
    // Saved config may reference fields removed from the data source since
    // it was last edited — leave results hidden rather than surface an error.
  }
}

async function runPreview() {
  if (!state.dataSource) {
    toast({
      type: "warning",
      title: "Select a data source",
      message: "Choose a data source before previewing.",
    });
    return;
  }
  state.config = readConfigFromForm();
  document.getElementById("rp-crb-export-btn")?.setAttribute("hidden", "");

  const btn = document.getElementById("rp-crb-preview-btn");
  const snap = snapshotButton(btn);
  setBusyButton(btn, "Running…");
  try {
    const { href, method } = API_URLS.reports.customPreview();
    const res = await apiFetch(href, {
      method,
      body: JSON.stringify({
        data_source: state.dataSource,
        visualization: state.visualization,
        config: state.config,
      }),
    });
    lastResult = res?.data;
    renderResult(lastResult);
    document.getElementById("rp-crb-results")?.removeAttribute("hidden");
  } catch (err) {
    const msg =
      err?.data?.error?.message ?? "Failed to run the report. Please check your configuration.";
    toast({ type: "error", title: "Error", message: msg });
  } finally {
    restoreButton(btn, snap);
  }
}

async function saveReport() {
  if (!state.dataSource) {
    toast({
      type: "warning",
      title: "Select a data source",
      message: "Choose a data source before saving.",
    });
    return;
  }
  const config = readConfigFromForm();
  const payload = {
    data_source: state.dataSource,
    visualization: state.visualization,
    config,
  };

  const btn = document.getElementById("rp-crb-save-btn");
  const snap = snapshotButton(btn);
  setBusyButton(btn, "Saving…");
  try {
    const { href, method } = API_URLS.reports.customUpdate(state.code);
    await apiFetch(href, { method, body: JSON.stringify(payload) });
    state.config = config;
    restoreButton(btn, snap, { label: "Saved", suffixIcon: "bi-check-circle-fill" });
    toast({ type: "success", title: "Report saved", message: "Your changes have been saved." });
    await executeSavedAndRender();
  } catch (err) {
    restoreButton(btn, snap);
    const msg = err?.data?.error?.message ?? "Failed to save the report. Please try again.";
    toast({ type: "error", title: "Error", message: msg });
  }
}

// ---- Export ----

function initExportButton() {
  const exportBtn = document.getElementById("rp-crb-export-btn");
  const exportView = document.getElementById("rp-crb-export-view");
  if (!exportBtn || !exportView) return;

  exportBtn.addEventListener("click", () => {
    const specsHref = `${API_URLS.reports.customExportSpecs().href}?code=${encodeURIComponent(state.code)}`;
    const exportHref = `${API_URLS.reports.customExport().href}?code=${encodeURIComponent(state.code)}`;
    exportView.setAttribute("specs-url", specsHref);
    exportView.setAttribute("export-url", exportHref);
    exportView.show();
  });
}

// ---- Share drawer ----

async function loadShares() {
  const listEl = document.getElementById("rp-crb-share-list");
  if (!listEl) return;
  listEl.innerHTML = `<div class="text-center py-3"><span class="spinner-border spinner-border-sm text-muted"></span></div>`;
  try {
    const { href, method } = API_URLS.reports.customShareList(state.code);
    const res = await apiFetch(href, { method });
    const shares = res?.data ?? [];
    if (!shares.length) {
      listEl.innerHTML = `<p class="small mb-0" style="color:var(--rp-text-muted)">Not shared with anyone yet.</p>`;
      return;
    }
    listEl.innerHTML = shares
      .map(
        (s) => `
      <div class="d-flex justify-content-between align-items-center py-2 border-bottom" data-member-code="${esc(s.member_code)}">
        <div>
          <div class="fw-medium">${esc(s.member_name || s.email)}</div>
          <div class="small" style="color:var(--rp-text-muted)">${esc(s.email)} — ${esc(s.permission)}</div>
        </div>
        <muted-button class="rp-crb-share-remove-btn" label="Remove" prefix-icon="bi-x-lg"></muted-button>
      </div>`,
      )
      .join("");
    listEl.querySelectorAll(".rp-crb-share-remove-btn").forEach((btn) => {
      btn.addEventListener("click", async () => {
        const row = btn.closest("[data-member-code]");
        const memberCode = row?.getAttribute("data-member-code");
        if (!memberCode) return;
        try {
          const { href, method } = API_URLS.reports.customShareDelete(state.code, memberCode);
          await apiFetch(href, { method });
          toast({ type: "success", title: "Removed", message: "Share removed." });
          await loadShares();
        } catch (err) {
          const msg = err?.data?.error?.message ?? "Failed to remove share.";
          toast({ type: "error", title: "Error", message: msg });
        }
      });
    });
  } catch {
    listEl.innerHTML = `<p class="small mb-0" style="color:var(--rp-text-muted)">Unable to load shares.</p>`;
  }
}

function initShareDrawer() {
  const shareBtn = document.getElementById("rp-crb-share-btn");
  const drawer = document.getElementById("rp-crb-share-drawer");
  const addBtn = document.getElementById("rp-crb-share-add-btn");
  if (!shareBtn || !drawer) return;

  shareBtn.addEventListener("click", () => {
    drawer.show();
    loadShares();
  });

  addBtn?.addEventListener("click", async () => {
    const memberField = document.getElementById("rp-crb-share-member");
    const permissionField = document.getElementById("rp-crb-share-permission");
    const memberCode = memberField?.value;
    if (!memberCode) {
      toast({
        type: "warning",
        title: "Select a member",
        message: "Choose who to share this report with.",
      });
      return;
    }
    const snap = snapshotButton(addBtn);
    setBusyButton(addBtn, "Adding…");
    try {
      const { href, method } = API_URLS.reports.customShareCreate(state.code);
      await apiFetch(href, {
        method,
        body: JSON.stringify({
          member_code: memberCode,
          permission: permissionField?.value || "view",
        }),
      });
      restoreButton(addBtn, snap);
      if (memberField) memberField.value = "";
      toast({ type: "success", title: "Shared", message: "The report has been shared." });
      await loadShares();
    } catch (err) {
      restoreButton(addBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to share the report.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ---- Bootstrap ----

document.addEventListener("DOMContentLoaded", async () => {
  const segments = window.location.pathname.split("/").filter(Boolean);
  const code = segments[2];
  if (!code || segments[0] !== "reports" || segments[1] !== "custom") return;

  state.code = code;

  const vizField = document.getElementById("rp-crb-visualization");
  vizField && bindVisualizationChange(vizField);
  document.getElementById("rp-crb-preview-btn")?.addEventListener("click", runPreview);
  document.getElementById("rp-crb-save-btn")?.addEventListener("click", saveReport);
  initExportButton();
  initShareDrawer();

  try {
    await loadReport(code);
    await loadDataSources();
    applyReadonlyMode();

    if (state.dataSource) {
      if (state.canEdit) renderConfigPanel();
      await executeSavedAndRender();
    }
  } catch {
    toast({
      type: "error",
      title: "Error",
      message: "Failed to load this custom report.",
    });
  }
});
