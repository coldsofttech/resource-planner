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

window.renderFinancialYearsRow = function renderFinancialYearsRow(row) {
  const activeBadge = row.is_active
    ? '<span class="rp-badge rp-badge-soft rp-badge-success">Active</span>'
    : '<span class="rp-badge rp-badge-soft">Inactive</span>';

  const isExpiring = row.status === "in_progress" && row.in_threshold;
  const daysLeft = row.days_remaining ?? 0;
  const endDateCell = isExpiring
    ? `<span style="color:var(--rp-color-danger-text)">${esc(row.end_date || "—")}</span>` +
      `<span class="rp-badge rp-badge-soft rp-badge-danger ms-1">${daysLeft <= 0 ? "Today" : `${daysLeft}d`}</span>`
    : esc(row.end_date || "—");

  return `
    <td class="fw-medium">${esc(row.long_fy)}</td>
    <td style="color:var(--rp-text-muted)">${esc(row.short_fy)}</td>
    <td><code class="rp-mono">${esc(row.code)}</code></td>
    <td style="color:var(--rp-text-muted)">${esc(row.start_date || "—")}</td>
    <td style="color:var(--rp-text-muted)">${endDateCell}</td>
    <td style="color:var(--rp-text-muted)">${esc(String(row.span_days ?? "—"))}</td>
    <td>${statusBadge(row.status)}</td>
    <td>${activeBadge}</td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.created_at)}</td>
  `;
};

function openDeleteModal(row) {
  const modal = document.getElementById("rp-fy-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete "${row.long_fy}"?`);
  modal.setAttribute(
    "body",
    "This will permanently remove the financial year and all associated data.",
  );
  modal.setAttribute("confirm-value", row.long_fy);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-fy-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:fy:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;
    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");
    const { href, method } = API_URLS.fy.delete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Financial year deleted",
        message: `"${pendingRow.long_fy}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete financial year. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initToggleModals(table) {
  const activateModal = document.getElementById("rp-fy-activate-modal");
  const deactivateModal = document.getElementById("rp-fy-deactivate-modal");
  if (!activateModal || !deactivateModal) return;

  let toggleRow = null;

  table.addEventListener("rp:fy:toggle", (e) => {
    toggleRow = e.detail.row;
    if (toggleRow.is_active) {
      deactivateModal.setAttribute("title", `Deactivate "${toggleRow.long_fy}"?`);
      deactivateModal.setAttribute("body", "This will hide the financial year from active use.");
      deactivateModal.show();
    } else {
      activateModal.setAttribute("title", `Activate "${toggleRow.long_fy}"?`);
      activateModal.setAttribute("body", "This will re-enable the financial year.");
      activateModal.show();
    }
  });

  async function handleToggleConfirm(modal, isActivating) {
    if (!toggleRow) return;
    const actionBtn = modal.querySelector("[data-action-modal]");
    actionBtn?.setAttribute("disabled", "");
    const { href, method } = isActivating
      ? API_URLS.fy.activate(toggleRow.code)
      : API_URLS.fy.deactivate(toggleRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: isActivating ? "Financial year activated" : "Financial year deactivated",
        message: `"${toggleRow.long_fy}" has been ${isActivating ? "activated" : "deactivated"}.`,
      });
      toggleRow = null;
    } catch (err) {
      actionBtn?.removeAttribute("disabled");
      const msg =
        err?.data?.error?.message ??
        `Failed to ${isActivating ? "activate" : "deactivate"} financial year.`;
      toast({ type: "error", title: "Error", message: msg });
    }
  }

  activateModal.addEventListener("rp:confirm", () => handleToggleConfirm(activateModal, true));
  deactivateModal.addEventListener("rp:confirm", () => handleToggleConfirm(deactivateModal, false));
}

function initSetActiveAction(table) {
  table.addEventListener("rp:fy:set-active", (e) => {
    const row = e.detail.row;
    statusModal.open({
      iconType: "warning",
      title: `Set "${row.long_fy}" to In Progress?`,
      body: "This will mark the financial year as In Progress. Any currently active financial year will be set to Completed.",
      closeable: true,
      dismissBtn: { label: "Cancel", onClick: () => statusModal.close() },
      primaryBtn: {
        label: "Set In Progress",
        onClick: async () => {
          statusModal.update({ iconType: "info", title: "Updating…", body: "" });
          const { href, method } = API_URLS.fy.setActive(row.code);
          try {
            await apiFetch(href, { method });
            statusModal.close();
            table.refresh();
            toast({
              type: "success",
              title: "Status updated",
              message: `"${row.long_fy}" is now In Progress.`,
            });
          } catch (err) {
            statusModal.close();
            const msg = err?.data?.error?.message ?? "Failed to set financial year to In Progress.";
            toast({ type: "error", title: "Error", message: msg });
          }
        },
      },
    });
  });
}

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-fy-edit-drawer");
  if (!drawer) return;

  pendingRow = row;

  const longEl = document.getElementById("rp-edit-fy-long");
  const shortEl = document.getElementById("rp-edit-fy-short");
  const startField = document.getElementById("rp-edit-fy-start-date");
  const endField = document.getElementById("rp-edit-fy-end-date");
  const noteField = document.getElementById("rp-edit-fy-note");

  if (longEl) longEl.value = row.long_fy ?? "";
  if (shortEl) shortEl.value = row.short_fy ?? "";
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
  const drawer = document.getElementById("rp-fy-edit-drawer");
  if (!drawer) return;

  const startField = document.getElementById("rp-edit-fy-start-date");
  const endField = document.getElementById("rp-edit-fy-end-date");

  function validateForm() {
    startField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    endField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow || !validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const startField = document.getElementById("rp-edit-fy-start-date");
    const endField = document.getElementById("rp-edit-fy-end-date");
    const noteField = document.getElementById("rp-edit-fy-note");

    const payload = {
      start_date: startField?.value ?? "",
      end_date: endField?.value ?? "",
      note: noteField?.value ?? "",
    };

    const { href, method } = API_URLS.fy.update(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Financial year updated",
        message: `"${payload.start_date} – ${payload.end_date}" has been updated.`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to update financial year. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function openViewDrawer(row) {
  const drawer = document.getElementById("rp-fy-view-drawer");
  if (!drawer) return;

  pendingRow = row;

  const setView = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.value = val || "—";
  };

  drawer.setTitle(row.long_fy);
  setView("rp-view-fy-long", row.long_fy);
  setView("rp-view-fy-short", row.short_fy);
  setView("rp-view-fy-code", row.code);
  setView("rp-view-fy-start", row.start_date);
  setView("rp-view-fy-end", row.end_date);
  setView("rp-view-fy-span", row.span_days != null ? String(row.span_days) : "—");
  setView("rp-view-fy-status", statusBadge(row.status));
  setView("rp-view-fy-note", row.note || "—");
  setView("rp-view-fy-created", formatDate(row.created_at));
  setView("rp-view-fy-created-by", row.created_by?.email ?? "—");

  const metaEl = drawer.querySelector(".rp-rdrawer-foot-meta");
  if (metaEl) metaEl.textContent = formatMeta(row);

  drawer.show();
}

function initViewDrawer(table) {
  const drawer = document.getElementById("rp-fy-view-drawer");
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
  table.addEventListener("rp:fy:edit", (e) => openEditDrawer(e.detail.row));
}

function initAddButton(table) {
  const addBtn = document.getElementById("rp-fys-add-btn");
  const drawer = document.getElementById("rp-fy-create-drawer");
  if (!addBtn || !drawer) return;

  const startField = document.getElementById("rp-new-fy-start-date");
  const endField = document.getElementById("rp-new-fy-end-date");
  const noteField = document.getElementById("rp-new-fy-note");

  function resetForm() {
    if (startField) startField.value = "";
    if (endField) endField.value = "";
    if (noteField) noteField.value = "";
    drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
      el.textContent = "";
      el.hidden = true;
    });
    drawer
      .querySelectorAll(".rp-input.is-invalid")
      .forEach((el) => el.classList.remove("is-invalid"));
  }

  function validateForm() {
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
      start_date: startField?.value ?? "",
      end_date: endField?.value ?? "",
      note: noteField?.value ?? "",
      is_active: true,
    };

    const { href, method } = API_URLS.fy.create();
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      table.refresh();
      toast({
        type: "success",
        title: "Financial year created",
        message: `"${payload.start_date} – ${payload.end_date}" has been added.`,
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to create financial year. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initImportView(table) {
  const importView = document.getElementById("rp-fys-import-view");
  const importBtn = document.getElementById("rp-fys-import-btn");
  if (!importView || !importBtn) return;

  importView.setAttribute("specs-url", API_URLS.fy.importSpecs().href);
  importView.setAttribute("sample-url", API_URLS.fy.importSample().href);
  importView.setAttribute("import-url", API_URLS.fy.import().href);

  importBtn.addEventListener("click", () => importView.show());
  importView.addEventListener("rp:import:complete", () => table.refresh());
}

function initExportView() {
  const exportView = document.getElementById("rp-fys-export-view");
  const exportBtn = document.getElementById("rp-fys-export-btn");
  if (!exportView || !exportBtn) return;

  exportView.setAttribute("specs-url", API_URLS.fy.exportSpecs().href);
  exportView.setAttribute("export-url", API_URLS.fy.export().href);

  exportBtn.addEventListener("click", () => exportView.show());
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-fys-table");
  if (!table) return;

  setBreadcrumbs([
    { label: "Administration" },
    { label: "Planning" },
    { label: "Financial Years", href: UI_URLS.fy.list() },
  ]);

  initActions(table);
  initViewDrawer(table);

  if (hasPermission("financial_years.add_financialyear")) {
    document.getElementById("rp-fys-add-btn")?.removeAttribute("hidden");
    initAddButton(table);
  }
  if (hasPermission("financial_years.change_financialyear")) {
    initEditDrawer(table);
    initToggleModals(table);
    initSetActiveAction(table);
  }
  if (hasPermission("financial_years.delete_financialyear")) {
    initDeleteModal(table);
  }
  if (hasPermission("financial_years.import_financialyear")) {
    document.getElementById("rp-fys-import-btn")?.removeAttribute("hidden");
    initImportView(table);
  }
  if (hasPermission("financial_years.export_financialyear")) {
    document.getElementById("rp-fys-export-btn")?.removeAttribute("hidden");
    initExportView();
  }
});
