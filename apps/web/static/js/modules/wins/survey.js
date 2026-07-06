"use strict";

import { applyMeta, getAppLogo } from "../main/meta.js";
import { apiFetch, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { API_URLS } from "../main/urls.js";
import { renderNominationForm } from "./survey-form.js";

function show(id, visible) {
  const el = document.getElementById(id);
  if (el) el.hidden = !visible;
}

function setBanner(id, message) {
  const banner = document.getElementById(id);
  if (!banner) return;
  banner.setAttribute("subtitle", message || "");
  if (message) banner.setAttribute("open", "");
  else banner.removeAttribute("open");
}

function applyMetaToPage(meta) {
  if (!meta) return;
  const nameEl = document.getElementById("rp-app-name");
  if (nameEl) nameEl.innerHTML = meta.app_name ?? "";
  const logoEl = document.getElementById("rp-app-logo");
  if (logoEl) logoEl.textContent = getAppLogo(meta);
}

async function initSurvey() {
  const token = document.body.dataset.surveyToken;
  if (!token) return;

  show("rp-survey-loading", true);

  let data;
  try {
    const { href, method } = API_URLS.wins.monthly.survey.get(token);
    const res = await apiFetch(href, { method });
    data = res?.data;
  } catch {
    show("rp-survey-loading", false);
    show("rp-survey-invalid", true);
    return;
  }

  show("rp-survey-loading", false);

  if (!data) {
    show("rp-survey-invalid", true);
    return;
  }

  if (data.status !== "pending") {
    show("rp-survey-closed", true);
    return;
  }

  show("rp-survey-form-wrap", true);

  const phaseLabel = data.phase === "phase_1" ? "Phase 1" : "Phase 2 (Final Selection)";
  document.getElementById("rp-survey-title").textContent =
    `${data.monthly_win_name} — ${phaseLabel}`;

  const teamList = (data.team_names || []).join(", ");
  const deadlineStr = data.deadline
    ? ` Please respond by ${new Date(data.deadline).toLocaleString()}.`
    : "";
  const subtitle =
    data.phase === "phase_1"
      ? `Hi ${data.recipient_name}, nominate the best wins from your team(s): ${teamList}.${deadlineStr}`
      : `Hi ${data.recipient_name}, cast your final votes across all nominated wins.${deadlineStr}`;
  document.getElementById("rp-survey-subtitle").textContent = subtitle;

  const container = document.getElementById("rp-survey-nominations");
  const formHandle = renderNominationForm(container, data, {
    interactive: true,
    groupByTeam: data.phase === "phase_1",
  });

  const submitBtn = document.getElementById("rp-survey-submit-btn");
  submitBtn?.addEventListener("click", async () => {
    setBanner("rp-survey-error", "");
    const snap = snapshotButton(submitBtn);
    setBusyButton(submitBtn, "Submitting…");

    const payload = { nominations: formHandle?.getNominations() ?? [] };
    try {
      const { href, method } = API_URLS.wins.monthly.survey.submit(token);
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(submitBtn, snap);
      show("rp-survey-form-wrap", false);
      show("rp-survey-success", true);
    } catch (err) {
      restoreButton(submitBtn, snap);
      const msg = err?.data?.error?.message ?? "Failed to submit survey. Please try again.";
      setBanner("rp-survey-error", msg);
    }
  });
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!document.getElementById("rp-survey-card")) return;
  const meta = await applyMeta();
  applyMetaToPage(meta);
  initSurvey();
});
