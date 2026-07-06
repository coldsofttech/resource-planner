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

window.renderRolesRow = function renderRolesRow(row) {
  const badgeCls = row.is_active ? "rp-badge-soft rp-badge-success" : "rp-badge-soft";
  const statusLabel = row.is_active ? "Active" : "Inactive";
  const defaultBadge = row.is_default ? `<span class="rp-badge rp-badge-soft">Default</span>` : "—";
  const assignableBadge = row.is_assignable
    ? `<span class="rp-badge rp-badge-soft rp-badge-success">Yes</span>`
    : `<span class="rp-badge rp-badge-soft">No</span>`;
  const leadershipBadge = row.is_leadership
    ? `<span class="rp-badge rp-badge-soft rp-badge-success">Yes</span>`
    : `<span class="rp-badge rp-badge-soft">No</span>`;

  const membersCount = typeof row.members_count === "number" ? row.members_count : "—";

  return `
    <td class="fw-medium">${esc(row.role)}</td>
    <td><code class="rp-mono">${esc(row.code)}</code></td>
    <td>${assignableBadge}</td>
    <td>${leadershipBadge}</td>
    <td>${defaultBadge}</td>
    <td style="color:var(--rp-text-muted)">${membersCount}</td>
    <td><span class="rp-badge ${badgeCls}">${statusLabel}</span></td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.created_at)}</td>
  `;
};

function openDeleteModal(row) {
  const modal = document.getElementById("rp-role-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete "${row.role}"?`);
  modal.setAttribute("body", "This will permanently remove the role and all associated data.");
  modal.setAttribute("confirm-value", row.role);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-role-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:role:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;

    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.roles.delete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Role deleted",
        message: `"${pendingRow.role}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.message ?? "Failed to delete role. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initToggleModals(table) {
  const activateModal = document.getElementById("rp-role-activate-modal");
  const deactivateModal = document.getElementById("rp-role-deactivate-modal");
  if (!activateModal || !deactivateModal) return;

  let toggleRow = null;

  table.addEventListener("rp:role:toggle", (e) => {
    toggleRow = e.detail.row;
    if (toggleRow.is_active) {
      deactivateModal.setAttribute("title", `Deactivate "${toggleRow.role}"?`);
      deactivateModal.setAttribute(
        "body",
        "This will disable the role and prevent it from being assigned.",
      );
      deactivateModal.show();
    } else {
      activateModal.setAttribute("title", `Activate "${toggleRow.role}"?`);
      activateModal.setAttribute("body", "This will re-enable the role for assignment.");
      activateModal.show();
    }
  });

  async function handleToggleConfirm(modal, isActivating) {
    if (!toggleRow) return;

    const actionBtn = modal.querySelector("[data-action-modal]");
    actionBtn?.setAttribute("disabled", "");

    const { href, method } = isActivating
      ? API_URLS.roles.activate(toggleRow.code)
      : API_URLS.roles.deactivate(toggleRow.code);

    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: isActivating ? "Role activated" : "Role deactivated",
        message: `"${toggleRow.role}" has been ${isActivating ? "activated" : "deactivated"}.`,
      });
      toggleRow = null;
    } catch (err) {
      actionBtn?.removeAttribute("disabled");
      const msg =
        err?.data?.message ??
        `Failed to ${isActivating ? "activate" : "deactivate"} role. Please try again.`;
      toast({ type: "error", title: "Error", message: msg });
    }
  }

  activateModal.addEventListener("rp:confirm", () => handleToggleConfirm(activateModal, true));
  deactivateModal.addEventListener("rp:confirm", () => handleToggleConfirm(deactivateModal, false));
}

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-role-edit-drawer");
  if (!drawer) return;

  pendingRow = row;

  const nameInput = document.getElementById("rp-edit-role-name")?.querySelector(".rp-input");
  const assignableToggle = document.getElementById("rp-edit-role-assignable");
  const leadershipToggle = document.getElementById("rp-edit-role-leadership");

  if (nameInput) nameInput.value = row.role ?? "";

  if (assignableToggle) assignableToggle.checked = !!row.is_assignable;
  if (leadershipToggle) leadershipToggle.checked = !!row.is_leadership;

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
  const drawer = document.getElementById("rp-role-edit-drawer");
  if (!drawer) return;

  const nameField = document.getElementById("rp-edit-role-name");

  function validateForm() {
    nameField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow || !validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const nameInput = document.getElementById("rp-edit-role-name")?.querySelector(".rp-input");
    const assignableToggle = document.getElementById("rp-edit-role-assignable");
    const leadershipToggle = document.getElementById("rp-edit-role-leadership");

    const payload = {
      role: nameInput?.value.trim() ?? "",
      is_assignable: assignableToggle?.checked ?? false,
      is_leadership: leadershipToggle?.checked ?? false,
    };

    const { href, method } = API_URLS.roles.update(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Role updated",
        message: `"${payload.role}" has been updated.`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.message ??
        err?.data?.errors?.role?.[0] ??
        "Failed to update role. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initRowNavigation(table) {
  table.addEventListener("click", (e) => {
    if (e.target.closest("[data-rp-action]") || e.target.closest(".rp-table-more-btn")) return;
    const tr = e.target.closest("tr[data-rp-row]");
    if (!tr) return;
    const idx = parseInt(tr.getAttribute("data-rp-row"), 10);
    const row = table.rows[idx];
    if (!row) return;
    window.location.href = UI_URLS.roles.detail(row.code);
  });
}

function initActions(table) {
  table.addEventListener("rp:role:edit", (e) => openEditDrawer(e.detail.row));
}

function initAddButton(table) {
  const addBtn = document.getElementById("rp-roles-add-btn");
  const drawer = document.getElementById("rp-role-create-drawer");
  if (!addBtn || !drawer) return;

  const nameField = document.getElementById("rp-new-role-name");
  const assignableField = document.getElementById("rp-new-role-assignable");
  const leadershipField = document.getElementById("rp-new-role-leadership");

  function resetForm() {
    const nameInput = nameField?.querySelector(".rp-input");
    if (nameInput) nameInput.value = "";
    if (assignableField) assignableField.checked = false;
    if (leadershipField) leadershipField.checked = false;
    drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
      el.textContent = "";
      el.hidden = true;
    });
    drawer
      .querySelectorAll(".rp-input.is-invalid")
      .forEach((el) => el.classList.remove("is-invalid"));
  }

  function validateForm() {
    nameField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
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

    const payload = {
      role: nameField?.querySelector(".rp-input")?.value.trim() ?? "",
      is_assignable: assignableField?.checked ?? false,
      is_leadership: leadershipField?.checked ?? false,
      is_active: true,
    };

    const { href, method } = API_URLS.roles.create();
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      table.refresh();
      toast({
        type: "success",
        title: "Role created",
        message: `"${payload.role}" has been added.`,
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.message ??
        err?.data?.errors?.role?.[0] ??
        "Failed to create role. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initSetDefaultModal(table) {
  const modal = document.getElementById("rp-role-set-default-modal");
  if (!modal) return;

  let defaultRow = null;

  table.addEventListener("rp:role:set-default", (e) => {
    defaultRow = e.detail.row;
    modal.setAttribute("title", `Set "${defaultRow.role}" as Default?`);
    modal.setAttribute(
      "body",
      "This will replace the current default role. Only one role can be the default at a time.",
    );
    modal.show();
  });

  modal.addEventListener("rp:confirm", async () => {
    if (!defaultRow) return;

    const actionBtn = modal.querySelector("[data-action-modal]");
    actionBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.roles.setDefault(defaultRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Default role set",
        message: `"${defaultRow.role}" is now the default role.`,
      });
      defaultRow = null;
    } catch (err) {
      actionBtn?.removeAttribute("disabled");
      const msg = err?.data?.message ?? "Failed to set default role. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initImportView(table) {
  const importView = document.getElementById("rp-roles-import-view");
  const importBtn = document.getElementById("rp-roles-import-btn");
  if (!importView || !importBtn) return;

  importView.setAttribute("specs-url", API_URLS.roles.importSpecs().href);
  importView.setAttribute("sample-url", API_URLS.roles.importSample().href);
  importView.setAttribute("import-url", API_URLS.roles.import().href);

  importBtn.addEventListener("click", () => importView.show());
  importView.addEventListener("rp:import:complete", () => table.refresh());
}

function initExportView() {
  const exportView = document.getElementById("rp-roles-export-view");
  const exportBtn = document.getElementById("rp-roles-export-btn");
  if (!exportView || !exportBtn) return;

  exportView.setAttribute("specs-url", API_URLS.roles.exportSpecs().href);
  exportView.setAttribute("export-url", API_URLS.roles.export().href);

  exportBtn.addEventListener("click", () => exportView.show());
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-roles-table");
  if (!table) return;

  setBreadcrumbs([
    { label: "Organisation" },
    { label: "Configurations" },
    { label: "Roles", href: UI_URLS.roles.list() },
  ]);

  initActions(table);
  initRowNavigation(table);

  if (hasPermission("roles.add_role")) {
    document.getElementById("rp-roles-add-btn")?.removeAttribute("hidden");
    initAddButton(table);
  }
  if (hasPermission("roles.change_role")) {
    initEditDrawer(table);
    initToggleModals(table);
    initSetDefaultModal(table);
  }
  if (hasPermission("roles.delete_role")) {
    initDeleteModal(table);
  }
  if (hasPermission("roles.import_role")) {
    document.getElementById("rp-roles-import-btn")?.removeAttribute("hidden");
    initImportView(table);
  }
  if (hasPermission("roles.export_role")) {
    document.getElementById("rp-roles-export-btn")?.removeAttribute("hidden");
    initExportView();
  }
});
