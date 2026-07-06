"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import { apiFetch } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

const STATUS_BADGES = {
  draft: { cls: "rp-badge-soft", label: "Draft" },
  phase_1_open: { cls: "rp-badge-soft rp-badge-info", label: "Phase 1 Open" },
  phase_1_closed: { cls: "rp-badge-soft rp-badge-warning", label: "Phase 1 Closed" },
  phase_2_open: { cls: "rp-badge-soft rp-badge-info", label: "Phase 2 Open" },
  phase_2_closed: { cls: "rp-badge-soft rp-badge-warning", label: "Phase 2 Closed" },
  wins_declared: { cls: "rp-badge-soft rp-badge-success", label: "Wins Declared" },
};

window.renderMonthlyWinsPhase1Row = function renderMonthlyWinsPhase1Row(row) {
  const badge = STATUS_BADGES[row.status] || STATUS_BADGES.draft;

  return `
    <td class="fw-medium">${esc(row.label)}</td>
    <td>${esc(row.phase1_votes)}</td>
    <td><span class="rp-badge ${badge.cls}">${esc(row.status_display)}</span></td>
    <td>${esc(row.team)}</td>
    <td style="color:var(--rp-text-muted)">${esc(row.week)}</td>
    <td style="color:var(--rp-text-muted)">${esc(row.date_range)}</td>
    <td style="color:var(--rp-text-muted)">${esc(row.win)}</td>
    <td>${esc(row.category_display)}</td>
  `;
};

function renderPhase2Category(containerId, categoryData) {
  const container = document.getElementById(containerId);
  if (!container) return;

  const entries = categoryData?.entries ?? [];
  if (!entries.length) {
    container.innerHTML = `<p class="small mb-0" style="color:var(--rp-text-muted)">No wins selected yet.</p>`;
    return;
  }

  const items = entries
    .map((e) => `<li>${esc(e.team)}: ${esc(e.title)}: ${esc(e.description)}</li>`)
    .join("");
  container.innerHTML = `<ol class="mb-0 ps-3">${items}</ol>`;
}

function validateActiveField() {
  const field = document.getElementById("rp-monthly-wins-select");
  field?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
  return !field?.querySelector("[data-rp-error]:not([hidden])");
}

async function loadReport() {
  if (!validateActiveField()) return;

  const field = document.getElementById("rp-monthly-wins-select");
  const code = field?.value ?? "";
  const { href, method } = API_URLS.reports.monthlyWinsData();

  const loadBtn = document.getElementById("rp-monthly-wins-load-btn");
  loadBtn?.setAttribute("disabled", "");

  try {
    const params = new URLSearchParams({ code });
    const res = await apiFetch(`${href}?${params.toString()}`, { method });
    const data = res?.data ?? {};

    const table = document.getElementById("rp-monthly-wins-phase1-table");
    if (table) table.rows = data.phase1 ?? [];

    renderPhase2Category("rp-monthly-wins-phase2-delivery", data.phase2?.delivery);
    renderPhase2Category(
      "rp-monthly-wins-phase2-operational_excellence",
      data.phase2?.operational_excellence,
    );

    document.getElementById("rp-monthly-wins-results-container")?.removeAttribute("hidden");
    document.getElementById("rp-monthly-wins-export-btn")?.removeAttribute("hidden");
  } catch (err) {
    const msg =
      err?.data?.error?.message ?? "Failed to load the Monthly Wins report. Please try again.";
    toast({ type: "error", title: "Error", message: msg });
  } finally {
    loadBtn?.removeAttribute("disabled");
  }
}

function initExport() {
  const exportBtn = document.getElementById("rp-monthly-wins-export-btn");
  const exportView = document.getElementById("rp-monthly-wins-export-view");
  if (!exportBtn || !exportView) return;

  exportView.setAttribute("specs-url", API_URLS.reports.monthlyWinsExportSpecs().href);

  exportBtn.addEventListener("click", () => {
    const field = document.getElementById("rp-monthly-wins-select");
    const params = new URLSearchParams({ code: field?.value ?? "" });
    const baseHref = API_URLS.reports.monthlyWinsExport().href;
    exportView.setAttribute("export-url", `${baseHref}?${params.toString()}`);
    exportView.show();
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const selectField = document.getElementById("rp-monthly-wins-select");
  if (!selectField) return;

  setBreadcrumbs([
    { label: "Reports" },
    { label: "Standard Reports", href: UI_URLS.reports.standardList() },
    { label: "Monthly Wins" },
  ]);

  document.getElementById("rp-monthly-wins-load-btn")?.addEventListener("click", loadReport);

  selectField.addEventListener("change", () => {
    document.getElementById("rp-monthly-wins-results-container")?.setAttribute("hidden", "");
    document.getElementById("rp-monthly-wins-export-btn")?.setAttribute("hidden", "");
  });

  initExport();
});
