"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import { apiFetch, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { hasPermission } from "../utils/index.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

let pendingRow = null;

window.renderGroupsRow = function renderGroupsRow(row) {
  const badgeCls = row.is_active ? "rp-badge-soft rp-badge-success" : "rp-badge-soft";
  const statusLabel = row.is_active ? "Active" : "Inactive";
  const typeBadge = row.is_admin_group
    ? `<span class="rp-badge rp-badge-soft rp-badge-warning">Admin</span>`
    : `<span class="rp-badge rp-badge-soft">Standard</span>`;

  return `
    <td class="fw-medium">${esc(row.name || "—")}</td>
    <td><span class="rp-mono rp-subtle">${esc(row.code || "")}</span></td>
    <td style="color:var(--rp-text-muted)">${row.member_count ?? 0}</td>
    <td>${typeBadge}</td>
    <td><span class="rp-badge ${badgeCls}">${statusLabel}</span></td>
  `;
};

function openDeleteModal(row) {
  const modal = document.getElementById("rp-group-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete "${row.name}"?`);
  modal.setAttribute(
    "body",
    "This will permanently remove the group and all associated data. This cannot be undone.",
  );
  modal.setAttribute("confirm-value", row.name);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-group-delete-modal");
  if (!modal) return;

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;
    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");
    const { href, method } = API_URLS.groups.delete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Group deleted",
        message: `"${pendingRow.name}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete group. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initToggleModals(table) {
  const activateModal = document.getElementById("rp-group-activate-modal");
  const deactivateModal = document.getElementById("rp-group-deactivate-modal");
  if (!activateModal || !deactivateModal) return;

  let toggleRow = null;

  table.addEventListener("rp:group:toggle", (e) => {
    toggleRow = e.detail.row;
    if (toggleRow.is_active) {
      deactivateModal.setAttribute("title", `Deactivate "${toggleRow.name}"?`);
      deactivateModal.setAttribute(
        "body",
        "Deactivating this group will mark it inactive. Members will retain their association.",
      );
      deactivateModal.show();
    } else {
      activateModal.setAttribute("title", `Activate "${toggleRow.name}"?`);
      activateModal.setAttribute("body", "This will mark the group as active.");
      activateModal.show();
    }
  });

  async function handleToggleConfirm(modal, isActivating) {
    if (!toggleRow) return;
    const actionBtn = modal.querySelector("[data-action-modal]");
    actionBtn?.setAttribute("disabled", "");
    const urlFn = isActivating ? API_URLS.groups.activate : API_URLS.groups.deactivate;
    const { href, method } = urlFn(toggleRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      const verb = isActivating ? "activated" : "deactivated";
      toast({
        type: "success",
        title: `Group ${verb}`,
        message: `"${toggleRow.name}" has been ${verb}.`,
      });
      toggleRow = null;
    } catch (err) {
      actionBtn?.removeAttribute("disabled");
      const verb = isActivating ? "activate" : "deactivate";
      const msg = err?.data?.error?.message ?? `Failed to ${verb} group. Please try again.`;
      toast({ type: "error", title: "Error", message: msg });
    }
  }

  activateModal.addEventListener("rp:confirm", () => handleToggleConfirm(activateModal, true));
  deactivateModal.addEventListener("rp:confirm", () => handleToggleConfirm(deactivateModal, false));
}

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-group-edit-drawer");
  if (!drawer) return;
  pendingRow = row;

  const nameField = document.getElementById("rp-edit-group-name");
  const descField = document.getElementById("rp-edit-group-description");
  if (nameField) {
    nameField.value = row.name || "";
    if (row.is_system) nameField.setAttribute("readonly", "");
    else nameField.removeAttribute("readonly");
  }
  if (descField) descField.value = row.description || "";

  drawer.querySelectorAll("[data-rp-error]").forEach((el) => el.setAttribute("hidden", ""));
  drawer.show();
}

function initEditDrawer(table) {
  const drawer = document.getElementById("rp-group-edit-drawer");
  if (!drawer) return;

  function validateForm() {
    const nameField = document.getElementById("rp-edit-group-name");
    nameField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  table.addEventListener("rp:group:edit", (e) => openEditDrawer(e.detail.row));

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow || !validateForm()) return;
    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const name = document.getElementById("rp-edit-group-name")?.value?.trim() ?? "";
    const description = document.getElementById("rp-edit-group-description")?.value?.trim() ?? "";
    const payload = {};
    if (!pendingRow.is_system) payload.name = name;
    payload.description = description;

    const { href, method } = API_URLS.groups.update(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap, { label: "Saved", suffixIcon: "bi-check-circle-fill" });
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Group updated",
        message: `"${name || pendingRow.name}" has been updated.`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to update group. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initAssignMemberDrawer(table) {
  const drawer = document.getElementById("rp-group-assign-member-drawer");
  if (!drawer) return;

  table.addEventListener("rp:group:assign-member", (e) => {
    pendingRow = e.detail.row;
    const memberField = document.getElementById("rp-assign-group-member-field");
    if (memberField) memberField.value = "";
    drawer.setTitle(`Assign member to "${pendingRow.name}"`);
    drawer.querySelectorAll("[data-rp-error]").forEach((el) => el.setAttribute("hidden", ""));
    drawer.show();
  });

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow) return;
    const memberField = document.getElementById("rp-assign-group-member-field");
    memberField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    if (drawer.querySelector("[data-rp-error]:not([hidden])")) return;

    const memberCode = memberField?.value ?? "";
    if (!memberCode) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Assigning…");

    const { href, method } = API_URLS.groups.assignMember(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify({ member_code: memberCode }) });
      restoreButton(submitBtn, snap, { label: "Assigned", suffixIcon: "bi-check-circle-fill" });
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Member assigned",
        message: `Member added to "${pendingRow.name}".`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to assign member. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initAssignPermissionsDrawer(table) {
  const drawer = document.getElementById("rp-group-assign-permissions-drawer");
  const panel = document.getElementById("rp-group-permissions-panel");
  if (!drawer || !panel) return;

  table.addEventListener("rp:group:assign-permissions", async (e) => {
    pendingRow = e.detail.row;
    drawer.setTitle(`Permissions for "${pendingRow.name}"`);
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
      table.refresh();
      toast({
        type: "success",
        title: "Permissions updated",
        message: `Permissions for "${pendingRow.name}" have been updated.`,
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

function initRowNavigation(table) {
  table.addEventListener("click", (e) => {
    if (e.target.closest("[data-rp-action]") || e.target.closest(".rp-table-more-btn")) return;
    const tr = e.target.closest("tr[data-rp-row]");
    if (!tr) return;
    const idx = parseInt(tr.getAttribute("data-rp-row"), 10);
    const row = table.rows?.[idx];
    if (!row) return;
    window.location.href = UI_URLS.groups.detail(row.code);
  });
}

function initActions(table) {
  table.addEventListener("rp:group:delete", (e) => openDeleteModal(e.detail.row));
}

function initAddButton(table) {
  const addBtn = document.getElementById("rp-groups-add-btn");
  const drawer = document.getElementById("rp-group-create-drawer");
  if (!addBtn) return;

  addBtn.removeAttribute("hidden");

  if (!drawer) return;

  function resetForm() {
    ["rp-new-group-name", "rp-new-group-description"].forEach((id) => {
      const el = document.getElementById(id);
      if (el) el.value = "";
    });
    drawer.querySelectorAll("[data-rp-error]").forEach((el) => el.setAttribute("hidden", ""));
  }

  function validateForm() {
    document
      .getElementById("rp-new-group-name")
      ?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
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

    const name = document.getElementById("rp-new-group-name")?.value?.trim() ?? "";
    const description = document.getElementById("rp-new-group-description")?.value?.trim() ?? "";

    const { href, method } = API_URLS.groups.create();
    try {
      await apiFetch(href, { method, body: JSON.stringify({ name, description }) });
      restoreButton(submitBtn, snap, { label: "Created", suffixIcon: "bi-check-circle-fill" });
      drawer.hide();
      resetForm();
      table.refresh();
      toast({
        type: "success",
        title: "Group created",
        message: `"${esc(name)}" has been created.`,
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to create group. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initImportView(table) {
  const importView = document.getElementById("rp-groups-import-view");
  const importBtn = document.getElementById("rp-groups-import-btn");
  if (!importView || !importBtn) return;

  importView.setAttribute("specs-url", API_URLS.groups.importSpecs().href);
  importView.setAttribute("sample-url", API_URLS.groups.importSample().href);
  importView.setAttribute("import-url", API_URLS.groups.import().href);

  importBtn.removeAttribute("hidden");
  importBtn.addEventListener("click", () => importView.show());
  importView.addEventListener("rp:import:complete", () => table.refresh());
}

function initExportView() {
  const exportView = document.getElementById("rp-groups-export-view");
  const exportBtn = document.getElementById("rp-groups-export-btn");
  if (!exportView || !exportBtn) return;

  exportView.setAttribute("specs-url", API_URLS.groups.exportSpecs().href);
  exportView.setAttribute("export-url", API_URLS.groups.export().href);

  exportBtn.removeAttribute("hidden");
  exportBtn.addEventListener("click", () => exportView.show());
}

document.addEventListener("DOMContentLoaded", () => {
  setBreadcrumbs([{ label: "Administration" }, { label: "Users" }, { label: "Groups" }]);

  const table = document.getElementById("rp-groups-table");
  if (!table) return;

  initActions(table);
  initRowNavigation(table);

  if (hasPermission("users.add_group")) {
    initAddButton(table);
  }
  if (hasPermission("users.change_group")) {
    initEditDrawer(table);
    initToggleModals(table);
    initAssignMemberDrawer(table);
    initAssignPermissionsDrawer(table);
  }
  if (hasPermission("users.delete_group")) {
    initDeleteModal(table);
  }
  if (hasPermission("users.import_group")) {
    initImportView(table);
  }
  if (hasPermission("users.export_group")) {
    initExportView();
  }
});
