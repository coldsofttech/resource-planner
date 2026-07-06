"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import {
  apiFetch,
  formatDate,
  formatMeta,
  snapshotButton,
  setBusyButton,
  restoreButton,
} from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";
import { hasPermission } from "../utils/index.js";

let pendingRow = null;

function renderProjectBadges(projects) {
  if (!projects || projects.length === 0) {
    return `<span style="color:var(--rp-text-muted)">—</span>`;
  }
  return projects
    .map(
      (p) =>
        `<span class="rp-badge rp-badge-soft me-1 mb-1">${esc(p.display_name || p.name)}</span>`,
    )
    .join("");
}

window.renderRechargeProjectGroupRow = function renderRechargeProjectGroupRow(row) {
  return `
    <td class="fw-medium">${esc(row.name)}</td>
    <td><code class="rp-mono">${esc(row.code)}</code></td>
    <td>${renderProjectBadges(row.projects)}</td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.created_at)}</td>
  `;
};

function openDeleteModal(row) {
  const modal = document.getElementById("rp-recharge-project-group-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete "${row.name}"?`);
  modal.setAttribute(
    "body",
    "This will permanently remove the project group. Projects themselves will not be deleted.",
  );
  modal.setAttribute("confirm-value", row.name);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-recharge-project-group-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:recharge-project-group:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;

    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.rechargeProjectGroups.delete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Project group deleted",
        message: `"${pendingRow.name}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete project group. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-recharge-project-group-edit-drawer");
  if (!drawer) return;

  pendingRow = row;

  const nameInput = document
    .getElementById("rp-edit-recharge-project-group-name")
    ?.querySelector(".rp-input");
  if (nameInput) nameInput.value = row.name ?? "";

  const projectsField = document.getElementById("rp-edit-recharge-project-group-projects");
  if (projectsField) {
    projectsField.value = JSON.stringify((row.projects || []).map((p) => p.code));
  }

  drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
    el.textContent = "";
    el.hidden = true;
  });
  drawer
    .querySelectorAll(".rp-input.is-invalid, .rp-multiselect.is-invalid")
    .forEach((el) => el.classList.remove("is-invalid"));

  const metaEl = drawer.querySelector(".rp-rdrawer-foot-meta");
  if (metaEl) metaEl.textContent = formatMeta(row);

  drawer.show();
}

function initEditDrawer(table) {
  const drawer = document.getElementById("rp-recharge-project-group-edit-drawer");
  if (!drawer) return;

  const nameField = document.getElementById("rp-edit-recharge-project-group-name");

  function validateForm() {
    nameField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow || !validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const nameInput = nameField?.querySelector(".rp-input");
    const projectsField = document.getElementById("rp-edit-recharge-project-group-projects");

    const payload = {
      name: nameInput?.value.trim() ?? "",
      project_codes: JSON.parse(projectsField?.value || "[]"),
    };

    const { href, method } = API_URLS.rechargeProjectGroups.update(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Project group updated",
        message: `"${payload.name}" has been updated.`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.error?.message ??
        err?.data?.name?.[0] ??
        "Failed to update project group. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initViewDrawer(table) {
  table.addEventListener("click", (e) => {
    if (e.target.closest("[data-rp-action]") || e.target.closest(".rp-table-more-btn")) return;
    const tr = e.target.closest("tr[data-rp-row]");
    if (!tr) return;
    const idx = parseInt(tr.getAttribute("data-rp-row"), 10);
    const row = table.rows?.[idx];
    if (!row) return;
    openEditDrawer(row);
  });
}

function initActions(table) {
  table.addEventListener("rp:recharge-project-group:edit", (e) => openEditDrawer(e.detail.row));
}

function initAddButton(table) {
  const addBtn = document.getElementById("rp-recharge-project-groups-add-btn");
  const drawer = document.getElementById("rp-recharge-project-group-create-drawer");
  if (!addBtn || !drawer) return;

  const nameField = document.getElementById("rp-new-recharge-project-group-name");
  const projectsField = document.getElementById("rp-new-recharge-project-group-projects");

  function resetForm() {
    const nameInput = nameField?.querySelector(".rp-input");
    if (nameInput) nameInput.value = "";
    if (projectsField) projectsField.value = "";
    drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
      el.textContent = "";
      el.hidden = true;
    });
    drawer
      .querySelectorAll(".rp-input.is-invalid, .rp-multiselect.is-invalid")
      .forEach((el) => el.classList.remove("is-invalid"));
  }

  function validateForm() {
    nameField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
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
      name: nameField?.querySelector(".rp-input")?.value.trim() ?? "",
      project_codes: JSON.parse(projectsField?.value || "[]"),
    };

    const { href, method } = API_URLS.rechargeProjectGroups.create();
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      table.refresh();
      toast({
        type: "success",
        title: "Project group created",
        message: `"${payload.name}" has been added.`,
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.error?.message ??
        err?.data?.name?.[0] ??
        "Failed to create project group. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-recharge-project-groups-table");
  if (!table) return;

  setBreadcrumbs([
    { label: "Recharges", href: UI_URLS.recharges.index() },
    { label: "Configurations" },
    { label: "Project Groups", href: UI_URLS.recharges.projectGroups() },
  ]);

  initActions(table);
  initViewDrawer(table);

  if (hasPermission("recharges.add_rechargeprojectgroup")) {
    document.getElementById("rp-recharge-project-groups-add-btn")?.removeAttribute("hidden");
    initAddButton(table);
  }
  if (hasPermission("recharges.change_rechargeprojectgroup")) {
    initEditDrawer(table);
  }
  if (hasPermission("recharges.delete_rechargeprojectgroup")) {
    initDeleteModal(table);
  }
});
