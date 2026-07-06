"use strict";

import { esc } from "../../components/utils.js";
import { apiFetch, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

let pendingRow = null;

function planTypeBadge(planType, displayValue) {
  const label = displayValue || planType || "—";
  const cls = "rp-badge rp-badge-soft rp-badge-info";
  return `<span class="${cls}">${esc(label)}</span>`;
}

// ── Row renderer ─────────────────────────────────────────────────────────────

window.renderResourcePlansRow = function renderResourcePlansRow(row) {
  const statusBadgeCls = row.is_active ? "rp-badge-soft rp-badge-success" : "rp-badge-soft";
  const headBadge = row.is_head
    ? `<span class="rp-badge rp-badge-soft rp-badge-warning ms-1">Head</span>`
    : "";

  return `
    <td><identicon-field name="${esc(row.name)}" variant="hexagon"></identicon-field></td>
    <td class="fw-medium">${esc(row.name)}${headBadge}</td>
    <td><code class="rp-mono">${esc(row.code)}</code></td>
    <td>${planTypeBadge(row.plan_type, row.plan_type_display)}</td>
    <td style="color:var(--rp-text-muted)">${esc(row.financial_year_display || "—")}</td>
    <td><span class="rp-badge ${statusBadgeCls}">${row.is_active ? "Active" : "Inactive"}</span></td>
    <td style="color:var(--rp-text-muted)">${esc(row.created_at ? new Date(row.created_at).toLocaleDateString() : "—")}</td>
  `;
};

// ── Delete modal ──────────────────────────────────────────────────────────────

function openDeleteModal(row) {
  const modal = document.getElementById("rp-resource-plan-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete "${row.name}"?`);
  modal.setAttribute(
    "body",
    "This will permanently remove the resource plan and all associated versions and scope data.",
  );
  modal.setAttribute("confirm-value", row.name);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-resource-plan-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:resource-plan:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;
    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");
    const { href, method } = API_URLS.resourcePlans.delete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Plan deleted",
        message: `"${pendingRow.name}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete resource plan. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ── Toggle modals ─────────────────────────────────────────────────────────────

function initToggleModals(table) {
  const activateModal = document.getElementById("rp-resource-plan-activate-modal");
  const deactivateModal = document.getElementById("rp-resource-plan-deactivate-modal");
  if (!activateModal || !deactivateModal) return;

  let toggleRow = null;

  table.addEventListener("rp:resource-plan:toggle", (e) => {
    toggleRow = e.detail.row;
    if (toggleRow.is_active) {
      deactivateModal.setAttribute("title", `Deactivate "${toggleRow.name}"?`);
      deactivateModal.setAttribute(
        "body",
        "This plan will be marked as inactive and hidden from default views.",
      );
      deactivateModal.show();
    } else {
      activateModal.setAttribute("title", `Activate "${toggleRow.name}"?`);
      activateModal.setAttribute("body", "This plan will be marked as active.");
      activateModal.show();
    }
  });

  async function handleToggleConfirm(modal, isActivating) {
    if (!toggleRow) return;
    const { href, method } = isActivating
      ? API_URLS.resourcePlans.activate(toggleRow.code)
      : API_URLS.resourcePlans.deactivate(toggleRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      const label = isActivating ? "activated" : "deactivated";
      toast({
        type: "success",
        title: `Plan ${label}`,
        message: `"${toggleRow.name}" has been ${label}.`,
      });
      toggleRow = null;
    } catch (err) {
      const msg =
        err?.data?.error?.message ?? `Failed to ${isActivating ? "activate" : "deactivate"} plan.`;
      toast({ type: "error", title: "Error", message: msg });
    }
  }

  activateModal.addEventListener("rp:confirm", () => handleToggleConfirm(activateModal, true));
  deactivateModal.addEventListener("rp:confirm", () => handleToggleConfirm(deactivateModal, false));
}

// ── Edit drawer ───────────────────────────────────────────────────────────────

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-resource-plan-edit-drawer");
  if (!drawer) return;
  pendingRow = row;

  const nameField = drawer.querySelector("#rp-edit-resource-plan-name");
  const descField = drawer.querySelector("#rp-edit-resource-plan-description");
  const thresholdField = drawer.querySelector("#rp-edit-resource-plan-threshold");

  if (nameField) nameField.value = row.name || "";
  if (descField) descField.value = row.description || "";
  if (thresholdField) {
    thresholdField.value =
      row.latest_version_threshold != null ? String(row.latest_version_threshold) : "10";
  }

  drawer.querySelectorAll("[data-rp-error]").forEach((el) => el.setAttribute("hidden", ""));
  drawer.show();
}

function initEditDrawer(table) {
  const drawer = document.getElementById("rp-resource-plan-edit-drawer");
  if (!drawer) return;

  table.addEventListener("rp:resource-plan:edit", (e) => openEditDrawer(e.detail.row));

  function validateForm() {
    const nameField = drawer.querySelector("#rp-edit-resource-plan-name");
    nameField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow || !validateForm()) return;
    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const nameField = drawer.querySelector("#rp-edit-resource-plan-name");
    const descField = drawer.querySelector("#rp-edit-resource-plan-description");
    const thresholdField = drawer.querySelector("#rp-edit-resource-plan-threshold");
    const rawThreshold = parseFloat(thresholdField?.value);

    const payload = {
      name: nameField?.value?.trim() || "",
      description: descField?.value?.trim() || "",
      threshold_percentage: isNaN(rawThreshold) ? 10.0 : rawThreshold,
    };

    const { href, method } = API_URLS.resourcePlans.update(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap, { label: "Saved", suffixIcon: "bi-check-circle-fill" });
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Plan updated",
        message: `"${payload.name}" has been updated.`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to update resource plan. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ── Create drawer ─────────────────────────────────────────────────────────────

function initAddButton(table) {
  const addBtn = document.getElementById("rp-resource-plans-add-btn");
  const drawer = document.getElementById("rp-resource-plan-create-drawer");
  if (!addBtn || !drawer) return;

  const nameField = drawer.querySelector("#rp-new-resource-plan-name");
  const fyField = drawer.querySelector("#rp-new-resource-plan-fy");
  const typeField = drawer.querySelector("#rp-new-resource-plan-type");
  const descField = drawer.querySelector("#rp-new-resource-plan-description");
  const thresholdField = drawer.querySelector("#rp-new-resource-plan-threshold");
  const scopeSection = drawer.querySelector("#rp-new-resource-plan-scope-section");
  const scopeProgrammeField = drawer.querySelector("#rp-new-resource-plan-scope-programme");
  const scopeProjectField = drawer.querySelector("#rp-new-resource-plan-scope-project");
  const scopeTeamField = drawer.querySelector("#rp-new-resource-plan-scope-team");

  function hideScopeField(f) {
    if (!f) return;
    f.value = "";
    f.setAttribute("hidden", "");
    const errEl = f.querySelector("[data-rp-error]");
    if (errEl) errEl.hidden = true;
  }

  function resetForm() {
    if (nameField) nameField.value = "";
    if (fyField) fyField.value = "";
    if (typeField) typeField.value = "";
    if (descField) descField.value = "";
    if (thresholdField) thresholdField.value = "10";
    if (scopeSection) scopeSection.setAttribute("hidden", "");
    hideScopeField(scopeProgrammeField);
    hideScopeField(scopeProjectField);
    hideScopeField(scopeTeamField);
    drawer.querySelectorAll("[data-rp-error]").forEach((el) => el.setAttribute("hidden", ""));
  }

  function validateForm() {
    nameField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    fyField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    typeField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    const planType = typeField?.value;
    if (planType === "programme") {
      scopeProgrammeField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    } else if (planType === "project") {
      scopeProjectField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    } else if (planType === "team") {
      scopeTeamField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    }
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  addBtn.addEventListener("click", () => {
    resetForm();
    drawer.show();
  });

  typeField?.addEventListener("change", () => {
    const type = typeField.value;
    hideScopeField(scopeProgrammeField);
    hideScopeField(scopeProjectField);
    hideScopeField(scopeTeamField);
    if (scopeSection) scopeSection.setAttribute("hidden", "");

    if (type === "programme") {
      scopeSection?.removeAttribute("hidden");
      scopeProgrammeField?.removeAttribute("hidden");
    } else if (type === "project") {
      scopeSection?.removeAttribute("hidden");
      scopeProjectField?.removeAttribute("hidden");
    } else if (type === "team") {
      scopeSection?.removeAttribute("hidden");
      scopeTeamField?.removeAttribute("hidden");
    }
    // plan type = financial_year: scope section stays hidden; FY field above is the scope
  });

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!validateForm()) return;
    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Creating…");

    const planType = typeField?.value || "";
    const rawThreshold = parseFloat(thresholdField?.value);
    const payload = {
      name: nameField?.value?.trim() || "",
      financial_year_code: fyField?.value || "",
      plan_type: planType,
      description: descField?.value?.trim() || "",
      threshold_percentage: isNaN(rawThreshold) ? 10.0 : rawThreshold,
      is_active: true,
      scope_financial_year_code: planType === "financial_year" ? fyField?.value || null : null,
      scope_programme_code: planType === "programme" ? scopeProgrammeField?.value || null : null,
      scope_project_code: planType === "project" ? scopeProjectField?.value || null : null,
      scope_team_code: planType === "team" ? scopeTeamField?.value || null : null,
    };

    const { href, method } = API_URLS.resourcePlans.create();
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap, { label: "Created", suffixIcon: "bi-check-circle-fill" });
      drawer.hide();
      resetForm();
      table.refresh();
      toast({
        type: "success",
        title: "Plan created",
        message: `"${payload.name}" has been created.`,
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to create resource plan. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ── Table action handlers ─────────────────────────────────────────────────────

function initActions(table) {
  // No extra action handler needed — events dispatched by table component
}

// ── Row click → navigate to detail page ──────────────────────────────────────

function initRowNavigation(table) {
  table.addEventListener("click", (e) => {
    if (e.target.closest("[data-rp-action]") || e.target.closest(".rp-table-more-btn")) return;
    const tr = e.target.closest("tr[data-rp-row]");
    if (!tr) return;
    const idx = parseInt(tr.getAttribute("data-rp-row"), 10);
    const row = table.rows[idx];
    if (!row) return;
    window.location.href = UI_URLS.resourcePlans.detail(row.code);
  });
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-resource-plans-table");
  if (!table) return;

  initActions(table);
  initAddButton(table);
  initDeleteModal(table);
  initToggleModals(table);
  initEditDrawer(table);
  initRowNavigation(table);
});
