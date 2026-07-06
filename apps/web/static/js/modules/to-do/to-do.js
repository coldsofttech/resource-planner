"use strict";

import { esc } from "../../components/utils.js";
import {
  apiFetch,
  formatDate,
  snapshotButton,
  setBusyButton,
  restoreButton,
} from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS } from "../main/urls.js";

let pendingRow = null;

const PRIORITY_BADGE = {
  low: "rp-badge-neutral",
  medium: "rp-badge-info",
  high: "rp-badge-warning",
  urgent: "rp-badge-danger",
};

const STATUS_LABEL = { open: "Not started", in_progress: "In progress", done: "Done" };

function formatMeta(row) {
  if (!row.due_date) return "";
  return row.is_overdue ? `Overdue — ${formatDate(row.due_date)}` : formatDate(row.due_date);
}

window.renderToDoRow = function renderToDoRow(row) {
  const priorityBadge = PRIORITY_BADGE[row.priority] ?? "rp-badge-neutral";
  const statusBadge = row.status === "done" ? "rp-badge-success" : "rp-badge-neutral";
  const dueText = formatMeta(row);
  const dueStyle = row.is_overdue ? 'style="color:var(--rp-danger)"' : "";

  return `
    <td><span class="rp-badge-soft ${priorityBadge}" style="width:10px;height:10px;border-radius:50%;display:inline-block;padding:0;"></span></td>
    <td class="fw-medium">${esc(row.title)}</td>
    <td style="color:var(--rp-text-muted)">${esc(row.group || "—")}</td>
    <td ${dueStyle}>${esc(dueText || "—")}</td>
    <td><span class="rp-badge ${statusBadge}">${esc(STATUS_LABEL[row.status] ?? row.status)}</span></td>
  `;
};

function openDeleteModal(row) {
  const modal = document.getElementById("rp-todo-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete "${row.title}"?`);
  modal.setAttribute("body", "This will permanently remove the to-do. This cannot be undone.");
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-todo-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:todo:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;
    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");
    const { href, method } = API_URLS.toDo.delete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "To-do deleted",
        message: `"${pendingRow.title}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete to-do.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initActions(table) {
  table.addEventListener("rp:todo:complete", async (e) => {
    const { href, method } = API_URLS.toDo.complete(e.detail.row.code);
    try {
      await apiFetch(href, { method });
      table.refresh();
      toast({ type: "success", title: "To-do completed", message: "Nice work." });
    } catch {
      toast({ type: "error", title: "Error", message: "Failed to mark to-do complete." });
    }
  });

  table.addEventListener("rp:todo:reopen", async (e) => {
    const { href, method } = API_URLS.toDo.reopen(e.detail.row.code);
    try {
      await apiFetch(href, { method });
      table.refresh();
      toast({ type: "success", title: "To-do reopened" });
    } catch {
      toast({ type: "error", title: "Error", message: "Failed to reopen to-do." });
    }
  });
}

function fillFormFromRow(prefix, row) {
  document.getElementById(`${prefix}-title`).value = row.title;
  document.getElementById(`${prefix}-description`).value = row.description ?? "";
  document.getElementById(`${prefix}-priority`).value = row.priority;
  document.getElementById(`${prefix}-group`).value = row.group ?? "";
  document.getElementById(`${prefix}-due-date`).value = row.due_date ?? "";
  document.getElementById(`${prefix}-reminder-date`).value = row.reminder_at
    ? row.reminder_at.slice(0, 10)
    : "";
  document.getElementById(`${prefix}-is-recurring`).checked = !!row.is_recurring;
  document.getElementById(`${prefix}-recurrence-rule`).value = row.recurrence_rule ?? "";
  document.getElementById(`${prefix}-recurrence-end-date`).value = row.recurrence_end_date ?? "";
}

function buildPayloadFromForm(prefix) {
  const reminderDate = document.getElementById(`${prefix}-reminder-date`).value;
  return {
    title: document.getElementById(`${prefix}-title`).value.trim(),
    description: document.getElementById(`${prefix}-description`).value,
    priority: document.getElementById(`${prefix}-priority`).value,
    group: document.getElementById(`${prefix}-group`).value,
    due_date: document.getElementById(`${prefix}-due-date`).value || null,
    reminder_at: reminderDate ? `${reminderDate}T09:00:00` : null,
    is_recurring: document.getElementById(`${prefix}-is-recurring`).checked,
    recurrence_rule: document.getElementById(`${prefix}-recurrence-rule`).value,
    recurrence_interval: 1,
    recurrence_end_date: document.getElementById(`${prefix}-recurrence-end-date`).value || null,
  };
}

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-todo-edit-drawer");
  if (!drawer) return;
  pendingRow = row;
  fillFormFromRow("rp-edit-todo", row);
  drawer.show();
}

function initEditDrawer(table) {
  const drawer = document.getElementById("rp-todo-edit-drawer");
  if (!drawer) return;

  table.addEventListener("rp:todo:edit", (e) => openEditDrawer(e.detail.row));

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow) return;
    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");
    const { href, method } = API_URLS.toDo.update(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(buildPayloadFromForm("rp-edit-todo")) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({ type: "success", title: "To-do updated" });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to update to-do.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function openViewDrawer(row) {
  const drawer = document.getElementById("rp-todo-view-drawer");
  if (!drawer) return;
  pendingRow = row;
  document.getElementById("rp-view-todo-title").setAttribute("value", row.title);
  document.getElementById("rp-view-todo-description").setAttribute("value", row.description || "—");
  document
    .getElementById("rp-view-todo-status")
    .setAttribute("value", STATUS_LABEL[row.status] ?? row.status);
  document
    .getElementById("rp-view-todo-priority")
    .setAttribute("value", row.priority_display ?? row.priority);
  document.getElementById("rp-view-todo-group").setAttribute("value", row.group || "—");
  document
    .getElementById("rp-view-todo-due-date")
    .setAttribute("value", row.due_date ? formatDate(row.due_date) : "—");
  document
    .getElementById("rp-view-todo-source")
    .setAttribute("value", row.source === "mention" ? "Comment mention" : "Manual");
  document.getElementById("rp-view-todo-code").setAttribute("value", row.code);
  document.getElementById("rp-view-todo-created").setAttribute("value", formatDate(row.created_at));
  document
    .getElementById("rp-view-todo-created-by")
    .setAttribute("value", row.created_by?.display_name || row.created_by?.email || "—");
  drawer.show();
}

function initViewDrawer(table) {
  const drawer = document.getElementById("rp-todo-view-drawer");
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

function resetCreateForm() {
  const prefix = "rp-new-todo";
  document.getElementById(`${prefix}-title`).value = "";
  document.getElementById(`${prefix}-description`).value = "";
  document.getElementById(`${prefix}-priority`).value = "medium";
  document.getElementById(`${prefix}-group`).value = "";
  document.getElementById(`${prefix}-due-date`).value = "";
  document.getElementById(`${prefix}-reminder-date`).value = "";
  document.getElementById(`${prefix}-is-recurring`).checked = false;
  document.getElementById(`${prefix}-recurrence-rule`).value = "";
  document.getElementById(`${prefix}-recurrence-end-date`).value = "";
}

function validateCreateForm() {
  const titleField = document.getElementById("rp-new-todo-title");
  titleField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
  return !document
    .getElementById("rp-todo-create-drawer")
    .querySelector("[data-rp-error]:not([hidden])");
}

function initAddButton(table) {
  const addBtn = document.getElementById("rp-to-do-add-btn");
  const drawer = document.getElementById("rp-todo-create-drawer");
  if (!addBtn || !drawer) return;

  addBtn.addEventListener("click", () => {
    resetCreateForm();
    drawer.show();
  });

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!validateCreateForm()) return;
    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Creating…");
    const { href, method } = API_URLS.toDo.create();
    try {
      await apiFetch(href, {
        method,
        body: JSON.stringify(buildPayloadFromForm("rp-new-todo")),
      });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetCreateForm();
      table.refresh();
      window.dispatchEvent(new CustomEvent("rp:todo-created"));
      toast({ type: "success", title: "To-do created" });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to create to-do.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-to-do-table");
  if (!table) return;

  initActions(table);
  initAddButton(table);
  initDeleteModal(table);
  initEditDrawer(table);
  initViewDrawer(table);
});
