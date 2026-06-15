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

/* ── Shared state ─────────────────────────────────────────────────────── */

let pendingRow = null;

/* ── Row renderer ─────────────────────────────────────────────────────── */

window.renderEmpTypesRow = function renderEmpTypesRow(row) {
  const badgeCls = row.is_active ? "rp-badge-soft rp-badge-success" : "rp-badge-soft";
  const statusLabel = row.is_active ? "Active" : "Inactive";
  const defaultCell = row.is_default
    ? '<span class="rp-badge rp-badge-soft">Default</span>'
    : '<span style="color:var(--rp-text-muted)">—</span>';

  return `
    <td class="fw-medium">${esc(row.name)}</td>
    <td><code class="rp-mono">${esc(row.code)}</code></td>
    <td>${defaultCell}</td>
    <td><span class="rp-badge ${badgeCls}">${statusLabel}</span></td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.created_at)}</td>
  `;
};

/* ── Delete modal ─────────────────────────────────────────────────────── */

function openDeleteModal(row) {
  const modal = document.getElementById("rp-emp-type-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete "${row.name}"?`);
  modal.setAttribute(
    "body",
    "This will permanently remove the employment type and all associated data.",
  );
  modal.setAttribute("confirm-value", row.name);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-emp-type-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:emp-type:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;

    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.empTypes.delete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Employment type deleted",
        message: `"${pendingRow.name}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg =
        err?.data?.error?.message ?? "Failed to delete employment type. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

/* ── Toggle (activate / deactivate) modals ───────────────────────────── */

function initToggleModals(table) {
  const activateModal = document.getElementById("rp-emp-type-activate-modal");
  const deactivateModal = document.getElementById("rp-emp-type-deactivate-modal");
  if (!activateModal || !deactivateModal) return;

  let toggleRow = null;

  table.addEventListener("rp:emp-type:toggle", (e) => {
    toggleRow = e.detail.row;
    if (toggleRow.is_active) {
      deactivateModal.setAttribute("title", `Deactivate "${toggleRow.name}"?`);
      deactivateModal.setAttribute(
        "body",
        "This will disable the employment type and prevent it from being assigned.",
      );
      deactivateModal.show();
    } else {
      activateModal.setAttribute("title", `Activate "${toggleRow.name}"?`);
      activateModal.setAttribute("body", "This will re-enable the employment type for assignment.");
      activateModal.show();
    }
  });

  async function handleToggleConfirm(modal, isActivating) {
    if (!toggleRow) return;

    const actionBtn = modal.querySelector("[data-action-modal]");
    actionBtn?.setAttribute("disabled", "");

    const { href, method } = isActivating
      ? API_URLS.empTypes.activate(toggleRow.code)
      : API_URLS.empTypes.deactivate(toggleRow.code);

    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: isActivating ? "Employment type activated" : "Employment type deactivated",
        message: `"${toggleRow.name}" has been ${isActivating ? "activated" : "deactivated"}.`,
      });
      toggleRow = null;
    } catch (err) {
      actionBtn?.removeAttribute("disabled");
      const msg =
        err?.data?.error?.message ??
        `Failed to ${isActivating ? "activate" : "deactivate"} employment type. Please try again.`;
      toast({ type: "error", title: "Error", message: msg });
    }
  }

  activateModal.addEventListener("rp:confirm", () => handleToggleConfirm(activateModal, true));
  deactivateModal.addEventListener("rp:confirm", () => handleToggleConfirm(deactivateModal, false));
}

/* ── Set-default modal ───────────────────────────────────────────────── */

function initSetDefaultModal(table) {
  const modal = document.getElementById("rp-emp-type-set-default-modal");
  if (!modal) return;

  let defaultRow = null;

  table.addEventListener("rp:emp-type:set-default", (e) => {
    defaultRow = e.detail.row;
    modal.setAttribute("title", `Set "${defaultRow.name}" as Default?`);
    modal.setAttribute(
      "body",
      "This will replace the current default employment type. Only one employment type can be the default at a time.",
    );
    modal.show();
  });

  modal.addEventListener("rp:confirm", async () => {
    if (!defaultRow) return;

    const actionBtn = modal.querySelector("[data-action-modal]");
    actionBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.empTypes.setDefault(defaultRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Default employment type set",
        message: `"${defaultRow.name}" is now the default employment type.`,
      });
      defaultRow = null;
    } catch (err) {
      actionBtn?.removeAttribute("disabled");
      const msg =
        err?.data?.error?.message ?? "Failed to set default employment type. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

/* ── Edit drawer ──────────────────────────────────────────────────────── */

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-emp-type-edit-drawer");
  if (!drawer) return;

  pendingRow = row;

  const nameInput = document.getElementById("rp-edit-emp-type-name")?.querySelector(".rp-input");
  if (nameInput) nameInput.value = row.name ?? "";

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
  const drawer = document.getElementById("rp-emp-type-edit-drawer");
  if (!drawer) return;

  const nameField = document.getElementById("rp-edit-emp-type-name");

  function validateForm() {
    nameField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow || !validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const nameInput = document.getElementById("rp-edit-emp-type-name")?.querySelector(".rp-input");

    const payload = {
      name: nameInput?.value.trim() ?? "",
    };

    const { href, method } = API_URLS.empTypes.update(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Employment type updated",
        message: `"${payload.name}" has been updated.`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.error?.message ??
        err?.data?.name?.[0] ??
        "Failed to update employment type. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

/* ── Row navigation ───────────────────────────────────────────────────── */

function initRowNavigation(table) {
  table.addEventListener("click", (e) => {
    if (e.target.closest("[data-rp-action]") || e.target.closest(".rp-table-more-btn")) return;
    const tr = e.target.closest("tr[data-rp-row]");
    if (!tr) return;
    const idx = parseInt(tr.getAttribute("data-rp-row"), 10);
    const row = table.rows[idx];
    if (!row) return;
    window.location.href = UI_URLS.empTypes.detail(row.code);
  });
}

/* ── Table action handlers ────────────────────────────────────────────── */

function initActions(table) {
  table.addEventListener("rp:emp-type:edit", (e) => openEditDrawer(e.detail.row));
}

/* ── Create drawer ───────────────────────────────────────────────────── */

function initAddButton(table) {
  const addBtn = document.getElementById("rp-emp-types-add-btn");
  const drawer = document.getElementById("rp-emp-type-create-drawer");
  if (!addBtn || !drawer) return;

  const nameField = document.getElementById("rp-new-emp-type-name");

  function resetForm() {
    const nameInput = nameField?.querySelector(".rp-input");
    if (nameInput) nameInput.value = "";
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
      is_active: true,
    };

    const { href, method } = API_URLS.empTypes.create();
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      table.refresh();
      toast({
        type: "success",
        title: "Employment type created",
        message: `"${payload.name}" has been added.`,
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.error?.message ??
        err?.data?.name?.[0] ??
        "Failed to create employment type. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

/* ── Import view ─────────────────────────────────────────────────────── */

function initImportView(table) {
  const importView = document.getElementById("rp-emp-types-import-view");
  const importBtn = document.getElementById("rp-emp-types-import-btn");
  if (!importView || !importBtn) return;

  importView.setAttribute("specs-url", API_URLS.empTypes.importSpecs().href);
  importView.setAttribute("sample-url", API_URLS.empTypes.importSample().href);
  importView.setAttribute("import-url", API_URLS.empTypes.import().href);

  importBtn.addEventListener("click", () => importView.show());

  importView.addEventListener("rp:import:complete", () => table.refresh());
}

/* ── Export view ─────────────────────────────────────────────────────── */

function initExportView() {
  const exportView = document.getElementById("rp-emp-types-export-view");
  const exportBtn = document.getElementById("rp-emp-types-export-btn");
  if (!exportView || !exportBtn) return;

  exportView.setAttribute("specs-url", API_URLS.empTypes.exportSpecs().href);
  exportView.setAttribute("export-url", API_URLS.empTypes.export().href);

  exportBtn.addEventListener("click", () => exportView.show());
}

/* ── Bootstrap ───────────────────────────────────────────────────────── */

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-emp-types-table");
  if (!table) return;

  setBreadcrumbs([
    { label: "Organisation" },
    { label: "Configurations" },
    { label: "Employment Types", href: UI_URLS.empTypes.list() },
  ]);

  initActions(table);
  initRowNavigation(table);

  if (hasPermission("employment_types.add_employmenttype")) {
    document.getElementById("rp-emp-types-add-btn")?.removeAttribute("hidden");
    initAddButton(table);
  }
  if (hasPermission("employment_types.change_employmenttype")) {
    initEditDrawer(table);
    initToggleModals(table);
    initSetDefaultModal(table);
  }
  if (hasPermission("employment_types.delete_employmenttype")) {
    initDeleteModal(table);
  }
  if (hasPermission("employment_types.import_employmenttype")) {
    document.getElementById("rp-emp-types-import-btn")?.removeAttribute("hidden");
    initImportView(table);
  }
  if (hasPermission("employment_types.export_employmenttype")) {
    document.getElementById("rp-emp-types-export-btn")?.removeAttribute("hidden");
    initExportView();
  }
});
