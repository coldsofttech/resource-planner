"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import { apiFetch } from "../utils/utils.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

function buildReportCard(report) {
  const description = report.description
    ? `<p class="small mb-0" style="color:var(--rp-text-muted)">${esc(report.description)}</p>`
    : "";

  const col = document.createElement("div");
  col.className = "col-12 col-md-6 col-lg-4";

  const card = document.createElement("a");
  card.className = "rp-card rp-card-link p-3 h-100 d-block";
  card.href = `${UI_URLS.reports.standardList()}${report.slug}/`;
  card.innerHTML = `
    <div class="d-flex align-items-center gap-2 mb-2">
      <identicon-field name="${esc(report.slug)}" label="${esc(report.name)}" variant="bars" no-border></identicon-field>
      <span class="fw-bold">${esc(report.name)}</span>
    </div>
    ${description}
  `;

  col.appendChild(card);
  return col;
}

async function loadStandardReports() {
  const container = document.getElementById("rp-reports-standard-cards");
  if (!container) return;

  try {
    const { href, method } = API_URLS.reports.standardList();
    const res = await apiFetch(`${href}?page_size=100`, { method });
    const reports = res?.data?.results ?? [];

    if (!reports.length) {
      container.innerHTML = `<div class="col-12 text-center py-5" style="color:var(--rp-text-muted)">No standard reports available yet.</div>`;
      return;
    }

    container.innerHTML = "";
    reports.forEach((report) => container.appendChild(buildReportCard(report)));
  } catch {
    container.innerHTML = `<div class="col-12 text-center py-5" style="color:var(--rp-text-muted)">Unable to load standard reports.</div>`;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("rp-reports-standard-cards");
  if (!container) return;

  setBreadcrumbs([
    { label: "Reports" },
    { label: "Standard Reports", href: UI_URLS.reports.standardList() },
  ]);

  loadStandardReports();
});
