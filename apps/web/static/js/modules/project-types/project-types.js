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

window.renderProjectTypesRow = function renderProjectTypesRow(row) {
  const badgeCls = row.is_active ? "rp-badge-soft rp-badge-success" : "rp-badge-soft";
  const statusLabel = row.is_active ? "Active" : "Inactive";
  const description = row.description
    ? esc(row.description)
    : `<span style="color:var(--rp-text-muted)">—</span>`;
  const nameSuffix = row.is_protected
    ? ` <span class="rp-badge rp-badge-soft" style="font-size:0.7em">Protected</span>`
    : "";

  return `
    <td class="fw-medium">${esc(row.name)}${nameSuffix}</td>
    <td><code class="rp-mono">${esc(row.code)}</code></td>
    <td style="color:var(--rp-text-muted)">${description}</td>
    <td><span class="rp-badge ${badgeCls}">${statusLabel}</span></td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.created_at)}</td>
  `;
};

function openDeleteModal(row) {
  const modal = document.getElementById("rp-project-type-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete "${row.name}"?`);
  modal.setAttribute(
    "body",
    "This will permanently remove the project type and all associated data.",
  );
  modal.setAttribute("confirm-value", row.name);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-project-type-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:project-type:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;

    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.projectTypes.delete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Project type deleted",
        message: `"${pendingRow.name}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete project type. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initToggleModals(table) {
  const activateModal = document.getElementById("rp-project-type-activate-modal");
  const deactivateModal = document.getElementById("rp-project-type-deactivate-modal");
  if (!activateModal || !deactivateModal) return;

  let toggleRow = null;

  table.addEventListener("rp:project-type:toggle", (e) => {
    toggleRow = e.detail.row;
    if (toggleRow.is_active) {
      deactivateModal.setAttribute("title", `Deactivate "${toggleRow.name}"?`);
      deactivateModal.setAttribute(
        "body",
        "This will disable the project type and prevent it from being assigned to projects.",
      );
      deactivateModal.show();
    } else {
      activateModal.setAttribute("title", `Activate "${toggleRow.name}"?`);
      activateModal.setAttribute(
        "body",
        "This will re-enable the project type for project assignment.",
      );
      activateModal.show();
    }
  });

  async function handleToggleConfirm(modal, isActivating) {
    if (!toggleRow) return;

    const actionBtn = modal.querySelector("[data-action-modal]");
    actionBtn?.setAttribute("disabled", "");

    const { href, method } = isActivating
      ? API_URLS.projectTypes.activate(toggleRow.code)
      : API_URLS.projectTypes.deactivate(toggleRow.code);

    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: isActivating ? "Project type activated" : "Project type deactivated",
        message: `"${toggleRow.name}" has been ${isActivating ? "activated" : "deactivated"}.`,
      });
      toggleRow = null;
    } catch (err) {
      actionBtn?.removeAttribute("disabled");
      const msg =
        err?.data?.error?.message ??
        `Failed to ${isActivating ? "activate" : "deactivate"} project type. Please try again.`;
      toast({ type: "error", title: "Error", message: msg });
    }
  }

  activateModal.addEventListener("rp:confirm", () => handleToggleConfirm(activateModal, true));
  deactivateModal.addEventListener("rp:confirm", () => handleToggleConfirm(deactivateModal, false));
}

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-project-type-edit-drawer");
  if (!drawer) return;

  pendingRow = row;

  const nameInput = document
    .getElementById("rp-edit-project-type-name")
    ?.querySelector(".rp-input");
  const descInput = document
    .getElementById("rp-edit-project-type-description")
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
  const drawer = document.getElementById("rp-project-type-edit-drawer");
  if (!drawer) return;

  const nameField = document.getElementById("rp-edit-project-type-name");

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
      .getElementById("rp-edit-project-type-name")
      ?.querySelector(".rp-input");
    const descInput = document
      .getElementById("rp-edit-project-type-description")
      ?.querySelector(".rp-input");

    const payload = {
      name: nameInput?.value.trim() ?? "",
      description: descInput?.value.trim() ?? "",
    };

    const { href, method } = API_URLS.projectTypes.update(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Project type updated",
        message: `"${payload.name}" has been updated.`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.error?.message ??
        err?.data?.name?.[0] ??
        "Failed to update project type. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function openViewDrawer(row) {
  const drawer = document.getElementById("rp-project-type-view-drawer");
  if (!drawer) return;

  pendingRow = row;

  const setView = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.value = val || "—";
  };

  const statusBadge = row.is_active
    ? `<span class="rp-badge rp-badge-soft rp-badge-success">Active</span>`
    : `<span class="rp-badge rp-badge-soft">Inactive</span>`;
  const protectedBadge = row.is_protected
    ? `<span class="rp-badge rp-badge-soft">Protected</span>`
    : "No";

  setView("rp-view-project-type-name", row.name);
  setView("rp-view-project-type-code", row.code);
  setView("rp-view-project-type-status", statusBadge);
  setView("rp-view-project-type-protected", protectedBadge);
  setView("rp-view-project-type-description", row.description || "—");
  setView("rp-view-project-type-created", formatDate(row.created_at));
  setView("rp-view-project-type-created-by", row.created_by?.email ?? "—");

  const metaEl = drawer.querySelector(".rp-rdrawer-foot-meta");
  if (metaEl) metaEl.textContent = formatMeta(row);

  drawer.show();
}

function initViewDrawer(table) {
  const drawer = document.getElementById("rp-project-type-view-drawer");
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
  table.addEventListener("rp:project-type:edit", (e) => openEditDrawer(e.detail.row));
}

function initAddButton(table) {
  const addBtn = document.getElementById("rp-project-types-add-btn");
  const drawer = document.getElementById("rp-project-type-create-drawer");
  if (!addBtn || !drawer) return;

  const nameField = document.getElementById("rp-new-project-type-name");
  const descField = document.getElementById("rp-new-project-type-description");

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

    const { href, method } = API_URLS.projectTypes.create();
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      table.refresh();
      toast({
        type: "success",
        title: "Project type created",
        message: `"${payload.name}" has been added.`,
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.error?.message ??
        err?.data?.name?.[0] ??
        "Failed to create project type. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initImportView(table) {
  const importView = document.getElementById("rp-project-types-import-view");
  const importBtn = document.getElementById("rp-project-types-import-btn");
  if (!importView || !importBtn) return;

  importView.setAttribute("specs-url", API_URLS.projectTypes.importSpecs().href);
  importView.setAttribute("sample-url", API_URLS.projectTypes.importSample().href);
  importView.setAttribute("import-url", API_URLS.projectTypes.import().href);

  importBtn.addEventListener("click", () => importView.show());
  importView.addEventListener("rp:import:complete", () => table.refresh());
}

function initExportView() {
  const exportView = document.getElementById("rp-project-types-export-view");
  const exportBtn = document.getElementById("rp-project-types-export-btn");
  if (!exportView || !exportBtn) return;

  exportView.setAttribute("specs-url", API_URLS.projectTypes.exportSpecs().href);
  exportView.setAttribute("export-url", API_URLS.projectTypes.export().href);

  exportBtn.addEventListener("click", () => exportView.show());
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-project-types-table");
  if (!table) return;

  setBreadcrumbs([
    { label: "Project" },
    { label: "Configurations" },
    { label: "Project Types", href: UI_URLS.projectTypes.list() },
  ]);

  initActions(table);
  initViewDrawer(table);

  if (hasPermission("projects.add_projecttype")) {
    document.getElementById("rp-project-types-add-btn")?.removeAttribute("hidden");
    initAddButton(table);
  }
  if (hasPermission("projects.change_projecttype")) {
    initEditDrawer(table);
    initToggleModals(table);
  }
  if (hasPermission("projects.delete_projecttype")) {
    initDeleteModal(table);
  }
  if (hasPermission("projects.import_projecttype")) {
    document.getElementById("rp-project-types-import-btn")?.removeAttribute("hidden");
    initImportView(table);
  }
  if (hasPermission("projects.export_projecttype")) {
    document.getElementById("rp-project-types-export-btn")?.removeAttribute("hidden");
    initExportView();
  }
});
