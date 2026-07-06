"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import {
  apiFetch,
  formatDate,
  snapshotButton,
  setBusyButton,
  restoreButton,
} from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";
import { hasPermission } from "../utils/index.js";

let pendingRow = null;
let pendingRecipient = null;

const MONTHLY_STATUS_BADGES = {
  draft: { cls: "rp-badge-soft", label: "Draft" },
  phase_1_open: { cls: "rp-badge-soft rp-badge-info", label: "Phase 1 Open" },
  phase_1_closed: { cls: "rp-badge-soft rp-badge-warning", label: "Phase 1 Closed" },
  phase_2_open: { cls: "rp-badge-soft rp-badge-info", label: "Phase 2 Open" },
  phase_2_closed: { cls: "rp-badge-soft rp-badge-warning", label: "Phase 2 Closed" },
  wins_declared: { cls: "rp-badge-soft rp-badge-success", label: "Wins Declared" },
};

window.renderMonthlyWinsRow = function renderMonthlyWinsRow(row) {
  const badge = MONTHLY_STATUS_BADGES[row.status] || MONTHLY_STATUS_BADGES.draft;

  return `
    <td class="fw-medium">${esc(row.name)}</td>
    <td><span class="rp-badge ${badge.cls}">${badge.label}</span></td>
    <td>${esc(row.weeks_count)}</td>
    <td style="color:var(--rp-text-muted)">${row.phase1_deadline ? formatDate(row.phase1_deadline) : "—"}</td>
    <td style="color:var(--rp-text-muted)">${row.phase2_deadline ? formatDate(row.phase2_deadline) : "—"}</td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.created_at)}</td>
  `;
};

window.renderRecipientsRow = function renderRecipientsRow(row) {
  const memberName = row.user?.display_name || row.user?.email || "—";
  return `
    <td><span class="rp-badge rp-badge-soft">${esc(row.team?.name || "—")}</span></td>
    <td class="fw-medium">${esc(memberName)}</td>
  `;
};

function initRowNavigation(table) {
  table.addEventListener("click", (e) => {
    if (e.target.closest("[data-rp-action]") || e.target.closest(".rp-table-more-btn")) return;
    const tr = e.target.closest("tr[data-rp-row]");
    if (!tr) return;
    const idx = parseInt(tr.getAttribute("data-rp-row"), 10);
    const row = table.rows[idx];
    if (!row) return;
    window.location.href = UI_URLS.wins.monthlyDetail(row.code);
  });
}

function openDeleteModal(row) {
  const modal = document.getElementById("rp-monthly-win-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete "${row.name}"?`);
  modal.setAttribute(
    "body",
    "This will permanently remove this Monthly Win and all of its surveys and results. Only Draft Monthly Wins can be deleted.",
  );
  modal.setAttribute("confirm-value", row.name);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-monthly-win-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:monthly-win:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;

    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.wins.monthly.delete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Monthly Win deleted",
        message: `"${pendingRow.name}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete Monthly Win. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initAddButton(table) {
  const addBtn = document.getElementById("rp-monthly-wins-add-btn");
  const drawer = document.getElementById("rp-monthly-win-create-drawer");
  if (!addBtn || !drawer) return;

  const nameField = document.getElementById("rp-new-monthly-win-name");
  const weeksField = document.getElementById("rp-new-monthly-win-weeks");
  const deadlineField = document.getElementById("rp-new-monthly-win-phase1-deadline");

  function resetForm() {
    if (nameField) nameField.value = "";
    if (weeksField) weeksField.value = "";
    if (deadlineField) deadlineField.value = "";
    drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
      el.textContent = "";
      el.hidden = true;
    });
  }

  function validateForm() {
    nameField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    weeksField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
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

    let winCodes = [];
    try {
      winCodes = JSON.parse(weeksField?.value || "[]");
    } catch {
      winCodes = [];
    }

    const deadlineValue = deadlineField?.value ?? "";
    const payload = {
      name: nameField?.value.trim() ?? "",
      win_codes: winCodes,
      phase1_deadline: deadlineValue ? `${deadlineValue}T23:59:59` : null,
    };

    const { href, method } = API_URLS.wins.monthly.create();
    try {
      const res = await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      toast({
        type: "success",
        title: "Monthly Win created",
        message: `"${payload.name}" has been created.`,
      });
      window.location.href = UI_URLS.wins.monthlyDetail(res?.data?.code);
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to create Monthly Win. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function openEditRecipientDrawer(row) {
  const drawer = document.getElementById("rp-recipient-edit-drawer");
  if (!drawer) return;
  pendingRecipient = row;

  const teamField = document.getElementById("rp-edit-recipient-team");
  const userField = document.getElementById("rp-edit-recipient-user");
  if (teamField) teamField.value = row.team?.code ?? "";
  if (userField) userField.value = row.user?.id ?? "";

  drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
    el.textContent = "";
    el.hidden = true;
  });
  drawer.show();
}

function initEditRecipientDrawer(recipientsTable) {
  const drawer = document.getElementById("rp-recipient-edit-drawer");
  if (!drawer) return;

  recipientsTable.addEventListener("rp:recipient:edit", (e) =>
    openEditRecipientDrawer(e.detail.row),
  );

  function validateForm() {
    const teamField = document.getElementById("rp-edit-recipient-team");
    const userField = document.getElementById("rp-edit-recipient-user");
    teamField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    userField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRecipient || !validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const payload = {
      team: document.getElementById("rp-edit-recipient-team")?.value ?? "",
      user: document.getElementById("rp-edit-recipient-user")?.value ?? "",
    };

    const { href, method } = API_URLS.wins.monthly.recipients.update(pendingRecipient.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      recipientsTable.refresh();
      toast({ type: "success", title: "Recipient updated" });
      pendingRecipient = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to update recipient. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function openDeleteRecipientModal(row) {
  const modal = document.getElementById("rp-recipient-delete-modal");
  if (!modal) return;
  pendingRecipient = row;
  const memberName = row.user?.display_name || row.user?.email || "this recipient";
  modal.setAttribute("title", `Remove ${memberName}?`);
  modal.setAttribute("body", "This will remove the recipient from future Monthly Wins surveys.");
  modal.setAttribute("confirm-value", memberName);
  modal.show();
}

function initDeleteRecipientModal(recipientsTable) {
  const modal = document.getElementById("rp-recipient-delete-modal");
  if (!modal) return;

  recipientsTable.addEventListener("rp:recipient:delete", (e) =>
    openDeleteRecipientModal(e.detail.row),
  );

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRecipient) return;

    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.wins.monthly.recipients.delete(pendingRecipient.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      recipientsTable.refresh();
      toast({ type: "success", title: "Recipient removed" });
      pendingRecipient = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to remove recipient. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initRecipientsDrawer() {
  const openBtn = document.getElementById("rp-monthly-wins-recipients-btn");
  const drawer = document.getElementById("rp-monthly-recipients-drawer");
  const recipientsTable = document.getElementById("rp-recipients-table");
  if (!openBtn || !drawer || !recipientsTable) return;

  openBtn.addEventListener("click", () => drawer.show());

  initDeleteRecipientModal(recipientsTable);
  if (hasPermission("wins.change_monthlywinsrecipient")) {
    initEditRecipientDrawer(recipientsTable);
  }

  const addBtn = document.getElementById("rp-recipient-add-btn");
  const teamField = document.getElementById("rp-new-recipient-team");
  const userField = document.getElementById("rp-new-recipient-user");
  if (!addBtn || !teamField || !userField) return;

  addBtn.addEventListener("click", async () => {
    teamField.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    userField.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    if (
      drawer.querySelector("#rp-new-recipient-team [data-rp-error]:not([hidden])") ||
      drawer.querySelector("#rp-new-recipient-user [data-rp-error]:not([hidden])")
    ) {
      return;
    }

    const snap = snapshotButton(addBtn);
    setBusyButton(addBtn, "Adding…");

    const payload = { team: teamField.value, user: userField.value };
    const { href, method } = API_URLS.wins.monthly.recipients.create();
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(addBtn, snap);
      teamField.value = "";
      userField.value = "";
      recipientsTable.refresh();
      toast({ type: "success", title: "Recipient added" });
    } catch (err) {
      restoreButton(addBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to add recipient. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-monthly-wins-table");
  if (!table) return;

  setBreadcrumbs([
    { label: "Insights" },
    { label: "Weekly Wins", href: UI_URLS.wins.list() },
    { label: "Monthly Wins", href: UI_URLS.wins.monthlyList() },
  ]);

  initRowNavigation(table);

  if (hasPermission("wins.add_monthlywin")) {
    document.getElementById("rp-monthly-wins-add-btn")?.removeAttribute("hidden");
    initAddButton(table);
  }
  if (hasPermission("wins.delete_monthlywin")) {
    initDeleteModal(table);
  }
  if (
    hasPermission("wins.add_monthlywinsrecipient") ||
    hasPermission("wins.view_monthlywinsrecipient")
  ) {
    document.getElementById("rp-monthly-wins-recipients-btn")?.removeAttribute("hidden");
    initRecipientsDrawer();
  }
});
