"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import { apiFetch, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

// /sprints/SPRINT-x/forecast/SPTIMP-y/  →  parts[1]=SPRINT-x, parts[3]=SPTIMP-y
const pathParts = window.location.pathname.split("/").filter(Boolean);
const sprintCode = pathParts[1] || null;
const importCode = pathParts[3] || null;

let pendingRow = null;

// null = review not yet run; object = keyed by row.code → {CHECK_*: bool}
let reviewResults = null;

// true when the most recent review had any row or capacity check failures
let hasReviewErrors = false;

// Set from loadImportDetail once the import record is fetched
let teamCode = null;

const CHECK_ASSIGNEE = "CHECK_ASSIGNEE";
const CHECK_SPRINT = "CHECK_SPRINT";
const CHECK_LABEL = "CHECK_LABEL";
const CHECK_MAPPING = "CHECK_MAPPING";

const CHECK_CONFIG = {
  [CHECK_ASSIGNEE]: { icon: "bi-person-x-fill", label: "Assignee not found or inactive" },
  [CHECK_SPRINT]: { icon: "bi-calendar-x-fill", label: "Sprint not found or inactive" },
  [CHECK_LABEL]: { icon: "bi-tag-fill", label: "Label not found in system" },
  [CHECK_MAPPING]: { icon: "bi-diagram-3-fill", label: "Mapping invalid for project type" },
};

window.renderForecastImportRowDetail = function renderForecastImportRowDetail(row) {
  const rowChecks = reviewResults ? (reviewResults[row.code] ?? null) : null;
  const isReviewed = rowChecks !== null;

  const failedChecks = isReviewed
    ? Object.entries(rowChecks)
        .filter(([, pass]) => !pass)
        .map(([k]) => k)
    : [];

  // Renders a cell with optional check-failure highlighting.
  // displayVal: resolved FK display text (bold if set), rawVal: CSV fallback.
  const cell = (displayVal, rawVal, checkKey) => {
    const hasResolved = displayVal !== null && displayVal !== undefined;
    const text = hasResolved ? displayVal : rawVal || "—";
    if (isReviewed && rowChecks[checkKey] === false) {
      return `<span style="color:var(--rp-danger);font-weight:700">${esc(text)}</span>`;
    }
    if (hasResolved) return `<span style="font-weight:600">${esc(displayVal)}</span>`;
    return esc(rawVal || "—");
  };

  // Checks column content — use raw <i> tags since <icon-field> doesn't render in JS row renderers
  let checksCell;
  if (!isReviewed) {
    checksCell = `<span style="color:var(--rp-muted);font-size:0.8em">—</span>`;
  } else if (failedChecks.length === 0) {
    checksCell = `<i class="bi bi-check-circle-fill" style="color:var(--rp-success);font-size:0.9rem" title="All checks passed" aria-label="All checks passed"></i>`;
  } else {
    checksCell = failedChecks
      .map((k) => {
        const cfg = CHECK_CONFIG[k] ?? { icon: "bi-exclamation-circle-fill", label: k };
        return `<i class="bi ${cfg.icon}" style="color:var(--rp-danger);font-size:0.9rem;margin-right:2px" title="${esc(cfg.label)}" aria-label="${esc(cfg.label)}"></i>`;
      })
      .join("");
  }

  return `
    <td>${esc(row.story_type || "—")}</td>
    <td><code class="rp-mono">${esc(row.jira_id || "—")}</code></td>
    <td>${esc(row.title || "—")}</td>
    <td>${cell(row.assignee_code, row.assignee, CHECK_ASSIGNEE)}</td>
    <td style="text-align:right">${esc(row.efforts || "—")}</td>
    <td style="text-align:right">${row.days != null ? esc(String(row.days)) : "—"}</td>
    <td>${cell(row.sprint_code, row.sprint, CHECK_SPRINT)}</td>
    <td>${cell(row.label_code, row.label, CHECK_LABEL)}</td>
    <td>${cell(row.mapping_code, row.mapping, CHECK_MAPPING)}</td>
    <td style="white-space:nowrap">${checksCell}</td>
  `;
};

window.renderForecastImportCapacityRow = function renderForecastImportCapacityRow(row) {
  const member = row.member ?? {};
  const name = esc(member.full_name || member.email || "—");
  const net = row.net_capacity != null ? esc(String(row.net_capacity)) : "—";
  const allocated =
    row.allocated_days != null
      ? esc(String(row.allocated_days))
      : `<span style="color:var(--rp-muted);font-size:0.8em">—</span>`;

  let checksCell;
  if (row.capacity_status === "pass") {
    checksCell = `<i class="bi bi-check-circle-fill" style="color:var(--rp-success);font-size:0.9rem" title="Capacity fully allocated" aria-label="Capacity fully allocated"></i>`;
  } else if (row.capacity_status === "fail") {
    checksCell = `<i class="bi bi-exclamation-circle-fill" style="color:var(--rp-danger);font-size:0.9rem" title="Allocated days less than net capacity" aria-label="Allocated days less than net capacity"></i>`;
  } else {
    checksCell = `<span style="color:var(--rp-muted);font-size:0.8em">—</span>`;
  }

  return `
    <td>${name}</td>
    <td style="text-align:right">${net}</td>
    <td style="text-align:right">${allocated}</td>
    <td>${checksCell}</td>
  `;
};

function enablePostReviewUI() {
  // Reveal the Engineer Capacity tab button.
  // <tab-panel> renders <tab-item> children as <button data-tab="id"> buttons;
  // the original <tab-item> element is consumed at connectedCallback time, so
  // we target the rendered button directly.
  const capacityTabBtn = document.querySelector('[data-tab="capacity"]');
  if (capacityTabBtn) capacityTabBtn.hidden = false;

  // Enable the Confirm button
  const confirmBtn = document.getElementById("rp-forecast-import-confirm-btn");
  if (confirmBtn) confirmBtn.removeAttribute("disabled");

  // Initialise capacity table URL now that teamCode is known.
  // Only set if not already done (idempotent — safe to call multiple times).
  const table = document.getElementById("rp-forecast-import-capacity-table");
  if (table && sprintCode && teamCode && !table.getAttribute("url")) {
    const base = API_URLS.sprints.capacity(sprintCode).href;
    const params = new URLSearchParams({ team: teamCode });
    if (importCode) params.set("import", importCode);
    const baseUrl = `${base}?${params.toString()}`;
    table.setAttribute("url", baseUrl);
    const listView = document.getElementById("rp-forecast-import-capacity-list");
    if (listView) listView._baseUrl = baseUrl;
  }
}

async function loadImportDetail() {
  if (!sprintCode || !importCode) return;

  try {
    const { href, method } = API_URLS.sprints.forecastImportDetail(sprintCode, importCode);
    const resp = await apiFetch(href, { method });
    const record = resp?.data ?? null;
    if (!record) return;

    teamCode = record.team_code || null;

    const teamName = record.team_name || importCode;
    const sprintName = record.sprint_name || sprintCode;
    const titleEl = document.getElementById("rp-forecast-import-title");
    if (titleEl) titleEl.textContent = `${teamName} | ${sprintName} — Forecast`;

    setBreadcrumbs([
      { label: "Project" },
      { label: "Planning" },
      { label: "Sprints", href: UI_URLS.sprints.list() },
      { label: sprintName, href: UI_URLS.sprints.detail(sprintCode) },
      { label: "Forecast", href: UI_URLS.sprints.forecast(sprintCode) },
      { label: `v${record.version_number}` },
    ]);

    // Enable the Review button now that we know the import exists
    const reviewBtn = document.getElementById("rp-forecast-import-review-btn");
    if (reviewBtn) reviewBtn.removeAttribute("disabled");

    // If a review already exists, reveal the post-review UI immediately
    if (record.has_review) enablePostReviewUI();

    // Lock UI when a completion record already exists
    if (record.is_confirmed) {
      const confirmBtn = document.getElementById("rp-forecast-import-confirm-btn");
      if (confirmBtn) {
        confirmBtn.setAttribute("label", "Confirmed");
        confirmBtn.setAttribute("suffix-icon", "bi-check-circle-fill");
      }
      lockImportUI();
    }
  } catch {
    // Non-critical — page still works without breadcrumb/title update
  }
}

function initRowsTable(table) {
  if (!sprintCode || !importCode) return;
  const baseUrl = API_URLS.sprints.forecastImportRows(sprintCode, importCode).href;
  table.setAttribute("url", baseUrl);

  // <list-view> captures _baseUrl from table[url] at connectedCallback time
  // (element upgrade), which fires before DOMContentLoaded. At that point the
  // url attribute is not yet set, so _baseUrl is "". Patching it here ensures
  // the filter coordinator uses the correct URL when the user changes a filter.
  // _baseUrl is read at event-handler call time (not closure-capture time), so
  // this assignment takes effect before any user interaction can occur.
  const listView = document.getElementById("rp-forecast-import-rows-list");
  if (listView) listView._baseUrl = baseUrl;
}

function initReviewButton(table) {
  const btn = document.getElementById("rp-forecast-import-review-btn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    if (!sprintCode || !importCode) return;
    const snap = snapshotButton(btn);
    setBusyButton(btn, "Reviewing…");

    try {
      const { href, method } = API_URLS.sprints.forecastImportReview(sprintCode, importCode);
      const resp = await apiFetch(href, { method });
      const data = resp?.data ?? {};
      reviewResults = data.results ?? {};
      hasReviewErrors = !!data.has_errors;

      restoreButton(btn, snap);
      table.refresh();
      enablePostReviewUI();

      // Refresh the capacity table so it picks up results from the new review.
      // enablePostReviewUI() must run first to ensure the URL is set.
      const capacityTable = document.getElementById("rp-forecast-import-capacity-table");
      if (capacityTable && capacityTable.getAttribute("url")) capacityTable.refresh();

      if (data.has_errors) {
        toast({
          type: "warning",
          title: "Review complete",
          message: "Some rows have check failures — highlighted in red.",
        });
      } else {
        toast({ type: "success", title: "Review complete", message: "All checks passed." });
      }
    } catch (err) {
      restoreButton(btn, snap);
      const msg = err?.data?.error?.message ?? "Review failed. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function openDeleteModal(row) {
  const modal = document.getElementById("rp-import-row-delete-modal");
  if (!modal) return;
  pendingRow = row;
  const label = row.jira_id || row.title || row.code;
  if (row.is_manually_added) {
    modal.setAttribute("title", `Delete "${label}"?`);
    modal.setAttribute("body", "This row was added manually. It will be permanently removed.");
    modal.setAttribute("confirm-value", label);
  } else {
    modal.setAttribute("title", `Remove "${label}" from import?`);
    modal.setAttribute(
      "body",
      "This row was imported from CSV. It will be excluded from the import but the original data is preserved.",
    );
    modal.removeAttribute("confirm-value");
  }
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-import-row-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:import-row:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow || !sprintCode || !importCode) return;
    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    const { href, method } = API_URLS.sprints.forecastImportRowDelete(
      sprintCode,
      importCode,
      pendingRow.code,
    );
    try {
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      const label = pendingRow.jira_id || pendingRow.title || pendingRow.code;
      const msg = pendingRow.is_manually_added
        ? `"${label}" has been permanently deleted.`
        : `"${label}" has been excluded from this import.`;
      toast({ type: "success", title: "Row removed", message: msg });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to remove row. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initActions(table) {
  table.addEventListener("rp:import-row:edit", (e) => openEditDrawer(e.detail.row));
  table.addEventListener("rp:import-row:delete", (e) => openDeleteModal(e.detail.row));
}

function resetAddRowForm() {
  const ids = [
    "rp-new-import-row-story-type",
    "rp-new-import-row-jira-id",
    "rp-new-import-row-title",
    "rp-new-import-row-assignee",
    "rp-new-import-row-efforts",
    "rp-new-import-row-sprint",
    "rp-new-import-row-label",
    "rp-new-import-row-mapping",
  ];
  ids.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.value = "";
  });
}

function initAddRowButton(table) {
  const addBtn = document.getElementById("rp-forecast-import-add-row-btn");
  const drawer = document.getElementById("rp-import-add-row-drawer");
  if (!addBtn || !drawer) return;

  addBtn.addEventListener("click", () => {
    resetAddRowForm();
    drawer.show();
  });

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!sprintCode || !importCode) return;

    const storyType = document.getElementById("rp-new-import-row-story-type");
    const jiraId = document.getElementById("rp-new-import-row-jira-id");
    const title = document.getElementById("rp-new-import-row-title");
    const assignee = document.getElementById("rp-new-import-row-assignee");
    const efforts = document.getElementById("rp-new-import-row-efforts");
    const sprint = document.getElementById("rp-new-import-row-sprint");
    const label = document.getElementById("rp-new-import-row-label");
    const mapping = document.getElementById("rp-new-import-row-mapping");

    const payload = {
      story_type: (storyType?.value || "").trim(),
      jira_id: (jiraId?.value || "").trim(),
      title: (title?.value || "").trim(),
      assignee_code: (assignee?.value || "").trim(),
      efforts: (efforts?.value || "").trim(),
      sprint_code: (sprint?.value || "").trim(),
      label_code: (label?.value || "").trim(),
      mapping_code: (mapping?.value || "").trim(),
    };

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Adding…");

    try {
      const { href, method } = API_URLS.sprints.forecastImportRowCreate(sprintCode, importCode);
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      resetAddRowForm();
      table.refresh();
      toast({
        type: "success",
        title: "Row added",
        message: "The row has been added to this import.",
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to add row. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-import-edit-row-drawer");
  if (!drawer) return;

  pendingRow = row;

  const storyType = document.getElementById("rp-edit-import-row-story-type");
  const jiraId = document.getElementById("rp-edit-import-row-jira-id");
  const title = document.getElementById("rp-edit-import-row-title");
  const assignee = document.getElementById("rp-edit-import-row-assignee");
  const efforts = document.getElementById("rp-edit-import-row-efforts");
  const sprint = document.getElementById("rp-edit-import-row-sprint");
  const label = document.getElementById("rp-edit-import-row-label");
  const mapping = document.getElementById("rp-edit-import-row-mapping");

  if (storyType) storyType.value = row.story_type ?? "";
  if (jiraId) jiraId.value = row.jira_id ?? "";
  if (title) title.value = row.title ?? "";
  if (assignee) assignee.value = row.edit_assignee_code ?? "";
  if (efforts) efforts.value = row.efforts ?? "";
  if (sprint) sprint.value = row.edit_sprint_code ?? "";
  if (label) label.value = row.edit_label_code ?? "";
  if (mapping) mapping.value = row.edit_mapping_code ?? "";

  drawer.show();
}

function initEditDrawer(table) {
  const drawer = document.getElementById("rp-import-edit-row-drawer");
  if (!drawer) return;

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow || !sprintCode || !importCode) return;

    const storyType = document.getElementById("rp-edit-import-row-story-type");
    const jiraId = document.getElementById("rp-edit-import-row-jira-id");
    const title = document.getElementById("rp-edit-import-row-title");
    const assignee = document.getElementById("rp-edit-import-row-assignee");
    const efforts = document.getElementById("rp-edit-import-row-efforts");
    const sprint = document.getElementById("rp-edit-import-row-sprint");
    const label = document.getElementById("rp-edit-import-row-label");
    const mapping = document.getElementById("rp-edit-import-row-mapping");

    const payload = {
      story_type: (storyType?.value || "").trim(),
      jira_id: (jiraId?.value || "").trim(),
      title: (title?.value || "").trim(),
      assignee_code: (assignee?.value || "").trim(),
      efforts: (efforts?.value || "").trim(),
      sprint_code: (sprint?.value || "").trim(),
      label_code: (label?.value || "").trim(),
      mapping_code: (mapping?.value || "").trim(),
    };

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    try {
      const { href, method } = API_URLS.sprints.forecastImportRowUpdate(
        sprintCode,
        importCode,
        pendingRow.code,
      );
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Row updated",
        message: "The row overrides have been saved.",
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to update row. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function lockImportUI() {
  // Disable all page-action buttons
  [
    "rp-forecast-import-confirm-btn",
    "rp-forecast-import-review-btn",
    "rp-forecast-import-add-row-btn",
  ].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.setAttribute("disabled", "");
  });

  const table = document.getElementById("rp-forecast-import-rows-table");
  if (!table) return;

  // The <data-table> component caches <table-action> children at mount time, so
  // DOM removal has no effect. Instead, hide every rendered action button/cell
  // immediately and re-hide after each re-render via MutationObserver.
  function hideActions() {
    table.querySelectorAll("[data-rp-action], .rp-table-more-btn").forEach((el) => {
      el.hidden = true;
    });
  }

  const observer = new MutationObserver(hideActions);
  observer.observe(table, { childList: true, subtree: true });

  hideActions();
  table.refresh();
}

function initConfirmButton() {
  const btn = document.getElementById("rp-forecast-import-confirm-btn");
  const drawer = document.getElementById("rp-forecast-import-confirm-drawer");
  if (!btn || !drawer) return;

  btn.addEventListener("click", () => {
    const notesField = document.getElementById("rp-confirm-import-notes");
    const msgEl = document.getElementById("rp-confirm-import-message");

    // Reset notes field state on each open
    if (notesField) {
      notesField.value = "";
      notesField.removeAttribute("required");
      notesField.dispatchEvent(new Event("rp:reset", { bubbles: false }));
    }

    if (hasReviewErrors) {
      if (msgEl)
        msgEl.textContent =
          "Some checks are failing. You must provide override notes before confirming.";
      if (notesField) {
        notesField.removeAttribute("hidden");
        notesField.setAttribute("required", "");
      }
    } else {
      if (msgEl)
        msgEl.textContent = "All checks passed. Are you sure you want to confirm this import?";
      if (notesField) notesField.setAttribute("hidden", "");
    }

    drawer.show();
  });

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!sprintCode || !importCode) return;

    const notesField = document.getElementById("rp-confirm-import-notes");

    // When failures exist, require a non-empty note before proceeding
    if (hasReviewErrors) {
      notesField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
      if (!notesField || !notesField.value.trim()) return;
    }

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Confirming…");

    try {
      const { href, method } = API_URLS.sprints.forecastImportConfirm(sprintCode, importCode);
      await apiFetch(href, {
        method,
        body: JSON.stringify({ notes: notesField?.value.trim() ?? "" }),
      });
      restoreButton(submitBtn, snap);
      drawer.hide();

      btn.setAttribute("label", "Confirmed");
      btn.setAttribute("suffix-icon", "bi-check-circle-fill");
      lockImportUI();
      toast({
        type: "success",
        title: "Import confirmed",
        message: "This forecast import has been confirmed.",
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to confirm import. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-forecast-import-rows-table");
  if (!table) return;

  // <tab-panel> renders all <tab-item> children as buttons at connectedCallback
  // time, before DOMContentLoaded. Hide the capacity tab until a review exists.
  const capacityTabBtn = document.querySelector('[data-tab="capacity"]');
  if (capacityTabBtn) capacityTabBtn.hidden = true;

  initRowsTable(table);
  initActions(table);
  initDeleteModal(table);
  initAddRowButton(table);
  initEditDrawer(table);
  initReviewButton(table);
  initConfirmButton();
  loadImportDetail();
});
