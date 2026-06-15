"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import { apiFetch, formatDate } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";
import { hasPermission } from "../utils/index.js";

const teamCode = window.location.pathname.split("/").filter(Boolean)[1];

window.renderTeamMembersRow = function renderTeamMembersRow(row) {
  const name =
    row.display_name || [row.first_name, row.last_name].filter(Boolean).join(" ") || row.email;
  const role = row.role?.label || "—";
  const statusBadge = row.is_active
    ? `<span class="rp-badge rp-badge-success">Active</span>`
    : `<span class="rp-badge rp-badge-soft">Inactive</span>`;

  return `
    <td><user-avatar avatar-url="${esc(row.avatar_url || "")}" name="${esc(name)}" size="sm"></user-avatar></td>
    <td class="fw-medium">${esc(name)}</td>
    <td style="color:var(--rp-text-muted)">${esc(row.email)}</td>
    <td style="color:var(--rp-text-muted)">${esc(role)}</td>
    <td>${statusBadge}</td>
  `;
};

async function loadTeamDetails() {
  try {
    const { href, method } = API_URLS.teams.detail(teamCode);
    const resp = await apiFetch(href, { method });
    const team = resp?.data ?? null;
    if (!team) return;

    const titleEl = document.getElementById("rp-team-detail-title");
    if (titleEl) titleEl.textContent = team.name;

    setBreadcrumbs([
      { label: "Organisation" },
      { label: "People" },
      { label: "Teams", href: UI_URLS.teams.list() },
      { label: team.name },
    ]);

    const setView = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.value = val || "—";
    };

    setView("rp-team-detail-name", team.name);
    setView("rp-team-detail-code", team.code);

    const statusEl = document.getElementById("rp-team-detail-status");
    if (statusEl) {
      statusEl.setAttribute(
        "badge",
        team.is_active ? "rp-badge rp-badge-soft rp-badge-success" : "rp-badge rp-badge-soft",
      );
      statusEl.value = team.is_active ? "Active" : "Inactive";
    }

    setView("rp-team-detail-desc", team.description || "—");
    setView("rp-team-detail-created", formatDate(team.created_at));
    setView("rp-team-detail-created-by", team.created_by?.email ?? "—");
  } catch {
    toast({
      type: "error",
      title: "Could not load team",
      message: "Refresh the page to retry.",
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (!teamCode) return;
  loadTeamDetails();
  if (hasPermission("auth.view_user")) {
    document.getElementById("rp-team-members-col")?.removeAttribute("hidden");
  }
});
