"use strict";

import { esc } from "../../components/utils.js";
import {
  apiFetch,
  formatDate,
  formatMeta,
  snapshotButton,
  setBusyButton,
  restoreButton,
} from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS } from "../main/urls.js";
import { hasPermission } from "../utils/index.js";

let pendingRow = null;

window.renderSkillsRow = function renderSkillsRow(row) {
  const badgeCls = row.is_active ? "rp-badge-soft rp-badge-success" : "rp-badge-soft";
  const statusLabel = row.is_active ? "Active" : "Inactive";

  return `
    <td class="fw-medium">${esc(row.skill)}</td>
    <td><code class="rp-mono">${esc(row.code)}</code></td>
    <td style="color:var(--rp-text-muted)">${esc(row.description || "—")}</td>
    <td><span class="rp-badge ${badgeCls}">${statusLabel}</span></td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.created_at)}</td>
  `;
};

function openDeleteModal(row) {
  const modal = document.getElementById("rp-skill-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete "${row.skill}"?`);
  modal.setAttribute("body", "This will permanently remove the skill and all associated data.");
  modal.setAttribute("confirm-value", row.skill);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-skill-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:skill:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;

    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.skills.delete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Skill deleted",
        message: `"${pendingRow.skill}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete skill. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initToggleModals(table) {
  const activateModal = document.getElementById("rp-skill-activate-modal");
  const deactivateModal = document.getElementById("rp-skill-deactivate-modal");
  if (!activateModal || !deactivateModal) return;

  let toggleRow = null;

  table.addEventListener("rp:skill:toggle", (e) => {
    toggleRow = e.detail.row;
    if (toggleRow.is_active) {
      deactivateModal.setAttribute("title", `Deactivate "${toggleRow.skill}"?`);
      deactivateModal.setAttribute(
        "body",
        "This will disable the skill and prevent it from being assigned.",
      );
      deactivateModal.show();
    } else {
      activateModal.setAttribute("title", `Activate "${toggleRow.skill}"?`);
      activateModal.setAttribute("body", "This will re-enable the skill for assignment.");
      activateModal.show();
    }
  });

  async function handleToggleConfirm(modal, isActivating) {
    if (!toggleRow) return;

    const actionBtn = modal.querySelector("[data-action-modal]");
    actionBtn?.setAttribute("disabled", "");

    const { href, method } = isActivating
      ? API_URLS.skills.activate(toggleRow.code)
      : API_URLS.skills.deactivate(toggleRow.code);

    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: isActivating ? "Skill activated" : "Skill deactivated",
        message: `"${toggleRow.skill}" has been ${isActivating ? "activated" : "deactivated"}.`,
      });
      toggleRow = null;
    } catch (err) {
      actionBtn?.removeAttribute("disabled");
      const msg =
        err?.data?.error?.message ??
        `Failed to ${isActivating ? "activate" : "deactivate"} skill. Please try again.`;
      toast({ type: "error", title: "Error", message: msg });
    }
  }

  activateModal.addEventListener("rp:confirm", () => handleToggleConfirm(activateModal, true));
  deactivateModal.addEventListener("rp:confirm", () => handleToggleConfirm(deactivateModal, false));
}

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-skill-edit-drawer");
  if (!drawer) return;

  pendingRow = row;

  const skillInput = document.getElementById("rp-edit-skill-skill")?.querySelector(".rp-input");
  const descInput = document.getElementById("rp-edit-skill-desc")?.querySelector(".rp-input");
  if (skillInput) skillInput.value = row.skill ?? "";
  if (descInput) descInput.value = row.description ?? "";

  drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
    el.textContent = "";
    el.hidden = true;
  });
  drawer
    .querySelectorAll(".rp-input.is-invalid")
    .forEach((el) => el.classList.remove("is-invalid"));

  const metaEl = drawer.querySelector(".rp-rdrawer-foot-meta");
  if (metaEl) metaEl.textContent = formatMeta(row);

  drawer.show();
}

function initEditDrawer(table) {
  const drawer = document.getElementById("rp-skill-edit-drawer");
  if (!drawer) return;

  const skillField = document.getElementById("rp-edit-skill-skill");

  function validateForm() {
    skillField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow || !validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const skillInput = document.getElementById("rp-edit-skill-skill")?.querySelector(".rp-input");
    const descInput = document.getElementById("rp-edit-skill-desc")?.querySelector(".rp-input");

    const payload = {
      skill: skillInput?.value.trim() ?? "",
      description: descInput?.value.trim() ?? "",
    };

    const { href, method } = API_URLS.skills.update(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Skill updated",
        message: `"${payload.skill}" has been updated.`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.error?.message ??
        err?.data?.skill?.[0] ??
        "Failed to update skill. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function openViewDrawer(row) {
  const drawer = document.getElementById("rp-skill-view-drawer");
  if (!drawer) return;

  pendingRow = row;

  const statusEl = document.getElementById("rp-view-skill-status");
  if (statusEl) {
    statusEl.setAttribute(
      "badge",
      `rp-badge rp-badge-soft${row.is_active ? " rp-badge-success" : ""}`,
    );
    statusEl.value = row.is_active ? "Active" : "Inactive";
  }

  const fields = {
    "rp-view-skill-skill": esc(row.skill),
    "rp-view-skill-code": esc(row.code),
    "rp-view-skill-desc": esc(row.description || "—"),
    "rp-view-skill-created": esc(formatDate(row.created_at)),
    "rp-view-skill-created-by": esc(row.created_by?.email ?? "—"),
  };

  Object.entries(fields).forEach(([id, html]) => {
    const el = document.getElementById(id);
    if (el) el.value = html;
  });

  const metaEl = drawer.querySelector(".rp-rdrawer-foot-meta");
  if (metaEl) metaEl.textContent = formatMeta(row);

  drawer.show();
}

function initViewDrawer(table) {
  const drawer = document.getElementById("rp-skill-view-drawer");
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

function initActions(table) {
  table.addEventListener("rp:skill:edit", (e) => openEditDrawer(e.detail.row));
}

function initAddButton(table) {
  const addBtn = document.getElementById("rp-skills-add-btn");
  const drawer = document.getElementById("rp-skill-create-drawer");
  if (!addBtn || !drawer) return;

  const skillField = document.getElementById("rp-new-skill-skill");
  const descField = document.getElementById("rp-new-skill-desc");

  function resetForm() {
    const skillInput = skillField?.querySelector(".rp-input");
    const descInput = descField?.querySelector(".rp-input");
    if (skillInput) skillInput.value = "";
    if (descInput) descInput.value = "";
    drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
      el.textContent = "";
      el.hidden = true;
    });
    drawer
      .querySelectorAll(".rp-input.is-invalid")
      .forEach((el) => el.classList.remove("is-invalid"));
  }

  function validateForm() {
    skillField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
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
      skill: skillField?.querySelector(".rp-input")?.value.trim() ?? "",
      description: descField?.querySelector(".rp-input")?.value.trim() ?? "",
      is_active: true,
    };

    const { href, method } = API_URLS.skills.create();
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      table.refresh();
      toast({
        type: "success",
        title: "Skill created",
        message: `"${payload.skill}" has been added.`,
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.error?.message ??
        err?.data?.skill?.[0] ??
        "Failed to create skill. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initImportView(table) {
  const importView = document.getElementById("rp-skills-import-view");
  const importBtn = document.getElementById("rp-skills-import-btn");
  if (!importView || !importBtn) return;

  importView.setAttribute("specs-url", API_URLS.skills.importSpecs().href);
  importView.setAttribute("sample-url", API_URLS.skills.importSample().href);
  importView.setAttribute("import-url", API_URLS.skills.import().href);

  importBtn.addEventListener("click", () => importView.show());

  importView.addEventListener("rp:import:complete", () => table.refresh());
}

function initExportView() {
  const exportView = document.getElementById("rp-skills-export-view");
  const exportBtn = document.getElementById("rp-skills-export-btn");
  if (!exportView || !exportBtn) return;

  exportView.setAttribute("specs-url", API_URLS.skills.exportSpecs().href);
  exportView.setAttribute("export-url", API_URLS.skills.export().href);

  exportBtn.addEventListener("click", () => exportView.show());
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-skills-table");
  if (!table) return;

  initActions(table);
  initViewDrawer(table);

  if (hasPermission("skills.add_skill")) {
    document.getElementById("rp-skills-add-btn")?.removeAttribute("hidden");
    initAddButton(table);
  }
  if (hasPermission("skills.change_skill")) {
    initEditDrawer(table);
    initToggleModals(table);
  }
  if (hasPermission("skills.delete_skill")) {
    initDeleteModal(table);
  }
  if (hasPermission("skills.import_skill")) {
    document.getElementById("rp-skills-import-btn")?.removeAttribute("hidden");
    initImportView(table);
  }
  if (hasPermission("skills.export_skill")) {
    document.getElementById("rp-skills-export-btn")?.removeAttribute("hidden");
    initExportView();
  }
});
