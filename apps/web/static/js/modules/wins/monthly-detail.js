"use strict";

import { esc, setBreadcrumbs } from "../../components/utils.js";
import {
  apiFetch,
  formatDateTime,
  snapshotButton,
  setBusyButton,
  restoreButton,
} from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { statusModal } from "../utils/modal.js";
import { API_URLS } from "../main/urls.js";
import { hasPermission } from "../utils/index.js";
import { renderNominationForm } from "./survey-form.js";

const monthlyWinCode = window.location.pathname.split("/").filter(Boolean)[2];

let currentMonthlyWin = null;
let pendingOverrideSurveyCode = null;
let overrideFormHandle = null;

const MONTHLY_STATUS_BADGES = {
  draft: { cls: "rp-badge-soft", label: "Draft" },
  phase_1_open: { cls: "rp-badge-soft rp-badge-info", label: "Phase 1 Open" },
  phase_1_closed: { cls: "rp-badge-soft rp-badge-warning", label: "Phase 1 Closed" },
  phase_2_open: { cls: "rp-badge-soft rp-badge-info", label: "Phase 2 Open" },
  phase_2_closed: { cls: "rp-badge-soft rp-badge-warning", label: "Phase 2 Closed" },
  wins_declared: { cls: "rp-badge-soft rp-badge-success", label: "Wins Declared" },
};

const SURVEY_STATUS_BADGES = {
  pending: { cls: "rp-badge-soft", label: "Pending" },
  completed: { cls: "rp-badge-soft rp-badge-success", label: "Completed" },
  overridden: { cls: "rp-badge-soft rp-badge-warning", label: "Overridden" },
};

const CATEGORY_LABELS = {
  delivery: "Delivery",
  operational_excellence: "Operational Excellence",
};

window.renderMonthlySurveyRow = function renderMonthlySurveyRow(row) {
  const phaseLabel = row.phase === "phase_1" ? "Phase 1" : "Phase 2";
  const badge = SURVEY_STATUS_BADGES[row.status] || SURVEY_STATUS_BADGES.pending;
  const recipientName = row.recipient?.display_name || row.recipient?.email || "—";

  return `
    <td class="fw-medium">${esc(recipientName)}</td>
    <td>${phaseLabel}</td>
    <td style="color:var(--rp-text-muted)">${esc((row.teams || []).join(", ") || "—")}</td>
    <td><span class="rp-badge ${badge.cls}">${badge.label}</span></td>
    <td style="color:var(--rp-text-muted)">${row.sent_at ? formatDateTime(row.sent_at) : "—"}</td>
  `;
};

function setView(id, val) {
  const el = document.getElementById(id);
  if (el) el.value = val || "—";
}

function updateActionButtons() {
  if (!currentMonthlyWin) return;
  const status = currentMonthlyWin.status;
  const canManage = hasPermission("wins.manage_monthlywin");
  const canView = hasPermission("wins.view_monthlywin");

  const show = (id, cond) => {
    const el = document.getElementById(id);
    if (el) el.hidden = !cond;
  };

  show(
    "rp-monthly-win-preview-phase1-btn",
    canView && (status === "draft" || status === "phase_1_open"),
  );
  show("rp-monthly-win-launch-phase1-btn", canManage && status === "draft");
  show("rp-monthly-win-complete-phase1-btn", canManage && status === "phase_1_open");
  show(
    "rp-monthly-win-preview-phase2-btn",
    canView && (status === "phase_1_closed" || status === "phase_2_open"),
  );
  show("rp-monthly-win-launch-phase2-btn", canManage && status === "phase_1_closed");
  show("rp-monthly-win-complete-phase2-btn", canManage && status === "phase_2_open");
  show("rp-monthly-win-declare-btn", canManage && status === "phase_2_closed");
  show("rp-monthly-win-download-results-btn", canManage && status === "wins_declared");
  show("rp-monthly-win-send-results-btn", canManage && status === "wins_declared");
}

async function loadSurveys() {
  const table = document.getElementById("rp-monthly-win-surveys-table");
  if (!table) return;
  try {
    const { href, method } = API_URLS.wins.monthly.surveys(monthlyWinCode);
    const res = await apiFetch(href, { method });
    table.rows = res?.data ?? [];
  } catch {
    toast({ type: "error", title: "Error", message: "Could not load surveys." });
  }
}

async function loadResults() {
  const col = document.getElementById("rp-monthly-win-results-col");
  const body = document.getElementById("rp-monthly-win-results-body");
  if (!col || !body || currentMonthlyWin?.status !== "wins_declared") {
    if (col) col.hidden = true;
    return;
  }

  try {
    const { href, method } = API_URLS.wins.monthly.results(monthlyWinCode);
    const res = await apiFetch(href, { method });
    const results = res?.data ?? [];
    const byCategory = new Map();
    results.forEach((r) => {
      if (!byCategory.has(r.category)) byCategory.set(r.category, []);
      byCategory.get(r.category).push(r);
    });

    body.innerHTML =
      Array.from(byCategory.entries())
        .map(([category, rows]) => {
          const rowsHtml = rows
            .sort((a, b) => a.rank - b.rank)
            .map(
              (r) => `
                <div class="d-flex align-items-start gap-2 border rounded p-2 mb-2">
                  <span class="rp-badge rp-badge-soft rp-badge-success">#${r.rank}</span>
                  <div>
                    <div class="fw-medium">${esc(r.team_name)} — ${esc(r.title)}</div>
                    <div class="rp-help">${esc(r.description || "")}</div>
                    <div class="rp-help">${r.vote_count} vote(s)</div>
                  </div>
                </div>
              `,
            )
            .join("");
          return `
            <div class="mb-3">
              <div class="fw-semibold mb-2">${esc(CATEGORY_LABELS[category] || category)}</div>
              ${rowsHtml || `<p class="rp-muted">No results.</p>`}
            </div>
          `;
        })
        .join("") || `<p class="rp-muted">No results declared yet.</p>`;

    col.hidden = false;
  } catch {
    toast({ type: "error", title: "Error", message: "Could not load results." });
  }
}

async function loadMonthlyWinDetails() {
  try {
    const { href, method } = API_URLS.wins.monthly.detail(monthlyWinCode);
    const res = await apiFetch(href, { method });
    const mw = res?.data ?? null;
    if (!mw) return;
    currentMonthlyWin = mw;

    const titleEl = document.getElementById("rp-monthly-win-detail-title");
    if (titleEl) titleEl.textContent = mw.name;

    setBreadcrumbs([
      { label: "Insights" },
      { label: "Weekly Wins", href: "/wins/" },
      { label: "Monthly Wins", href: "/wins/monthly/" },
      { label: mw.name },
    ]);

    const badge = MONTHLY_STATUS_BADGES[mw.status] || MONTHLY_STATUS_BADGES.draft;
    const statusEl = document.getElementById("rp-monthly-win-detail-status");
    if (statusEl) {
      statusEl.setAttribute("badge", `rp-badge ${badge.cls}`);
      statusEl.value = badge.label;
    }

    setView(
      "rp-monthly-win-detail-weeks",
      (mw.weeks || []).map((w) => `Week ${w.week_number}`).join(", "),
    );
    setView(
      "rp-monthly-win-detail-phase1-deadline",
      mw.phase1_deadline ? formatDateTime(mw.phase1_deadline) : "—",
    );
    setView(
      "rp-monthly-win-detail-phase2-deadline",
      mw.phase2_deadline ? formatDateTime(mw.phase2_deadline) : "—",
    );

    updateActionButtons();
    await loadSurveys();
    await loadResults();
  } catch {
    toast({
      type: "error",
      title: "Could not load Monthly Win",
      message: "Refresh the page to retry.",
    });
  }
}

function initPreviewDrawer() {
  const drawer = document.getElementById("rp-monthly-win-preview-drawer");
  const header = document.getElementById("rp-monthly-win-preview-header");
  const subtitle = document.getElementById("rp-monthly-win-preview-subtitle");
  const teamRow = document.getElementById("rp-monthly-win-preview-team-row");
  const teamField = document.getElementById("rp-monthly-win-preview-team");
  const body = document.getElementById("rp-monthly-win-preview-body");
  if (!drawer || !body) return;

  let currentPhase = "phase_1";

  async function loadPreview(teamCode) {
    body.innerHTML = `<p class="rp-muted">Loading…</p>`;
    try {
      const { href, method } = API_URLS.wins.monthly.previewSurvey(
        monthlyWinCode,
        currentPhase,
        teamCode,
      );
      const res = await apiFetch(href, { method });
      renderNominationForm(body, res?.data ?? { entries: [], categories: [] }, {
        interactive: false,
        groupByTeam: true,
      });
    } catch (err) {
      const msg = err?.data?.error?.message ?? "Could not load the preview.";
      body.innerHTML = `<p class="rp-muted">${esc(msg)}</p>`;
    }
  }

  async function openPreview(phase) {
    currentPhase = phase;
    header?.setAttribute(
      "title",
      phase === "phase_1" ? "Phase 1 Survey Preview" : "Phase 2 Survey Preview",
    );
    if (subtitle) {
      subtitle.textContent =
        phase === "phase_1"
          ? "Select a team to see the exact survey recipients will receive."
          : "This is the consolidated survey covering all Phase 1 nominated wins.";
    }

    if (phase === "phase_1") {
      if (teamRow) teamRow.hidden = false;
      const select = teamField?.querySelector(".rp-input");
      try {
        const { href, method } = API_URLS.wins.monthly.previewTeams(monthlyWinCode);
        const res = await apiFetch(href, { method });
        const teams = res?.data ?? [];
        if (select) {
          select.innerHTML = teams
            .map((t) => `<option value="${esc(t.code)}">${esc(t.name)}</option>`)
            .join("");
          select.disabled = false;
        }
        if (teams.length) {
          await loadPreview(teams[0].code);
        } else {
          body.innerHTML = `<p class="rp-muted">No teams have wins in the selected weeks.</p>`;
        }
      } catch {
        body.innerHTML = `<p class="rp-muted">Could not load teams.</p>`;
      }
    } else {
      if (teamRow) teamRow.hidden = true;
      await loadPreview(null);
    }

    drawer.show();
  }

  teamField?.querySelector(".rp-input")?.addEventListener("change", (e) => {
    if (currentPhase === "phase_1") loadPreview(e.target.value);
  });

  document
    .getElementById("rp-monthly-win-preview-phase1-btn")
    ?.addEventListener("click", () => openPreview("phase_1"));
  document
    .getElementById("rp-monthly-win-preview-phase2-btn")
    ?.addEventListener("click", () => openPreview("phase_2"));
}

function confirmAndRun({ title, body, onConfirm }) {
  statusModal.open({
    iconType: "warning",
    title,
    body,
    closeable: true,
    dismissBtn: { label: "Cancel", onClick: () => statusModal.close() },
    primaryBtn: { label: "Confirm", onClick: onConfirm },
  });
}

function initPhaseActionButtons() {
  const launch1 = document.getElementById("rp-monthly-win-launch-phase1-btn");
  launch1?.addEventListener("click", () => {
    confirmAndRun({
      title: "Launch Phase 1?",
      body: "This emails a survey link to every recipient for the teams with wins in the selected weeks. This cannot be undone.",
      onConfirm: async () => {
        const { href, method } = API_URLS.wins.monthly.launchPhase1(monthlyWinCode);
        try {
          await apiFetch(href, { method });
          statusModal.close();
          toast({
            type: "success",
            title: "Phase 1 launched",
            message: "Survey emails have been sent.",
          });
          await loadMonthlyWinDetails();
        } catch (err) {
          statusModal.close();
          toast({
            type: "error",
            title: "Error",
            message: err?.data?.error?.message ?? "Failed to launch Phase 1.",
          });
        }
      },
    });
  });

  const complete1 = document.getElementById("rp-monthly-win-complete-phase1-btn");
  complete1?.addEventListener("click", () => {
    confirmAndRun({
      title: "Close Phase 1?",
      body: "No further Phase 1 nominations will be accepted after this.",
      onConfirm: async () => {
        const { href, method } = API_URLS.wins.monthly.completePhase1(monthlyWinCode);
        try {
          await apiFetch(href, { method });
          statusModal.close();
          toast({ type: "success", title: "Phase 1 closed" });
          await loadMonthlyWinDetails();
        } catch (err) {
          statusModal.close();
          toast({
            type: "error",
            title: "Error",
            message: err?.data?.error?.message ?? "Failed to close Phase 1.",
          });
        }
      },
    });
  });

  const launch2 = document.getElementById("rp-monthly-win-launch-phase2-btn");
  launch2?.addEventListener("click", () => {
    confirmAndRun({
      title: "Launch Phase 2?",
      body: "This emails one consolidated survey to every Phase 1 recipient, covering all nominated wins. This cannot be undone.",
      onConfirm: async () => {
        const { href, method } = API_URLS.wins.monthly.launchPhase2(monthlyWinCode);
        try {
          await apiFetch(href, { method });
          statusModal.close();
          toast({
            type: "success",
            title: "Phase 2 launched",
            message: "Survey emails have been sent.",
          });
          await loadMonthlyWinDetails();
        } catch (err) {
          statusModal.close();
          toast({
            type: "error",
            title: "Error",
            message: err?.data?.error?.message ?? "Failed to launch Phase 2.",
          });
        }
      },
    });
  });

  const complete2 = document.getElementById("rp-monthly-win-complete-phase2-btn");
  complete2?.addEventListener("click", () => {
    confirmAndRun({
      title: "Close Phase 2?",
      body: "No further Phase 2 votes will be accepted after this.",
      onConfirm: async () => {
        const { href, method } = API_URLS.wins.monthly.completePhase2(monthlyWinCode);
        try {
          await apiFetch(href, { method });
          statusModal.close();
          toast({ type: "success", title: "Phase 2 closed" });
          await loadMonthlyWinDetails();
        } catch (err) {
          statusModal.close();
          toast({
            type: "error",
            title: "Error",
            message: err?.data?.error?.message ?? "Failed to close Phase 2.",
          });
        }
      },
    });
  });

  const declare = document.getElementById("rp-monthly-win-declare-btn");
  declare?.addEventListener("click", () => {
    confirmAndRun({
      title: "Declare winners?",
      body: "This tallies Phase 2 votes and ranks the top 2 wins per category. This cannot be undone.",
      onConfirm: async () => {
        const { href, method } = API_URLS.wins.monthly.declare(monthlyWinCode);
        try {
          await apiFetch(href, { method });
          statusModal.close();
          toast({ type: "success", title: "Winners declared" });
          await loadMonthlyWinDetails();
        } catch (err) {
          statusModal.close();
          toast({
            type: "error",
            title: "Error",
            message: err?.data?.error?.message ?? "Failed to declare winners.",
          });
        }
      },
    });
  });

  const download = document.getElementById("rp-monthly-win-download-results-btn");
  download?.addEventListener("click", () => {
    const { href } = API_URLS.wins.monthly.resultsPdf(monthlyWinCode);
    window.open(href, "_blank");
  });

  const send = document.getElementById("rp-monthly-win-send-results-btn");
  send?.addEventListener("click", async () => {
    const snap = snapshotButton(send);
    setBusyButton(send, "Sending…");
    const { href, method } = API_URLS.wins.monthly.sendResults(monthlyWinCode);
    try {
      await apiFetch(href, { method });
      restoreButton(send, snap);
      toast({ type: "success", title: "Sent", message: "Results email has been sent." });
    } catch (err) {
      restoreButton(send, snap);
      toast({
        type: "error",
        title: "Error",
        message: err?.data?.error?.message ?? "Failed to send results email.",
      });
    }
  });
}

function initOverrideDrawer(surveysTable) {
  const drawer = document.getElementById("rp-monthly-win-override-drawer");
  const header = document.getElementById("rp-monthly-win-override-header");
  const body = document.getElementById("rp-monthly-win-override-body");
  if (!drawer || !surveysTable) return;

  surveysTable.addEventListener("rp:survey:override", async (e) => {
    const row = e.detail.row;
    pendingOverrideSurveyCode = row.code;
    header?.setAttribute(
      "title",
      `Override survey — ${row.recipient?.display_name || row.recipient?.email || ""}`,
    );
    body.innerHTML = `<p class="rp-muted">Loading…</p>`;
    drawer.show();

    try {
      const { href, method } = API_URLS.wins.monthly.surveyAdminData(row.code);
      const res = await apiFetch(href, { method });
      const data = res?.data ?? { entries: [], categories: [] };
      overrideFormHandle = renderNominationForm(body, data, {
        interactive: true,
        groupByTeam: data.phase === "phase_1",
      });
    } catch (err) {
      const msg = err?.data?.error?.message ?? "Could not load this survey.";
      body.innerHTML = `<p class="rp-muted">${esc(msg)}</p>`;
      overrideFormHandle = null;
    }
  });

  drawer.addEventListener("rp:footer-primary", async () => {
    if (!pendingOverrideSurveyCode || !overrideFormHandle) return;

    const submitBtn = drawer.querySelector("[data-footer-primary]");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Saving…");

    const payload = { nominations: overrideFormHandle.getNominations() };
    const { href, method } = API_URLS.wins.monthly.overrideSurvey(pendingOverrideSurveyCode);
    try {
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      drawer.hide();
      surveysTable.refresh?.();
      loadSurveys();
      toast({ type: "success", title: "Survey overridden" });
      pendingOverrideSurveyCode = null;
      overrideFormHandle = null;
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to override survey. Please try again.";
      toast({ type: "error", title: "Error", message: msg });
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  if (!monthlyWinCode) return;
  if (!document.getElementById("rp-monthly-win-detail-title")) return;

  loadMonthlyWinDetails();
  initPreviewDrawer();
  initPhaseActionButtons();
  initOverrideDrawer(document.getElementById("rp-monthly-win-surveys-table"));
});
