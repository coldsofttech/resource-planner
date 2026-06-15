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

let pendingSubRow = null;
const subStatusTables = new Map(); // statusCode → data-table element
const tabFilterState = new Map(); // statusCode → { is_active, search }

function canAddSub() {
  return hasPermission("projects.add_projectsubstatus");
}
function canChangeSub() {
  return hasPermission("projects.change_projectsubstatus");
}
function canDeleteSub() {
  return hasPermission("projects.delete_projectsubstatus");
}
function canImportSub() {
  return hasPermission("projects.import_projectsubstatus");
}
function canExportSub() {
  return hasPermission("projects.export_projectsubstatus");
}

function subStatusApiUrl(statusCode) {
  const fs = tabFilterState.get(statusCode) || { is_active: "true", search: "" };
  const params = new URLSearchParams({ page_size: "500" });
  if (fs.is_active && fs.is_active !== "all") params.set("is_active", fs.is_active);
  if (fs.search) params.set("search", fs.search);
  const { href } = API_URLS.projectSubStatuses.list(statusCode);
  return `${href}?${params}`;
}

window.renderSubStatusRow = function renderSubStatusRow(row) {
  const badgeCls = row.is_active ? "rp-badge-soft rp-badge-success" : "rp-badge-soft";
  const reorderCell = canChangeSub()
    ? `<td class="rp-reorder-cell">
        <div class="rp-reorder-btns">
          <button class="rp-iconbtn" data-action="move-up" aria-label="Move up" title="Move up"><span class="bi bi-chevron-up"></span></button>
          <button class="rp-iconbtn" data-action="move-down" aria-label="Move down" title="Move down"><span class="bi bi-chevron-down"></span></button>
        </div>
      </td>`
    : "";
  return `
    ${reorderCell}
    <td class="fw-medium">${esc(row.name)}</td>
    <td><code class="rp-mono">${esc(row.code)}</code></td>
    <td><span class="rp-badge ${badgeCls}">${row.is_active ? "Active" : "Inactive"}</span></td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.created_at)}</td>
  `;
};

function createSubStatusTable(statusCode) {
  const table = document.createElement("data-table");
  table.id = `rp-substatus-table-${statusCode}`;
  table.dataset.statusCode = statusCode;
  table.setAttribute("url", subStatusApiUrl(statusCode));
  table.setAttribute("row-template", "renderSubStatusRow");
  table.setAttribute("page-size", "500");
  table.setAttribute("empty-message", "No sub-statuses found.");

  const cols = document.createElement("table-columns");
  const addCol = (label, key = "", width = "") => {
    const col = document.createElement("table-column");
    col.setAttribute("label", label);
    if (key) col.setAttribute("key", key);
    if (width) col.setAttribute("width", width);
    cols.appendChild(col);
  };

  if (canChangeSub()) addCol("", "", "30px");
  addCol("Sub-Status", "name");
  addCol("Code", "code", "140px");
  addCol("Status", "is_active", "100px");
  addCol("Created", "created_at", "120px");
  table.appendChild(cols);

  if (canChangeSub() || canDeleteSub()) {
    const actions = document.createElement("table-actions");
    const addAction = (event, icon, label, opts = {}) => {
      const action = document.createElement("table-action");
      action.setAttribute("event", event);
      action.setAttribute("icon", icon);
      action.setAttribute("label", label);
      if (opts.danger) action.setAttribute("danger", "");
      if (opts.colorKey) action.setAttribute("color-key", opts.colorKey);
      actions.appendChild(action);
    };
    if (canChangeSub()) {
      addAction("rp:substatus:edit", "bi-pencil", "Edit");
      addAction("rp:substatus:toggle", "bi-toggle-on", "Toggle", { colorKey: "is_active" });
    }
    if (canDeleteSub()) {
      addAction("rp:substatus:delete", "bi-trash", "Delete", { danger: true });
    }
    table.appendChild(actions);
  }

  return table;
}

function createTabContent(statusCode) {
  const filterPanel = document.createElement("filter-panel");
  filterPanel.id = `rp-filter-panel-${statusCode}`;
  filterPanel.classList.add("mt-2");

  const searchField = document.createElement("search-field");
  searchField.id = `rp-filter-search-${statusCode}`;
  searchField.setAttribute("name", "search");
  searchField.setAttribute("show-label", "");
  searchField.setAttribute("label", "Search");
  searchField.setAttribute("shortcut", "none");
  filterPanel.appendChild(searchField);

  const isActiveField = document.createElement("is-active-field");
  isActiveField.id = `rp-filter-is-active-${statusCode}`;
  isActiveField.setAttribute("name", "is_active");
  isActiveField.setAttribute("value", "true");
  isActiveField.setAttribute("show-label", "");
  filterPanel.appendChild(isActiveField);

  const table = createSubStatusTable(statusCode);
  table.classList.add("mt-2");

  const frag = document.createDocumentFragment();
  frag.appendChild(filterPanel);
  frag.appendChild(table);
  return frag;
}

function buildTabPanel(statuses) {
  const tabPanel = document.createElement("tab-panel");
  tabPanel.id = "rp-statuses-tab-panel";

  const tabItems = document.createElement("tab-items");

  statuses.forEach((status, i) => {
    tabFilterState.set(status.code, { is_active: "true", search: "" });

    const tabItem = document.createElement("tab-item");
    tabItem.id = status.code;
    if (i === 0) tabItem.setAttribute("active", "");

    const tabHeader = document.createElement("tab-header");
    tabHeader.setAttribute("title", status.name);

    const tabContent = document.createElement("tab-content");
    tabContent.appendChild(createTabContent(status.code));

    tabItem.appendChild(tabHeader);
    tabItem.appendChild(tabContent);
    tabItems.appendChild(tabItem);
  });

  tabPanel.appendChild(tabItems);
  return tabPanel;
}

function wireTabFilters(tabPanel, statuses) {
  statuses.forEach((status) => {
    const code = status.code;
    const table = subStatusTables.get(code);
    if (!table) return;

    const searchField = tabPanel.querySelector(`#rp-filter-search-${code}`);
    const isActiveField = tabPanel.querySelector(`#rp-filter-is-active-${code}`);

    const refreshTable = () => table.setAttribute("url", subStatusApiUrl(code));

    isActiveField?.addEventListener("change", () => {
      tabFilterState.get(code).is_active = isActiveField.value;
      refreshTable();
    });

    const onSearch = () => {
      tabFilterState.get(code).search = searchField.value.trim();
      refreshTable();
    };
    searchField?.addEventListener("rp:search", onSearch);
    searchField?.addEventListener("input", onSearch);
  });
}

function wireTableEvents(table) {
  table.addEventListener("rp:substatus:edit", (ev) => openEditDrawer(ev.detail.row));
  table.addEventListener("rp:substatus:delete", (ev) => openDeleteModal(ev.detail.row));
  table.addEventListener("rp:substatus:toggle", (ev) => openToggleModal(ev.detail.row));
}

async function reorderSubStatuses(statusCode, codes, table) {
  try {
    const { href, method } = API_URLS.projectSubStatuses.reorder(statusCode);
    await apiFetch(href, { method, body: JSON.stringify({ codes }) });
    table.refresh();
    toast({ type: "success", title: "Order saved", message: "Sub-status order updated." });
  } catch (err) {
    const msg = err?.data?.error?.message ?? "Failed to save order.";
    toast({ type: "error", title: "Reorder failed", message: msg });
    table.refresh();
  }
}

function initRowActions(container) {
  container.addEventListener("click", (e) => {
    const isUp = !!e.target.closest("[data-action='move-up']");
    const isDown = !!e.target.closest("[data-action='move-down']");
    if (!isUp && !isDown) return;

    const tableEl = e.target.closest("data-table");
    const statusCode = tableEl?.dataset.statusCode;
    const table = statusCode ? subStatusTables.get(statusCode) : null;
    if (!table) return;

    const tr = e.target.closest("tr[data-rp-row]");
    const idx = parseInt(tr?.getAttribute("data-rp-row"), 10);
    if (isNaN(idx) || !table.rows) return;

    const rows = [...table.rows];
    const newIdx = isUp ? idx - 1 : idx + 1;
    if (newIdx < 0 || newIdx >= rows.length) return;

    const reordered = [...rows];
    [reordered[idx], reordered[newIdx]] = [reordered[newIdx], reordered[idx]];
    reorderSubStatuses(
      statusCode,
      reordered.map((r) => r.code),
      table,
    );
  });
}

async function loadStatuses() {
  const container = document.getElementById("rp-statuses-container");
  const loadingEl = document.getElementById("rp-statuses-loading");
  if (!container) return;

  try {
    const { href, method } = API_URLS.projectStatuses.list();
    const res = await apiFetch(`${href}?page_size=200`, { method });
    const statuses = res?.data?.results ?? [];

    if (loadingEl) loadingEl.hidden = true;

    if (!statuses.length) {
      container.innerHTML = `<p class="text-muted text-center py-4 small">No project statuses found.</p>`;
      return null;
    }

    const STATUS_ORDER = ["New", "In Progress", "On Hold", "Completed", "Cancelled"];
    statuses.sort((a, b) => {
      const ai = STATUS_ORDER.indexOf(a.name);
      const bi = STATUS_ORDER.indexOf(b.name);
      if (ai === -1 && bi === -1) return 0;
      if (ai === -1) return 1;
      if (bi === -1) return -1;
      return ai - bi;
    });

    // Build the tab-panel before connecting so connectedCallback captures all children
    const tabPanel = buildTabPanel(statuses);

    // Collect data-table references before insert (elements exist inside tab-panel subtree)
    statuses.forEach((s) => {
      const table = tabPanel.querySelector(`#rp-substatus-table-${s.code}`);
      if (table) {
        subStatusTables.set(s.code, table);
        wireTableEvents(table);
      }
    });

    // Insert into DOM — triggers tab-panel connectedCallback which renders and re-slots content
    container.appendChild(tabPanel);

    // Wire per-tab filter events (elements are now in their final slot positions)
    wireTabFilters(tabPanel, statuses);

    // Wire reorder click delegation
    initRowActions(container);

    return tabPanel;
  } catch {
    if (loadingEl) loadingEl.hidden = true;
    toast({ type: "error", title: "Load failed", message: "Could not load project statuses." });
    return null;
  }
}

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-substatus-edit-drawer");
  if (!drawer) return;
  pendingSubRow = row;

  const statusField = document.getElementById("rp-edit-substatus-status");
  const nameField = document.getElementById("rp-edit-substatus-name");

  if (statusField) statusField.value = row.main_status_name || row.main_status_code;
  if (nameField) nameField.value = row.name;

  drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
    el.textContent = "";
    el.hidden = true;
  });
  drawer.show();
}

function openDeleteModal(row) {
  const modal = document.getElementById("rp-substatus-delete-modal");
  if (!modal) return;
  pendingSubRow = row;
  modal.setAttribute("title", `Delete "${row.name}"?`);
  modal.setAttribute("body", "This will permanently remove the sub-status.");
  modal.setAttribute("confirm-value", row.name);
  modal.show();
}

function openToggleModal(row) {
  pendingSubRow = row;
  const activateModal = document.getElementById("rp-substatus-activate-modal");
  const deactivateModal = document.getElementById("rp-substatus-deactivate-modal");
  if (row.is_active && deactivateModal) {
    deactivateModal.setAttribute("title", `Deactivate "${row.name}"?`);
    deactivateModal.setAttribute("body", "This sub-status will be marked inactive.");
    deactivateModal.show();
  } else if (!row.is_active && activateModal) {
    activateModal.setAttribute("title", `Activate "${row.name}"?`);
    activateModal.setAttribute("body", "This sub-status will be marked active.");
    activateModal.show();
  }
}

function refreshSubTable(statusCode) {
  subStatusTables.get(statusCode)?.refresh();
}

function initEditDrawer() {
  const drawer = document.getElementById("rp-substatus-edit-drawer");
  if (!drawer) return;

  const nameField = document.getElementById("rp-edit-substatus-name");

  function validateForm() {
    nameField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!validateForm() || !pendingSubRow) return;
    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const row = pendingSubRow;
    try {
      const { href, method } = API_URLS.projectSubStatuses.update(row.main_status_code, row.code);
      await apiFetch(href, { method, body: JSON.stringify({ name: nameField?.value?.trim() }) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      toast({
        type: "success",
        title: "Sub-status updated",
        message: `"${nameField?.value?.trim()}" has been saved.`,
      });
      refreshSubTable(row.main_status_code);
      pendingSubRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to update sub-status.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initDeleteModal() {
  const modal = document.getElementById("rp-substatus-delete-modal");
  if (!modal) return;

  modal.addEventListener("rp:delete", async () => {
    if (!pendingSubRow) return;
    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");
    const row = pendingSubRow;

    try {
      const { href, method } = API_URLS.projectSubStatuses.delete(row.main_status_code, row.code);
      await apiFetch(href, { method });
      modal.hide();
      toast({
        type: "success",
        title: "Sub-status deleted",
        message: `"${row.name}" has been removed.`,
      });
      refreshSubTable(row.main_status_code);
      pendingSubRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete sub-status.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initToggleModals() {
  const activateModal = document.getElementById("rp-substatus-activate-modal");
  const deactivateModal = document.getElementById("rp-substatus-deactivate-modal");
  if (!activateModal || !deactivateModal) return;

  async function handleToggle(modal, isActivating) {
    if (!pendingSubRow) return;
    const row = pendingSubRow;
    const btn = modal.querySelector("[data-action-modal]");
    btn?.setAttribute("disabled", "");

    try {
      const urlFn = isActivating
        ? API_URLS.projectSubStatuses.activate
        : API_URLS.projectSubStatuses.deactivate;
      const { href, method } = urlFn(row.main_status_code, row.code);
      await apiFetch(href, { method });
      modal.hide();
      const label = isActivating ? "activated" : "deactivated";
      toast({
        type: "success",
        title: `Sub-status ${label}`,
        message: `"${row.name}" has been ${label}.`,
      });
      refreshSubTable(row.main_status_code);
      pendingSubRow = null;
    } catch (err) {
      btn?.removeAttribute("disabled");
      const msg =
        err?.data?.error?.message ??
        `Failed to ${isActivating ? "activate" : "deactivate"} sub-status.`;
      toast({ type: "error", title: "Error", message: msg });
    }
  }

  activateModal.addEventListener("rp:confirm", () => handleToggle(activateModal, true));
  deactivateModal.addEventListener("rp:confirm", () => handleToggle(deactivateModal, false));
}

function initCreateDrawer(tabPanel) {
  const addBtn = document.getElementById("rp-substatus-add-btn");
  const drawer = document.getElementById("rp-substatus-create-drawer");
  if (!drawer) return;

  const statusField = document.getElementById("rp-new-substatus-status");
  const nameField = document.getElementById("rp-new-substatus-name");

  function resetForm() {
    if (statusField) statusField.value = "";
    if (nameField) nameField.value = "";
    drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
      el.textContent = "";
      el.hidden = true;
    });
  }

  function validateForm() {
    statusField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    nameField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  addBtn?.addEventListener("click", () => {
    resetForm();
    if (tabPanel && statusField) {
      const activeTabId = tabPanel.activeTab;
      if (activeTabId) statusField.value = activeTabId;
    }
    drawer.show();
  });

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!validateForm()) return;
    const statusCode = statusField?.value;
    if (!statusCode) return;
    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Creating…");

    const name = nameField?.value?.trim();
    try {
      const { href, method } = API_URLS.projectSubStatuses.create(statusCode);
      await apiFetch(href, { method, body: JSON.stringify({ name, is_active: true }) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetForm();
      toast({ type: "success", title: "Sub-status created", message: `"${name}" has been added.` });
      tabPanel?.setTab(statusCode);
      refreshSubTable(statusCode);
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to create sub-status.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initImport() {
  const importBtn = document.getElementById("rp-substatus-import-btn");
  const importView = document.getElementById("rp-substatus-import-view");
  if (!importBtn || !importView) return;

  importView.setAttribute("specs-url", API_URLS.projectSubStatuses.importAllSpecs().href);
  importView.setAttribute("sample-url", API_URLS.projectSubStatuses.importAllSample().href);
  importView.setAttribute("import-url", API_URLS.projectSubStatuses.importAll().href);

  importBtn.addEventListener("click", () => importView.show());

  importView.addEventListener("rp:import:complete", () => {
    subStatusTables.forEach((table) => table.refresh());
  });
}

function initExport(tabPanel) {
  const exportBtn = document.getElementById("rp-substatus-export-btn");
  const exportView = document.getElementById("rp-substatus-export-view");
  if (!exportBtn || !exportView) return;

  exportBtn.addEventListener("click", () => {
    const statusCode = tabPanel?.activeTab;
    if (statusCode) {
      exportView.setAttribute(
        "specs-url",
        API_URLS.projectSubStatuses.exportSpecs(statusCode).href,
      );
      exportView.setAttribute("export-url", API_URLS.projectSubStatuses.export(statusCode).href);
    } else {
      exportView.setAttribute("specs-url", API_URLS.projectSubStatuses.exportAllSpecs().href);
      exportView.setAttribute("export-url", API_URLS.projectSubStatuses.exportAll().href);
    }
    exportView.show();
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  setBreadcrumbs([
    { label: "Project" },
    { label: "Configuration" },
    { label: "Project Statuses", href: UI_URLS.projectStatuses.list() },
  ]);

  initEditDrawer();
  initDeleteModal();
  initToggleModals();

  const tabPanel = await loadStatuses();

  if (canAddSub()) {
    document.getElementById("rp-substatus-add-btn")?.removeAttribute("hidden");
    initCreateDrawer(tabPanel);
  }
  if (canImportSub()) {
    document.getElementById("rp-substatus-import-btn")?.removeAttribute("hidden");
    initImport();
  }
  if (canExportSub()) {
    document.getElementById("rp-substatus-export-btn")?.removeAttribute("hidden");
    initExport(tabPanel);
  }
});
