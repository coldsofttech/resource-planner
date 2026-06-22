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

window.renderRechargeTypesRow = function renderRechargeTypesRow(row) {
  const badgeCls = row.is_active ? "rp-badge-soft rp-badge-success" : "rp-badge-soft";
  const statusLabel = row.is_active ? "Active" : "Inactive";
  const description = row.description
    ? esc(row.description)
    : `<span style="color:var(--rp-text-muted)">—</span>`;

  return `
    <td class="fw-medium">${esc(row.name)}</td>
    <td><code class="rp-mono">${esc(row.code)}</code></td>
    <td style="color:var(--rp-text-muted)">${description}</td>
    <td><span class="rp-badge ${badgeCls}">${statusLabel}</span></td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.created_at)}</td>
  `;
};

function openDeleteModal(row) {
  const modal = document.getElementById("rp-recharge-type-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete "${row.name}"?`);
  modal.setAttribute(
    "body",
    "This will permanently remove the recharge type and all associated data.",
  );
  modal.setAttribute("confirm-value", row.name);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-recharge-type-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:recharge-type:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;

    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.rechargeTypes.delete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Recharge type deleted",
        message: `"${pendingRow.name}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete recharge type. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initToggleModals(table) {
  const activateModal = document.getElementById("rp-recharge-type-activate-modal");
  const deactivateModal = document.getElementById("rp-recharge-type-deactivate-modal");
  if (!activateModal || !deactivateModal) return;

  let toggleRow = null;

  table.addEventListener("rp:recharge-type:toggle", (e) => {
    toggleRow = e.detail.row;
    if (toggleRow.is_active) {
      deactivateModal.setAttribute("title", `Deactivate "${toggleRow.name}"?`);
      deactivateModal.setAttribute(
        "body",
        "This will disable the recharge type and prevent it from being assigned.",
      );
      deactivateModal.show();
    } else {
      activateModal.setAttribute("title", `Activate "${toggleRow.name}"?`);
      activateModal.setAttribute("body", "This will re-enable the recharge type for assignment.");
      activateModal.show();
    }
  });

  async function handleToggleConfirm(modal, isActivating) {
    if (!toggleRow) return;

    const actionBtn = modal.querySelector("[data-action-modal]");
    actionBtn?.setAttribute("disabled", "");

    const { href, method } = isActivating
      ? API_URLS.rechargeTypes.activate(toggleRow.code)
      : API_URLS.rechargeTypes.deactivate(toggleRow.code);

    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: isActivating ? "Recharge type activated" : "Recharge type deactivated",
        message: `"${toggleRow.name}" has been ${isActivating ? "activated" : "deactivated"}.`,
      });
      toggleRow = null;
    } catch (err) {
      actionBtn?.removeAttribute("disabled");
      const msg =
        err?.data?.error?.message ??
        `Failed to ${isActivating ? "activate" : "deactivate"} recharge type. Please try again.`;
      toast({ type: "error", title: "Error", message: msg });
    }
  }

  activateModal.addEventListener("rp:confirm", () => handleToggleConfirm(activateModal, true));
  deactivateModal.addEventListener("rp:confirm", () => handleToggleConfirm(deactivateModal, false));
}

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-recharge-type-edit-drawer");
  if (!drawer) return;

  pendingRow = row;

  const nameInput = document
    .getElementById("rp-edit-recharge-type-name")
    ?.querySelector(".rp-input");
  const descInput = document
    .getElementById("rp-edit-recharge-type-description")
    ?.querySelector(".rp-input");

  if (nameInput) nameInput.value = row.name ?? "";
  if (descInput) descInput.value = row.description ?? "";

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
  const drawer = document.getElementById("rp-recharge-type-edit-drawer");
  if (!drawer) return;

  const nameField = document.getElementById("rp-edit-recharge-type-name");

  function validateForm() {
    nameField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow || !validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const nameInput = document
      .getElementById("rp-edit-recharge-type-name")
      ?.querySelector(".rp-input");
    const descInput = document
      .getElementById("rp-edit-recharge-type-description")
      ?.querySelector(".rp-input");

    const payload = {
      name: nameInput?.value.trim() ?? "",
      description: descInput?.value.trim() ?? "",
    };

    const { href, method } = API_URLS.rechargeTypes.update(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Recharge type updated",
        message: `"${payload.name}" has been updated.`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.error?.message ??
        err?.data?.name?.[0] ??
        "Failed to update recharge type. Please try again.";
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
    window.location.href = UI_URLS.recharges.detail(row.code);
  });
}

function initActions(table) {
  table.addEventListener("rp:recharge-type:edit", (e) => openEditDrawer(e.detail.row));
}

function initAddButton(table) {
  const addBtn = document.getElementById("rp-recharge-types-add-btn");
  const drawer = document.getElementById("rp-recharge-type-create-drawer");
  if (!addBtn || !drawer) return;

  const nameField = document.getElementById("rp-new-recharge-type-name");
  const descField = document.getElementById("rp-new-recharge-type-description");

  function resetForm() {
    const nameInput = nameField?.querySelector(".rp-input");
    const descInput = descField?.querySelector(".rp-input");
    if (nameInput) nameInput.value = "";
    if (descInput) descInput.value = "";
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
      name: nameField?.querySelector(".rp-input")?.value.trim() ?? "",
      description: descField?.querySelector(".rp-input")?.value.trim() ?? "",
      is_active: true,
    };

    const { href, method } = API_URLS.rechargeTypes.create();
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      table.refresh();
      toast({
        type: "success",
        title: "Recharge type created",
        message: `"${payload.name}" has been added.`,
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.error?.message ??
        err?.data?.name?.[0] ??
        "Failed to create recharge type. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initImportView(table) {
  const importView = document.getElementById("rp-recharge-types-import-view");
  const importBtn = document.getElementById("rp-recharge-types-import-btn");
  if (!importView || !importBtn) return;

  importView.setAttribute("specs-url", API_URLS.rechargeTypes.importSpecs().href);
  importView.setAttribute("sample-url", API_URLS.rechargeTypes.importSample().href);
  importView.setAttribute("import-url", API_URLS.rechargeTypes.import().href);

  importBtn.addEventListener("click", () => importView.show());
  importView.addEventListener("rp:import:complete", () => table.refresh());
}

function initExportView() {
  const exportView = document.getElementById("rp-recharge-types-export-view");
  const exportBtn = document.getElementById("rp-recharge-types-export-btn");
  if (!exportView || !exportBtn) return;

  exportView.setAttribute("specs-url", API_URLS.rechargeTypes.exportSpecs().href);
  exportView.setAttribute("export-url", API_URLS.rechargeTypes.export().href);

  exportBtn.addEventListener("click", () => exportView.show());
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-recharge-types-table");
  if (!table) return;

  setBreadcrumbs([
    { label: "Recharges" },
    { label: "Configurations" },
    { label: "Recharge Types", href: UI_URLS.recharges.types() },
  ]);

  initActions(table);
  initRowNavigation(table);

  if (hasPermission("recharges.add_rechargetype")) {
    document.getElementById("rp-recharge-types-add-btn")?.removeAttribute("hidden");
    initAddButton(table);
  }
  if (hasPermission("recharges.change_rechargetype")) {
    initEditDrawer(table);
    initToggleModals(table);
  }
  if (hasPermission("recharges.delete_rechargetype")) {
    initDeleteModal(table);
  }
  if (hasPermission("recharges.import_rechargetype")) {
    document.getElementById("rp-recharge-types-import-btn")?.removeAttribute("hidden");
    initImportView(table);
  }
  if (hasPermission("recharges.export_rechargetype")) {
    document.getElementById("rp-recharge-types-export-btn")?.removeAttribute("hidden");
    initExportView();
  }
});
