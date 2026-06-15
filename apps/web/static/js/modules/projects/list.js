"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import { apiFetch, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";
import { hasPermission } from "../utils/index.js";

let pendingRow = null;

function confidenceBadge(value) {
  if (!value) return `<span style="color:var(--rp-text-muted)">—</span>`;
  const labels = { low: "Low", medium: "Medium", high: "High", very_high: "Very High" };
  const cls =
    value === "high" || value === "very_high"
      ? "rp-badge rp-badge-soft rp-badge-danger"
      : value === "medium"
        ? "rp-badge rp-badge-soft rp-badge-warning"
        : "rp-badge rp-badge-soft rp-badge-info";
  return `<span class="${cls}">${labels[value] ?? esc(value)}</span>`;
}

function priorityBadge(value) {
  if (!value) return `<span style="color:var(--rp-text-muted)">—</span>`;
  const labels = { low: "Low", medium: "Medium", high: "High", very_high: "Very High" };
  const cls =
    value === "high" || value === "very_high"
      ? "rp-badge rp-badge-soft rp-badge-danger"
      : value === "medium"
        ? "rp-badge rp-badge-soft rp-badge-warning"
        : "rp-badge rp-badge-soft rp-badge-info";
  return `<span class="${cls}">${labels[value] ?? esc(value)}</span>`;
}

window.renderProjectsRow = function renderProjectsRow(row) {
  const statusBadgeCls = row.is_active ? "rp-badge-soft rp-badge-success" : "rp-badge-soft";

  return `
    <td><identicon-field name="${esc(row.name)}" variant="geometric" no-border></identicon-field></td>
    <td><code class="rp-mono">${esc(row.code)}</code></td>
    <td class="fw-medium">${esc(row.name)}</td>
    <td style="color:var(--rp-text-muted)">${esc(row.programme_name || "—")}</td>
    <td style="color:var(--rp-text-muted)">${esc(row.project_type_name || "—")}</td>
    <td><span class="rp-badge ${statusBadgeCls}">${esc(row.status_name || "—")}</span></td>
    <td style="color:var(--rp-text-muted)">${esc(row.assigned_team_name || "—")}</td>
    <td>${confidenceBadge(row.confidence)}</td>
    <td>${priorityBadge(row.priority)}</td>
  `;
};

function openDeleteModal(row) {
  const modal = document.getElementById("rp-project-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete "${row.name}"?`);
  modal.setAttribute("body", "This will permanently remove the project and all associated data.");
  modal.setAttribute("confirm-value", row.name);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-project-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:project:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;

    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.projects.delete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Project deleted",
        message: `"${pendingRow.name}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete project. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initToggleModals(table) {
  const activateModal = document.getElementById("rp-project-activate-modal");
  const deactivateModal = document.getElementById("rp-project-deactivate-modal");
  if (!activateModal || !deactivateModal) return;

  let toggleRow = null;

  table.addEventListener("rp:project:toggle", (e) => {
    toggleRow = e.detail.row;
    if (toggleRow.is_active) {
      deactivateModal.setAttribute("title", `Deactivate "${toggleRow.name}"?`);
      deactivateModal.setAttribute(
        "body",
        "This will disable the project and hide it from active planning views.",
      );
      deactivateModal.show();
    } else {
      activateModal.setAttribute("title", `Activate "${toggleRow.name}"?`);
      activateModal.setAttribute("body", "This will re-enable the project for active use.");
      activateModal.show();
    }
  });

  async function handleToggleConfirm(modal, isActivating) {
    if (!toggleRow) return;

    const actionBtn = modal.querySelector("[data-action-modal]");
    actionBtn?.setAttribute("disabled", "");

    const { href, method } = isActivating
      ? API_URLS.projects.activate(toggleRow.code)
      : API_URLS.projects.deactivate(toggleRow.code);

    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: isActivating ? "Project activated" : "Project deactivated",
        message: `"${toggleRow.name}" has been ${isActivating ? "activated" : "deactivated"}.`,
      });
      toggleRow = null;
    } catch (err) {
      actionBtn?.removeAttribute("disabled");
      const msg =
        err?.data?.error?.message ??
        `Failed to ${isActivating ? "activate" : "deactivate"} project. Please try again.`;
      toast({ type: "error", title: "Error", message: msg });
    }
  }

  activateModal.addEventListener("rp:confirm", () => handleToggleConfirm(activateModal, true));
  deactivateModal.addEventListener("rp:confirm", () => handleToggleConfirm(deactivateModal, false));
}

function openAssignTeamDrawer(row) {
  const drawer = document.getElementById("rp-project-assign-team-drawer");
  if (!drawer) return;

  pendingRow = row;

  const teamField = document.getElementById("rp-assign-project-team");
  if (teamField) teamField.value = row.assigned_team_code ?? "";

  drawer.setTitle(`Assign Team — ${row.name}`);
  drawer.show();
}

function initAssignTeamDrawer(table) {
  const drawer = document.getElementById("rp-project-assign-team-drawer");
  if (!drawer) return;

  table.addEventListener("rp:project:assign-team", (e) => openAssignTeamDrawer(e.detail.row));

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const teamField = document.getElementById("rp-assign-project-team");
    const teamCode = teamField?.value ?? "";

    const payload = { assigned_team_code: teamCode || null };

    const { href, method } = API_URLS.projects.update(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Team assigned",
        message: teamCode
          ? `Team has been assigned to "${pendingRow.name}".`
          : `Team assignment cleared for "${pendingRow.name}".`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to assign team. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initAddButton(table) {
  const addBtn = document.getElementById("rp-projects-add-btn");
  const drawer = document.getElementById("rp-project-create-drawer");
  if (!addBtn || !drawer) return;

  addBtn.removeAttribute("hidden");

  function resetForm() {
    [
      "rp-new-project-name",
      "rp-new-project-type",
      "rp-new-project-programme",
      "rp-new-project-sub-status",
      "rp-new-project-confidence",
      "rp-new-project-priority",
      "rp-new-project-start-date",
      "rp-new-project-end-date",
      "rp-new-project-description",
    ].forEach((id) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.value = "";
      el.querySelector?.("[data-rp-error]") && (el.querySelector("[data-rp-error]").hidden = true);
    });
    const statusField = document.getElementById("rp-new-project-status");
    if (statusField) {
      statusField.value = "PROJSTAT-1";
      const err = statusField.querySelector("[data-rp-error]");
      if (err) err.hidden = true;
    }
  }

  function validateForm() {
    ["rp-new-project-name", "rp-new-project-type", "rp-new-project-status"].forEach((id) => {
      document.getElementById(id)?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    });
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  addBtn.addEventListener("click", () => {
    resetForm();
    drawer.show();
  });

  // Re-fetch dropdown options each time the drawer opens so newly created
  // programmes/types/statuses appear without a full page refresh.
  drawer.addEventListener("rp:open", () => {
    document.getElementById("rp-new-project-type")?.refresh?.();
    document.getElementById("rp-new-project-programme")?.refresh?.();
    document.getElementById("rp-new-project-status")?.refresh?.();
  });

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Creating…");

    const name = document.getElementById("rp-new-project-name")?.value?.trim() ?? "";
    const projectTypeCode = document.getElementById("rp-new-project-type")?.value ?? "";
    const programmeField = document.getElementById("rp-new-project-programme");
    let programmeCode = programmeField?.value ?? "";
    const statusCode = document.getElementById("rp-new-project-status")?.value ?? "";
    const subStatusCode = document.getElementById("rp-new-project-sub-status")?.value ?? "";
    const confidence = document.getElementById("rp-new-project-confidence")?.value ?? "";
    const priority = document.getElementById("rp-new-project-priority")?.value ?? "";
    const startDate = document.getElementById("rp-new-project-start-date")?.value ?? "";
    const endDate = document.getElementById("rp-new-project-end-date")?.value ?? "";
    const description = document.getElementById("rp-new-project-description")?.value?.trim() ?? "";

    // If user typed a programme name that doesn't match any existing option,
    // create it on the fly and use the returned code.
    if (!programmeCode) {
      const typedProgramme = programmeField?.inputText ?? "";
      if (typedProgramme) {
        try {
          const { href: ph, method: pm } = API_URLS.programmes.create();
          const pr = await apiFetch(ph, {
            method: pm,
            body: JSON.stringify({ name: typedProgramme, is_active: true }),
          });
          programmeCode = pr?.data?.code ?? "";
        } catch {
          restoreButton(submitBtn, snap);
          toast({
            type: "error",
            title: "Error",
            message: "Failed to create programme. Please try again.",
          });
          return;
        }
      }
    }

    const payload = {
      name,
      project_type_code: projectTypeCode,
      status_code: statusCode,
      programme_code: programmeCode || null,
      sub_status_code: subStatusCode || null,
      confidence: confidence || null,
      priority: priority || null,
      start_date: startDate || null,
      end_date: endDate || null,
      description: description || "",
      is_active: true,
    };

    const { href, method } = API_URLS.projects.create();
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      table.refresh();
      toast({
        type: "success",
        title: "Project created",
        message: `"${name}" has been created.`,
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to create project. Please try again.";
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
    window.location.href = UI_URLS.projects.detail(row.code);
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-projects-table");
  if (!table) return;

  setBreadcrumbs([
    { label: "Project" },
    { label: "Projects" },
    { label: "Projects", href: UI_URLS.projects.list() },
  ]);

  initRowNavigation(table);

  if (hasPermission("projects.add_project")) {
    initAddButton(table);
  }
  if (hasPermission("projects.change_project")) {
    initAssignTeamDrawer(table);
    initToggleModals(table);
  }
  if (hasPermission("projects.delete_project")) {
    initDeleteModal(table);
  }
});
