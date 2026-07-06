"use strict";

import { esc } from "../../components/utils.js";
import { apiFetch, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS } from "../main/urls.js";

// ---- Shared state ----
let planCode = "";
let versionNumber = 0;
let pendingRow = null;

// ---- Row renderer ----

window.renderPlaceholderLeaveRow = function renderPlaceholderLeaveRow(row) {
  const badgeCls = row.is_auto ? "rp-badge-soft" : "rp-badge-soft rp-badge-info";
  return `
    <td><user-avatar avatar-url="${esc(row.member_avatar_url || "")}" name="${esc(row.member_name)}" size="sm"></user-avatar></td>
    <td class="fw-medium">${esc(row.member_name)}</td>
    <td>${esc(row.sprint_name)}</td>
    <td>${esc(Number(row.days).toFixed(2))}d</td>
    <td><span class="rp-badge ${badgeCls}">${esc(row.source_display)}</span></td>
    <td style="color:var(--rp-text-muted)">${row.notes ? esc(row.notes) : "—"}</td>
  `;
};

// ---- Delete modal ----

function openDeleteModal(row) {
  const modal = document.getElementById("rp-placeholder-leave-delete-modal");
  if (!modal) return;
  pendingRow = row;
  modal.setAttribute("title", `Delete placeholder leave for "${row.member_name}"?`);
  modal.setAttribute(
    "body",
    `This will permanently remove the ${row.days}d placeholder leave in ${row.sprint_name}.`,
  );
  modal.show();
}

function initDeleteModal(table) {
  const modal = document.getElementById("rp-placeholder-leave-delete-modal");
  if (!modal) return;

  table.addEventListener("rp:placeholder-leave:delete", (e) => openDeleteModal(e.detail.row));

  modal.addEventListener("rp:delete", async () => {
    if (!pendingRow) return;
    const deleteBtn = modal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");

    try {
      const { href, method } = API_URLS.resourcePlans.placeholderLeaveDelete(
        planCode,
        versionNumber,
        pendingRow.code,
      );
      await apiFetch(href, { method });
      modal.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Placeholder leave deleted",
        message: `The placeholder leave for "${pendingRow.member_name}" has been removed.`,
      });
      pendingRow = null;
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg =
        err?.data?.error?.message ?? "Failed to delete placeholder leave. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ---- Edit drawer ----

function openEditDrawer(row) {
  const drawer = document.getElementById("rp-placeholder-leave-edit-drawer");
  if (!drawer) return;

  pendingRow = row;

  const memberField = document.getElementById("rp-edit-placeholder-leave-member");
  const sprintField = document.getElementById("rp-edit-placeholder-leave-sprint");
  if (memberField) memberField.value = esc(row.member_name);
  if (sprintField) sprintField.value = esc(row.sprint_name);

  const daysInput = document
    .getElementById("rp-edit-placeholder-leave-days")
    ?.querySelector(".rp-input");
  const notesInput = document
    .getElementById("rp-edit-placeholder-leave-notes")
    ?.querySelector(".rp-input");
  if (daysInput) daysInput.value = row.days ?? "";
  if (notesInput) notesInput.value = row.notes ?? "";

  drawer.querySelectorAll("[data-rp-error]").forEach((el) => {
    el.textContent = "";
    el.hidden = true;
  });
  drawer
    .querySelectorAll(".rp-input.is-invalid")
    .forEach((el) => el.classList.remove("is-invalid"));

  drawer.show();
}

function initEditDrawer(table) {
  const drawer = document.getElementById("rp-placeholder-leave-edit-drawer");
  if (!drawer) return;

  const daysField = document.getElementById("rp-edit-placeholder-leave-days");

  function validateForm() {
    daysField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    return !drawer.querySelector("[data-rp-error]:not([hidden])");
  }

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingRow || !validateForm()) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const daysInput = document
      .getElementById("rp-edit-placeholder-leave-days")
      ?.querySelector(".rp-input");
    const notesInput = document
      .getElementById("rp-edit-placeholder-leave-notes")
      ?.querySelector(".rp-input");

    const payload = {
      days: daysInput?.value ?? "0",
      notes: notesInput?.value.trim() ?? "",
    };

    try {
      const { href, method } = API_URLS.resourcePlans.placeholderLeaveUpdate(
        planCode,
        versionNumber,
        pendingRow.code,
      );
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      table.refresh();
      toast({
        type: "success",
        title: "Placeholder leave updated",
        message: `The placeholder leave for "${pendingRow.member_name}" has been updated.`,
      });
      pendingRow = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.error?.message ?? "Failed to update placeholder leave. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ---- Table action handlers ----

function initActions(table) {
  table.addEventListener("rp:placeholder-leave:edit", (e) => openEditDrawer(e.detail.row));
}

// ---- Regenerate ----

function initRegenerateButton(table) {
  const regenerateBtn = document.getElementById("rp-placeholder-leaves-regenerate-btn");
  const modal = document.getElementById("rp-placeholder-leaves-regenerate-modal");
  if (!regenerateBtn || !modal) return;

  const includeCurrentField = document.getElementById(
    "rp-placeholder-leaves-regen-include-current",
  );
  const removeOverridesField = document.getElementById(
    "rp-placeholder-leaves-regen-remove-overrides",
  );

  regenerateBtn.addEventListener("click", () => {
    if (includeCurrentField) includeCurrentField.checked = false;
    if (removeOverridesField) removeOverridesField.checked = false;
    modal.show();
  });

  modal.addEventListener("rp:primary", async () => {
    const submitBtn = modal.querySelector("[data-primary-modal]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Regenerating…");

    try {
      const { href, method } = API_URLS.resourcePlans.placeholderLeavesRegenerate(
        planCode,
        versionNumber,
      );
      const res = await apiFetch(href, {
        method,
        body: JSON.stringify({
          include_current_sprint: includeCurrentField?.checked === true,
          remove_overrides: removeOverridesField?.checked === true,
        }),
      });
      restoreButton(submitBtn, snap);
      modal.hide();
      table.refresh();
      const count = res?.data?.regenerated_count ?? 0;
      toast({
        type: "success",
        title: "Regenerated",
        message: `${count} placeholder leave${count === 1 ? "" : "s"} generated.`,
      });
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg =
        err?.data?.error?.message ?? "Failed to regenerate placeholder leaves. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ---- Bootstrap ----

document.addEventListener("DOMContentLoaded", () => {
  const table = document.getElementById("rp-placeholder-leaves-table");
  const planCodeField = document.getElementById("rp-placeholder-leaves-plan-code");
  const versionField = document.getElementById("rp-placeholder-leaves-version-number");
  if (!table || !planCodeField || !versionField) return;

  planCode = planCodeField.value;
  versionNumber = parseInt(versionField.value, 10);

  initActions(table);
  initEditDrawer(table);
  initDeleteModal(table);
  initRegenerateButton(table);
});
