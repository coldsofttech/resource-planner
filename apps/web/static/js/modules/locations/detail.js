"use strict";

import { esc } from "../../components/utils.js";
import { apiFetch, formatDate } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";
import { hasPermission } from "../utils/index.js";

const locationCode = window.location.pathname.split("/").filter(Boolean)[1];

window.renderLocationMembersRow = function renderLocationMembersRow(row) {
  const name = row.display_name || row.email;
  const role = row.role?.label || "—";
  const empType = row.employment_type?.label || "—";

  return `
    <td><user-avatar avatar-url="${esc(row.avatar_url || "")}" name="${esc(name)}" size="sm"></user-avatar></td>
    <td class="fw-medium">${esc(name)}</td>
    <td style="color:var(--rp-text-muted)">${esc(row.email)}</td>
    <td style="color:var(--rp-text-muted)">${esc(role)}</td>
    <td style="color:var(--rp-text-muted)">${esc(empType)}</td>
  `;
};

async function loadLocationDetails() {
  try {
    const { href, method } = API_URLS.locations.detail(locationCode);
    const resp = await apiFetch(href, { method });
    const location = resp?.data ?? null;
    if (!location) return;

    const label = `${location.city}, ${location.country}`;

    const titleEl = document.getElementById("rp-location-detail-title");
    if (titleEl) titleEl.textContent = label;

    const breadcrumbs = document.getElementById("app-breadcrumbs");
    if (breadcrumbs?.setCrumbs) {
      breadcrumbs.setCrumbs([{ label: "Locations", href: UI_URLS.locations.list() }, { label }]);
    }

    const setView = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.value = val || "—";
    };

    setView("rp-location-detail-city", location.city);
    setView("rp-location-detail-country", location.country);
    setView("rp-location-detail-code", location.code);

    const statusEl = document.getElementById("rp-location-detail-status");
    if (statusEl) {
      statusEl.setAttribute(
        "badge",
        location.is_active ? "rp-badge rp-badge-soft rp-badge-success" : "rp-badge rp-badge-soft",
      );
      statusEl.value = location.is_active ? "Active" : "Inactive";
    }

    setView("rp-location-detail-created", formatDate(location.created_at));
    setView("rp-location-detail-created-by", location.created_by?.email ?? "—");
  } catch {
    toast({
      type: "error",
      title: "Could not load location",
      message: "Refresh the page to retry.",
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadLocationDetails();
  if (hasPermission("auth.view_user")) {
    document.getElementById("rp-location-members-col")?.removeAttribute("hidden");
  }
});
