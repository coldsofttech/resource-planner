"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import { apiFetch, formatDate } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";
import { hasPermission } from "../utils/index.js";

const roleCode = window.location.pathname.split("/").filter(Boolean)[1];

window.renderRoleMembersRow = function renderRoleMembersRow(row) {
  const name = row.display_name || row.email;
  const location = row.location?.label || "—";
  const empType = row.employment_type?.label || "—";

  return `
    <td><user-avatar avatar-url="${esc(row.avatar_url || "")}" name="${esc(name)}" size="sm"></user-avatar></td>
    <td class="fw-medium">${esc(name)}</td>
    <td style="color:var(--rp-text-muted)">${esc(row.email)}</td>
    <td style="color:var(--rp-text-muted)">${esc(location)}</td>
    <td style="color:var(--rp-text-muted)">${esc(empType)}</td>
  `;
};

async function loadRoleDetails() {
  try {
    const { href, method } = API_URLS.roles.detail(roleCode);
    const resp = await apiFetch(href, { method });
    const role = resp?.data ?? null;
    if (!role) return;

    const titleEl = document.getElementById("rp-role-detail-title");
    if (titleEl) titleEl.textContent = role.role;

    setBreadcrumbs([
      { label: "Organisation" },
      { label: "Configurations" },
      { label: "Roles", href: UI_URLS.roles.list() },
      { label: role.role },
    ]);

    const setView = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.value = val || "—";
    };

    setView("rp-role-detail-name", role.role);
    setView("rp-role-detail-code", role.code);

    const statusEl = document.getElementById("rp-role-detail-status");
    if (statusEl) {
      statusEl.setAttribute(
        "badge",
        role.is_active ? "rp-badge rp-badge-soft rp-badge-success" : "rp-badge rp-badge-soft",
      );
      statusEl.value = role.is_active ? "Active" : "Inactive";
    }

    const defaultEl = document.getElementById("rp-role-detail-default");
    if (defaultEl) {
      if (role.is_default) {
        defaultEl.setAttribute("badge", "rp-badge rp-badge-soft");
        defaultEl.value = "Default";
      } else {
        defaultEl.removeAttribute("badge");
        defaultEl.value = "—";
      }
    }

    const yesNo = (val) => (val ? "Yes" : "No");
    setView("rp-role-detail-assignable", yesNo(role.is_assignable));
    setView("rp-role-detail-leadership", yesNo(role.is_leadership));
    setView("rp-role-detail-created", formatDate(role.created_at));
    setView("rp-role-detail-created-by", role.created_by?.email ?? "—");
  } catch {
    toast({
      type: "error",
      title: "Could not load role",
      message: "Refresh the page to retry.",
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (!roleCode) return;
  loadRoleDetails();
  if (hasPermission("auth.view_user")) {
    document.getElementById("rp-role-members-col")?.removeAttribute("hidden");
  }

  const membersTable = document.getElementById("rp-role-members-table");
  if (membersTable) {
    membersTable.addEventListener("rp:data:loaded", (e) => {
      const count = e.detail.pagination?.total_count ?? e.detail.rows?.length ?? 0;
      const countEl = document.getElementById("rp-role-members-count");
      if (countEl) countEl.textContent = `(${count})`;
    });
  }
});
