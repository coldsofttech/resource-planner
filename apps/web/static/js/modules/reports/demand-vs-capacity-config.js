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
let currentPlanCode = "";
let currentVersion = "";

// ---- Row renderer ----

window.renderDvcConfigRow = function renderDvcConfigRow(row) {
  return `
    <td class="fw-medium">${esc(row.category)}</td>
    <td>${esc(row.programme_name)}</td>
    <td><code class="rp-mono">${esc(row.code)}</code></td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.created_at)}</td>
  `;
};

// ---- Scope (plan + version) handling ----

function refreshScope(table) {
  const addBtn = document.getElementById("rp-dvc-configs-add-btn");
  const hintPanel = document.getElementById("rp-dvc-configs-hint-panel");

  if (currentPlanCode && currentVersion) {
    const params = new URLSearchParams({ plan: currentPlanCode, version: currentVersion });
    table.setAttribute(
      "url",
      `${API_URLS.reports.demandVsCapacityConfigList().href}?${params.toString()}`,
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
  const modal = document.getElementById("rp-dvc-config-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete mapping "${row.category}"?`);
  modal.setAttribute(
    "body",
    `This will remove the mapping between "${row.programme_name}" and "${row.category}".`,
  );
  modal.setAttribute("confirm-value", row.category);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-dvc-config-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:dvc-config:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;
    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");
    const { href, method } = API_URLS.reports.demandVsCapacityConfigDelete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Mapping deleted",
        message: `"${pendingRow.category}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete mapping. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ---- Edit drawer ----

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-dvc-config-edit-drawer");
  if (!drawer) return;
  pendingRow = row;

  const programmeField = document.getElementById("rp-edit-dvc-config-programme");
  const categoryField = document.getElementById("rp-edit-dvc-config-category");
  if (programmeField) programmeField.value = row.programme ?? "";
  if (categoryField) {
    const input = categoryField.querySelector(".rp-input");
    if (input) input.value = row.category ?? "";
  }

  drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
    el.textContent = "";
    el.hidden = true;
  });

  drawer.show();
}

function initEditDrawer(table) {
  const drawer = document.getElementById("rp-dvc-config-edit-drawer");
  if (!drawer) return;

  const programmeField = document.getElementById("rp-edit-dvc-config-programme");
  const categoryField = document.getElementById("rp-edit-dvc-config-category");

  function validateForm() {
    programmeField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    categoryField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow || !validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const payload = {
      programme_code: programmeField?.value ?? "",
      category: categoryField?.querySelector(".rp-input")?.value.trim() ?? "",
    };

    const { href, method } = API_URLS.reports.demandVsCapacityConfigUpdate(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Mapping updated",
        message: `"${payload.category}" has been updated.`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to update mapping. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ---- Table action handlers ----

function initActions(table) {
  table.addEventListener("rp:dvc-config:edit", (e) => openEditDrawer(e.detail.row));
}

// ---- Create drawer ----

function initAddButton(table) {
  const addBtn = document.getElementById("rp-dvc-configs-add-btn");
  const drawer = document.getElementById("rp-dvc-config-create-drawer");
  if (!addBtn || !drawer) return;

  const programmeField = document.getElementById("rp-new-dvc-config-programme");
  const categoryField = document.getElementById("rp-new-dvc-config-category");

  function resetForm() {
    if (programmeField) programmeField.value = "";
    const categoryInput = categoryField?.querySelector(".rp-input");
    if (categoryInput) categoryInput.value = "";
    drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
      el.textContent = "";
      el.hidden = true;
    });
  }

  function validateForm() {
    programmeField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    categoryField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
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
      plan_code: currentPlanCode,
      version: Number(currentVersion),
      programme_code: programmeField?.value ?? "",
      category: categoryField?.querySelector(".rp-input")?.value.trim() ?? "",
    };

    const { href, method } = API_URLS.reports.demandVsCapacityConfigCreate();
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      table.refresh();
      toast({
        type: "success",
        title: "Mapping added",
        message: `"${payload.category}" has been added.`,
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to add mapping. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ---- Bootstrap ----

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-dvc-configs-table");
  const planField = document.getElementById("rp-dvc-configs-plan");
  const versionField = document.getElementById("rp-dvc-configs-version");
  if (!table || !planField || !versionField) return;

  setBreadcrumbs([
    { label: "Reports" },
    { label: "Standard Reports", href: UI_URLS.reports.standardList() },
    { label: "Demand vs. Capacity", href: UI_URLS.reports.standardDemandVsCapacity() },
    { label: "Configure Categories" },
  ]);

  initActions(table);
  initAddButton(table);
  initDeleteModal(table);
  initEditDrawer(table);

  planField.addEventListener("change", () => {
    currentPlanCode = planField.value;
    currentVersion = "";
    versionField.value = "";
    if (currentPlanCode) versionField.setAttribute("plan-code", currentPlanCode);
    else versionField.removeAttribute("plan-code");
    refreshScope(table);
  });

  versionField.addEventListener("change", () => {
    currentVersion = versionField.value;
    refreshScope(table);
  });

  refreshScope(table);
});
