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

const sprintCode = window.location.pathname.split("/").filter(Boolean)[1];

function formatMonth(monthStr) {
  if (!monthStr) return "—";
  const [year, month] = monthStr.split("-");
  const d = new Date(parseInt(year, 10), parseInt(month, 10) - 1, 1);
  return d.toLocaleString("en-US", { month: "short" }) + " " + year;
}

const STATUS_LABELS = {
  in_progress: "In Progress",
  future: "Future",
  completed: "Completed",
  expired: "Expired",
};

const STATUS_BADGE_CLASS = {
  in_progress: "rp-badge-soft rp-badge-success",
  future: "rp-badge-soft rp-badge-info",
  completed: "rp-badge-soft rp-badge-neutral",
  expired: "rp-badge-soft rp-badge-danger",
};

const PROGRESS_VARIANT = {
  in_progress: "success",
  future: "",
  completed: "success",
  expired: "danger",
};

window.renderSprintCapacityRow = function renderSprintCapacityRow(row) {
  const member = row.member ?? {};
  const name =
    member.full_name ||
    [member.first_name, member.last_name].filter(Boolean).join(" ") ||
    member.email ||
    "—";
  const teamName = member.team || "";
  const teamCell = teamName ? `<span class="rp-badge rp-badge-soft">${esc(teamName)}</span>` : "—";
  const location = esc(member.location || "—");

  return `
    <td class="fw-medium">${esc(name)}</td>
    <td>${teamCell}</td>
    <td style="color:var(--rp-text-muted)">${location}</td>
    <td style="color:var(--rp-text-muted)">${esc(String(row.working_days ?? "—"))}</td>
    <td style="color:var(--rp-text-muted)">${esc(String(row.holiday_days ?? "—"))}</td>
    <td style="color:var(--rp-text-muted)">${esc(String(row.leave_days ?? "—"))}</td>
    <td class="fw-medium">${esc(String(row.net_capacity ?? "—"))}</td>
  `;
};

function sprintCountdown(endDateStr) {
  const diff = new Date(endDateStr).getTime() - Date.now();
  if (diff <= 0) return "Ends today";
  const days = Math.floor(diff / 86400000);
  const hours = Math.floor((diff % 86400000) / 3600000);
  if (days > 0) return `${days}d ${hours}h remaining`;
  const mins = Math.floor((diff % 3600000) / 60000);
  return hours > 0 ? `${hours}h ${mins}m remaining` : `${mins}m remaining`;
}

function renderTimer(sprint) {
  const progressEl = document.getElementById("rp-sprint-progress");
  const metaEl = document.getElementById("rp-sprint-timer-meta");

  if (!progressEl) return;

  const variant = PROGRESS_VARIANT[sprint.status] || "";
  const label = STATUS_LABELS[sprint.status] || sprint.status;
  let pct = 0;
  let metaText = "";

  if (sprint.status === "future") {
    pct = 0;
    metaText = `Starts ${sprint.start_date || "—"}`;
  } else if (sprint.status === "in_progress") {
    const start = new Date(sprint.start_date);
    const end = new Date(sprint.end_date);
    const now = Date.now();
    const total = end - start;
    const elapsed = now - start;
    pct = total > 0 ? Math.round((elapsed / total) * 100) : 0;
    pct = Math.min(100, Math.max(0, pct));
    metaText = sprintCountdown(sprint.end_date);
  } else if (sprint.status === "completed" || sprint.status === "expired") {
    pct = 100;
    metaText = `Ended ${sprint.end_date || "—"}`;
  }

  progressEl.setAttribute("percent", String(pct));
  if (variant) {
    progressEl.setAttribute("variant", variant);
  } else {
    progressEl.removeAttribute("variant");
  }
  progressEl.setAttribute("label", label);

  if (metaEl) metaEl.textContent = metaText;
}

async function loadSprintDetails() {
  try {
    const { href, method } = API_URLS.sprints.detail(sprintCode);
    const resp = await apiFetch(href, { method });
    const sprint = resp?.data ?? null;
    if (!sprint) return;

    const titleEl = document.getElementById("rp-sprint-detail-title");
    if (titleEl) {
      let titleHTML = esc(sprint.name);
      if (sprint.is_overridden) {
        titleHTML += ` <span class="rp-badge rp-badge-soft rp-badge-warning ms-2" style="font-size:0.55em;vertical-align:middle">Overridden</span>`;
      }
      titleEl.innerHTML = titleHTML;
    }

    setBreadcrumbs([
      { label: "Project" },
      { label: "Planning" },
      { label: "Sprints", href: UI_URLS.sprints.list() },
      { label: sprint.name },
    ]);

    const setView = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.value = val || "—";
    };

    setView("rp-sprint-detail-number", String(sprint.sprint_number));
    setView("rp-sprint-detail-name", sprint.name);
    setView("rp-sprint-detail-fy", sprint.financial_year?.long_fy || sprint.financial_year?.code);
    setView("rp-sprint-detail-code", sprint.code);
    setView("rp-sprint-detail-start", sprint.start_date);
    setView("rp-sprint-detail-end", sprint.end_date);
    setView("rp-sprint-detail-month", formatMonth(sprint.month));

    const statusEl = document.getElementById("rp-sprint-detail-status");
    if (statusEl) {
      const badgeCls = STATUS_BADGE_CLASS[sprint.status] || "rp-badge-soft";
      const label = STATUS_LABELS[sprint.status] || sprint.status;
      statusEl.setAttribute("badge", badgeCls);
      statusEl.value = label;
    }

    const closedEl = document.getElementById("rp-sprint-detail-closed");
    if (closedEl) {
      closedEl.setAttribute(
        "badge",
        sprint.is_closed ? "rp-badge rp-badge-soft rp-badge-warning" : "rp-badge rp-badge-soft",
      );
      closedEl.value = sprint.is_closed ? "Locked" : "Open";
    }

    setView("rp-sprint-detail-note", sprint.note || "—");
    setView("rp-sprint-detail-created", formatDate(sprint.created_at));
    setView("rp-sprint-detail-created-by", sprint.created_by?.email ?? "—");

    renderTimer(sprint);
  } catch {
    toast({
      type: "error",
      title: "Could not load sprint",
      message: "Refresh the page to retry.",
    });
  }
}

function initCapacityFilters(table) {
  const panel = document.getElementById("rp-sprint-capacity-filters");
  if (!panel || !table) return;

  const baseUrl = `/api/v1/sprints/${sprintCode}/capacity/`;

  panel.addEventListener("rp:filter:change", (e) => {
    const qs = e.detail.params.toString();
    table.setAttribute("url", qs ? `${baseUrl}?${qs}` : baseUrl);
  });
}

function initRebuildButton() {
  const btn = document.getElementById("rp-sprint-rebuild-btn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const snap = snapshotButton(btn);
    setBusyButton(btn, "Rebuilding…");
    const { href, method } = API_URLS.sprints.capacityRebuild(sprintCode);
    try {
      await apiFetch(href, { method });
      restoreButton(btn, snap);
      const table = document.getElementById("rp-sprint-capacity-table");
      table?.refresh();
      toast({
        type: "success",
        title: "Capacity rebuilt",
        message: "Member capacity has been recomputed.",
      });
    } catch (err) {
      restoreButton(btn, snap);
      const msg = err?.data?.message ?? "Failed to rebuild capacity. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  if (!sprintCode) return;
  loadSprintDetails();
  initRebuildButton();

  const table = document.getElementById("rp-sprint-capacity-table");
  initCapacityFilters(table);
});
