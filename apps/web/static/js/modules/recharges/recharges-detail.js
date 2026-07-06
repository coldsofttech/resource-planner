"use strict";

import { esc } from "../../components/utils.js";
import { formatCurrency } from "../utils/utils.js";
import { API_URLS } from "../main/urls.js";

function formatNum(val) {
  const n = parseFloat(val);
  if (isNaN(n)) return "—";
  return n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function getRechargeCode() {
  // URL shape: /recharges/<code>/
  const parts = window.location.pathname.replace(/\/$/, "").split("/");
  return parts[parts.length - 1] ?? "";
}

window.renderRechargeJiraRow = function renderRechargeJiraRow(row) {
  return `
    <td><code class="rp-mono">${esc(row.jira_id || "—")}</code></td>
    <td>${esc(row.title || "—")}</td>
    <td>${esc(row.team || "—")}</td>
    <td>${esc(row.engineer || "—")}</td>
    <td>${row.label ? `<span class="rp-badge rp-badge-soft">${esc(row.label)}</span>` : "—"}</td>
    <td>${formatNum(row.total_days)}</td>
    <td>${formatCurrency(parseFloat(row.total_cost) || 0)}</td>
  `;
};

document.addEventListener("DOMContentLoaded", () => {
  const code = getRechargeCode();
  if (!code) return;

  const titleEl = document.getElementById("rp-recharge-detail-title");
  if (titleEl) titleEl.textContent = code;

  const table = document.getElementById("rp-recharge-jira-table");
  if (!table) return;

  table.setAttribute("url", API_URLS.recharges.jira(code).href);
  if (typeof table.refresh === "function") table.refresh();
});
