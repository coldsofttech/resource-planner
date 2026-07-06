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
import { API_URLS, UI_URLS } from "../main/urls.js";

let currentSprint = "";
let pendingRecharge = null;

function formatNum(val) {
  const n = parseFloat(val);
  if (isNaN(n)) return "—";
  return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function varianceStyle(val) {
  const n = parseFloat(val);
  if (n > 0) return `style="color:var(--rp-success)"`;
  if (n < 0) return `style="color:var(--rp-danger)"`;
  return "";
}

function renderContactBadges(contacts) {
  if (!contacts || contacts.length === 0) return `<span style="color:var(--rp-muted)">—</span>`;
  return contacts
    .map((c) => {
      const name = esc(c.name || c.email || "Unknown");
      const email = esc(c.email || "");
      return `<span class="rp-badge rp-badge-soft me-1 mb-1" title="${email}"><i class="bi bi-envelope-fill me-1" aria-hidden="true"></i>${name}</span>`;
    })
    .join("");
}

window.renderRechargesByTypeRow = function renderRechargesByTypeRow(row) {
  return `
    <td>${esc(row.type_name || "—")}</td>
    <td>${formatNum(row.forecast_days)}</td>
    <td>${formatCurrency(parseFloat(row.forecast_cost) || 0)}</td>
    <td>${formatNum(row.actual_days)}</td>
    <td>${formatCurrency(parseFloat(row.actual_cost) || 0)}</td>
    <td ${varianceStyle(row.variance_days)}>${formatNum(row.variance_days)}</td>
    <td ${varianceStyle(row.variance_cost)}>${formatCurrency(parseFloat(row.variance_cost) || 0)}</td>
  `;
};

window.renderRechargeRow = function renderRechargeRow(row) {
  return `
    <td>${esc(row.programme_name || "—")}</td>
    <td>${esc(row.project_name || "—")}</td>
    <td>${formatNum(row.total_days)}</td>
    <td>${formatCurrency(parseFloat(row.total_cost) || 0)}</td>
    <td>${renderContactBadges(row.project_contacts)}</td>
    <td>${renderContactBadges(row.finance_contacts)}</td>
  `;
};

window.renderRechargeDetailEngineerRow = function renderRechargeDetailEngineerRow(row) {
  return `
    <td>${esc(row.team || "—")}</td>
    <td>${esc(row.engineer || "—")}</td>
    <td>${formatNum(row.total_days)}</td>
    <td>${formatCurrency(parseFloat(row.total_cost) || 0)}</td>
  `;
};

window.renderRechargeDetailTeamRow = function renderRechargeDetailTeamRow(row) {
  return `
    <td>${esc(row.team || "—")}</td>
    <td>${formatNum(row.total_days)}</td>
    <td>${formatCurrency(parseFloat(row.total_cost) || 0)}</td>
  `;
};

window.renderRechargeDetailLabelRow = function renderRechargeDetailLabelRow(row) {
  return `
    <td>${esc(row.label || "—")}</td>
    <td>${formatNum(row.total_days)}</td>
    <td>${formatCurrency(parseFloat(row.total_cost) || 0)}</td>
  `;
};

function loadDrawerTab(code, groupBy, tableId) {
  const table = document.getElementById(tableId);
  if (!table) return;
  table.setAttribute("url", API_URLS.recharges.details(code, groupBy).href);
  if (typeof table.refresh === "function") table.refresh();
}

function openRechargeDrawer(row) {
  const drawer = document.getElementById("rp-recharge-view-drawer");
  if (!drawer) return;

  pendingRecharge = row;

  // Update header title dynamically via the component's API
  drawer.setTitle(row.project_name || row.code);

  // Update eyebrow and footer meta in-place (both exist in DOM after first render)
  const eyebrow = drawer.querySelector(".rp-rdrawer-eyebrow");
  if (eyebrow) eyebrow.textContent = row.programme_name || "Recharge";

  const footerMeta = drawer.querySelector(".rp-rdrawer-foot-meta");
  if (footerMeta) footerMeta.textContent = row.code || "";

  const tabs = document.getElementById("rp-recharge-detail-tabs");
  if (tabs && typeof tabs.setTab === "function") tabs.setTab("by-engineer");

  loadDrawerTab(row.code, "engineer", "rp-recharge-detail-engineer-table");
  loadDrawerTab(row.code, "team", "rp-recharge-detail-team-table");
  loadDrawerTab(row.code, "label", "rp-recharge-detail-label-table");

  drawer.show();
}

function initViewDrawer() {
  const forecastTable = document.getElementById("rp-recharges-forecast-table");
  const actualsTable = document.getElementById("rp-recharges-actuals-table");
  const drawer = document.getElementById("rp-recharge-view-drawer");

  function onRowClick(tableEl) {
    if (!tableEl) return;
    tableEl.addEventListener("click", (e) => {
      if (e.target.closest("[data-rp-action]") || e.target.closest(".rp-table-more-btn")) return;
      const tr = e.target.closest("tr[data-rp-row]");
      if (!tr) return;
      const idx = parseInt(tr.getAttribute("data-rp-row"), 10);
      const row = tableEl.rows?.[idx];
      if (!row) return;
      openRechargeDrawer(row);
    });
  }

  onRowClick(forecastTable);
  onRowClick(actualsTable);

  if (drawer) {
    drawer.addEventListener("rp:footer-secondary", () => {
      if (!pendingRecharge) return;
      window.location.href = UI_URLS.recharges.detail(pendingRecharge.code);
    });
  }
}

function renderSummaryCards(summary) {
  const setText = (id, text) => {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  };

  setText("rp-recharges-forecast-cost", formatCurrency(parseFloat(summary.forecast_cost) || 0));
  setText("rp-recharges-forecast-days", `${formatNum(summary.forecast_days)} days`);
  setText("rp-recharges-actual-cost", formatCurrency(parseFloat(summary.actual_cost) || 0));
  setText("rp-recharges-actual-days", `${formatNum(summary.actual_days)} days`);

  const vcEl = document.getElementById("rp-recharges-variance-cost");
  const vdEl = document.getElementById("rp-recharges-variance-days");
  if (vcEl) {
    const vc = parseFloat(summary.variance_cost);
    vcEl.textContent = formatCurrency(vc || 0);
    vcEl.style.color = vc > 0 ? "var(--rp-success)" : vc < 0 ? "var(--rp-danger)" : "";
  }
  if (vdEl) {
    const vd = parseFloat(summary.variance_days);
    vdEl.textContent = `${formatNum(summary.variance_days)} days`;
    vdEl.style.color = vd > 0 ? "var(--rp-success)" : vd < 0 ? "var(--rp-danger)" : "";
  }
}

async function loadRecharges(sprintCode, showBtn) {
  const snap = snapshotButton(showBtn);
  setBusyButton(showBtn, "Loading…");

  try {
    const { href: summaryHref } = API_URLS.recharges.summary(sprintCode);
    const res = await apiFetch(summaryHref);
    const data = res?.data ?? res;

    renderSummaryCards(data.summary ?? {});

    const typeTable = document.getElementById("rp-recharges-type-table");
    if (typeTable) {
      typeTable.setAttribute("url", summaryHref);
      if (typeof typeTable.refresh === "function") typeTable.refresh();
    }

    const forecastTable = document.getElementById("rp-recharges-forecast-table");
    if (forecastTable) {
      forecastTable.setAttribute("url", API_URLS.recharges.list(sprintCode, "forecast").href);
      if (typeof forecastTable.refresh === "function") forecastTable.refresh();
    }

    const actualsTable = document.getElementById("rp-recharges-actuals-table");
    if (actualsTable) {
      actualsTable.setAttribute("url", API_URLS.recharges.list(sprintCode, "actual").href);
      if (typeof actualsTable.refresh === "function") actualsTable.refresh();
    }

    const results = document.getElementById("rp-recharges-results");
    if (results) results.removeAttribute("hidden");

    // Enable Email Review buttons now that sprint is loaded
    const forecastEmailBtn = document.getElementById("rp-recharges-forecast-email-btn");
    if (forecastEmailBtn) forecastEmailBtn.removeAttribute("disabled");
    const actualsEmailBtn = document.getElementById("rp-recharges-actuals-email-btn");
    if (actualsEmailBtn) actualsEmailBtn.removeAttribute("disabled");

    restoreButton(showBtn, snap);
  } catch (err) {
    restoreButton(showBtn, snap);
    const msg = err?.data?.error?.message ?? "Failed to load recharge data.";
    toast({ type: "error", title: "Error", message: msg });
  }
}

function initFilters() {
  const fyField = document.getElementById("rp-recharges-fy");
  const sprintField = document.getElementById("rp-recharges-sprint");
  const showBtn = document.getElementById("rp-recharges-show-btn");

  if (!fyField || !sprintField || !showBtn) return;

  fyField.addEventListener("change", () => {
    const fy = fyField.value;
    if (fy) {
      sprintField.setAttribute("fy-code", fy);
    } else {
      sprintField.removeAttribute("fy-code");
    }
  });

  showBtn.addEventListener("click", () => {
    const sprint = sprintField.value;
    if (!sprint) {
      toast({ type: "warning", title: "Sprint required", message: "Please select a sprint." });
      return;
    }
    currentSprint = sprint;
    loadRecharges(sprint, showBtn);
  });
}

function initProjectGroupsBtn() {
  const btn = document.getElementById("rp-recharges-project-groups-btn");
  if (!btn) return;
  btn.addEventListener("click", () => {
    window.location.href = UI_URLS.recharges.projectGroups();
  });
}

function initEmailReviewButtons() {
  const forecastBtn = document.getElementById("rp-recharges-forecast-email-btn");
  if (forecastBtn) {
    forecastBtn.addEventListener("click", () => {
      if (!currentSprint) return;
      window.location.href = UI_URLS.recharges.emailReviewForecasts(currentSprint);
    });
  }

  const actualsBtn = document.getElementById("rp-recharges-actuals-email-btn");
  if (actualsBtn) {
    actualsBtn.addEventListener("click", () => {
      if (!currentSprint) return;
      window.location.href = UI_URLS.recharges.emailReviewActuals(currentSprint);
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initFilters();
  initViewDrawer();
  initProjectGroupsBtn();
  initEmailReviewButtons();
});
