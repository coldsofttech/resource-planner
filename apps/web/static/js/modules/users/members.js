"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import {
  apiFetch,
  formatDate,
  formatMeta,
  snapshotButton,
  setBusyButton,
  restoreButton,
} from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";
import { hasPermission } from "../utils/index.js";

let pendingRow = null;

window.renderMembersRow = function renderMembersRow(row) {
  const name =
    row.display_name || [row.first_name, row.last_name].filter(Boolean).join(" ") || row.email;
  const location = row.location?.label || "—";
  const empType = row.employment_type?.label || "—";
  const role = row.role?.label || "—";
  const statusBadge = row.is_active
    ? `<span class="rp-badge rp-badge-success">Active</span>`
    : `<span class="rp-badge rp-badge-soft">Inactive</span>`;

  const teams = row.teams ?? [];
  const teamsCell =
    teams.length === 0
      ? `<span style="color:var(--rp-text-muted)">—</span>`
      : teams.map((t) => `<span class="rp-badge rp-badge-soft">${esc(t.name)}</span>`).join(" ");

  return `
    <td><user-avatar avatar-url="${esc(row.avatar_url || "")}" name="${esc(name)}" seed="${esc(row.email || "")}" size="sm"></user-avatar></td>
    <td class="fw-medium">${esc(name)}</td>
    <td style="color:var(--rp-text-muted)">${esc(row.email)}</td>
    <td style="color:var(--rp-text-muted)">${esc(location)}</td>
    <td style="color:var(--rp-text-muted)">${esc(empType)}</td>
    <td style="color:var(--rp-text-muted)">${esc(role)}</td>
    <td>${statusBadge}</td>
    <td>${teamsCell}</td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.joined_date)}</td>
  `;
};

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-member-edit-drawer");
  if (!drawer) return;

  pendingRow = row;

  const name =
    row.display_name || [row.first_name, row.last_name].filter(Boolean).join(" ") || row.email;

  // Populate header avatar and title
  drawer
    .querySelector("#rp-edit-member-avatar-cell")
    ?.setAttribute("avatar-url", row.avatar_url || "");
  drawer.querySelector("#rp-edit-member-avatar-cell")?.setAttribute("name", name);
  drawer.querySelector("#rp-edit-member-avatar-cell")?.setAttribute("seed", row.email || "");
  drawer.setTitle(name);

  // Populate fields — use setAttribute so async-loaded dropdowns pick up the value
  const locationField = document.getElementById("rp-edit-member-location");
  const empTypeField = document.getElementById("rp-edit-member-emp-type");
  const roleField = document.getElementById("rp-edit-member-role");
  const joinedField = document.getElementById("rp-edit-member-joined-date");
  const leavingField = document.getElementById("rp-edit-member-leaving-date");
  const holidaysField = document.getElementById("rp-edit-member-holidays");

  if (locationField) locationField.value = row.location?.code ?? "";
  if (empTypeField) empTypeField.value = row.employment_type?.code ?? "";
  if (roleField) roleField.value = row.role?.code ?? "";
  if (joinedField) joinedField.value = row.joined_date ?? "";
  if (leavingField) leavingField.value = row.leaving_date ?? "";
  if (holidaysField) {
    const input = holidaysField.querySelector(".rp-input");
    if (input) input.value = row.default_holidays != null ? String(row.default_holidays) : "";
  }

  drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
    el.textContent = "";
    el.hidden = true;
  });
  drawer
    .querySelectorAll(".rp-input.is-invalid")
    .forEach((el) => el.classList.remove("is-invalid"));

  const metaEl = drawer.querySelector(".rp-rdrawer-foot-meta");
  if (metaEl) metaEl.textContent = formatMeta(row);

  drawer.show();
}

function initEditDrawer(table) {
  const drawer = document.getElementById("rp-member-edit-drawer");
  if (!drawer) return;

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const locationField = document.getElementById("rp-edit-member-location");
    const empTypeField = document.getElementById("rp-edit-member-emp-type");
    const roleField = document.getElementById("rp-edit-member-role");
    const joinedField = document.getElementById("rp-edit-member-joined-date");
    const leavingField = document.getElementById("rp-edit-member-leaving-date");
    const holidaysField = document.getElementById("rp-edit-member-holidays");

    const holidaysInput = holidaysField?.querySelector(".rp-input");

    const payload = {
      location: locationField?.value || null,
      employment_type: empTypeField?.value || null,
      role: roleField?.value || null,
      joined_date: joinedField?.value || null,
      leaving_date: leavingField?.value || null,
      default_holidays:
        holidaysInput?.value !== "" && holidaysInput?.value != null
          ? parseInt(holidaysInput.value, 10)
          : null,
    };

    const { href, method } = API_URLS.members.update(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Member updated",
        message: "Workforce details have been saved.",
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to update member. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function openViewDrawer(row) {
  const drawer = document.getElementById("rp-member-view-drawer");
  if (!drawer) return;

  pendingRow = row;

  const name =
    row.display_name || [row.first_name, row.last_name].filter(Boolean).join(" ") || row.email;

  // Populate header avatar and title
  drawer
    .querySelector("#rp-view-member-avatar-cell")
    ?.setAttribute("avatar-url", row.avatar_url || "");
  drawer.querySelector("#rp-view-member-avatar-cell")?.setAttribute("name", name);
  drawer.querySelector("#rp-view-member-avatar-cell")?.setAttribute("seed", row.email || "");
  drawer.setTitle(name);

  // Field values
  const setView = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.value = val || "—";
  };

  setView("rp-view-member-code", row.code);

  // badge class is state-dependent — set dynamically then write value
  const statusEl = document.getElementById("rp-view-member-status");
  if (statusEl) {
    statusEl.setAttribute(
      "badge",
      row.is_active ? "rp-badge rp-badge-success" : "rp-badge rp-badge-soft",
    );
    statusEl.value = row.is_active ? "Active" : "Inactive";
  }

  setView("rp-view-member-first-name", row.first_name);
  setView("rp-view-member-last-name", row.last_name);
  setView("rp-view-member-display-name", row.display_name);
  setView("rp-view-member-email", row.email);
  setView("rp-view-member-location", row.location?.label);
  setView("rp-view-member-emp-type", row.employment_type?.label);
  setView("rp-view-member-role", row.role?.label);
  setView("rp-view-member-joined", formatDate(row.joined_date));

  // Leaving date — only show if set
  const leavingField = document.getElementById("rp-view-member-leaving");
  if (leavingField) {
    leavingField.hidden = !row.leaving_date;
    leavingField.value = row.leaving_date ? formatDate(row.leaving_date) : "—";
  }

  setView(
    "rp-view-member-holidays",
    row.default_holidays != null ? String(row.default_holidays) : "—",
  );
  setView("rp-view-member-created", formatDate(row.created_at));
  setView("rp-view-member-created-by", row.created_by?.email ?? "—");

  const skillsEl = document.getElementById("rp-view-member-skills");
  if (skillsEl) skillsEl.value = row.skills?.map((s) => s.skill) ?? [];

  const teamsEl = document.getElementById("rp-view-member-teams");
  if (teamsEl) teamsEl.value = row.teams?.map((t) => t.name) ?? [];

  const metaEl = drawer.querySelector(".rp-rdrawer-foot-meta");
  if (metaEl) metaEl.textContent = formatMeta(row);

  drawer.show();
}

function initViewDrawer(table) {
  const drawer = document.getElementById("rp-member-view-drawer");
  if (!drawer) return;

  table.addEventListener("click", (e) => {
    if (e.target.closest("[data-rp-action]") || e.target.closest(".rp-table-more-btn")) return;
    const tr = e.target.closest("tr[data-rp-row]");
    if (!tr) return;
    const idx = parseInt(tr.getAttribute("data-rp-row"), 10);
    const row = table.rows[idx];
    if (!row) return;
    openViewDrawer(row);
  });

  drawer.addEventListener("rp:footer-primary", () => {
    if (!pendingRow) return;
    drawer.hide();
    openEditDrawer(pendingRow);
  });
}

function openAssignTeamDrawer(row) {
  const drawer = document.getElementById("rp-member-assign-team-drawer");
  if (!drawer) return;

  pendingRow = row;

  const name =
    row.display_name || [row.first_name, row.last_name].filter(Boolean).join(" ") || row.email;

  drawer
    .querySelector("#rp-assign-team-member-avatar")
    ?.setAttribute("avatar-url", row.avatar_url || "");
  drawer.querySelector("#rp-assign-team-member-avatar")?.setAttribute("name", name);
  drawer.querySelector("#rp-assign-team-member-avatar")?.setAttribute("seed", row.email || "");
  drawer.setTitle(name);

  const isLeadership = row.role?.is_leadership ?? false;
  const currentTeams = row.teams ?? [];
  const teamField = document.getElementById("rp-assign-team-field");

  if (teamField) {
    if (isLeadership) {
      teamField.setAttribute("multi-select", "");
      teamField.setAttribute("label", "Teams");
      teamField.removeAttribute("unassign");
      teamField.value = currentTeams.map((t) => t.code);
    } else {
      teamField.removeAttribute("multi-select");
      teamField.setAttribute("label", "Team");
      if (currentTeams.length > 0) {
        teamField.setAttribute("unassign", "");
      } else {
        teamField.removeAttribute("unassign");
      }
      teamField.value = currentTeams[0]?.code ?? "";
    }
  }

  const noteInput = document.getElementById("rp-assign-team-note");
  if (noteInput) noteInput.value = "";

  drawer.show();
}

function initAssignTeamDrawer(table) {
  const drawer = document.getElementById("rp-member-assign-team-drawer");
  if (!drawer) return;

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const isLeadership = pendingRow.role?.is_leadership ?? false;
    const teamField = document.getElementById("rp-assign-team-field");
    let teams = [];

    if (isLeadership) {
      teams = teamField ? teamField.values.map((v) => v.value) : [];
    } else {
      const val = teamField?.value || "";
      teams = val ? [val] : [];
    }

    const noteInput = document.getElementById("rp-assign-team-note");
    const note = noteInput?.value?.trim() ?? "";

    const { href, method } = API_URLS.members.assignTeam(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify({ teams, note }) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Team assignment updated",
        message: "Changes have been saved.",
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.error?.message ?? "Failed to update team assignment. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initActions(table) {
  table.addEventListener("rp:member:edit", (e) => openEditDrawer(e.detail.row));
  table.addEventListener("rp:member:assign-team", (e) => openAssignTeamDrawer(e.detail.row));
}

function initExportView() {
  const exportView = document.getElementById("rp-members-export-view");
  const exportBtn = document.getElementById("rp-members-export-btn");
  if (!exportView || !exportBtn) return;

  exportView.setAttribute("specs-url", API_URLS.members.exportSpecs().href);
  exportView.setAttribute("export-url", API_URLS.members.export().href);

  exportBtn.addEventListener("click", () => exportView.show());
}

async function initHolidaysFieldMeta() {
  const field = document.getElementById("rp-edit-member-holidays");
  if (!field) return;
  try {
    const { href, method } = API_URLS.members.options();
    const data = await apiFetch(href, { method });
    const days = data?.data?.default_holidays;
    if (days != null) {
      field.setAttribute("placeholder", `e.g. ${days}`);
      field.setAttribute(
        "hint",
        `Holiday days per financial year. Leave blank to use the organisation default (${days} days).`,
      );
    }
  } catch {
    // retain static defaults
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-members-table");
  if (!table) return;

  setBreadcrumbs([
    { label: "Organisation" },
    { label: "People" },
    { label: "Members", href: UI_URLS.members.list() },
  ]);

  initActions(table);
  initViewDrawer(table);

  if (hasPermission("users.change_user_workforce")) {
    initEditDrawer(table);
    initHolidaysFieldMeta();
  }
  if (hasPermission("users.export_member")) {
    document.getElementById("rp-members-export-btn")?.removeAttribute("hidden");
    initExportView();
  }
  if (hasPermission("teams.assign_team")) {
    initAssignTeamDrawer(table);
  }
});
