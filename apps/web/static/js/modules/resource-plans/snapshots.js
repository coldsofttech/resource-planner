"use strict";

import { esc } from "../../components/utils.js";
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
let planCode = "";
let versionNumber = 0;
let pendingSnapshot = null;
let takePolling = false;

// ---- Utility functions ----

function statusBadgeClass(status) {
  if (status === "complete") return "rp-badge rp-badge-soft rp-badge-success";
  if (status === "failed") return "rp-badge rp-badge-soft rp-badge-danger";
  if (status === "in_progress") return "rp-badge rp-badge-soft rp-badge-warning";
  return "rp-badge rp-badge-soft";
}

// ---- Row renderer ----

window.renderSnapshotRow = function renderSnapshotRow(row) {
  return `
    <td class="fw-medium">${esc(row.label)}</td>
    <td><span class="${statusBadgeClass(row.status)}">${esc(row.status_display)}</span></td>
    <td>${esc(row.total_allocation_days)}d</td>
    <td>${esc(row.total_members)}</td>
    <td>${esc(row.total_projects)}</td>
    <td style="color:var(--rp-text-muted)">${formatDate(row.initiated_at)}</td>
  `;
};

// ---- View Allocations (new tab) ----

function initViewAllocations(table) {
  table.addEventListener("rp:snapshot:view-allocations", (e) => {
    const row = e.detail.row;
    const url = UI_URLS.resourcePlans.versionSnapshotAllocations(planCode, versionNumber, row.code);
    window.open(url, "_blank", "noopener,noreferrer");
  });
}

// ---- Delete modal ----

function openDeleteModal(row) {
  const modal = document.getElementById("rp-snapshot-delete-modal");
  if (!modal) return;
  pendingSnapshot = row;
  modal.setAttribute("title", `Delete "${row.label}"?`);
  modal.setAttribute(
    "body",
    "This will permanently remove the snapshot and all its captured allocation/capacity data.",
  );
  modal.setAttribute("confirm-value", row.label);
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-snapshot-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:snapshot:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingSnapshot) return;
    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    try {
      const { href, method } = API_URLS.resourcePlans.snapshotDelete(
        planCode,
        versionNumber,
        pendingSnapshot.code,
      );
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Snapshot deleted",
        message: `"${pendingSnapshot.label}" has been removed.`,
      });
      pendingSnapshot = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? "Failed to delete snapshot. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ---- Take Snapshot drawer ----

function renderTakeSnapshotProgress(snapshot) {
  const pill = document.getElementById("rp-snapshot-take-status-pill");
  const statusText = document.getElementById("rp-snapshot-take-status-text");
  const errorEl = document.getElementById("rp-snapshot-take-error");

  if (pill) {
    pill.className = statusBadgeClass(snapshot.status);
    pill.textContent = snapshot.status_display.toUpperCase();
  }
  if (statusText) statusText.textContent = snapshot.status_display;

  const errors = Array.isArray(snapshot.error_log) ? snapshot.error_log : [];
  if (errorEl) {
    errorEl.hidden = errors.length === 0;
    errorEl.textContent = errors.map((e) => e.message).join(" ");
  }
}

async function pollTakeSnapshot(table, snapshotCode) {
  takePolling = true;
  while (takePolling) {
    try {
      const { href, method } = API_URLS.resourcePlans.snapshotDetail(
        planCode,
        versionNumber,
        snapshotCode,
      );
      const res = await apiFetch(href, { method });
      const snapshot = res?.data;
      if (snapshot) renderTakeSnapshotProgress(snapshot);
      if (snapshot && (snapshot.status === "complete" || snapshot.status === "failed")) {
        takePolling = false;
        table.refresh();
        break;
      }
    } catch {
      takePolling = false;
      break;
    }
    if (takePolling) await new Promise((resolve) => setTimeout(resolve, 2000));
  }
}

function initTakeSnapshotDrawer(table) {
  const takeBtn = document.getElementById("rp-snapshots-take-btn");
  const drawer = document.getElementById("rp-snapshot-take-drawer");
  const formView = document.getElementById("rp-snapshot-take-form-view");
  const progressView = document.getElementById("rp-snapshot-take-progress-view");
  if (!drawer || !formView || !progressView) return;

  const labelField = document.getElementById("rp-new-snapshot-label");
  const notesField = document.getElementById("rp-new-snapshot-notes");

  function resetForm() {
    const labelInput = labelField?.querySelector(".rp-input");
    const notesInput = notesField?.querySelector(".rp-input");
    if (labelInput) labelInput.value = "";
    if (notesInput) notesInput.value = "";
    drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
      el.textContent = "";
      el.hidden = true;
    });
  }

  function validateForm() {
    labelField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  takeBtn?.addEventListener("click", () => {
    takePolling = false;
    resetForm();
    formView.hidden = false;
    progressView.hidden = true;
    drawer.show();
  });

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!formView.hidden) {
      if (!validateForm()) return;

      const submitBtn = drawer.querySelector("[data-footer-primary]");
      const snap = snapshotButton(submitBtn);
      setBusyButton(submitBtn, "Starting…");

      const labelInput = labelField?.querySelector(".rp-input");
      const notesInput = notesField?.querySelector(".rp-input");

      try {
        const { href, method } = API_URLS.resourcePlans.snapshotsCreate(planCode, versionNumber);
        const res = await apiFetch(href, {
          method,
          body: JSON.stringify({
            label: labelInput?.value.trim() ?? "",
            notes: notesInput?.value.trim() ?? "",
          }),
        });
        restoreButton(submitBtn, snap);

        const snapshot = res?.data;
        formView.hidden = true;
        progressView.hidden = false;
        if (snapshot) {
          renderTakeSnapshotProgress(snapshot);
          table.refresh();
          if (snapshot.status !== "complete" && snapshot.status !== "failed") {
            pollTakeSnapshot(table, snapshot.code);
          }
        }
        toast({ type: "success", title: "Snapshot started", message: "Generating the snapshot…" });
      } catch (err) {
        restoreButton(submitBtn, snap);
        const msg = err?.data?.error?.message ?? "Failed to start the snapshot. Please try again.";
        toast({ type: "error", title: "Error", message: msg });
      }
    } else {
      drawer.hide();
    }
  });
}

// ---- Compare drawer ----

async function fetchCompletedSnapshots() {
  const { href, method } = API_URLS.resourcePlans.snapshotsList(planCode, versionNumber);
  const res = await apiFetch(`${href}?page_size=100`, { method });
  const results = res?.data?.results ?? [];
  return results.filter((s) => s.status === "complete");
}

function buildSnapshotDropdown(containerId, fieldId, snapshots) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const optionsHtml = snapshots
    .map((s) => `<value value="${esc(s.code)}">${esc(s.label)}</value>`)
    .join("");
  container.innerHTML = `
    <dropdown-field id="${fieldId}" name="${fieldId}" placeholder="Select snapshot…">
      <values-list>${optionsHtml}</values-list>
    </dropdown-field>
  `;
}

function initCompareDrawer() {
  const compareBtn = document.getElementById("rp-snapshots-compare-btn");
  const drawer = document.getElementById("rp-snapshot-compare-drawer");
  const formView = document.getElementById("rp-snapshot-compare-form-view");
  const resultView = document.getElementById("rp-snapshot-compare-result-view");
  if (!drawer || !formView || !resultView) return;

  compareBtn?.addEventListener("click", async () => {
    formView.hidden = false;
    resultView.hidden = true;
    const snapshots = await fetchCompletedSnapshots();
    buildSnapshotDropdown("rp-snapshot-compare-a-container", "rp-snapshot-compare-a", snapshots);
    buildSnapshotDropdown("rp-snapshot-compare-b-container", "rp-snapshot-compare-b", snapshots);
    drawer.show();
  });

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!formView.hidden) {
      const aField = document.getElementById("rp-snapshot-compare-a");
      const bField = document.getElementById("rp-snapshot-compare-b");
      const aCode = aField?.value;
      const bCode = bField?.value;
      if (!aCode || !bCode) {
        toast({
          type: "warning",
          title: "Select both snapshots",
          message: "Choose Snapshot A and Snapshot B to compare.",
        });
        return;
      }

      const submitBtn = drawer.querySelector("[data-footer-primary]");
      const snap = snapshotButton(submitBtn);
      setBusyButton(submitBtn, "Comparing…");

      try {
        const { href, method } = API_URLS.resourcePlans.snapshotsCompare(planCode, versionNumber);
        const res = await apiFetch(
          `${href}?a=${encodeURIComponent(aCode)}&b=${encodeURIComponent(bCode)}`,
          { method },
        );
        restoreButton(submitBtn, snap);

        const result = res?.data;
        const diffEl = document.getElementById("rp-snapshot-diff");
        if (diffEl && result) {
          diffEl.columns = [
            { key: "sprintName", label: "Sprint" },
            { key: "memberName", label: "Member" },
            { key: "teamName", label: "Team" },
            { key: "projectName", label: "Project" },
            { key: "phaseName", label: "Phase" },
            { key: "assignmentType", label: "Type" },
            { key: "days", label: "Days" },
          ];
          diffEl.setAttribute("title", `${result.snapshot_a.label} → ${result.snapshot_b.label}`);
          diffEl.data = { rows: result.rows };
        }
        formView.hidden = true;
        resultView.hidden = false;
      } catch (err) {
        restoreButton(submitBtn, snap);
        const msg = err?.data?.error?.message ?? "Failed to compare snapshots. Please try again.";
        toast({ type: "error", title: "Error", message: msg });
      }
    } else {
      drawer.hide();
    }
  });
}

// ---- Allocation Grid navigation ----

function initGridButton() {
  document.getElementById("rp-snapshots-grid-btn")?.addEventListener("click", () => {
    window.location.href = UI_URLS.resourcePlans.versionGrid(planCode, versionNumber);
  });
}

// ---- Bootstrap ----

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-snapshots-table");
  const planCodeField = document.getElementById("rp-snapshots-plan-code");
  const versionField = document.getElementById("rp-snapshots-version-number");
  if (!table || !planCodeField || !versionField) return;

  planCode = planCodeField.value;
  versionNumber = parseInt(versionField.value, 10);

  initViewAllocations(table);
  initDeleteModal(table);
  initTakeSnapshotDrawer(table);
  initCompareDrawer();
  initGridButton();
});
