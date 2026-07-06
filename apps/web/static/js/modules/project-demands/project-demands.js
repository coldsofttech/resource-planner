"use strict";

import { esc } from "../../components/utils.js";
import { apiFetch } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

// ---------------------------------------------------------------------------
// Shared state
// ---------------------------------------------------------------------------

let pendingRow = null;

// ---------------------------------------------------------------------------
// Utility functions
// ---------------------------------------------------------------------------

function formatDate(value) {
  if (!value) return "—";
  try {
    return new Date(value).toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return value;
  }
}

function statusBadge(status) {
  const map = {
    pending: "rp-badge",
    accepted: "rp-badge-success",
    rejected: "rp-badge rp-badge--danger",
  };
  const cls = map[status] || "rp-badge";
  const label = status ? status.charAt(0).toUpperCase() + status.slice(1) : "—";
  return `<span class="${esc(cls)}">${esc(label)}</span>`;
}

// ---------------------------------------------------------------------------
// Row renderer
// ---------------------------------------------------------------------------

window.renderOnboardingRow = function renderOnboardingRow(row) {
  const requesterName = esc(row.requester?.name || row.requester?.email || "—");
  const products = (row.product_names || []).map(esc).join(", ") || "—";
  const date = esc(formatDate(row.created_at));
  return `
    <td>${esc(row.project_name || "—")}</td>
    <td>${requesterName}</td>
    <td>${products}</td>
    <td>${statusBadge(row.status)}</td>
    <td>${date}</td>
  `;
};

// ---------------------------------------------------------------------------
// View drawer
// ---------------------------------------------------------------------------

function openViewDrawer(row) {
  const drawer = document.getElementById("rp-onboarding-view-drawer");
  if (!drawer) return;
  pendingRow = row;

  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.value = val ? esc(String(val)) : "—";
  };

  const setRaw = (id, html) => {
    const el = document.getElementById(id);
    if (el) el.value = html || "—";
  };

  const setMultiline = (id, val) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.value = val ? esc(String(val)).replace(/\n/g, "<br>") : "—";
  };

  // Project link at top — show if accepted and project was created
  const projectSection = document.getElementById("rp-view-onb-project-section");
  const projectLinkField = document.getElementById("rp-view-onb-project-link");
  if (projectSection) {
    if (row.project_code_ref) {
      const href = esc(UI_URLS.projects.detail(row.project_code_ref));
      const label = esc(row.project_name_ref || row.project_code_ref);
      if (projectLinkField) {
        projectLinkField.value = `<a href="${href}" target="_blank" rel="noopener noreferrer" class="rp-link">${label}</a>`;
      }
      projectSection.hidden = false;
    } else {
      projectSection.hidden = true;
    }
  }

  set("rp-view-onb-project-name", row.project_name);
  setRaw("rp-view-onb-status", statusBadge(row.status));
  set(
    "rp-view-onb-requester",
    row.requester ? `${row.requester.name || ""} <${row.requester.email}>`.trim() : null,
  );
  set(
    "rp-view-onb-exec",
    row.accountable_executive
      ? `${row.accountable_executive.name || ""} <${row.accountable_executive.email}>`.trim()
      : null,
  );
  set("rp-view-onb-products", (row.products || []).map((p) => p.name).join(", ") || null);
  set("rp-view-onb-bu", (row.business_unit_names || []).join(", ") || null);
  set("rp-view-onb-project-code", row.project_code || null);
  set("rp-view-onb-start", formatDate(row.tentative_start_date));
  set("rp-view-onb-end", formatDate(row.tentative_end_date));
  setMultiline("rp-view-onb-requirements", row.requirements);
  setMultiline("rp-view-onb-risk", row.risk);
  set("rp-view-onb-contacts", (row.contacts || []).map((c) => c.email).join(", ") || null);

  // Links rendered as clickable anchors opening in a new tab
  const linkItems = (row.links || []).map((l) => {
    const href = esc(l.url);
    const label = esc(l.title || l.url);
    return `<a href="${href}" target="_blank" rel="noopener noreferrer" class="rp-link">${label}</a>`;
  });
  setRaw("rp-view-onb-links", linkItems.join("<br>") || null);

  // Attachments rendered as download links (session auth covers the download endpoint)
  const attachmentItems = (row.attachments || []).map((a) => {
    const { href } = API_URLS.demands.attachments.download(row.code, a.code);
    const label = esc(a.file_name || a.name || a.code);
    return `<a href="${esc(href)}" class="rp-link" download>${label}</a>`;
  });
  setRaw("rp-view-onb-attachments", attachmentItems.join("<br>") || null);
  set("rp-view-onb-created-at", formatDate(row.created_at));

  const isPending = row.status === "pending";
  const primaryBtn = drawer.querySelector("[data-footer-primary]");
  const secondaryBtn = drawer.querySelector("[data-footer-secondary]");
  if (primaryBtn) {
    if (isPending) primaryBtn.removeAttribute("disabled");
    else primaryBtn.setAttribute("disabled", "");
  }
  if (secondaryBtn) {
    if (isPending) secondaryBtn.removeAttribute("disabled");
    else secondaryBtn.setAttribute("disabled", "");
  }

  drawer.show();
}

function initViewDrawer(table) {
  const drawer = document.getElementById("rp-onboarding-view-drawer");
  if (!drawer) return;

  table.addEventListener("click", (e) => {
    if (e.target.closest("[data-rp-action]") || e.target.closest(".rp-table-more-btn")) return;
    const tr = e.target.closest("tr[data-rp-row]");
    if (!tr) return;
    const idx = parseInt(tr.getAttribute("data-rp-row"), 10);
    const row = table.rows[idx];
    if (!row) return;

    const { href, method } = API_URLS.demands.detail(row.code);
    apiFetch(href, { method })
      .then((data) => openViewDrawer(data?.data ?? row))
      .catch(() => openViewDrawer(row));
  });
}

// ---------------------------------------------------------------------------
// Accept / Reject from the view drawer
// ---------------------------------------------------------------------------

function initViewDrawerActions(table) {
  const drawer = document.getElementById("rp-onboarding-view-drawer");
  const acceptModal = document.getElementById("rp-onboarding-accept-modal");
  const rejectModal = document.getElementById("rp-onboarding-reject-modal");
  if (!drawer) return;

  drawer.addEventListener("rp:footer-primary", () => {
    if (!pendingRow || pendingRow.status !== "pending") return;
    if (acceptModal) {
      acceptModal.setAttribute("title", `Accept "${esc(pendingRow.project_name)}"?`);
      acceptModal.setAttribute(
        "body",
        "This will create a new project from this demand request and mark it as accepted.",
      );
      acceptModal.show();
    }
  });

  drawer.addEventListener("rp:footer-secondary", () => {
    if (!pendingRow || pendingRow.status !== "pending") return;
    if (rejectModal) {
      rejectModal.setAttribute("title", `Reject "${esc(pendingRow.project_name)}"?`);
      rejectModal.setAttribute("body", "This will mark the demand request as rejected.");
      rejectModal.show();
    }
  });

  if (acceptModal) {
    acceptModal.addEventListener("rp:confirm", async () => {
      if (!pendingRow) return;
      const confirmBtn = acceptModal.querySelector("[data-action-modal]");
      confirmBtn?.setAttribute("disabled", "");
      const { href, method } = API_URLS.demands.accept(pendingRow.code);
      try {
        await apiFetch(href, { method });
        acceptModal.hide();
        drawer.hide();
        table.refresh();
        toast({ type: "success", title: "Request accepted", message: "Project has been created." });
        pendingRow = null;
      } catch (err) {
        confirmBtn?.removeAttribute("disabled");
        const msg = err?.data?.error?.message ?? "Failed to accept. Please try again.";
        toast({ type: "error", title: "Error", message: msg });
      }
    });
  }

  if (rejectModal) {
    rejectModal.addEventListener("rp:confirm", async () => {
      if (!pendingRow) return;
      const confirmBtn = rejectModal.querySelector("[data-action-modal]");
      confirmBtn?.setAttribute("disabled", "");
      const { href, method } = API_URLS.demands.reject(pendingRow.code);
      try {
        await apiFetch(href, { method });
        rejectModal.hide();
        drawer.hide();
        table.refresh();
        toast({
          type: "success",
          title: "Request rejected",
          message: "The demand request has been rejected.",
        });
        pendingRow = null;
      } catch (err) {
        confirmBtn?.removeAttribute("disabled");
        const msg = err?.data?.error?.message ?? "Failed to reject. Please try again.";
        toast({ type: "error", title: "Error", message: msg });
      }
    });
  }
}

// ---------------------------------------------------------------------------
// Table actions (accept / reject from row action buttons)
// ---------------------------------------------------------------------------

function initActions(table) {
  table.addEventListener("rp:onboarding:accept", (e) => {
    const row = e.detail.row;
    const acceptModal = document.getElementById("rp-onboarding-accept-modal");
    if (!acceptModal) return;
    pendingRow = row;
    acceptModal.setAttribute("title", `Accept "${esc(row.project_name)}"?`);
    acceptModal.setAttribute(
      "body",
      "This will create a new project from this demand request and mark it as accepted.",
    );
    acceptModal.show();
  });

  table.addEventListener("rp:onboarding:reject", (e) => {
    const row = e.detail.row;
    const rejectModal = document.getElementById("rp-onboarding-reject-modal");
    if (!rejectModal) return;
    pendingRow = row;
    rejectModal.setAttribute("title", `Reject "${esc(row.project_name)}"?`);
    rejectModal.setAttribute("body", "This will mark the demand request as rejected.");
    rejectModal.show();
  });
}

// ---------------------------------------------------------------------------
// Create button
// ---------------------------------------------------------------------------

function initCreateButton() {
  const btn = document.getElementById("rp-demands-create-btn");
  if (!btn) return;
  btn.addEventListener("click", () => {
    window.location.href = UI_URLS.onboarding.create();
  });
}

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  initCreateButton();

  const table = document.getElementById("rp-onboardings-table");
  if (!table) return;

  initActions(table);
  initViewDrawer(table);
  initViewDrawerActions(table);
});
