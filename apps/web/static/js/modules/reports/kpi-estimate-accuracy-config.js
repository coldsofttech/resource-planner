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

// ---- Shared state ----
let pendingRow = null;
let currentMonth = "";

// ---- Row renderer ----

window.renderKpiEeaConfigRow = function renderKpiEeaConfigRow(row) {
  return `
    <td class="fw-medium">${esc(row.project_name)}</td>
    <td>${esc(row.comment)}</td>
    <td><code class="rp-mono">${esc(row.code)}</code></td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.created_at)}</td>
  `;
};

// ---- Scope (month) handling ----

function refreshScope(table) {
  const addBtn = document.getElementById("rp-kpi-eea-configs-add-btn");
  const hintPanel = document.getElementById("rp-kpi-eea-configs-hint-panel");

  if (currentMonth) {
    const params = new URLSearchParams({ month: currentMonth });
    table.setAttribute(
      "url",
      `${API_URLS.reports.kpiEstimateAccuracyConfigList().href}?${params.toString()}`,
    );
    table.removeAttribute("hidden");
    hintPanel?.setAttribute("hidden", "");
    addBtn?.removeAttribute("hidden");
  } else {
    table.setAttribute("hidden", "");
    hintPanel?.removeAttribute("hidden");
    addBtn?.setAttribute("hidden", "");
  }
}

// ---- Delete modal ----

function openDeleteModal(row) {
  const modal = document.getElementById("rp-kpi-eea-config-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete comment for "${row.project_name}"?`);
  modal.setAttribute(
    "body",
    `This will remove the exception comment recorded against "${row.project_name}" for this month.`,
  );
  modal.setAttribute("confirm-value", row.project_name);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-kpi-eea-config-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:kpi-eea-config:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;
    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");
    const { href, method } = API_URLS.reports.kpiEstimateAccuracyConfigDelete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Comment deleted",
        message: `The comment for "${pendingRow.project_name}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete comment. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ---- Edit drawer ----

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-kpi-eea-config-edit-drawer");
  if (!drawer) return;
  pendingRow = row;

  const projectField = document.getElementById("rp-edit-kpi-eea-config-project");
  const commentField = document.getElementById("rp-edit-kpi-eea-config-comment");
  if (projectField) projectField.value = row.project_name ?? "";
  if (commentField) {
    const input = commentField.querySelector(".rp-input");
    if (input) input.value = row.comment ?? "";
  }

  drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
    el.textContent = "";
    el.hidden = true;
  });

  drawer.show();
}

function initEditDrawer(table) {
  const drawer = document.getElementById("rp-kpi-eea-config-edit-drawer");
  if (!drawer) return;

  const commentField = document.getElementById("rp-edit-kpi-eea-config-comment");

  function validateForm() {
    commentField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow || !validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const payload = {
      comment: commentField?.querySelector(".rp-input")?.value.trim() ?? "",
    };

    const { href, method } = API_URLS.reports.kpiEstimateAccuracyConfigUpdate(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Comment updated",
        message: `The comment for "${pendingRow.project_name}" has been updated.`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to update comment. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ---- Table action handlers ----

function initActions(table) {
  table.addEventListener("rp:kpi-eea-config:edit", (e) => openEditDrawer(e.detail.row));
}

// ---- Create drawer ----

function initAddButton(table) {
  const addBtn = document.getElementById("rp-kpi-eea-configs-add-btn");
  const drawer = document.getElementById("rp-kpi-eea-config-create-drawer");
  if (!addBtn || !drawer) return;

  const projectField = document.getElementById("rp-new-kpi-eea-config-project");
  const commentField = document.getElementById("rp-new-kpi-eea-config-comment");

  function resetForm() {
    if (projectField) projectField.value = "";
    const commentInput = commentField?.querySelector(".rp-input");
    if (commentInput) commentInput.value = "";
    drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
      el.textContent = "";
      el.hidden = true;
    });
  }

  function validateForm() {
    projectField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    commentField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
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
    setBusyButton(submitBtn, "Adding…");

    const payload = {
      project_code: projectField?.value ?? "",
      month: currentMonth,
      comment: commentField?.querySelector(".rp-input")?.value.trim() ?? "",
    };

    const { href, method } = API_URLS.reports.kpiEstimateAccuracyConfigCreate();
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      table.refresh();
      toast({
        type: "success",
        title: "Comment added",
        message: "The exception comment has been recorded.",
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to add comment. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ---- Bootstrap ----

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-kpi-eea-configs-table");
  const fyField = document.getElementById("rp-kpi-eea-configs-fy");
  const monthField = document.getElementById("rp-kpi-eea-configs-month");
  if (!table || !fyField || !monthField) return;

  setBreadcrumbs([
    { label: "Reports" },
    { label: "Standard Reports", href: UI_URLS.reports.standardList() },
    {
      label: "KPI Report - Estimate % Accuracy",
      href: UI_URLS.reports.standardKpiEstimateAccuracy(),
    },
    { label: "Configure Exceptions" },
  ]);

  initActions(table);
  initAddButton(table);
  initDeleteModal(table);
  initEditDrawer(table);

  fyField.addEventListener("change", () => {
    const fyCode = fyField.value;
    currentMonth = "";
    monthField.value = "";
    if (fyCode) monthField.setAttribute("fy-code", fyCode);
    else monthField.removeAttribute("fy-code");
    refreshScope(table);
  });

  monthField.addEventListener("change", () => {
    currentMonth = monthField.value;
    refreshScope(table);
  });

  refreshScope(table);
});
