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

window.renderBusinessUnitsRow = function renderBusinessUnitsRow(row) {
  const badgeCls = row.is_active ? "rp-badge-soft rp-badge-success" : "rp-badge-soft";
  const statusLabel = row.is_active ? "Active" : "Inactive";

  return `
    <td><identicon-field name="${esc(row.name)}" variant="monogram" no-border></identicon-field></td>
    <td class="fw-medium">${esc(row.name)}</td>
    <td><code class="rp-mono">${esc(row.code)}</code></td>
    <td style="color:var(--rp-text-muted)">${esc(row.short_name || "—")}</td>
    <td><span class="rp-badge ${badgeCls}">${statusLabel}</span></td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.created_at)}</td>
  `;
};

function openDeleteModal(row) {
  const modal = document.getElementById("rp-business-unit-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete "${row.name}"?`);
  modal.setAttribute(
    "body",
    "This will permanently remove the business unit and all associated data.",
  );
  modal.setAttribute("confirm-value", row.name);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-business-unit-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:business-unit:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;

    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.businessUnits.delete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Business unit deleted",
        message: `"${pendingRow.name}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete business unit. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initToggleModals(table) {
  const activateModal = document.getElementById("rp-business-unit-activate-modal");
  const deactivateModal = document.getElementById("rp-business-unit-deactivate-modal");
  if (!activateModal || !deactivateModal) return;

  let toggleRow = null;

  table.addEventListener("rp:business-unit:toggle", (e) => {
    toggleRow = e.detail.row;
    if (toggleRow.is_active) {
      deactivateModal.setAttribute("title", `Deactivate "${toggleRow.name}"?`);
      deactivateModal.setAttribute(
        "body",
        "This will disable the business unit from selection in new records.",
      );
      deactivateModal.show();
    } else {
      activateModal.setAttribute("title", `Activate "${toggleRow.name}"?`);
      activateModal.setAttribute(
        "body",
        "This will re-enable the business unit for use in records.",
      );
      activateModal.show();
    }
  });

  async function handleToggleConfirm(modal, isActivating) {
    if (!toggleRow) return;

    const actionBtn = modal.querySelector("[data-action-modal]");
    actionBtn?.setAttribute("disabled", "");

    const { href, method } = isActivating
      ? API_URLS.businessUnits.activate(toggleRow.code)
      : API_URLS.businessUnits.deactivate(toggleRow.code);

    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: isActivating ? "Business unit activated" : "Business unit deactivated",
        message: `"${toggleRow.name}" has been ${isActivating ? "activated" : "deactivated"}.`,
      });
      toggleRow = null;
    } catch (err) {
      actionBtn?.removeAttribute("disabled");
      const msg =
        err?.data?.error?.message ??
        `Failed to ${isActivating ? "activate" : "deactivate"} business unit. Please try again.`;
      toast({ type: "error", title: "Error", message: msg });
    }
  }

  activateModal.addEventListener("rp:confirm", () => handleToggleConfirm(activateModal, true));
  deactivateModal.addEventListener("rp:confirm", () => handleToggleConfirm(deactivateModal, false));
}

function openViewDrawer(row) {
  const drawer = document.getElementById("rp-business-unit-view-drawer");
  if (!drawer) return;

  pendingRow = row;

  document.getElementById("rp-view-business-unit-identicon")?.setAttribute("name", row.name);
  document.getElementById("rp-view-business-unit-identicon")?.setAttribute("variant", "monogram");

  drawer.setTitle(row.name);

  const setView = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.value = val || "—";
  };

  setView("rp-view-business-unit-name", row.name);
  setView("rp-view-business-unit-short-name", row.short_name);
  setView("rp-view-business-unit-code", row.code);
  setView("rp-view-business-unit-status", row.is_active ? "Active" : "Inactive");
  setView("rp-view-business-unit-created", formatDate(row.created_at));
  setView("rp-view-business-unit-created-by", row.created_by?.email || "—");

  drawer.show();
}

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-business-unit-edit-drawer");
  if (!drawer) return;

  pendingRow = row;

  document.getElementById("rp-edit-business-unit-identicon")?.setAttribute("name", row.name);
  document.getElementById("rp-edit-business-unit-identicon")?.setAttribute("variant", "monogram");

  const nameInput = document
    .getElementById("rp-edit-business-unit-name")
    ?.querySelector(".rp-input");
  const shortNameInput = document
    .getElementById("rp-edit-business-unit-short-name")
    ?.querySelector(".rp-input");

  if (nameInput) nameInput.value = row.name ?? "";
  if (shortNameInput) shortNameInput.value = row.short_name ?? "";

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
  const drawer = document.getElementById("rp-business-unit-edit-drawer");
  if (!drawer) return;

  const nameField = document.getElementById("rp-edit-business-unit-name");
  const shortNameField = document.getElementById("rp-edit-business-unit-short-name");

  function validateForm() {
    nameField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    shortNameField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow || !validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const nameInput = document
      .getElementById("rp-edit-business-unit-name")
      ?.querySelector(".rp-input");
    const shortNameInput = document
      .getElementById("rp-edit-business-unit-short-name")
      ?.querySelector(".rp-input");

    const payload = {
      name: nameInput?.value.trim() ?? "",
      short_name: shortNameInput?.value.trim() ?? "",
    };

    const { href, method } = API_URLS.businessUnits.update(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Business unit updated",
        message: `"${payload.name}" has been updated.`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.error?.message ??
        err?.data?.name?.[0] ??
        "Failed to update business unit. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initViewDrawer(table) {
  const drawer = document.getElementById("rp-business-unit-view-drawer");
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

function initActions(table) {
  table.addEventListener("rp:business-unit:edit", (e) => openEditDrawer(e.detail.row));
}

function initAddButton(table) {
  const addBtn = document.getElementById("rp-business-units-add-btn");
  const drawer = document.getElementById("rp-business-unit-create-drawer");
  if (!addBtn || !drawer) return;

  const nameField = document.getElementById("rp-new-business-unit-name");
  const shortNameField = document.getElementById("rp-new-business-unit-short-name");

  function resetForm() {
    const nameInput = nameField?.querySelector(".rp-input");
    const shortNameInput = shortNameField?.querySelector(".rp-input");
    if (nameInput) nameInput.value = "";
    if (shortNameInput) shortNameInput.value = "";
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
    shortNameField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
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
      short_name: shortNameField?.querySelector(".rp-input")?.value.trim() ?? "",
      is_active: true,
    };

    const { href, method } = API_URLS.businessUnits.create();
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      table.refresh();
      toast({
        type: "success",
        title: "Business unit created",
        message: `"${payload.name}" has been added.`,
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.error?.message ??
        err?.data?.name?.[0] ??
        "Failed to create business unit. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initImportView(table) {
  const importView = document.getElementById("rp-business-units-import-view");
  const importBtn = document.getElementById("rp-business-units-import-btn");
  if (!importView || !importBtn) return;

  importView.setAttribute("specs-url", API_URLS.businessUnits.importSpecs().href);
  importView.setAttribute("sample-url", API_URLS.businessUnits.importSample().href);
  importView.setAttribute("import-url", API_URLS.businessUnits.import().href);

  importBtn.addEventListener("click", () => importView.show());
  importView.addEventListener("rp:import:complete", () => table.refresh());
}

function initExportView() {
  const exportView = document.getElementById("rp-business-units-export-view");
  const exportBtn = document.getElementById("rp-business-units-export-btn");
  if (!exportView || !exportBtn) return;

  exportView.setAttribute("specs-url", API_URLS.businessUnits.exportSpecs().href);
  exportView.setAttribute("export-url", API_URLS.businessUnits.export().href);

  exportBtn.addEventListener("click", () => exportView.show());
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-business-units-table");
  if (!table) return;

  setBreadcrumbs([
    { label: "Organisations" },
    { label: "Structure" },
    { label: "Business Units", href: UI_URLS.businessUnits.list() },
  ]);

  initActions(table);
  initViewDrawer(table);

  if (hasPermission("business_units.add_businessunit")) {
    document.getElementById("rp-business-units-add-btn")?.removeAttribute("hidden");
    initAddButton(table);
  }
  if (hasPermission("business_units.change_businessunit")) {
    initEditDrawer(table);
    initToggleModals(table);
  }
  if (hasPermission("business_units.delete_businessunit")) {
    initDeleteModal(table);
  }
  if (hasPermission("business_units.import_businessunit")) {
    document.getElementById("rp-business-units-import-btn")?.removeAttribute("hidden");
    initImportView(table);
  }
  if (hasPermission("business_units.export_businessunit")) {
    document.getElementById("rp-business-units-export-btn")?.removeAttribute("hidden");
    initExportView();
  }
});
