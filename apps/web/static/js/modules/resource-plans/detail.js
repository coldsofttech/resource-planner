"use strict";

import { esc } from "../../components/utils.js";
import { apiFetch, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

// ── Shared state ──────────────────────────────────────────────────────────────

let pendingVersionRow = null;

// ── Version row renderer ─────────────────────────────────────────────────────

function versionStatusBadge(status) {
  if (status === "active") return "rp-badge rp-badge-soft rp-badge-success";
  if (status === "locked") return "rp-badge rp-badge-soft rp-badge-warning";
  return "rp-badge rp-badge-soft";
}

window.renderResourcePlanVersionRow = function renderResourcePlanVersionRow(row) {
  const statusCls = versionStatusBadge(row.status);
  const createdAt = row.created_at ? new Date(row.created_at).toLocaleDateString() : "—";
  return `
    <td><code class="rp-mono">v${esc(String(row.version))}</code></td>
    <td><span class="${statusCls}">${esc(row.status_display)}</span></td>
    <td>${esc(String(row.threshold_percentage))}%</td>
    <td style="color:var(--rp-text-muted)">${esc(createdAt)}</td>
  `;
};

// ── Version history panel ────────────────────────────────────────────────────

function historyVersionNumber(row) {
  return row.after?.version ?? row.before?.version ?? "";
}

function historyActionLabel(row) {
  const v = historyVersionNumber(row);
  const label = row.action_display || row.action;
  return v ? `${label} — v${v}` : label;
}

function historyActionIcon(action) {
  switch (action) {
    case "create":
      return "bi-plus-circle";
    case "activate":
      return "bi-play-circle";
    case "restore":
      return "bi-arrow-counterclockwise";
    case "lock":
      return "bi-lock-fill";
    case "delete":
      return "bi-trash";
    default:
      return "bi-clock-history";
  }
}

function historyActionColor(action) {
  switch (action) {
    case "create":
      return "accent";
    case "activate":
      return "success";
    case "restore":
      return "info";
    case "lock":
      return "warning";
    case "delete":
      return "danger";
    default:
      return "muted";
  }
}

async function loadVersionHistory(planCode) {
  const historyItems = document.getElementById("rp-resource-plan-versions-history");
  if (!historyItems) return;

  historyItems.loading?.();
  try {
    const { href } = API_URLS.resourcePlans.versionHistory(planCode);
    const res = await apiFetch(href, { method: "GET" });
    const rows = res?.data ?? [];

    if (!rows.length) {
      historyItems.empty?.();
      return;
    }

    historyItems.setItems(
      rows.map((row, idx) => {
        const el = document.createElement("history-item");
        el.setAttribute("label", historyActionLabel(row));
        el.setAttribute("icon", historyActionIcon(row.action));
        el.setAttribute("icon-color", historyActionColor(row.action));
        if (row.timestamp) {
          el.setAttribute("meta", new Date(row.timestamp).toLocaleString());
        }
        const actorName = row.actor?.display_name || row.actor?.email;
        if (actorName) el.setAttribute("note", `by ${actorName}`);
        if (idx !== rows.length - 1) el.setAttribute("connector", "");
        return el;
      }),
    );
  } catch {
    historyItems.error?.();
  }
}

// ── Versions table rows ───────────────────────────────────────────────────────

function applyVersionRows(planCode, versions) {
  const versionsTable = document.getElementById("rp-resource-plan-versions-table");
  if (!versionsTable || !Array.isArray(versions)) return;

  const rows = versions.map((v) => ({
    ...v,
    plan_code: planCode,
    rp_hide_activate: v.status === "active" || v.status === "locked",
    rp_hide_lock: v.status !== "active",
    rp_hide_delete: v.status !== "draft",
  }));

  versionsTable.rows = rows;
  versionsTable.render?.();
}

// ── Add Version drawer ───────────────────────────────────────────────────────

function openCreateVersionDrawer() {
  const drawer = document.getElementById("rp-resource-plan-version-create-drawer");
  if (!drawer) return;
  const thresholdField = document.getElementById("rp-new-version-threshold");
  if (thresholdField) thresholdField.value = "10";
  drawer.querySelectorAll("[data-rp-error]:not([hidden])").forEach((el) => {
    el.hidden = true;
  });
  drawer.show();
}

function initCreateVersionDrawer(planCode, reload) {
  const addBtn = document.getElementById("rp-resource-plan-versions-add-btn");
  const drawer = document.getElementById("rp-resource-plan-version-create-drawer");
  if (!addBtn || !drawer) return;

  addBtn.addEventListener("click", () => openCreateVersionDrawer());

  drawer.addEventListener("rp:footer-primary", async () => {
    const thresholdField = document.getElementById("rp-new-version-threshold");
    thresholdField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    if (drawer.querySelector("[data-rp-error]:not([hidden])")) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Adding…");
    try {
      const { href, method } = API_URLS.resourcePlans.versionCreate(planCode);
      await apiFetch(href, {
        method,
        body: JSON.stringify({ threshold_percentage: Number(thresholdField.value) }),
      });
      restoreButton(submitBtn, snap);
      drawer.hide();
      toast({
        type: "success",
        title: "Version added",
        message: "The new version has been created.",
      });
      await reload();
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? err?.data?.message ?? "Failed to add version.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

// ── Row click navigation ──────────────────────────────────────────────────────

function initVersionRowNavigation(table, planCode) {
  table.addEventListener("click", (e) => {
    if (e.target.closest("[data-rp-action]") || e.target.closest(".rp-table-more-btn")) {
      return;
    }
    const tr = e.target.closest("tr[data-rp-row]");
    if (!tr) return;
    const idx = parseInt(tr.getAttribute("data-rp-row"), 10);
    const row = table.rows[idx];
    if (!row) return;
    window.location.href = UI_URLS.resourcePlans.versionDetail(planCode, row.version);
  });
}

// ── Action modals (activate / restore / lock / delete / clone) ──────────────

function initVersionActionModals(table, planCode, reload) {
  const activateModal = document.getElementById("rp-resource-plan-version-activate-modal");
  const restoreModal = document.getElementById("rp-resource-plan-version-restore-modal");
  const lockModal = document.getElementById("rp-resource-plan-version-lock-modal");
  const deleteModal = document.getElementById("rp-resource-plan-version-delete-modal");

  table.addEventListener("rp:resource-plan-version:activate", (e) => {
    pendingVersionRow = e.detail.row;
    if (!activateModal) return;
    activateModal.setAttribute("title", `Activate version v${pendingVersionRow.version}?`);
    activateModal.setAttribute(
      "body",
      "This will mark the version as the active version of this resource plan.",
    );
    activateModal.show();
  });

  table.addEventListener("rp:resource-plan-version:restore", (e) => {
    pendingVersionRow = e.detail.row;
    if (!restoreModal) return;
    restoreModal.setAttribute("title", `Restore version v${pendingVersionRow.version}?`);
    restoreModal.setAttribute(
      "body",
      "This creates a new draft version with the same settings as this version.",
    );
    restoreModal.show();
  });

  table.addEventListener("rp:resource-plan-version:lock", (e) => {
    pendingVersionRow = e.detail.row;
    if (!lockModal) return;
    lockModal.setAttribute("title", `Lock version v${pendingVersionRow.version}?`);
    lockModal.setAttribute("body", "Locked versions can no longer be modified.");
    lockModal.show();
  });

  table.addEventListener("rp:resource-plan-version:delete", (e) => {
    pendingVersionRow = e.detail.row;
    if (!deleteModal) return;
    deleteModal.setAttribute("title", `Delete version v${pendingVersionRow.version}?`);
    deleteModal.setAttribute(
      "body",
      "This will permanently remove the draft version. This action cannot be undone.",
    );
    deleteModal.setAttribute("confirm-value", `v${pendingVersionRow.version}`);
    deleteModal.show();
  });

  table.addEventListener("rp:resource-plan-version:clone", () => {
    toast({
      type: "info",
      title: "Coming soon",
      message: "Cloning a version isn't available yet.",
    });
  });

  activateModal?.addEventListener("rp:confirm", async () => {
    if (!pendingVersionRow) return;
    try {
      const { href, method } = API_URLS.resourcePlans.versionActivate(
        planCode,
        pendingVersionRow.version,
      );
      await apiFetch(href, { method });
      activateModal.hide();
      toast({
        type: "success",
        title: "Version activated",
        message: `Version v${pendingVersionRow.version} is now active.`,
      });
      pendingVersionRow = null;
      await reload();
    } catch (err) {
      const msg = err?.data?.error?.message ?? err?.data?.message ?? "Failed to activate version.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });

  restoreModal?.addEventListener("rp:confirm", async () => {
    if (!pendingVersionRow) return;
    try {
      const { href, method } = API_URLS.resourcePlans.versionRestore(
        planCode,
        pendingVersionRow.version,
      );
      await apiFetch(href, { method });
      restoreModal.hide();
      toast({
        type: "success",
        title: "Version restored",
        message: `Version v${pendingVersionRow.version} was restored as a new version.`,
      });
      pendingVersionRow = null;
      await reload();
    } catch (err) {
      const msg = err?.data?.error?.message ?? err?.data?.message ?? "Failed to restore version.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });

  lockModal?.addEventListener("rp:confirm", async () => {
    if (!pendingVersionRow) return;
    try {
      const { href, method } = API_URLS.resourcePlans.versionLock(
        planCode,
        pendingVersionRow.version,
      );
      await apiFetch(href, { method });
      lockModal.hide();
      toast({
        type: "success",
        title: "Version locked",
        message: `Version v${pendingVersionRow.version} has been locked.`,
      });
      pendingVersionRow = null;
      await reload();
    } catch (err) {
      const msg = err?.data?.error?.message ?? err?.data?.message ?? "Failed to lock version.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });

  deleteModal?.addEventListener("rp:delete", async () => {
    if (!pendingVersionRow) return;
    const deleteBtn = deleteModal.querySelector("[data-delete-modal]");
    deleteBtn?.setAttribute("disabled", "");
    try {
      const { href, method } = API_URLS.resourcePlans.versionDelete(
        planCode,
        pendingVersionRow.version,
      );
      await apiFetch(href, { method });
      deleteModal.hide();
      toast({
        type: "success",
        title: "Version deleted",
        message: `Version v${pendingVersionRow.version} has been removed.`,
      });
      pendingVersionRow = null;
      await reload();
    } catch (err) {
      deleteBtn?.removeAttribute("disabled");
      const msg = err?.data?.error?.message ?? err?.data?.message ?? "Failed to delete version.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

function initVersionsTab(planCode, reload) {
  const table = document.getElementById("rp-resource-plan-versions-table");
  if (!table) return;

  initVersionRowNavigation(table, planCode);
  initVersionActionModals(table, planCode, reload);
  initCreateVersionDrawer(planCode, reload);
  loadVersionHistory(planCode);
}

// ── Detail page ───────────────────────────────────────────────────────────────

function initDetailPage() {
  const codeInput = document.getElementById("rp-resource-plan-code");
  if (!codeInput) return;
  const code = codeInput.value;
  if (!code) return;

  const setView = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.value = val ?? "—";
  };

  const showView = (id, val) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.value = val;
    el.removeAttribute("hidden");
  };

  // Wire comments panel before the detail fetch so it loads in parallel.
  const commentsPanel = document.getElementById("rp-resource-plan-comments-panel");
  if (commentsPanel) {
    commentsPanel.setAttribute("comments-url", API_URLS.resourcePlans.comments(code).href);
  }

  const { href } = API_URLS.resourcePlans.detail(code);

  function loadPlan() {
    return apiFetch(href, { method: "GET" })
      .then((res) => {
        const plan = res?.data;
        if (!plan) return;

        document.title = `${plan.name} — Resource Plans`;

        const titleEl = document.getElementById("rp-resource-plan-detail-title");
        if (titleEl) titleEl.textContent = plan.name;

        const headerIdenticon = document.getElementById("rp-resource-plan-header-identicon");
        if (headerIdenticon) headerIdenticon.setAttribute("name", plan.name);

        // Plan Details
        setView("rp-plan-detail-code", plan.code);
        setView("rp-plan-detail-name", plan.name);
        setView("rp-plan-detail-type", plan.plan_type_display || plan.plan_type);
        setView("rp-plan-detail-fy", plan.financial_year_display || "—");

        // Scope fields (merged into Plan Details, hidden until populated)
        const scope = plan.scope;
        if (scope) {
          if (scope.financial_year_display) {
            showView("rp-plan-detail-scope-fy", scope.financial_year_display);
          }
          if (scope.programme_name) {
            showView(
              "rp-plan-detail-scope-programme",
              `${scope.programme_name} (${scope.programme_code})`,
            );
          }
          if (scope.project_name) {
            showView(
              "rp-plan-detail-scope-project",
              `${scope.project_name} (${scope.project_code})`,
            );
          }
          if (scope.team_name) {
            showView("rp-plan-detail-scope-team", `${scope.team_name} (${scope.team_code})`);
          }
        }

        setView("rp-plan-detail-description", plan.description || "—");

        const statusEl = document.getElementById("rp-plan-detail-status");
        if (statusEl) {
          statusEl.setAttribute(
            "badge",
            plan.is_active ? "rp-badge rp-badge-soft rp-badge-success" : "rp-badge rp-badge-soft",
          );
          statusEl.value = plan.is_active ? "Active" : "Inactive";
        }

        if (plan.cloned_from_code) {
          showView("rp-plan-detail-cloned-from", plan.cloned_from_code);
        }

        // Metadata
        setView(
          "rp-plan-detail-created-at",
          plan.created_at ? new Date(plan.created_at).toLocaleString() : "—",
        );
        setView(
          "rp-plan-detail-created-by",
          plan.created_by?.display_name || plan.created_by?.email || "—",
        );
        setView(
          "rp-plan-detail-updated-at",
          plan.updated_at ? new Date(plan.updated_at).toLocaleString() : "—",
        );
        setView(
          "rp-plan-detail-updated-by",
          plan.updated_by?.display_name || plan.updated_by?.email || "—",
        );

        // Versions table (static load from detail response)
        applyVersionRows(code, plan.versions);
      })
      .catch(() => {
        toast({ type: "error", title: "Error", message: "Failed to load resource plan details." });
      });
  }

  function reloadAll() {
    return Promise.all([loadPlan(), loadVersionHistory(code)]);
  }

  loadPlan();
  initVersionsTab(code, reloadAll);
}

// ── Bootstrap ─────────────────────────────────────────────────────────────────

document.addEventListener("DOMContentLoaded", () => {
  initDetailPage();
});
