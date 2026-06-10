"use strict";

import { esc } from "../../components/utils.js";
import { apiFetch, formatDate } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";
import { hasPermission } from "../utils/index.js";

const empTypeCode = window.location.pathname.split("/").filter(Boolean)[1];

window.renderEmpTypeMembersRow = function renderEmpTypeMembersRow(row) {
  const name = row.display_name || row.email;
  const role = row.role?.label || "—";
  const location = row.location?.label || "—";

  return `
    <td><user-avatar avatar-url="${esc(row.avatar_url || "")}" name="${esc(name)}" size="sm"></user-avatar></td>
    <td class="fw-medium">${esc(name)}</td>
    <td style="color:var(--rp-text-muted)">${esc(row.email)}</td>
    <td style="color:var(--rp-text-muted)">${esc(role)}</td>
    <td style="color:var(--rp-text-muted)">${esc(location)}</td>
  `;
};

async function loadEmpTypeDetails() {
  try {
    const { href, method } = API_URLS.empTypes.detail(empTypeCode);
    const resp = await apiFetch(href, { method });
    const empType = resp?.data ?? null;
    if (!empType) return;

    const titleEl = document.getElementById("rp-emp-type-detail-title");
    if (titleEl) titleEl.textContent = empType.name;

    const breadcrumbs = document.getElementById("app-breadcrumbs");
    if (breadcrumbs?.setCrumbs) {
      breadcrumbs.setCrumbs([
        { label: "Employment Types", href: UI_URLS.empTypes.list() },
        { label: empType.name },
      ]);
    }

    const setView = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.value = val || "—";
    };

    setView("rp-emp-type-detail-name", empType.name);
    setView("rp-emp-type-detail-code", empType.code);

    const statusEl = document.getElementById("rp-emp-type-detail-status");
    if (statusEl) {
      statusEl.setAttribute(
        "badge",
        empType.is_active ? "rp-badge rp-badge-soft rp-badge-success" : "rp-badge rp-badge-soft",
      );
      statusEl.value = empType.is_active ? "Active" : "Inactive";
    }

    setView("rp-emp-type-detail-created", formatDate(empType.created_at));
    setView("rp-emp-type-detail-created-by", empType.created_by?.email ?? "—");
  } catch {
    toast({
      type: "error",
      title: "Could not load employment type",
      message: "Refresh the page to retry.",
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadEmpTypeDetails();
  if (hasPermission("auth.view_user")) {
    document.getElementById("rp-emp-type-members-col")?.removeAttribute("hidden");
  }
});
