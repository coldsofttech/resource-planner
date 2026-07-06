"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import {
  apiFetch,
  formatDate,
  formatDateTime,
  snapshotButton,
  setBusyButton,
  restoreButton,
} from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { statusModal } from "../utils/modal.js";
import { API_URLS } from "../main/urls.js";
import { hasPermission } from "../utils/index.js";

const winCode = window.location.pathname.split("/").filter(Boolean)[1];

let currentWin = null;
let pendingEntry = null;

const STATUS_BADGES = {
  open: { cls: "rp-badge-soft rp-badge-info", label: "Open" },
  review_complete: { cls: "rp-badge-soft rp-badge-warning", label: "Review Complete" },
  closed: { cls: "rp-badge-soft", label: "Closed" },
};

window.renderWinEntriesRow = function renderWinEntriesRow(row) {
  return `
    <td><span class="rp-badge rp-badge-soft">${esc(row.team?.name || "—")}</span></td>
    <td class="fw-medium">${esc(row.title)}</td>
    <td style="color:var(--rp-text-muted)">${esc(row.description || "—")}</td>
    <td style="color:var(--rp-text-muted)">${formatDateTime(row.created_at)}</td>
  `;
};

function updateActionButtons() {
  if (!currentWin) return;

  const addBtn = document.getElementById("rp-win-add-entry-btn");
  const reviewBtn = document.getElementById("rp-win-review-complete-btn");
  const downloadBtn = document.getElementById("rp-win-download-pdf-btn");
  const sendBtn = document.getElementById("rp-win-send-review-btn");

  const isOpen = currentWin.status === "open";
  const isReviewed = currentWin.status === "review_complete";

  if (addBtn) addBtn.hidden = !(isOpen && hasPermission("wins.add_winentry"));
  if (reviewBtn) {
    reviewBtn.hidden = !(isOpen && hasPermission("wins.review_complete_win"));
  }
  if (downloadBtn) {
    downloadBtn.hidden = !(isReviewed && hasPermission("wins.review_complete_win"));
  }
  if (sendBtn) {
    sendBtn.hidden = !(isReviewed && hasPermission("wins.review_complete_win"));
  }
}

async function loadWinDetails() {
  try {
    const { href, method } = API_URLS.wins.detail(winCode);
    const resp = await apiFetch(href, { method });
    const win = resp?.data ?? null;
    if (!win) return;
    currentWin = win;

    const titleEl = document.getElementById("rp-win-detail-title");
    if (titleEl) titleEl.textContent = `Week ${win.week_number}`;

    setBreadcrumbs([
      { label: "Insights" },
      { label: "Weekly Wins", href: "/wins/" },
      { label: `Week ${win.week_number}` },
    ]);

    const setView = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.value = val || "—";
    };

    setView("rp-win-detail-week", win.week_number);
    setView("rp-win-detail-start", formatDate(win.start_date));
    setView("rp-win-detail-end", formatDate(win.end_date));

    const statusEl = document.getElementById("rp-win-detail-status");
    if (statusEl) {
      const badge = STATUS_BADGES[win.status] || STATUS_BADGES.open;
      statusEl.setAttribute("badge", `rp-badge ${badge.cls}`);
      statusEl.value = badge.label;
    }

    setView("rp-win-detail-reviewed-at", win.reviewed_at ? formatDateTime(win.reviewed_at) : "—");
    setView("rp-win-detail-reviewed-by", win.reviewed_by?.display_name || "—");

    updateActionButtons();
  } catch {
    toast({
      type: "error",
      title: "Could not load Weekly Win",
      message: "Refresh the page to retry.",
    });
  }
}

function resetEntryForm() {
  const teamField = document.getElementById("rp-win-entry-team");
  const titleField = document.getElementById("rp-win-entry-title");
  const descField = document.getElementById("rp-win-entry-description");
  const projectField = document.getElementById("rp-win-entry-project-line");
  const deliveredField = document.getElementById("rp-win-entry-delivered");
  const benefitsField = document.getElementById("rp-win-entry-benefits");
  const nextStepsField = document.getElementById("rp-win-entry-next-steps");

  if (teamField) teamField.value = "";
  if (titleField) titleField.value = "";
  if (descField) descField.value = "";
  if (projectField) projectField.value = "";
  if (deliveredField) deliveredField.value = "";
  if (benefitsField) benefitsField.value = "";
  if (nextStepsField) nextStepsField.value = "";

  const drawer = document.getElementById("rp-win-entry-drawer");
  drawer?.querySelectorAll("[data-rp-error]").forEach((el) => {
    el.textContent = "";
    el.hidden = true;
  });
}

function openCreateEntryDrawer() {
  const drawer = document.getElementById("rp-win-entry-drawer");
  const header = document.getElementById("rp-win-entry-drawer-header");
  const aiFields = document.getElementById("rp-win-entry-ai-fields");
  if (!drawer) return;

  pendingEntry = null;
  resetEntryForm();
  header?.setAttribute("title", "Add entry");
  if (aiFields) aiFields.hidden = drawer.dataset.aiEnabled !== "true";
  drawer.show();
}

function openEditEntryDrawer(row) {
  const drawer = document.getElementById("rp-win-entry-drawer");
  const header = document.getElementById("rp-win-entry-drawer-header");
  const aiFields = document.getElementById("rp-win-entry-ai-fields");
  if (!drawer) return;

  pendingEntry = row;
  resetEntryForm();
  header?.setAttribute("title", "Edit entry");
  if (aiFields) aiFields.hidden = true;

  const teamField = document.getElementById("rp-win-entry-team");
  const titleField = document.getElementById("rp-win-entry-title");
  const descField = document.getElementById("rp-win-entry-description");
  if (teamField) teamField.value = row.team?.code ?? "";
  if (titleField) titleField.value = row.title ?? "";
  if (descField) descField.value = row.description ?? "";

  drawer.show();
}

function initEntryDrawer(table) {
  const drawer = document.getElementById("rp-win-entry-drawer");
  if (!drawer) return;

  table.addEventListener("rp:win-entry:edit", (e) => openEditEntryDrawer(e.detail.row));

  function validateForm() {
    const teamField = document.getElementById("rp-win-entry-team");
    const titleField = document.getElementById("rp-win-entry-title");
    teamField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    titleField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, pendingEntry ? "Saving…" : "Adding…");

    const payload = {
      team: document.getElementById("rp-win-entry-team")?.value ?? "",
      title: document.getElementById("rp-win-entry-title")?.value.trim() ?? "",
      description: document.getElementById("rp-win-entry-description")?.value.trim() ?? "",
    };

    const { href, method } = pendingEntry
      ? API_URLS.wins.entries.update(winCode, pendingEntry.code)
      : API_URLS.wins.entries.create(winCode);

    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: pendingEntry ? "Entry updated" : "Entry added",
        message: `"${payload.title}" has been saved.`,
      });
      pendingEntry = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to save entry. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initSuggestButton() {
  const btn = document.getElementById("rp-win-entry-suggest-btn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const teamSelect = document.querySelector("#rp-win-entry-team .rp-input");
    const teamName = teamSelect?.selectedOptions?.[0]?.textContent ?? "";
    if (!teamName) {
      toast({
        type: "warning",
        title: "Select a team",
        message: "Choose a team before suggesting.",
      });
      return;
    }

    const payload = {
      team_name: teamName,
      project_line: document.getElementById("rp-win-entry-project-line")?.value ?? "",
      delivered: document.getElementById("rp-win-entry-delivered")?.value ?? "",
      benefits: document.getElementById("rp-win-entry-benefits")?.value ?? "",
      next_steps: document.getElementById("rp-win-entry-next-steps")?.value ?? "",
    };

    const snap = snapshotButton(btn);
    setBusyButton(btn, "Suggesting…");

    try {
      const { href, method } = API_URLS.wins.entries.suggest(winCode);
      const res = await apiFetch(href, { method, body: JSON.stringify(payload) });
      const titleField = document.getElementById("rp-win-entry-title");
      const descField = document.getElementById("rp-win-entry-description");
      if (titleField) titleField.value = res?.data?.title ?? "";
      if (descField) descField.value = res?.data?.description ?? "";
      restoreButton(btn, snap);
      toast({
        type: "success",
        title: "Suggestion ready",
        message: "Review and tweak before saving.",
      });
    } catch (err) {
      restoreButton(btn, snap);
      const msg = err?.data?.error?.message ?? "Could not generate a suggestion. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function openDeleteEntryModal(row) {
  const modal = document.getElementById("rp-win-entry-delete-modal");
  if (!modal) return;
  pendingEntry = row;
  modal.setAttribute("title", `Delete "${row.title}"?`);
  modal.setAttribute("body", "This will permanently remove this entry.");
  modal.setAttribute("confirm-value", row.title);
  modal.show();
}

function initDeleteEntryModal(table) {
  const modal = document.getElementById("rp-win-entry-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:win-entry:delete", (e) => openDeleteEntryModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingEntry) return;

    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.wins.entries.delete(winCode, pendingEntry.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Entry deleted",
        message: `"${pendingEntry.title}" has been removed.`,
      });
      pendingEntry = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete entry. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initReviewCompleteButton() {
  const btn = document.getElementById("rp-win-review-complete-btn");
  if (!btn) return;

  btn.addEventListener("click", () => {
    statusModal.open({
      iconType: "warning",
      title: "Mark as review complete?",
      body: "This locks all entries for this week and prepares the review PDF. This cannot be undone.",
      closeable: true,
      dismissBtn: { label: "Cancel", onClick: () => statusModal.close() },
      primaryBtn: {
        label: "Confirm",
        onClick: async () => {
          const { href, method } = API_URLS.wins.reviewComplete(winCode);
          try {
            await apiFetch(href, { method });
            statusModal.close();
            toast({
              type: "success",
              title: "Review complete",
              message: "The week has been marked as review complete.",
            });
            await loadWinDetails();
          } catch (err) {
            statusModal.close();
            const msg =
              err?.data?.error?.message ?? "Failed to mark as review complete. Please try again.";
            toast({ type: "error", title: "Error", message: msg });
          }
        },
      },
    });
  });
}

function initDownloadPdfButton() {
  const btn = document.getElementById("rp-win-download-pdf-btn");
  if (!btn) return;

  btn.addEventListener("click", () => {
    const { href } = API_URLS.wins.reviewPdf(winCode);
    window.open(href, "_blank");
  });
}

function initSendReviewButton() {
  const btn = document.getElementById("rp-win-send-review-btn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const snap = snapshotButton(btn);
    setBusyButton(btn, "Sending…");

    const { href, method } = API_URLS.wins.sendReview(winCode);
    try {
      await apiFetch(href, { method });
      restoreButton(btn, snap);
      toast({ type: "success", title: "Sent", message: "Review email has been sent." });
    } catch (err) {
      restoreButton(btn, snap);
      const msg = err?.data?.error?.message ?? "Failed to send review email. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  if (!winCode) return;
  const table = document.getElementById("rp-win-entries-table");
  if (!table) return;

  loadWinDetails();
  initDeleteEntryModal(table);
  initSuggestButton();
  initReviewCompleteButton();
  initDownloadPdfButton();
  initSendReviewButton();

  const addBtn = document.getElementById("rp-win-add-entry-btn");
  addBtn?.addEventListener("click", openCreateEntryDrawer);

  if (hasPermission("wins.add_winentry") || hasPermission("wins.change_winentry")) {
    initEntryDrawer(table);
  }
});
