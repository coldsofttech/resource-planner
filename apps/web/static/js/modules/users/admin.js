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
import { statusModal } from "../utils/modal.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

let pendingRow = null;

function authTypeBadge(authType) {
  if (authType === "classic") return `<span class="rp-badge rp-badge-soft">Classic</span>`;
  if (authType === "oauth")
    return `<span class="rp-badge rp-badge-soft rp-badge-info">OAuth</span>`;
  if (authType === "saml") return `<span class="rp-badge rp-badge-soft rp-badge-info">SAML</span>`;
  return `<span class="rp-badge rp-badge-soft">${esc(authType)}</span>`;
}

window.renderUsersRow = function renderUsersRow(row) {
  const badgeCls = row.is_active ? "rp-badge-soft rp-badge-success" : "rp-badge-soft";
  const statusLabel = row.is_active ? "Active" : "Inactive";
  const adminBadge = row.is_superuser
    ? `<span class="rp-badge rp-badge-soft rp-badge-warning ms-1">Admin</span>`
    : "";
  const displayName = esc(row.display_name || `${row.first_name} ${row.last_name}`.trim() || "—");

  return `
    <td class="fw-medium">${displayName}${adminBadge}<br>
      <small class="rp-subtle">${esc(row.email)}</small>
    </td>
    <td style="color:var(--rp-text-muted)">${esc(row.email)}</td>
    <td>${authTypeBadge(row.auth_type)}</td>
    <td style="color:var(--rp-text-muted)">${row.last_login ? formatDate(row.last_login) : "—"}</td>
    <td><span class="rp-badge ${badgeCls}">${statusLabel}</span></td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.created_at)}</td>
  `;
};

function openDeleteModal(row) {
  const modal = document.getElementById("rp-user-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete "${row.display_name || row.email}"?`);
  modal.setAttribute(
    "body",
    "This will permanently remove the user account and all associated data. This cannot be undone.",
  );
  modal.setAttribute("confirm-value", row.email);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-user-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:user:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;

    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.users.adminDelete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "User deleted",
        message: `"${pendingRow.display_name || pendingRow.email}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete user. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initToggleModals(table) {
  const activateModal = document.getElementById("rp-user-activate-modal");
  const deactivateModal = document.getElementById("rp-user-deactivate-modal");
  if (!activateModal || !deactivateModal) return;

  let toggleRow = null;

  table.addEventListener("rp:user:toggle", (e) => {
    toggleRow = e.detail.row;
    if (toggleRow.is_active) {
      deactivateModal.setAttribute(
        "title",
        `Deactivate "${toggleRow.display_name || toggleRow.email}"?`,
      );
      deactivateModal.setAttribute(
        "body",
        "This will disable the account and prevent the user from signing in.",
      );
      deactivateModal.show();
    } else {
      activateModal.setAttribute(
        "title",
        `Activate "${toggleRow.display_name || toggleRow.email}"?`,
      );
      activateModal.setAttribute(
        "body",
        "This will re-enable the account and restore sign-in access.",
      );
      activateModal.show();
    }
  });

  async function handleToggleConfirm(modal, isActivating) {
    if (!toggleRow) return;

    const actionBtn = modal.querySelector("[data-action-modal]");
    actionBtn?.setAttribute("disabled", "");

    const urlFn = isActivating ? API_URLS.users.adminActivate : API_URLS.users.adminDeactivate;
    const { href, method } = urlFn(toggleRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      const verb = isActivating ? "activated" : "deactivated";
      toast({
        type: "success",
        title: `User ${verb}`,
        message: `"${toggleRow.display_name || toggleRow.email}" has been ${verb}.`,
      });
      toggleRow = null;
    } catch (err) {
      actionBtn?.removeAttribute("disabled");
      const verb = isActivating ? "activate" : "deactivate";
      const msg = err?.data?.error?.message ?? `Failed to ${verb} user. Please try again.`;
      toast({ type: "error", title: "Error", message: msg });
    }
  }

  activateModal.addEventListener("rp:confirm", () => handleToggleConfirm(activateModal, true));
  deactivateModal.addEventListener("rp:confirm", () => handleToggleConfirm(deactivateModal, false));
}

function initResetPasswordModal(table) {
  table.addEventListener("rp:user:reset-password", async (e) => {
    const row = e.detail.row;
    if (!row) return;

    if (row.is_superuser || row.auth_type !== "classic") {
      toast({
        type: "warning",
        title: "Not available",
        message: "Password reset is only available for classic auth users.",
      });
      return;
    }

    const displayName = row.display_name || row.email;

    statusModal.open({
      iconType: "warning",
      title: "Send password reset link?",
      body: `A password reset link will be emailed to ${esc(displayName)}. The link will expire based on the configured timeout.`,
      primaryBtn: {
        label: "Send reset link",
        icon: "bi-key",
        onClick: async () => {
          statusModal.update({
            iconType: "info",
            title: "Sending…",
            body: "Sending the password reset email.",
          });

          const { href, method } = API_URLS.users.adminResetPassword(row.code);
          try {
            await apiFetch(href, { method });
            statusModal.close();
            table.refresh();
            toast({
              type: "success",
              title: "Reset link sent",
              message: `A password reset link has been emailed to ${esc(row.email)}.`,
            });
          } catch (err) {
            statusModal.close();
            const msg = err?.data?.error?.message ?? "Failed to send reset link. Please try again.";
            toast({ type: "error", title: "Error", message: msg });
          }
        },
      },
      dismissBtn: { label: "Cancel", onClick: () => statusModal.close() },
    });
  });
}

function initRowNavigation(table) {
  table.addEventListener("click", (e) => {
    if (e.target.closest("[data-rp-action]") || e.target.closest(".rp-table-more-btn")) return;
    const tr = e.target.closest("tr[data-rp-row]");
    if (!tr) return;
    const idx = parseInt(tr.getAttribute("data-rp-row"), 10);
    const row = table.rows?.[idx];
    if (!row) return;
    window.location.href = UI_URLS.users.detail(row.code);
  });
}

function initAssignPermissionsDrawer(table) {
  const drawer = document.getElementById("rp-user-assign-permissions-drawer");
  const panel = document.getElementById("rp-user-permissions-panel");
  if (!drawer || !panel) return;

  table.addEventListener("rp:user:assign-permissions", async (e) => {
    pendingRow = e.detail.row;
    const displayName = pendingRow.display_name || pendingRow.email;
    drawer.setTitle(`Permissions for "${displayName}"`);
    drawer.show();
    await panel.load(pendingRow.code);
  });

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow) return;
    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");
    try {
      await panel.save();
      restoreButton(submitBtn, snap, { label: "Saved", suffixIcon: "bi-check-circle-fill" });
      drawer.hide();
      toast({
        type: "success",
        title: "Permissions updated",
        message: `Permissions for "${pendingRow.display_name || pendingRow.email}" have been updated.`,
      });
      pendingRow = null;
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

function initActions(table) {
  table.addEventListener("rp:user:delete", (e) => openDeleteModal(e.detail.row));
}

function initAddButton(table) {
  const addBtn = document.getElementById("rp-users-add-btn");
  const drawer = document.getElementById("rp-user-create-drawer");
  if (!addBtn) return;

  addBtn.removeAttribute("hidden");

  if (!drawer) return;

  function resetForm() {
    ["rp-new-user-first-name", "rp-new-user-last-name", "rp-new-user-email"].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.value = "";
    });
    drawer.querySelectorAll("[data-rp-error]").forEach((el) => el.setAttribute("hidden", ""));
  }

  function validateForm() {
    const ids = ["rp-new-user-first-name", "rp-new-user-last-name", "rp-new-user-email"];
    ids.forEach((id) =>
      document.getElementById(id)?.dispatchEvent(new Event("rp:validate", { bubbles: false })),
    );
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  addBtn.addEventListener("click", () => {
    resetForm();
    drawer.show();
  });

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Creating…");

    const first_name = document.getElementById("rp-new-user-first-name")?.value?.trim() ?? "";
    const last_name = document.getElementById("rp-new-user-last-name")?.value?.trim() ?? "";
    const email = document.getElementById("rp-new-user-email")?.value?.trim() ?? "";

    const { href, method } = API_URLS.users.adminCreate();
    try {
      await apiFetch(href, { method, body: JSON.stringify({ first_name, last_name, email }) });
      restoreButton(submitBtn, snap, { label: "Created", suffixIcon: "bi-check-circle-fill" });
      drawer.hide();
      resetForm();
      table.refresh();
      toast({
        type: "success",
        title: "User created",
        message: `A setup email has been sent to ${esc(email)}.`,
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to create user. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initExportView() {
  const exportView = document.getElementById("rp-users-export-view");
  const exportBtn = document.getElementById("rp-users-export-btn");
  if (!exportView || !exportBtn) return;

  exportView.setAttribute("specs-url", API_URLS.users.adminExportSpecs().href);
  exportView.setAttribute("export-url", API_URLS.users.adminExport().href);

  exportBtn.removeAttribute("hidden");
  exportBtn.addEventListener("click", () => exportView.show());
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-users-table");
  if (!table) return;

  setBreadcrumbs([
    { label: "Administration" },
    { label: "Users", href: UI_URLS.users.list() },
    { label: "Users" },
  ]);

  initActions(table);
  initDeleteModal(table);
  initToggleModals(table);
  initResetPasswordModal(table);
  initRowNavigation(table);
  initAssignPermissionsDrawer(table);
  initAddButton(table);
  initExportView();
});
