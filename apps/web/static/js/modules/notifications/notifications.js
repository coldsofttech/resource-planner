"use strict";

import { esc } from "../../components/utils.js";
import { apiFetch, formatDateTime } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS } from "../main/urls.js";

let pendingRow = null;

const TYPE_ICON = {
  info: "bi-info-circle-fill",
  success: "bi-check-circle-fill",
  warning: "bi-exclamation-triangle-fill",
  error: "bi-x-circle-fill",
  comment: "bi-chat-left-text-fill",
  reminder: "bi-alarm-fill",
};

const CATEGORY_LABEL = { general: "General", mention: "Mention", todo: "To-do" };

window.renderNotificationsRow = function renderNotificationsRow(row) {
  const icon = TYPE_ICON[row.notification_type] ?? "bi-info-circle-fill";
  const category = esc(CATEGORY_LABEL[row.category] ?? row.category);
  const statusBadge = row.is_read
    ? `<span class="rp-badge rp-badge-neutral">Read</span>`
    : `<span class="rp-badge rp-badge-info">Unread</span>`;

  return `
    <td><i class="bi ${icon}" style="color:var(--rp-text-muted)"></i></td>
    <td class="fw-medium">${esc(row.title)}</td>
    <td style="color:var(--rp-text-muted)">${category}</td>
    <td style="color:var(--rp-text-muted)">${esc(formatDateTime(row.created_at))}</td>
    <td>${statusBadge}</td>
  `;
};

function openDeleteModal(row) {
  const modal = document.getElementById("rp-notification-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete "${row.title}"?`);
  modal.setAttribute(
    "body",
    "This will permanently remove the notification. This cannot be undone.",
  );
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-notification-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:notification:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;
    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");
    const { href, method } = API_URLS.notifications.delete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Notification deleted",
        message: `"${pendingRow.title}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete notification.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initActions(table) {
  table.addEventListener("rp:notification:read", async (e) => {
    const { href, method } = API_URLS.notifications.markRead(e.detail.row.code);
    try {
      await apiFetch(href, { method });
      table.refresh();
    } catch {
      toast({ type: "error", title: "Error", message: "Failed to mark as read." });
    }
  });

  table.addEventListener("rp:notification:unread", async (e) => {
    const { href, method } = API_URLS.notifications.markUnread(e.detail.row.code);
    try {
      await apiFetch(href, { method });
      table.refresh();
    } catch {
      toast({ type: "error", title: "Error", message: "Failed to mark as unread." });
    }
  });

  table.addEventListener("rp:notification:dismiss", async (e) => {
    const { href, method } = API_URLS.notifications.dismiss(e.detail.row.code);
    try {
      await apiFetch(href, { method });
      table.refresh();
      toast({ type: "success", title: "Notification dismissed" });
    } catch {
      toast({ type: "error", title: "Error", message: "Failed to dismiss notification." });
    }
  });
}

function initMarkAllButton(table) {
  const btn = document.getElementById("rp-notifications-mark-all-btn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const { href, method } = API_URLS.notifications.markAllRead();
    try {
      await apiFetch(href, { method });
      table.refresh();
      toast({ type: "success", title: "All notifications marked as read" });
    } catch {
      toast({ type: "error", title: "Error", message: "Failed to mark all as read." });
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-notifications-table");
  if (!table) return;

  initActions(table);
  initDeleteModal(table);
  initMarkAllButton(table);
});
