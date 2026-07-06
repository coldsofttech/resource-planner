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
let dataSourceLabels = {};

window.renderCustomReportsRow = function renderCustomReportsRow(row) {
  const badgeCls = row.is_shared ? "rp-badge-soft rp-badge-success" : "rp-badge-soft";
  const sharedLabel = row.is_shared ? "Shared" : "Private";
  const ownerName = row.owner?.display_name || row.owner?.email || "—";
  const dataSourceLabel = row.data_source
    ? (dataSourceLabels[row.data_source] ?? row.data_source)
    : "—";

  return `
    <td><identicon-field name="${esc(row.name)}" variant="bars" no-border></identicon-field></td>
    <td class="fw-medium">${esc(row.name)}</td>
    <td style="color:var(--rp-text-muted)">${esc(dataSourceLabel)}</td>
    <td style="color:var(--rp-text-muted)">${esc(ownerName)}</td>
    <td><span class="rp-badge ${badgeCls}">${sharedLabel}</span></td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.updated_at)}</td>
  `;
};

async function loadDataSourceLabels() {
  try {
    const { href, method } = API_URLS.reports.customDataSources();
    const res = await apiFetch(href, { method });
    const sources = res?.data ?? [];
    dataSourceLabels = Object.fromEntries(sources.map((s) => [s.key, s.label]));
  } catch {
    dataSourceLabels = {};
  }
}

function openDeleteModal(row) {
  const modal = document.getElementById("rp-customreport-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete "${row.name}"?`);
  modal.setAttribute("body", "This will permanently remove the custom report.");
  modal.setAttribute("confirm-value", row.name);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-customreport-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:customreport:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;

    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.reports.customDelete(pendingRow.code);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Custom report deleted",
        message: `"${pendingRow.name}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete custom report. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-customreport-edit-drawer");
  if (!drawer) return;

  pendingRow = row;

  const nameInput = document
    .getElementById("rp-edit-customreport-name")
    ?.querySelector(".rp-input");
  const descInput = document
    .getElementById("rp-edit-customreport-desc")
    ?.querySelector(".rp-input");
  const sharedField = document.getElementById("rp-edit-customreport-shared");
  if (nameInput) nameInput.value = row.name ?? "";
  if (descInput) descInput.value = row.description ?? "";
  if (sharedField) sharedField.checked = !!row.is_shared;

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
  const drawer = document.getElementById("rp-customreport-edit-drawer");
  if (!drawer) return;

  const nameField = document.getElementById("rp-edit-customreport-name");

  function validateForm() {
    nameField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow || !validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const nameInput = document
      .getElementById("rp-edit-customreport-name")
      ?.querySelector(".rp-input");
    const descInput = document
      .getElementById("rp-edit-customreport-desc")
      ?.querySelector(".rp-input");
    const sharedField = document.getElementById("rp-edit-customreport-shared");

    const payload = {
      name: nameInput?.value.trim() ?? "",
      description: descInput?.value.trim() ?? "",
      is_shared: !!sharedField?.checked,
    };

    const { href, method } = API_URLS.reports.customUpdate(pendingRow.code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Custom report updated",
        message: `"${payload.name}" has been updated.`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.error?.message ??
        err?.data?.name?.[0] ??
        "Failed to update custom report. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initActions(table) {
  table.addEventListener("rp:customreport:edit", (e) => openEditDrawer(e.detail.row));
  table.addEventListener("rp:customreport:open", (e) => {
    window.location.href = UI_URLS.reports.customBuilder(e.detail.row.code);
  });
}

function initAddButton(table) {
  const addBtn = document.getElementById("rp-reports-custom-add-btn");
  const drawer = document.getElementById("rp-customreport-create-drawer");
  if (!addBtn || !drawer) return;

  const nameField = document.getElementById("rp-new-customreport-name");
  const descField = document.getElementById("rp-new-customreport-desc");
  const sharedField = document.getElementById("rp-new-customreport-shared");

  function resetForm() {
    const nameInput = nameField?.querySelector(".rp-input");
    const descInput = descField?.querySelector(".rp-input");
    if (nameInput) nameInput.value = "";
    if (descInput) descInput.value = "";
    if (sharedField) sharedField.checked = false;
    drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
      el.textContent = "";
      el.hidden = true;
    });
    drawer
      .querySelectorAll(".rp-input.is-invalid")
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
      description: descField?.querySelector(".rp-input")?.value.trim() ?? "",
      is_shared: !!sharedField?.checked,
    };

    const { href, method } = API_URLS.reports.customCreate();
    try {
      const res = await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      toast({
        type: "success",
        title: "Custom report created",
        message: `"${payload.name}" has been added. Configure it in the builder.`,
      });
      const code = res?.data?.code;
      if (code) window.location.href = UI_URLS.reports.customBuilder(code);
      else table.refresh();
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.error?.message ??
        err?.data?.name?.[0] ??
        "Failed to create custom report. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-reports-custom-table");
  if (!table) return;

  setBreadcrumbs([
    { label: "Reports" },
    { label: "Custom Reports", href: UI_URLS.reports.customList() },
  ]);

  loadDataSourceLabels().then(() => table.refresh());
  initActions(table);

  if (hasPermission("reports.add_customreport")) {
    document.getElementById("rp-reports-custom-add-btn")?.removeAttribute("hidden");
    initAddButton(table);
  }
  if (hasPermission("reports.change_customreport")) {
    initEditDrawer(table);
  }
  if (hasPermission("reports.delete_customreport")) {
    initDeleteModal(table);
  }
});
