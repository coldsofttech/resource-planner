"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import { apiFetch, formatDate } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";
import { hasPermission } from "../utils/index.js";

const buCode = window.location.pathname.split("/").filter(Boolean)[1];

window.renderBuProductsRow = function renderBuProductsRow(row) {
  const badgeCls = row.is_active ? "rp-badge-soft rp-badge-success" : "rp-badge-soft";
  const statusLabel = row.is_active ? "Active" : "Inactive";

  return `
    <td><identicon-field name="${esc(row.name)}" variant="monogram" no-border></identicon-field></td>
    <td class="fw-medium">${esc(row.name)}</td>
    <td><code class="rp-mono">${esc(row.code)}</code></td>
    <td style="color:var(--rp-text-muted)">${esc(row.short_name || "—")}</td>
    <td><span class="rp-badge ${badgeCls}">${statusLabel}</span></td>
  `;
};

async function loadBuDetails() {
  try {
    const { href, method } = API_URLS.businessUnits.detail(buCode);
    const resp = await apiFetch(href, { method });
    const bu = resp?.data ?? null;
    if (!bu) return;

    const titleEl = document.getElementById("rp-bu-detail-title");
    if (titleEl) titleEl.textContent = bu.name;

    setBreadcrumbs([
      { label: "Organisations" },
      { label: "Structure" },
      { label: "Business Units", href: UI_URLS.businessUnits.list() },
      { label: bu.name },
    ]);

    const setView = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.value = val || "—";
    };

    setView("rp-bu-detail-name", bu.name);
    setView("rp-bu-detail-short-name", bu.short_name);
    setView("rp-bu-detail-code", bu.code);

    const statusEl = document.getElementById("rp-bu-detail-status");
    if (statusEl) {
      statusEl.setAttribute(
        "badge",
        bu.is_active ? "rp-badge rp-badge-soft rp-badge-success" : "rp-badge rp-badge-soft",
      );
      statusEl.value = bu.is_active ? "Active" : "Inactive";
    }

    setView("rp-bu-detail-created", formatDate(bu.created_at));
    setView("rp-bu-detail-created-by", bu.created_by?.email ?? "—");
  } catch {
    toast({
      type: "error",
      title: "Could not load business unit",
      message: "Refresh the page to retry.",
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (!buCode) return;
  loadBuDetails();
  if (hasPermission("products.view_product")) {
    document.getElementById("rp-bu-products-col")?.removeAttribute("hidden");
  }
});
