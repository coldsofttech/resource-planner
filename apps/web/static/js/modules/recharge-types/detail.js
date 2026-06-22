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

function getRechargeTypeCode() {
  // URL shape: /recharges/types/<code>/
  const parts = window.location.pathname.replace(/\/$/, "").split("/");
  return parts[parts.length - 1] ?? "";
}

window.renderProjectTypeMappingRow = function renderProjectTypeMappingRow(row) {
  const badgeCls = row.project_type?.is_active ? "rp-badge-soft rp-badge-success" : "rp-badge-soft";
  const statusLabel = row.project_type?.is_active ? "Active" : "Inactive";

  return `
    <td class="fw-medium">${esc(row.project_type?.name ?? "—")}</td>
    <td><code class="rp-mono">${esc(row.project_type?.code ?? "—")}</code></td>
    <td><span class="rp-badge ${badgeCls}">${statusLabel}</span></td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.created_at)}</td>
  `;
};

function populateDetail(obj) {
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.value = val || "—";
  };

  const statusBadge = obj.is_active
    ? `<span class="rp-badge rp-badge-soft rp-badge-success">Active</span>`
    : `<span class="rp-badge rp-badge-soft">Inactive</span>`;

  const title = document.getElementById("rp-recharge-type-detail-title");
  if (title) title.textContent = obj.name ?? "Recharge Type";

  set("rp-detail-recharge-type-name", obj.name);
  set("rp-detail-recharge-type-code", obj.code);
  set("rp-detail-recharge-type-status", statusBadge);
  set("rp-detail-recharge-type-description", obj.description || "—");
  set("rp-detail-recharge-type-created-at", formatDate(obj.created_at));
  set("rp-detail-recharge-type-created-by", obj.created_by?.email ?? "—");
  set("rp-detail-recharge-type-updated-at", formatDate(obj.updated_at));
  set("rp-detail-recharge-type-updated-by", obj.updated_by?.email ?? "—");

  setBreadcrumbs([
    { label: "Recharges" },
    { label: "Configurations" },
    { label: "Recharge Types", href: UI_URLS.recharges.types() },
    { label: obj.name ?? "Recharge Type" },
  ]);
}

function initMappingDeleteModal(table, code) {
  const modal = document.getElementById("rp-mapping-delete-modal");
  if (!modal) return;

  let pendingRow = null;

  table.addEventListener("rp:mapping:delete", (e) => {
    pendingRow = e.detail.row;
    modal.setAttribute("title", `Remove "${pendingRow.project_type?.name}"?`);
    modal.setAttribute(
      "body",
      "This will remove the project type mapping from this recharge type.",
    );
    modal.setAttribute("confirm-value", pendingRow.project_type?.name ?? "");
    modal.show();
  });

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;
    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.projectTypeMappings.delete(code, pendingRow.id);
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Mapping removed",
        message: `"${pendingRow.project_type?.name}" mapping has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to remove mapping. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initMappingCreateDrawer(table, code) {
  const addBtn = document.getElementById("rp-mappings-add-btn");
  const drawer = document.getElementById("rp-mapping-create-drawer");
  if (!addBtn || !drawer) return;

  const dropdown = document.getElementById("rp-new-mapping-project-type");

  function resetForm() {
    if (dropdown) dropdown.value = "";
    drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
      el.textContent = "";
      el.hidden = true;
    });
  }

  addBtn.addEventListener("click", () => {
    resetForm();
    drawer.show();
  });

  drawer.addEventListener("rp:footer-primary", async () => {
    dropdown?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    if (drawer.querySelector("[data-rp-error]:not([hidden])")) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Adding…");

    const payload = { project_type_code: dropdown?.value ?? "" };

    const { href, method } = API_URLS.projectTypeMappings.create(code);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      table.refresh();
      toast({
        type: "success",
        title: "Mapping added",
        message: "Project type mapping has been added.",
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to add mapping. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initMappingImportView(table, code) {
  const importView = document.getElementById("rp-mappings-import-view");
  const importBtn = document.getElementById("rp-mappings-import-btn");
  if (!importView || !importBtn) return;

  importView.setAttribute("specs-url", API_URLS.projectTypeMappings.importSpecs(code).href);
  importView.setAttribute("sample-url", API_URLS.projectTypeMappings.importSample(code).href);
  importView.setAttribute("import-url", API_URLS.projectTypeMappings.import(code).href);

  importBtn.addEventListener("click", () => importView.show());
  importView.addEventListener("rp:import:complete", () => table.refresh());
}

function initMappingExportView(code) {
  const exportView = document.getElementById("rp-mappings-export-view");
  const exportBtn = document.getElementById("rp-mappings-export-btn");
  if (!exportView || !exportBtn) return;

  exportView.setAttribute("specs-url", API_URLS.projectTypeMappings.exportSpecs(code).href);
  exportView.setAttribute("export-url", API_URLS.projectTypeMappings.export(code).href);

  exportBtn.addEventListener("click", () => exportView.show());
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-mappings-table");
  if (!table) return;

  const code = getRechargeTypeCode();
  if (!code) return;

  // Set mapping table URL so it fetches the correct scoped list
  table.setAttribute("url", API_URLS.projectTypeMappings.list(code).href);

  // Load recharge type detail into left panel
  (async () => {
    const { href, method } = API_URLS.rechargeTypes.detail(code);
    try {
      const resp = await apiFetch(href, { method });
      const obj = resp?.data ?? null;
      if (obj) populateDetail(obj);
    } catch {
      setBreadcrumbs([
        { label: "Recharges" },
        { label: "Configurations" },
        { label: "Recharge Types", href: UI_URLS.recharges.types() },
        { label: code },
      ]);
      toast({ type: "error", title: "Error", message: "Failed to load recharge type details." });
    }
  })();

  if (hasPermission("recharges.add_projecttypemapping")) {
    document.getElementById("rp-mappings-add-btn")?.removeAttribute("hidden");
    initMappingCreateDrawer(table, code);
  }

  if (hasPermission("recharges.delete_projecttypemapping")) {
    initMappingDeleteModal(table, code);
  }

  if (hasPermission("recharges.import_projecttypemapping")) {
    document.getElementById("rp-mappings-import-btn")?.removeAttribute("hidden");
    initMappingImportView(table, code);
  }

  if (hasPermission("recharges.export_projecttypemapping")) {
    document.getElementById("rp-mappings-export-btn")?.removeAttribute("hidden");
    initMappingExportView(code);
  }
});
