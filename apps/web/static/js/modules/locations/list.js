"use strict";

import { esc } from "../../components/utils.js";
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

window.renderLocationsRow = function renderLocationsRow(row) {
  const badgeCls = row.is_active ? "rp-badge-soft rp-badge-success" : "rp-badge-soft";
  const statusLabel = row.is_active ? "Active" : "Inactive";
  const defaultBadge = row.is_default ? `<span class="rp-badge rp-badge-soft">Default</span>` : "—";

  return `
    <td class="fw-medium">${esc(row.city)}</td>
    <td style="color:var(--rp-text-muted)">${esc(row.country)}</td>
    <td><code class="rp-mono">${esc(row.code)}</code></td>
    <td>${defaultBadge}</td>
    <td><span class="rp-badge ${badgeCls}">${statusLabel}</span></td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.created_at)}</td>
  `;
};

function openDeleteModal(row) {
  const modal = document.getElementById("rp-location-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete "${row.city}, ${row.country}"?`);
  modal.setAttribute("body", "This will permanently remove the location and all associated data.");
  modal.setAttribute("confirm-value", row.city);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-location-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:location:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;

    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.locations.delete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Location deleted",
        message: `"${pendingRow.city}, ${pendingRow.country}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete location. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initToggleModals(table) {
  const activateModal = document.getElementById("rp-location-activate-modal");
  const deactivateModal = document.getElementById("rp-location-deactivate-modal");
  if (!activateModal || !deactivateModal) return;

  let toggleRow = null;

  table.addEventListener("rp:location:toggle", (e) => {
    toggleRow = e.detail.row;
    const label = `${toggleRow.city}, ${toggleRow.country}`;
    if (toggleRow.is_active) {
      deactivateModal.setAttribute("title", `Deactivate "${label}"?`);
      deactivateModal.setAttribute(
        "body",
        "This will disable the location and prevent it from being assigned.",
      );
      deactivateModal.show();
    } else {
      activateModal.setAttribute("title", `Activate "${label}"?`);
      activateModal.setAttribute("body", "This will re-enable the location for assignment.");
      activateModal.show();
    }
  });

  async function handleToggleConfirm(modal, isActivating) {
    if (!toggleRow) return;

    const actionBtn = modal.querySelector("[data-action-modal]");
    actionBtn?.setAttribute("disabled", "");

    const { href, method } = isActivating
      ? API_URLS.locations.activate(toggleRow.code)
      : API_URLS.locations.deactivate(toggleRow.code);

    const label = `${toggleRow.city}, ${toggleRow.country}`;
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: isActivating ? "Location activated" : "Location deactivated",
        message: `"${label}" has been ${isActivating ? "activated" : "deactivated"}.`,
      });
      toggleRow = null;
    } catch (err) {
      actionBtn?.removeAttribute("disabled");
      const msg =
        err?.data?.error?.message ??
        `Failed to ${isActivating ? "activate" : "deactivate"} location. Please try again.`;
      toast({ type: "error", title: "Error", message: msg });
    }
  }

  activateModal.addEventListener("rp:confirm", () => handleToggleConfirm(activateModal, true));
  deactivateModal.addEventListener("rp:confirm", () => handleToggleConfirm(deactivateModal, false));
}

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-location-edit-drawer");
  if (!drawer) return;

  pendingRow = row;

  const cityInput = document.getElementById("rp-edit-location-city")?.querySelector(".rp-input");
  const countryInput = document
    .getElementById("rp-edit-location-country")
    ?.querySelector(".rp-input");

  if (cityInput) cityInput.value = row.city ?? "";
  if (countryInput) countryInput.value = row.country ?? "";

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
  const drawer = document.getElementById("rp-location-edit-drawer");
  if (!drawer) return;

  const cityField = document.getElementById("rp-edit-location-city");
  const countryField = document.getElementById("rp-edit-location-country");

  function validateForm() {
    cityField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    countryField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow || !validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const cityInput = document.getElementById("rp-edit-location-city")?.querySelector(".rp-input");
    const countryInput = document
      .getElementById("rp-edit-location-country")
      ?.querySelector(".rp-input");

    const payload = {
      city: cityInput?.value.trim() ?? "",
      country: countryInput?.value.trim() ?? "",
    };

    const { href, method } = API_URLS.locations.update(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Location updated",
        message: `"${payload.city}, ${payload.country}" has been updated.`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.error?.message ??
        err?.data?.city?.[0] ??
        "Failed to update location. Please try again.";
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
    window.location.href = UI_URLS.locations.detail(row.code);
  });
}

function initActions(table) {
  table.addEventListener("rp:location:edit", (e) => openEditDrawer(e.detail.row));
}

function initAddButton(table) {
  const addBtn = document.getElementById("rp-locations-add-btn");
  const drawer = document.getElementById("rp-location-create-drawer");
  if (!addBtn || !drawer) return;

  const cityField = document.getElementById("rp-new-location-city");
  const countryField = document.getElementById("rp-new-location-country");

  function resetForm() {
    const cityInput = cityField?.querySelector(".rp-input");
    const countryInput = countryField?.querySelector(".rp-input");
    if (cityInput) cityInput.value = "";
    if (countryInput) countryInput.value = "";
    drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
      el.textContent = "";
      el.hidden = true;
    });
    drawer
      .querySelectorAll(".rp-input.is-invalid")
      .forEach((el) => el.classList.remove("is-invalid"));
  }

  function validateForm() {
    cityField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    countryField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
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
      city: cityField?.querySelector(".rp-input")?.value.trim() ?? "",
      country: countryField?.querySelector(".rp-input")?.value.trim() ?? "",
      is_active: true,
    };

    const { href, method } = API_URLS.locations.create();
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      table.refresh();
      toast({
        type: "success",
        title: "Location created",
        message: `"${payload.city}, ${payload.country}" has been added.`,
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.error?.message ??
        err?.data?.city?.[0] ??
        "Failed to create location. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initImportView(table) {
  const importView = document.getElementById("rp-locations-import-view");
  const importBtn = document.getElementById("rp-locations-import-btn");
  if (!importView || !importBtn) return;

  importView.setAttribute("specs-url", API_URLS.locations.importSpecs().href);
  importView.setAttribute("sample-url", API_URLS.locations.importSample().href);
  importView.setAttribute("import-url", API_URLS.locations.import().href);

  importBtn.addEventListener("click", () => importView.show());
  importView.addEventListener("rp:import:complete", () => table.refresh());
}

function initSetDefaultModal(table) {
  const modal = document.getElementById("rp-location-set-default-modal");
  if (!modal) return;

  let defaultRow = null;

  table.addEventListener("rp:location:set-default", (e) => {
    defaultRow = e.detail.row;
    const label = `${defaultRow.city}, ${defaultRow.country}`;
    modal.setAttribute("title", `Set "${label}" as Default?`);
    modal.setAttribute(
      "body",
      "This will replace the current default location. Only one location can be the default at a time.",
    );
    modal.show();
  });

  modal.addEventListener("rp:confirm", async () => {
    if (!defaultRow) return;

    const actionBtn = modal.querySelector("[data-action-modal]");
    actionBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.locations.setDefault(defaultRow.code);
    const label = `${defaultRow.city}, ${defaultRow.country}`;
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Default location set",
        message: `"${label}" is now the default location.`,
      });
      defaultRow = null;
    } catch (err) {
      actionBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to set default location. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initExportView() {
  const exportView = document.getElementById("rp-locations-export-view");
  const exportBtn = document.getElementById("rp-locations-export-btn");
  if (!exportView || !exportBtn) return;

  exportView.setAttribute("specs-url", API_URLS.locations.exportSpecs().href);
  exportView.setAttribute("export-url", API_URLS.locations.export().href);

  exportBtn.addEventListener("click", () => exportView.show());
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-locations-table");
  if (!table) return;

  initActions(table);
  initRowNavigation(table);

  if (hasPermission("locations.add_location")) {
    document.getElementById("rp-locations-add-btn")?.removeAttribute("hidden");
    initAddButton(table);
  }
  if (hasPermission("locations.change_location")) {
    initEditDrawer(table);
    initToggleModals(table);
    initSetDefaultModal(table);
  }
  if (hasPermission("locations.delete_location")) {
    initDeleteModal(table);
  }
  if (hasPermission("locations.import_location")) {
    document.getElementById("rp-locations-import-btn")?.removeAttribute("hidden");
    initImportView(table);
  }
  if (hasPermission("locations.export_location")) {
    document.getElementById("rp-locations-export-btn")?.removeAttribute("hidden");
    initExportView();
  }
});
