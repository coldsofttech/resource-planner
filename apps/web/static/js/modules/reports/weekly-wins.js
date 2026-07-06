"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import { apiFetch } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

let currentMode = "week";

const STATUS_BADGES = {
  open: { cls: "rp-badge-soft rp-badge-info", label: "Open" },
  review_complete: { cls: "rp-badge-soft rp-badge-warning", label: "Review Complete" },
  closed: { cls: "rp-badge-soft", label: "Closed" },
};

window.renderWeeklyWinsRow = function renderWeeklyWinsRow(row) {
  const badge = STATUS_BADGES[row.status] || STATUS_BADGES.open;
  const weekCells =
    currentMode === "date"
      ? `
        <td>${esc(row.week)}</td>
        <td style="color:var(--rp-text-muted)">${esc(row.date_range)}</td>
      `
      : "";

  return `
    <td class="fw-medium">${esc(row.team)}</td>
    ${weekCells}
    <td>${esc(row.title)}</td>
    <td style="color:var(--rp-text-muted)">${esc(row.description || "—")}</td>
    <td><span class="rp-badge ${badge.cls}">${esc(row.status_display)}</span></td>
  `;
};

function buildTableMarkup(mode) {
  const weekColumns =
    mode === "date"
      ? `
        <table-column label="Week" key="week"></table-column>
        <table-column label="Date Range" key="date_range" hide-mobile></table-column>
      `
      : "";

  return `
    <data-table id="rp-weekly-wins-table" row-template="renderWeeklyWinsRow" empty-message="No wins recorded for this week.">
      <table-columns>
        <table-column label="Team" key="team"></table-column>
        ${weekColumns}
        <table-column label="Title" key="title"></table-column>
        <table-column label="Description" key="description" hide-mobile></table-column>
        <table-column label="Status" key="status_display"></table-column>
      </table-columns>
    </data-table>
  `;
}

function toggleModeFields(isDateMode) {
  const weekWrapper = document.getElementById("rp-weekly-wins-week-wrapper");
  const dateWrapper = document.getElementById("rp-weekly-wins-date-wrapper");
  if (weekWrapper) weekWrapper.style.display = isDateMode ? "none" : "";
  if (dateWrapper) dateWrapper.style.display = isDateMode ? "" : "none";
}

function buildQuery() {
  if (currentMode === "date") {
    const dateField = document.getElementById("rp-weekly-wins-date");
    return { mode: "date", date: dateField?.value ?? "" };
  }
  const weekField = document.getElementById("rp-weekly-wins-week");
  return { mode: "week", win: weekField?.value ?? "" };
}

function validateActiveField() {
  const fieldId = currentMode === "date" ? "rp-weekly-wins-date" : "rp-weekly-wins-week";
  const field = document.getElementById(fieldId);
  field?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
  return !field?.querySelector("[data-rp-error]:not([hidden])");
}

async function loadReport() {
  if (!validateActiveField()) return;

  const query = buildQuery();
  const params = new URLSearchParams(query);
  const { href, method } = API_URLS.reports.weeklyWinsData();

  const loadBtn = document.getElementById("rp-weekly-wins-load-btn");
  loadBtn?.setAttribute("disabled", "");

  try {
    const res = await apiFetch(`${href}?${params.toString()}`, { method });
    const data = res?.data ?? {};

    const rangeLabel = document.getElementById("rp-weekly-wins-range-label");
    if (rangeLabel) rangeLabel.textContent = data.win?.date_range ?? "";

    const container = document.getElementById("rp-weekly-wins-table-container");
    if (container) {
      container.innerHTML = buildTableMarkup(currentMode);
      const table = document.getElementById("rp-weekly-wins-table");
      if (table) table.rows = data.entries ?? [];
    }

    document.getElementById("rp-weekly-wins-results-panel")?.removeAttribute("hidden");
    document.getElementById("rp-weekly-wins-export-btn")?.removeAttribute("hidden");
  } catch (err) {
    const msg =
      err?.data?.error?.message ?? "Failed to load the Weekly Wins report. Please try again.";
    toast({ type: "error", title: "Error", message: msg });
  } finally {
    loadBtn?.removeAttribute("disabled");
  }
}

function initExport() {
  const exportBtn = document.getElementById("rp-weekly-wins-export-btn");
  const exportView = document.getElementById("rp-weekly-wins-export-view");
  if (!exportBtn || !exportView) return;

  exportView.setAttribute("specs-url", API_URLS.reports.weeklyWinsExportSpecs().href);

  exportBtn.addEventListener("click", () => {
    const query = buildQuery();
    const params = new URLSearchParams(query);
    const baseHref = API_URLS.reports.weeklyWinsExport().href;
    exportView.setAttribute("export-url", `${baseHref}?${params.toString()}`);
    exportView.show();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const modeToggle = document.getElementById("rp-weekly-wins-mode");
  if (!modeToggle) return;

  setBreadcrumbs([
    { label: "Reports" },
    { label: "Standard Reports", href: UI_URLS.reports.standardList() },
    { label: "Weekly Wins" },
  ]);

  modeToggle.addEventListener("change", () => {
    currentMode = modeToggle.checked ? "date" : "week";
    toggleModeFields(modeToggle.checked);
    document.getElementById("rp-weekly-wins-results-panel")?.setAttribute("hidden", "");
    document.getElementById("rp-weekly-wins-export-btn")?.setAttribute("hidden", "");
  });

  document.getElementById("rp-weekly-wins-load-btn")?.addEventListener("click", loadReport);

  initExport();
});
