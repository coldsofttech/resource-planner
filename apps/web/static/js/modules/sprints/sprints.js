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
import { hasPermission, statusModal } from "../utils/index.js";

let pendingRow = null;

const STATUS_LABELS = {
  in_progress: "In Progress",
  future: "Future",
  completed: "Completed",
  expired: "Expired",
};

const STATUS_BADGE_CLASS = {
  in_progress: "rp-badge-soft rp-badge-success",
  future: "rp-badge-soft rp-badge-info",
  completed: "rp-badge-soft rp-badge-neutral",
  expired: "rp-badge-soft rp-badge-danger",
};

function formatStatus(status) {
  return STATUS_LABELS[status] || status;
}

function statusBadge(status) {
  const cls = STATUS_BADGE_CLASS[status] || "rp-badge-soft";
  return `<span class="rp-badge ${cls}">${esc(formatStatus(status))}</span>`;
}

function closedBadge(isClosed) {
  return isClosed
    ? '<span class="rp-badge rp-badge-soft rp-badge-warning">Locked</span>'
    : '<span class="rp-badge rp-badge-soft">Open</span>';
}

window.renderSprintsRow = function renderSprintsRow(row) {
  const activeBadge = row.is_active
    ? '<span class="rp-badge rp-badge-soft rp-badge-success">Active</span>'
    : '<span class="rp-badge rp-badge-soft">Inactive</span>';

  const fyLabel = row.financial_year
    ? esc(row.financial_year.short_fy || row.financial_year.long_fy)
    : "—";

  return `
    <td>${esc(row.name)}</td>
    <td style="color:var(--rp-text-muted)">${fyLabel}</td>
    <td><code class="rp-mono">${esc(row.code)}</code></td>
    <td style="color:var(--rp-text-muted)">${esc(row.start_date || "—")}</td>
    <td style="color:var(--rp-text-muted)">${esc(row.end_date || "—")}</td>
    <td style="color:var(--rp-text-muted)">${esc(row.month || "—")}</td>
    <td>${statusBadge(row.status)}</td>
    <td>${closedBadge(row.is_closed)}</td>
    <td>${activeBadge}</td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.created_at)}</td>
  `;
};

function openDeleteModal(row) {
  const modal = document.getElementById("rp-sprint-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete "${row.name}"?`);
  modal.setAttribute("body", "This will permanently remove the sprint and all associated data.");
  modal.setAttribute("confirm-value", row.name);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-sprint-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:sprint:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;
    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");
    const { href, method } = API_URLS.sprints.delete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Sprint deleted",
        message: `"${pendingRow.name}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.message ?? "Failed to delete sprint. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initToggleModals(table) {
  const activateModal = document.getElementById("rp-sprint-activate-modal");
  const deactivateModal = document.getElementById("rp-sprint-deactivate-modal");
  if (!activateModal || !deactivateModal) return;

  let toggleRow = null;

  table.addEventListener("rp:sprint:toggle", (e) => {
    toggleRow = e.detail.row;
    if (toggleRow.is_active) {
      deactivateModal.setAttribute("title", `Deactivate "${toggleRow.name}"?`);
      deactivateModal.setAttribute("body", "This will hide the sprint from active use.");
      deactivateModal.show();
    } else {
      activateModal.setAttribute("title", `Activate "${toggleRow.name}"?`);
      activateModal.setAttribute("body", "This will re-enable the sprint.");
      activateModal.show();
    }
  });

  async function handleToggleConfirm(modal, isActivating) {
    if (!toggleRow) return;
    const actionBtn = modal.querySelector("[data-action-modal]");
    actionBtn?.setAttribute("disabled", "");
    const { href, method } = isActivating
      ? API_URLS.sprints.activate(toggleRow.code)
      : API_URLS.sprints.deactivate(toggleRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: isActivating ? "Sprint activated" : "Sprint deactivated",
        message: `"${toggleRow.name}" has been ${isActivating ? "activated" : "deactivated"}.`,
      });
      toggleRow = null;
    } catch (err) {
      actionBtn?.removeAttribute("disabled");
      const msg =
        err?.data?.message ?? `Failed to ${isActivating ? "activate" : "deactivate"} sprint.`;
      toast({ type: "error", title: "Error", message: msg });
    }
  }

  activateModal.addEventListener("rp:confirm", () => handleToggleConfirm(activateModal, true));
  deactivateModal.addEventListener("rp:confirm", () => handleToggleConfirm(deactivateModal, false));
}

function initSetActiveAction(table) {
  table.addEventListener("rp:sprint:set-active", (e) => {
    const row = e.detail.row;
    statusModal.open({
      iconType: "warning",
      title: `Set "${row.name}" to In Progress?`,
      body: "This will mark the sprint as In Progress. Any currently in-progress sprint will be set to Completed.",
      closeable: true,
      dismissBtn: { label: "Cancel", onClick: () => statusModal.close() },
      primaryBtn: {
        label: "Set In Progress",
        onClick: async () => {
          statusModal.update({ iconType: "info", title: "Updating…", body: "" });
          const { href, method } = API_URLS.sprints.setActive(row.code);
          try {
            await apiFetch(href, { method });
            statusModal.close();
            table.refresh();
            toast({
              type: "success",
              title: "Status updated",
              message: `"${row.name}" is now In Progress.`,
            });
          } catch (err) {
            statusModal.close();
            const msg = err?.data?.message ?? "Failed to set sprint to In Progress.";
            toast({ type: "error", title: "Error", message: msg });
          }
        },
      },
    });
  });
}

function initCloseAction(table) {
  table.addEventListener("rp:sprint:close", (e) => {
    const row = e.detail.row;
    const isLocking = !row.is_closed;
    statusModal.open({
      iconType: isLocking ? "warning" : "info",
      title: isLocking ? `Lock "${row.name}"?` : `Unlock "${row.name}"?`,
      body: isLocking
        ? "Locking a sprint prevents further changes. You can unlock it later."
        : "Unlocking will allow changes to be made to this sprint again.",
      closeable: true,
      dismissBtn: { label: "Cancel", onClick: () => statusModal.close() },
      primaryBtn: {
        label: isLocking ? "Lock Sprint" : "Unlock Sprint",
        onClick: async () => {
          statusModal.update({ iconType: "info", title: "Updating…", body: "" });
          const { href, method } = API_URLS.sprints.close(row.code);
          try {
            await apiFetch(href, { method, body: JSON.stringify({ lock: isLocking }) });
            statusModal.close();
            table.refresh();
            toast({
              type: "success",
              title: isLocking ? "Sprint locked" : "Sprint unlocked",
              message: `"${row.name}" has been ${isLocking ? "locked" : "unlocked"}.`,
            });
          } catch (err) {
            statusModal.close();
            const msg = err?.data?.message ?? `Failed to ${isLocking ? "lock" : "unlock"} sprint.`;
            toast({ type: "error", title: "Error", message: msg });
          }
        },
      },
    });
  });
}

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-sprint-edit-drawer");
  if (!drawer) return;

  pendingRow = row;

  const nameField = document.getElementById("rp-edit-sprint-name");
  const startField = document.getElementById("rp-edit-sprint-start-date");
  const endField = document.getElementById("rp-edit-sprint-end-date");
  const noteField = document.getElementById("rp-edit-sprint-note");

  if (nameField) nameField.value = row.name ?? "";
  if (startField) startField.value = row.start_date ?? "";
  if (endField) endField.value = row.end_date ?? "";
  if (noteField) noteField.value = row.note ?? "";

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
  const drawer = document.getElementById("rp-sprint-edit-drawer");
  if (!drawer) return;

  const nameField = document.getElementById("rp-edit-sprint-name");
  const startField = document.getElementById("rp-edit-sprint-start-date");
  const endField = document.getElementById("rp-edit-sprint-end-date");

  function validateForm() {
    nameField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    startField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    endField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow || !validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const payload = {
      name: document.getElementById("rp-edit-sprint-name")?.value ?? "",
      start_date: document.getElementById("rp-edit-sprint-start-date")?.value ?? "",
      end_date: document.getElementById("rp-edit-sprint-end-date")?.value ?? "",
      note: document.getElementById("rp-edit-sprint-note")?.value ?? "",
    };

    const { href, method } = API_URLS.sprints.update(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Sprint updated",
        message: `"${payload.name}" has been updated.`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.message ?? "Failed to update sprint. Please try again.";
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
    window.location.href = UI_URLS.sprints.detail(row.code);
  });
}

function initActions(table) {
  table.addEventListener("rp:sprint:edit", (e) => openEditDrawer(e.detail.row));
}

function initAddButton(table) {
  const addBtn = document.getElementById("rp-sprints-add-btn");
  const drawer = document.getElementById("rp-sprint-create-drawer");
  if (!addBtn || !drawer) return;

  const fyField = document.getElementById("rp-new-sprint-fy-code");
  const numberField = document.getElementById("rp-new-sprint-number");
  const nameField = document.getElementById("rp-new-sprint-name");
  const startField = document.getElementById("rp-new-sprint-start-date");
  const endField = document.getElementById("rp-new-sprint-end-date");
  const noteField = document.getElementById("rp-new-sprint-note");

  function resetForm() {
    [fyField, numberField, nameField, startField, endField, noteField].forEach((f) => {
      if (f) f.value = "";
    });
    drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
      el.textContent = "";
      el.hidden = true;
    });
    drawer
      .querySelectorAll(".rp-input.is-invalid")
      .forEach((el) => el.classList.remove("is-invalid"));
  }

  function validateForm() {
    fyField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    numberField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    startField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    endField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
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
      fy_code: fyField?.value ?? "",
      sprint_number: parseInt(numberField?.value ?? "0", 10),
      name: nameField?.value ?? "",
      start_date: startField?.value ?? "",
      end_date: endField?.value ?? "",
      note: noteField?.value ?? "",
      is_active: true,
    };

    const { href, method } = API_URLS.sprints.create();
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      table.refresh();
      toast({
        type: "success",
        title: "Sprint created",
        message: `"${payload.name || `Sprint ${payload.sprint_number}`}" has been added.`,
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.message ?? "Failed to create sprint. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initGenerateButton(table) {
  const generateBtn = document.getElementById("rp-sprints-generate-btn");
  const drawer = document.getElementById("rp-sprint-generate-drawer");
  if (!generateBtn || !drawer) return;

  const fyField = document.getElementById("rp-generate-sprint-fy");

  function resetForm() {
    if (fyField) fyField.value = "";
    drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
      el.textContent = "";
      el.hidden = true;
    });
  }

  function validateForm() {
    fyField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  generateBtn.addEventListener("click", () => {
    resetForm();
    drawer.show();
  });

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!validateForm()) return;
    const fyCode = fyField?.value ?? "";
    if (!fyCode) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Generating…");

    const { href, method } = API_URLS.sprints.generate();
    try {
      const res = await apiFetch(href, { method, body: JSON.stringify({ fy_code: fyCode }) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      table.refresh();
      const count = Array.isArray(res?.data) ? res.data.length : "";
      toast({
        type: "success",
        title: "Sprints generated",
        message: count
          ? `${count} sprint(s) created for ${fyCode}.`
          : `Sprints created for ${fyCode}.`,
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.message ?? "Failed to generate sprints. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initImportView(table) {
  const importView = document.getElementById("rp-sprints-import-view");
  const importBtn = document.getElementById("rp-sprints-import-btn");
  if (!importView || !importBtn) return;

  importView.setAttribute("specs-url", API_URLS.sprints.importSpecs().href);
  importView.setAttribute("sample-url", API_URLS.sprints.importSample().href);
  importView.setAttribute("import-url", API_URLS.sprints.import().href);

  importBtn.addEventListener("click", () => importView.show());
  importView.addEventListener("rp:import:complete", () => table.refresh());
}

function initExportView() {
  const exportView = document.getElementById("rp-sprints-export-view");
  const exportBtn = document.getElementById("rp-sprints-export-btn");
  if (!exportView || !exportBtn) return;

  exportView.setAttribute("specs-url", API_URLS.sprints.exportSpecs().href);
  exportView.setAttribute("export-url", API_URLS.sprints.export().href);

  exportBtn.addEventListener("click", () => exportView.show());
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-sprints-table");
  if (!table) return;

  setBreadcrumbs([
    { label: "Project" },
    { label: "Planning" },
    { label: "Sprints", href: UI_URLS.sprints.list() },
  ]);

  initActions(table);
  initRowNavigation(table);

  if (hasPermission("sprints.add_sprint")) {
    document.getElementById("rp-sprints-add-btn")?.removeAttribute("hidden");
    initAddButton(table);
  }
  if (hasPermission("sprints.change_sprint")) {
    initEditDrawer(table);
    initToggleModals(table);
    initSetActiveAction(table);
  }
  if (hasPermission("sprints.close_sprint")) {
    initCloseAction(table);
  }
  if (hasPermission("sprints.delete_sprint")) {
    initDeleteModal(table);
  }
  if (hasPermission("sprints.generate_sprint")) {
    document.getElementById("rp-sprints-generate-btn")?.removeAttribute("hidden");
    initGenerateButton(table);
  }
  if (hasPermission("sprints.import_sprint")) {
    document.getElementById("rp-sprints-import-btn")?.removeAttribute("hidden");
    initImportView(table);
  }
  if (hasPermission("sprints.export_sprint")) {
    document.getElementById("rp-sprints-export-btn")?.removeAttribute("hidden");
    initExportView();
  }
});
