"use strict";

import { apiFetch, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { API_URLS } from "../main/urls.js";

function fmt(n) {
  return `£${Number(n).toLocaleString("en-GB")}`;
}

function fieldVal(id) {
  return parseInt(document.getElementById(id)?.value || "0", 10) || 0;
}

function updateRangeHints(xs, s, m, l) {
  const safe = (n) => Number.isFinite(n) && n > 0;
  const set = (id, text) => {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
  };

  set("rp-size-xs-range", safe(xs) ? `Up to ${fmt(xs)}` : "—");
  set("rp-size-s-range", safe(xs) && safe(s) ? `${fmt(xs + 1)} — ${fmt(s)}` : "—");
  set("rp-size-m-range", safe(s) && safe(m) ? `${fmt(s + 1)} — ${fmt(m)}` : "—");
  set("rp-size-l-range", safe(m) && safe(l) ? `${fmt(m + 1)} — ${fmt(l)}` : "—");
  set("rp-size-xl-range", safe(l) ? `${fmt(l + 1)} and above` : "—");
}

async function loadConfig() {
  const { href, method } = API_URLS.projectSizes.get();
  try {
    const res = await apiFetch(href, { method });
    const d = res.data;

    const editFields = {
      "rp-size-xs-max": d.xs_max_amount,
      "rp-size-s-max": d.s_max_amount,
      "rp-size-m-max": d.m_max_amount,
      "rp-size-l-max": d.l_max_amount,
    };
    for (const [id, val] of Object.entries(editFields)) {
      const el = document.getElementById(id);
      if (el) el.value = String(val);
    }

    const viewFields = {
      "rp-size-xs-view": d.xs_max_amount,
      "rp-size-s-view": d.s_max_amount,
      "rp-size-m-view": d.m_max_amount,
      "rp-size-l-view": d.l_max_amount,
    };
    for (const [id, val] of Object.entries(viewFields)) {
      const el = document.getElementById(id);
      if (el) el.textContent = fmt(val);
    }

    updateRangeHints(d.xs_max_amount, d.s_max_amount, d.m_max_amount, d.l_max_amount);
  } catch {
    toast({
      type: "error",
      title: "Load failed",
      message: "Could not load project size configuration.",
    });
  }
}

function initLiveHints() {
  ["rp-size-xs-max", "rp-size-s-max", "rp-size-m-max", "rp-size-l-max"].forEach((id) => {
    document.getElementById(id)?.addEventListener("input", () => {
      updateRangeHints(
        fieldVal("rp-size-xs-max"),
        fieldVal("rp-size-s-max"),
        fieldVal("rp-size-m-max"),
        fieldVal("rp-size-l-max"),
      );
    });
  });
}

function initSaveButton() {
  const btn = document.getElementById("rp-size-save-btn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    ["rp-size-xs-max", "rp-size-s-max", "rp-size-m-max", "rp-size-l-max"].forEach((id) =>
      document.getElementById(id)?.dispatchEvent(new Event("rp:validate", { bubbles: false })),
    );
    if (document.querySelector("[data-rp-error]:not([hidden])")) return;

    const xs = fieldVal("rp-size-xs-max");
    const s = fieldVal("rp-size-s-max");
    const m = fieldVal("rp-size-m-max");
    const l = fieldVal("rp-size-l-max");

    if (xs >= s || s >= m || m >= l) {
      toast({
        type: "error",
        title: "Invalid thresholds",
        message: "Amounts must be in ascending order: XS < S < M < L.",
      });
      return;
    }

    const snap = snapshotButton(btn);
    setBusyButton(btn, "Saving…");

    try {
      const { href, method } = API_URLS.projectSizes.update();
      const res = await apiFetch(href, {
        method,
        body: JSON.stringify({
          xs_max_amount: xs,
          s_max_amount: s,
          m_max_amount: m,
          l_max_amount: l,
        }),
      });
      restoreButton(btn, snap);
      const d = res.data;
      updateRangeHints(d.xs_max_amount, d.s_max_amount, d.m_max_amount, d.l_max_amount);
      toast({
        type: "success",
        title: "Saved",
        message: "Project size thresholds updated successfully.",
      });
    } catch (err) {
      restoreButton(btn, snap);
      toast({
        type: "error",
        title: "Error",
        message: err?.data?.error?.message ?? "Failed to save. Please try again.",
      });
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  loadConfig();
  initLiveHints();
  initSaveButton();
});
