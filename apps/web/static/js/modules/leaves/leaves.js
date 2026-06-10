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
import { API_URLS } from "../main/urls.js";
import { hasPermission } from "../utils/index.js";

let pendingRow = null;

function formatLeaveType(row) {
  if (!row.is_half_day) return "Full day";
  const period = row.half_day_period_display || row.half_day_period;
  return period ? `Half day (${period})` : "Half day";
}

function formatMemberName(row) {
  if (!row.member) return "—";
  return row.member.display_name || row.member.email || row.member.code || "—";
}

window.renderLeavesRow = function renderLeavesRow(row) {
  const member = esc(formatMemberName(row));
  const leaveType = esc(formatLeaveType(row));
  const days = row.days != null ? esc(String(row.days)) : "—";

  return `
    <td class="fw-medium">${member}</td>
    <td>${esc(row.start_date ?? "—")}</td>
    <td style="color:var(--rp-text-muted)">${esc(row.end_date ?? "—")}</td>
    <td style="color:var(--rp-text-muted)">${days}</td>
    <td style="color:var(--rp-text-muted)">${leaveType}</td>
    <td><code class="rp-mono">${esc(row.code)}</code></td>
  `;
};

function openDeleteModal(row) {
  const modal = document.getElementById("rp-leave-delete-modal");
  if (!modal) return;
  pendingRow = row;
  const label = formatMemberName(row);
  modal.setAttribute("title", `Delete leave for "${label}"?`);
  modal.setAttribute(
    "body",
    `This will permanently remove the leave record (${esc(row.start_date)} – ${esc(row.end_date)}).`,
  );
  modal.setAttribute("confirm-value", row.code);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-leave-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:leave:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;

    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.leaves.delete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Leave deleted",
        message: `Leave record has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete leave. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function _toggleHalfDayPeriod(drawerPrefix, isHalfDay) {
  const periodField = document.getElementById(`${drawerPrefix}-half-day-period`);
  if (!periodField) return;
  const wrapper = periodField.closest(".col-md-6, [class*='col']");
  if (wrapper) wrapper.style.display = isHalfDay ? "" : "none";
  if (!isHalfDay && periodField.value) periodField.value = "";
}

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-leave-edit-drawer");
  if (!drawer) return;

  pendingRow = row;

  const memberView = document.getElementById("rp-edit-leave-member");
  const startDateField = document.getElementById("rp-edit-leave-start-date");
  const endDateField = document.getElementById("rp-edit-leave-end-date");
  const isHalfDayField = document.getElementById("rp-edit-leave-is-half-day");
  const halfDayPeriodField = document.getElementById("rp-edit-leave-half-day-period");
  const noteField = document.getElementById("rp-edit-leave-note");

  if (memberView) memberView.value = formatMemberName(row);
  if (startDateField) startDateField.value = row.start_date ?? "";
  if (endDateField) endDateField.value = row.end_date ?? "";
  if (isHalfDayField) isHalfDayField.checked = Boolean(row.is_half_day);
  if (halfDayPeriodField) halfDayPeriodField.value = row.half_day_period ?? "";
  const noteInput = noteField?.querySelector(".rp-input");
  if (noteInput) noteInput.value = row.note ?? "";

  _toggleHalfDayPeriod("rp-edit-leave", Boolean(row.is_half_day));

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
  const drawer = document.getElementById("rp-leave-edit-drawer");
  if (!drawer) return;

  const startDateField = document.getElementById("rp-edit-leave-start-date");
  const endDateField = document.getElementById("rp-edit-leave-end-date");
  const isHalfDayField = document.getElementById("rp-edit-leave-is-half-day");

  isHalfDayField?.addEventListener("change", () => {
    _toggleHalfDayPeriod("rp-edit-leave", isHalfDayField.checked);
    if (isHalfDayField.checked && startDateField?.value) {
      if (endDateField) endDateField.value = startDateField.value;
    }
  });

  function validateForm() {
    startDateField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    endDateField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow || !validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const halfDayPeriodField = document.getElementById("rp-edit-leave-half-day-period");
    const noteField = document.getElementById("rp-edit-leave-note");
    const noteInput = noteField?.querySelector(".rp-input");
    const isHalfDay = Boolean(isHalfDayField?.checked);

    const payload = {
      start_date: startDateField?.value ?? "",
      end_date: endDateField?.value ?? "",
      is_half_day: isHalfDay,
      half_day_period: isHalfDay ? halfDayPeriodField?.value || null : null,
      note: noteInput?.value.trim() ?? "",
    };

    const { href, method } = API_URLS.leaves.update(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({ type: "success", title: "Leave updated", message: "Leave record has been updated." });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to update leave. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function openViewDrawer(row) {
  const drawer = document.getElementById("rp-leave-view-drawer");
  if (!drawer) return;

  pendingRow = row;

  const setView = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.value = val || "—";
  };

  const memberName = formatMemberName(row);
  drawer.setTitle(`${memberName} — Leave`);

  setView("rp-view-leave-member", memberName);
  setView("rp-view-leave-start-date", row.start_date);
  setView("rp-view-leave-end-date", row.end_date);
  setView("rp-view-leave-days", row.days != null ? String(row.days) : null);
  setView("rp-view-leave-type", formatLeaveType(row));
  setView("rp-view-leave-note", row.note || null);
  setView("rp-view-leave-code", row.code);
  setView("rp-view-leave-created", formatDate(row.created_at));
  setView("rp-view-leave-created-by", row.created_by?.email ?? null);

  const metaEl = drawer.querySelector(".rp-rdrawer-foot-meta");
  if (metaEl) metaEl.textContent = formatMeta(row);

  drawer.show();
}

function initViewDrawer(table) {
  const drawer = document.getElementById("rp-leave-view-drawer");
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
  table.addEventListener("rp:leave:edit", (e) => openEditDrawer(e.detail.row));
}

function initAddButton(table) {
  const addBtn = document.getElementById("rp-leaves-add-btn");
  const drawer = document.getElementById("rp-leave-create-drawer");
  if (!addBtn || !drawer) return;

  const memberField = document.getElementById("rp-new-leave-member");
  const startDateField = document.getElementById("rp-new-leave-start-date");
  const endDateField = document.getElementById("rp-new-leave-end-date");
  const isHalfDayField = document.getElementById("rp-new-leave-is-half-day");
  const halfDayPeriodField = document.getElementById("rp-new-leave-half-day-period");
  const noteField = document.getElementById("rp-new-leave-note");

  function resetForm() {
    if (memberField) memberField.value = "";
    if (startDateField) startDateField.value = "";
    if (endDateField) endDateField.value = "";
    if (isHalfDayField) isHalfDayField.checked = false;
    if (halfDayPeriodField) halfDayPeriodField.value = "";
    const noteInput = noteField?.querySelector(".rp-input");
    if (noteInput) noteInput.value = "";
    _toggleHalfDayPeriod("rp-new-leave", false);
    drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
      el.textContent = "";
      el.hidden = true;
    });
    drawer
      .querySelectorAll(".rp-input.is-invalid")
      .forEach((el) => el.classList.remove("is-invalid"));
  }

  function validateForm() {
    memberField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    startDateField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    endDateField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  isHalfDayField?.addEventListener("change", () => {
    _toggleHalfDayPeriod("rp-new-leave", isHalfDayField.checked);
    if (isHalfDayField.checked && startDateField?.value) {
      if (endDateField) endDateField.value = startDateField.value;
    }
  });

  addBtn.addEventListener("click", () => {
    resetForm();
    drawer.show();
  });

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Creating…");

    const noteInput = noteField?.querySelector(".rp-input");
    const isHalfDay = Boolean(isHalfDayField?.checked);

    const payload = {
      member_code: memberField?.value ?? "",
      start_date: startDateField?.value ?? "",
      end_date: endDateField?.value ?? "",
      is_half_day: isHalfDay,
      half_day_period: isHalfDay ? halfDayPeriodField?.value || null : null,
      note: noteInput?.value.trim() ?? "",
    };

    const { href, method } = API_URLS.leaves.create();
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      table.refresh();
      toast({ type: "success", title: "Leave created", message: "Leave record has been added." });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to create leave. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initImportView(table) {
  const importView = document.getElementById("rp-leaves-import-view");
  const importBtn = document.getElementById("rp-leaves-import-btn");
  if (!importView || !importBtn) return;

  importView.setAttribute("specs-url", API_URLS.leaves.importSpecs().href);
  importView.setAttribute("sample-url", API_URLS.leaves.importSample().href);
  importView.setAttribute("import-url", API_URLS.leaves.import().href);

  importBtn.addEventListener("click", () => importView.show());
  importView.addEventListener("rp:import:complete", () => table.refresh());
}

function initExportView() {
  const exportView = document.getElementById("rp-leaves-export-view");
  const exportBtn = document.getElementById("rp-leaves-export-btn");
  if (!exportView || !exportBtn) return;

  exportView.setAttribute("specs-url", API_URLS.leaves.exportSpecs().href);
  exportView.setAttribute("export-url", API_URLS.leaves.export().href);

  exportBtn.addEventListener("click", () => exportView.show());
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-leaves-table");
  if (!table) return;

  initActions(table);
  initViewDrawer(table);

  if (hasPermission("leaves.add_leave")) {
    document.getElementById("rp-leaves-add-btn")?.removeAttribute("hidden");
    initAddButton(table);
  }
  if (hasPermission("leaves.change_leave")) {
    initEditDrawer(table);
  }
  if (hasPermission("leaves.delete_leave")) {
    initDeleteModal(table);
  }
  if (hasPermission("leaves.import_leave")) {
    document.getElementById("rp-leaves-import-btn")?.removeAttribute("hidden");
    initImportView(table);
  }
  if (hasPermission("leaves.export_leave")) {
    document.getElementById("rp-leaves-export-btn")?.removeAttribute("hidden");
    initExportView();
  }
});
