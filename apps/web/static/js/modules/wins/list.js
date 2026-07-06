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

const STATUS_BADGES = {
  open: { cls: "rp-badge-soft rp-badge-info", label: "Open" },
  review_complete: { cls: "rp-badge-soft rp-badge-warning", label: "Review Complete" },
  closed: { cls: "rp-badge-soft", label: "Closed" },
};

function renderTeamsBadges(teams) {
  if (!teams || !teams.length) {
    return `<span style="color:var(--rp-text-muted)">—</span>`;
  }
  return teams
    .map((name) => `<span class="rp-badge rp-badge-soft me-1 mb-1">${esc(name)}</span>`)
    .join("");
}

window.renderWinsRow = function renderWinsRow(row) {
  const badge = STATUS_BADGES[row.status] || STATUS_BADGES.open;

  return `
    <td class="fw-medium">Week ${esc(row.week_number)}</td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.start_date)}</td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.end_date)}</td>
    <td>${esc(row.entries_count)}</td>
    <td>${renderTeamsBadges(row.teams)}</td>
    <td><span class="rp-badge ${badge.cls}">${badge.label}</span></td>
  `;
};

function openDeleteModal(row) {
  const modal = document.getElementById("rp-win-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete Week ${row.week_number}?`);
  modal.setAttribute(
    "body",
    "This will permanently remove this Weekly Win week and all of its entries.",
  );
  modal.setAttribute("confirm-value", `Week ${row.week_number}`);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-win-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:win:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;

    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.wins.delete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Week deleted",
        message: `Week ${pendingRow.week_number} has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete week. Please try again.";
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
    window.location.href = UI_URLS.wins.detail(row.code);
  });
}

function initAddButton(table) {
  const addBtn = document.getElementById("rp-wins-add-btn");
  const drawer = document.getElementById("rp-win-create-drawer");
  if (!addBtn || !drawer) return;

  const dateField = document.getElementById("rp-new-win-start-date");

  function resetForm() {
    if (dateField) dateField.value = "";
    drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
      el.textContent = "";
      el.hidden = true;
    });
  }

  function validateForm() {
    dateField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
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

    const payload = { start_date: dateField?.value ?? "" };

    const { href, method } = API_URLS.wins.create();
    try {
      const res = await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      table.refresh();
      toast({
        type: "success",
        title: "Week created",
        message: `Week ${res?.data?.week_number ?? ""} has been created.`,
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to create week. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-wins-table");
  if (!table) return;

  setBreadcrumbs([{ label: "Insights" }, { label: "Weekly Wins", href: UI_URLS.wins.list() }]);

  initRowNavigation(table);

  if (hasPermission("wins.add_win")) {
    document.getElementById("rp-wins-add-btn")?.removeAttribute("hidden");
    initAddButton(table);
  }
  if (hasPermission("wins.delete_win")) {
    initDeleteModal(table);
  }
  if (hasPermission("wins.view_monthlywin")) {
    const monthlyBtn = document.getElementById("rp-wins-monthly-btn");
    monthlyBtn?.removeAttribute("hidden");
    monthlyBtn?.addEventListener("click", () => {
      window.location.href = UI_URLS.wins.monthlyList();
    });
  }
});
