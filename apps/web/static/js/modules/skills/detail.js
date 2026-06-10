"use strict";

import { esc } from "../../components/utils.js";
import { apiFetch, formatDate } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";
import { hasPermission } from "../utils/index.js";

const skillCode = window.location.pathname.split("/").filter(Boolean)[1];

window.renderSkillMembersRow = function renderSkillMembersRow(row) {
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

async function loadSkillDetails() {
  try {
    const { href, method } = API_URLS.skills.detail(skillCode);
    const resp = await apiFetch(href, { method });
    const skill = resp?.data ?? null;
    if (!skill) return;

    const titleEl = document.getElementById("rp-skill-detail-title");
    if (titleEl) titleEl.textContent = skill.skill;

    const breadcrumbs = document.getElementById("app-breadcrumbs");
    if (breadcrumbs?.setCrumbs) {
      breadcrumbs.setCrumbs([
        { label: "Skills", href: UI_URLS.skills.list() },
        { label: skill.skill },
      ]);
    }

    const setView = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.value = val || "—";
    };

    setView("rp-skill-detail-name", skill.skill);
    setView("rp-skill-detail-code", skill.code);

    const statusEl = document.getElementById("rp-skill-detail-status");
    if (statusEl) {
      statusEl.setAttribute(
        "badge",
        skill.is_active ? "rp-badge rp-badge-soft rp-badge-success" : "rp-badge rp-badge-soft",
      );
      statusEl.value = skill.is_active ? "Active" : "Inactive";
    }

    setView("rp-skill-detail-desc", skill.description || "—");
    setView("rp-skill-detail-created", formatDate(skill.created_at));
    setView("rp-skill-detail-created-by", skill.created_by?.email ?? "—");
  } catch {
    toast({
      type: "error",
      title: "Could not load skill",
      message: "Refresh the page to retry.",
    });
  }
}

document.addEventListener("DOMContentLoaded", () => {
  loadSkillDetails();
  if (hasPermission("auth.view_user")) {
    document.getElementById("rp-skill-members-col")?.removeAttribute("hidden");
  }
});
