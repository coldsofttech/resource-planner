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

window.renderProductsRow = function renderProductsRow(row) {
  const badgeCls = row.is_active ? "rp-badge-soft rp-badge-success" : "rp-badge-soft";
  const statusLabel = row.is_active ? "Active" : "Inactive";
  const buName = esc(row.business_unit?.name || "—");

  return `
    <td><identicon-field name="${esc(row.name)}" variant="monogram" no-border></identicon-field></td>
    <td class="fw-medium">${esc(row.name)}</td>
    <td><code class="rp-mono">${esc(row.code)}</code></td>
    <td style="color:var(--rp-text-muted)">${esc(row.short_name || "—")}</td>
    <td style="color:var(--rp-text-muted)">${buName}</td>
    <td><span class="rp-badge ${badgeCls}">${statusLabel}</span></td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.created_at)}</td>
  `;
};

function openDeleteModal(row) {
  const modal = document.getElementById("rp-product-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete "${row.name}"?`);
  modal.setAttribute("body", "This will permanently remove the product and all associated data.");
  modal.setAttribute("confirm-value", row.name);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-product-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:product:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;

    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.products.delete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Product deleted",
        message: `"${pendingRow.name}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete product. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initToggleModals(table) {
  const activateModal = document.getElementById("rp-product-activate-modal");
  const deactivateModal = document.getElementById("rp-product-deactivate-modal");
  if (!activateModal || !deactivateModal) return;

  let toggleRow = null;

  table.addEventListener("rp:product:toggle", (e) => {
    toggleRow = e.detail.row;
    if (toggleRow.is_active) {
      deactivateModal.setAttribute("title", `Deactivate "${toggleRow.name}"?`);
      deactivateModal.setAttribute(
        "body",
        "This will disable the product from selection in new records.",
      );
      deactivateModal.show();
    } else {
      activateModal.setAttribute("title", `Activate "${toggleRow.name}"?`);
      activateModal.setAttribute("body", "This will re-enable the product for use in records.");
      activateModal.show();
    }
  });

  async function handleToggleConfirm(modal, isActivating) {
    if (!toggleRow) return;

    const actionBtn = modal.querySelector("[data-action-modal]");
    actionBtn?.setAttribute("disabled", "");

    const { href, method } = isActivating
      ? API_URLS.products.activate(toggleRow.code)
      : API_URLS.products.deactivate(toggleRow.code);

    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: isActivating ? "Product activated" : "Product deactivated",
        message: `"${toggleRow.name}" has been ${isActivating ? "activated" : "deactivated"}.`,
      });
      toggleRow = null;
    } catch (err) {
      actionBtn?.removeAttribute("disabled");
      const msg =
        err?.data?.error?.message ??
        `Failed to ${isActivating ? "activate" : "deactivate"} product. Please try again.`;
      toast({ type: "error", title: "Error", message: msg });
    }
  }

  activateModal.addEventListener("rp:confirm", () => handleToggleConfirm(activateModal, true));
  deactivateModal.addEventListener("rp:confirm", () => handleToggleConfirm(deactivateModal, false));
}

function openViewDrawer(row) {
  const drawer = document.getElementById("rp-product-view-drawer");
  if (!drawer) return;

  pendingRow = row;

  document.getElementById("rp-view-product-identicon")?.setAttribute("name", row.name);
  document.getElementById("rp-view-product-identicon")?.setAttribute("variant", "monogram");

  drawer.setTitle(row.name);

  const setView = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.value = val || "—";
  };

  setView("rp-view-product-name", row.name);
  setView("rp-view-product-short-name", row.short_name);
  setView("rp-view-product-bu", row.business_unit?.name);
  setView("rp-view-product-code", row.code);
  setView("rp-view-product-status", row.is_active ? "Active" : "Inactive");
  setView("rp-view-product-created", formatDate(row.created_at));
  setView("rp-view-product-created-by", row.created_by?.email || "—");

  drawer.show();
}

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-product-edit-drawer");
  if (!drawer) return;

  pendingRow = row;

  document.getElementById("rp-edit-product-identicon")?.setAttribute("name", row.name);
  document.getElementById("rp-edit-product-identicon")?.setAttribute("variant", "monogram");

  const nameInput = document.getElementById("rp-edit-product-name")?.querySelector(".rp-input");
  const shortNameInput = document
    .getElementById("rp-edit-product-short-name")
    ?.querySelector(".rp-input");
  const buField = document.getElementById("rp-edit-product-bu");

  if (nameInput) nameInput.value = row.name ?? "";
  if (shortNameInput) shortNameInput.value = row.short_name ?? "";
  if (buField) buField.value = row.business_unit?.code ?? "";

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
  const drawer = document.getElementById("rp-product-edit-drawer");
  if (!drawer) return;

  const nameField = document.getElementById("rp-edit-product-name");
  const shortNameField = document.getElementById("rp-edit-product-short-name");
  const buField = document.getElementById("rp-edit-product-bu");

  function validateForm() {
    nameField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    shortNameField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    buField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow || !validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const payload = {
      name: nameField?.querySelector(".rp-input")?.value.trim() ?? "",
      short_name: shortNameField?.querySelector(".rp-input")?.value.trim() ?? "",
      business_unit_code: buField?.value ?? "",
    };

    const { href, method } = API_URLS.products.update(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Product updated",
        message: `"${payload.name}" has been updated.`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.error?.message ??
        err?.data?.name?.[0] ??
        "Failed to update product. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initViewDrawer(table) {
  const drawer = document.getElementById("rp-product-view-drawer");
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
  table.addEventListener("rp:product:edit", (e) => openEditDrawer(e.detail.row));
}

function initAddButton(table) {
  const addBtn = document.getElementById("rp-products-add-btn");
  const drawer = document.getElementById("rp-product-create-drawer");
  if (!addBtn || !drawer) return;

  const nameField = document.getElementById("rp-new-product-name");
  const shortNameField = document.getElementById("rp-new-product-short-name");
  const buField = document.getElementById("rp-new-product-bu");

  function resetForm() {
    const nameInput = nameField?.querySelector(".rp-input");
    const shortNameInput = shortNameField?.querySelector(".rp-input");
    if (nameInput) nameInput.value = "";
    if (shortNameInput) shortNameInput.value = "";
    if (buField) buField.value = "";
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
    buField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
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
      business_unit_code: buField?.value ?? "",
      is_active: true,
    };

    const { href, method } = API_URLS.products.create();
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      table.refresh();
      toast({
        type: "success",
        title: "Product created",
        message: `"${payload.name}" has been added.`,
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.error?.message ??
        err?.data?.name?.[0] ??
        "Failed to create product. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initImportView(table) {
  const importView = document.getElementById("rp-products-import-view");
  const importBtn = document.getElementById("rp-products-import-btn");
  if (!importView || !importBtn) return;

  importView.setAttribute("specs-url", API_URLS.products.importSpecs().href);
  importView.setAttribute("sample-url", API_URLS.products.importSample().href);
  importView.setAttribute("import-url", API_URLS.products.import().href);

  importBtn.addEventListener("click", () => importView.show());
  importView.addEventListener("rp:import:complete", () => table.refresh());
}

function initExportView() {
  const exportView = document.getElementById("rp-products-export-view");
  const exportBtn = document.getElementById("rp-products-export-btn");
  if (!exportView || !exportBtn) return;

  exportView.setAttribute("specs-url", API_URLS.products.exportSpecs().href);
  exportView.setAttribute("export-url", API_URLS.products.export().href);

  exportBtn.addEventListener("click", () => exportView.show());
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-products-table");
  if (!table) return;

  setBreadcrumbs([
    { label: "Organisations" },
    { label: "Structure" },
    { label: "Products", href: UI_URLS.products.list() },
  ]);

  initActions(table);
  initViewDrawer(table);

  if (hasPermission("products.add_product")) {
    document.getElementById("rp-products-add-btn")?.removeAttribute("hidden");
    initAddButton(table);
  }
  if (hasPermission("products.change_product")) {
    initEditDrawer(table);
    initToggleModals(table);
  }
  if (hasPermission("products.delete_product")) {
    initDeleteModal(table);
  }
  if (hasPermission("products.import_product")) {
    document.getElementById("rp-products-import-btn")?.removeAttribute("hidden");
    initImportView(table);
  }
  if (hasPermission("products.export_product")) {
    document.getElementById("rp-products-export-btn")?.removeAttribute("hidden");
    initExportView();
  }
});
