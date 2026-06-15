"use strict";

import { esc } from "../../components/utils.js";
import { API_URLS } from "../main/urls.js";

function formatDate(val) {
  if (!val) return "—";
  return new Date(val).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function formatUser(user) {
  if (!user) return "—";
  return esc(user.email ?? "");
}

window.renderTagRow = function renderTagRow(row) {
  return `
    <td><span class="rp-tag-pill">${esc(row.name)}</span></td>
    <td class="hide-mobile"><span class="rp-mono">${esc(row.code)}</span></td>
    <td class="hide-mobile">${formatDate(row.created_at)}</td>
    <td class="hide-mobile">${formatUser(row.created_by)}</td>
  `;
};

function initExportView() {
  const exportView = document.getElementById("rp-tags-export-view");
  const exportBtn = document.getElementById("rp-tags-export-btn");
  if (!exportView || !exportBtn) return;

  exportView.setAttribute("specs-url", API_URLS.tags.exportSpecs().href);
  exportView.setAttribute("export-url", API_URLS.tags.export().href);

  exportBtn.addEventListener("click", () => exportView.show());
}

document.addEventListener("DOMContentLoaded", () => {
  initExportView();
});
