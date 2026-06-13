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

window.renderHolidaysRow = function renderHolidaysRow(row) {
  const location = row.location ? `${esc(row.location.city)}, ${esc(row.location.country)}` : "—";

  return `
    <td class="fw-medium">${esc(row.name)}</td>
    <td>${esc(row.date)}</td>
    <td style="color:var(--rp-text-muted)">${location}</td>
    <td><code class="rp-mono">${esc(row.code)}</code></td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.created_at)}</td>
  `;
};

function openDeleteModal(row) {
  const modal = document.getElementById("rp-holiday-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete "${row.name}"?`);
  modal.setAttribute("body", "This will permanently remove the holiday and all associated data.");
  modal.setAttribute("confirm-value", row.name);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-holiday-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:holiday:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;

    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.holidays.delete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Holiday deleted",
        message: `"${pendingRow.name}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete holiday. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-holiday-edit-drawer");
  if (!drawer) return;

  pendingRow = row;

  const nameField = document.getElementById("rp-edit-holiday-name");
  const dateField = document.getElementById("rp-edit-holiday-date");
  const locationField = document.getElementById("rp-edit-holiday-location");

  const nameInput = nameField?.querySelector(".rp-input");
  if (nameInput) nameInput.value = row.name ?? "";
  if (dateField) dateField.value = row.date ?? "";
  if (locationField) locationField.value = row.location?.code ?? "";

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
  const drawer = document.getElementById("rp-holiday-edit-drawer");
  if (!drawer) return;

  const nameField = document.getElementById("rp-edit-holiday-name");
  const dateField = document.getElementById("rp-edit-holiday-date");
  const locationField = document.getElementById("rp-edit-holiday-location");

  function validateForm() {
    nameField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    dateField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    locationField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow || !validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const nameInput = nameField?.querySelector(".rp-input");

    const payload = {
      name: nameInput?.value.trim() ?? "",
      date: dateField?.value ?? "",
      location_code: locationField?.value ?? "",
    };

    const { href, method } = API_URLS.holidays.update(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Holiday updated",
        message: `"${payload.name}" has been updated.`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to update holiday. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function openViewDrawer(row) {
  const drawer = document.getElementById("rp-holiday-view-drawer");
  if (!drawer) return;

  pendingRow = row;

  const location = row.location ? `${row.location.city}, ${row.location.country}` : "—";

  const setView = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.value = val || "—";
  };

  drawer.setTitle(row.name);
  setView("rp-view-holiday-name", row.name);
  setView("rp-view-holiday-date", row.date);
  setView("rp-view-holiday-location", location);
  setView("rp-view-holiday-code", row.code);
  setView("rp-view-holiday-created", formatDate(row.created_at));
  setView("rp-view-holiday-created-by", row.created_by?.email ?? "—");

  const metaEl = drawer.querySelector(".rp-rdrawer-foot-meta");
  if (metaEl) metaEl.textContent = formatMeta(row);

  drawer.show();
}

function initViewDrawer(table) {
  const drawer = document.getElementById("rp-holiday-view-drawer");
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
  table.addEventListener("rp:holiday:edit", (e) => openEditDrawer(e.detail.row));
}

function initAddButton(table) {
  const addBtn = document.getElementById("rp-holidays-add-btn");
  const drawer = document.getElementById("rp-holiday-create-drawer");
  if (!addBtn || !drawer) return;

  const nameField = document.getElementById("rp-new-holiday-name");
  const dateField = document.getElementById("rp-new-holiday-date");
  const locationField = document.getElementById("rp-new-holiday-location");

  function resetForm() {
    const nameInput = nameField?.querySelector(".rp-input");
    if (nameInput) nameInput.value = "";
    if (dateField) dateField.value = "";
    if (locationField) locationField.value = "";
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
    dateField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    locationField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
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

    const nameInput = nameField?.querySelector(".rp-input");

    const payload = {
      name: nameInput?.value.trim() ?? "",
      date: dateField?.value ?? "",
      location_code: locationField?.value ?? "",
    };

    const { href, method } = API_URLS.holidays.create();
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      table.refresh();
      toast({
        type: "success",
        title: "Holiday created",
        message: `"${payload.name}" has been added.`,
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to create holiday. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

async function initYearRange() {
  const yearField = document.getElementById("rp-holidays-year");
  if (!yearField) return;

  try {
    const { href, method } = API_URLS.holidays.options();
    const res = await apiFetch(href, { method });
    const minYear = res?.data?.min_year;
    const maxYear = res?.data?.max_year;
    if (minYear != null && maxYear != null) {
      yearField.setAttribute("min", String(minYear));
      yearField.setAttribute("max", String(maxYear));
    }
  } catch {
    // Non-critical — year-field remains without range bounds.
  }
}

function initImportView(table) {
  const importView = document.getElementById("rp-holidays-import-view");
  const importBtn = document.getElementById("rp-holidays-import-btn");
  if (!importView || !importBtn) return;

  importView.setAttribute("specs-url", API_URLS.holidays.importSpecs().href);
  importView.setAttribute("sample-url", API_URLS.holidays.importSample().href);
  importView.setAttribute("import-url", API_URLS.holidays.import().href);

  importBtn.addEventListener("click", () => importView.show());
  importView.addEventListener("rp:import:complete", () => table.refresh());
}

function initExportView() {
  const exportView = document.getElementById("rp-holidays-export-view");
  const exportBtn = document.getElementById("rp-holidays-export-btn");
  if (!exportView || !exportBtn) return;

  exportView.setAttribute("specs-url", API_URLS.holidays.exportSpecs().href);
  exportView.setAttribute("export-url", API_URLS.holidays.export().href);

  exportBtn.addEventListener("click", () => exportView.show());
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-holidays-table");
  if (!table) return;

  setBreadcrumbs([
    { label: "Organisation" },
    { label: "Holidays" },
    { label: "Holidays", href: UI_URLS.holidays.list() },
  ]);

  initActions(table);
  initYearRange();
  initViewDrawer(table);

  if (hasPermission("holidays.add_holiday")) {
    document.getElementById("rp-holidays-add-btn")?.removeAttribute("hidden");
    initAddButton(table);
  }
  if (hasPermission("holidays.change_holiday")) {
    initEditDrawer(table);
  }
  if (hasPermission("holidays.delete_holiday")) {
    initDeleteModal(table);
  }
  if (hasPermission("holidays.import_holiday")) {
    document.getElementById("rp-holidays-import-btn")?.removeAttribute("hidden");
    initImportView(table);
  }
  if (hasPermission("holidays.export_holiday")) {
    document.getElementById("rp-holidays-export-btn")?.removeAttribute("hidden");
    initExportView();
  }
});
