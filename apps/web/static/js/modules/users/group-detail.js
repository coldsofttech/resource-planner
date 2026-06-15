"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import {
  apiFetch,
  formatDate,
  snapshotButton,
  setBusyButton,
  restoreButton,
} from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { hasPermission } from "../utils/index.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

const _groupPathParts = window.location.pathname.split("/").filter(Boolean);
const groupCode = _groupPathParts[0] === "groups" && _groupPathParts[1] ? _groupPathParts[1] : null;

let pendingMemberRow = null;

function authTypeBadge(authType) {
  if (authType === "classic") return `<span class="rp-badge rp-badge-soft">Classic</span>`;
  if (authType === "oauth")
    return `<span class="rp-badge rp-badge-soft rp-badge-info">OAuth</span>`;
  if (authType === "saml") return `<span class="rp-badge rp-badge-soft rp-badge-info">SAML</span>`;
  return `<span class="rp-badge rp-badge-soft">${esc(authType || "—")}</span>`;
}

window.renderGroupDetailMembersRow = function renderGroupDetailMembersRow(row) {
  const name = row.display_name || row.email;
  const statusBadge = row.is_active
    ? `<span class="rp-badge rp-badge-soft rp-badge-success">Active</span>`
    : `<span class="rp-badge rp-badge-soft">Inactive</span>`;

  return `
    <td><user-avatar avatar-url="${esc(row.avatar_url || "")}" name="${esc(name)}" size="sm"></user-avatar></td>
    <td class="fw-medium">${esc(name)}<br><small class="rp-subtle">${esc(row.email)}</small></td>
    <td style="color:var(--rp-text-muted)">${esc(row.email)}</td>
    <td>${authTypeBadge(row.auth_type)}</td>
    <td>${statusBadge}</td>
  `;
};

async function loadGroupDetails() {
  try {
    const { href, method } = API_URLS.groups.detail(groupCode);
    const resp = await apiFetch(href, { method });
    const group = resp?.data ?? null;
    if (!group) return;

    const titleEl = document.getElementById("rp-group-detail-title");
    if (titleEl) titleEl.textContent = group.name;

    setBreadcrumbs([
      { label: "Administration" },
      { label: "Users" },
      { label: "Groups", href: UI_URLS.groups.list() },
      { label: group.name },
    ]);

    const setView = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.value = val || "—";
    };

    setView("rp-group-detail-name", group.name);
    setView("rp-group-detail-code", group.code);
    setView("rp-group-detail-desc", group.description || "—");
    setView("rp-group-detail-member-count", String(group.member_count ?? 0));

    const statusEl = document.getElementById("rp-group-detail-status");
    if (statusEl) {
      statusEl.setAttribute(
        "badge",
        group.is_active ? "rp-badge rp-badge-soft rp-badge-success" : "rp-badge rp-badge-soft",
      );
      statusEl.value = group.is_active ? "Active" : "Inactive";
    }

    const typeEl = document.getElementById("rp-group-detail-type");
    if (typeEl) {
      typeEl.setAttribute(
        "badge",
        group.is_admin_group ? "rp-badge rp-badge-soft rp-badge-warning" : "rp-badge rp-badge-soft",
      );
      typeEl.value = group.is_admin_group ? "Admin" : "Standard";
    }

    setView("rp-group-detail-created", group.created_at ? formatDate(group.created_at) : "—");
    setView("rp-group-detail-created-by", group.created_by?.email ?? "—");
  } catch {
    toast({
      type: "error",
      title: "Could not load group",
      message: "Refresh the page to retry.",
    });
  }
}

function loadGroupPermissions() {
  const panel = document.getElementById("rp-group-detail-permissions-view");
  if (panel) panel.loadAssigned(groupCode);
}

function initAssignPermissionsPage() {
  const btn = document.getElementById("rp-group-detail-assign-permissions-btn");
  const drawer = document.getElementById("rp-group-detail-assign-permissions-drawer");
  const panel = document.getElementById("rp-group-detail-permissions-panel");
  if (!btn || !drawer || !panel) return;

  btn.removeAttribute("hidden");

  btn.addEventListener("click", async () => {
    drawer.show();
    await panel.load(groupCode);
  });

  drawer.addEventListener("rp:footer-primary", async () => {
    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");
    try {
      await panel.save();
      restoreButton(submitBtn, snap, { label: "Saved", suffixIcon: "bi-check-circle-fill" });
      drawer.hide();
      loadGroupPermissions();
      toast({
        type: "success",
        title: "Permissions updated",
        message: "Group permissions have been saved.",
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      toast({
        type: "error",
        title: "Error",
        message: err?.message ?? "Failed to save permissions. Please try again.",
      });
    }
  });
}

function initAssignMember(membersTable) {
  const assignBtn = document.getElementById("rp-group-detail-assign-btn");
  const drawer = document.getElementById("rp-group-detail-assign-member-drawer");
  if (!assignBtn || !drawer) return;

  assignBtn.removeAttribute("hidden");

  assignBtn.addEventListener("click", () => {
    const memberField = document.getElementById("rp-group-detail-assign-member-field");
    if (memberField) memberField.value = "";
    drawer.querySelectorAll("[data-rp-error]").forEach((el) => el.setAttribute("hidden", ""));
    drawer.show();
  });

  drawer.addEventListener("rp:footer-primary", async () => {
    const memberField = document.getElementById("rp-group-detail-assign-member-field");
    memberField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    if (drawer.querySelector("[data-rp-error]:not([hidden])")) return;

    const memberCode = memberField?.value ?? "";
    if (!memberCode) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Assigning…");

    const { href, method } = API_URLS.groups.assignMember(groupCode);
    try {
      await apiFetch(href, { method, body: JSON.stringify({ member_code: memberCode }) });
      restoreButton(submitBtn, snap, { label: "Assigned", suffixIcon: "bi-check-circle-fill" });
      drawer.hide();
      membersTable.refresh();
      loadGroupDetails();
      toast({
        type: "success",
        title: "Member assigned",
        message: "Member has been added to this group.",
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to assign member. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initUnassignMember(membersTable) {
  const modal = document.getElementById("rp-group-detail-unassign-modal");
  if (!modal) return;

  membersTable.addEventListener("rp:group:unassign-member", (e) => {
    pendingMemberRow = e.detail.row;
    const name = pendingMemberRow.display_name || pendingMemberRow.email;
    modal.setAttribute("title", `Unassign "${name}"?`);
    modal.setAttribute(
      "body",
      "This will remove the member from the group. They will lose all associated permissions.",
    );
    modal.setAttribute("confirm-value", name);
    modal.show();
  });

  modal.addEventListener("rp:delete", async () => {
    if (!pendingMemberRow) return;
    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.groups.unassignMember(groupCode, pendingMemberRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      membersTable.refresh();
      loadGroupDetails();
      toast({
        type: "success",
        title: "Member unassigned",
        message: `Member has been removed from this group.`,
      });
      pendingMemberRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to unassign member. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  if (!groupCode) return;
  loadGroupDetails();
  loadGroupPermissions();

  const membersTable = document.getElementById("rp-group-detail-members-table");
  if (membersTable) {
    if (hasPermission("users.change_group")) {
      initAssignMember(membersTable);
      initUnassignMember(membersTable);
    }
  }

  if (hasPermission("users.change_group")) {
    initAssignPermissionsPage();
  }
});
