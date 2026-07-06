"use strict";

import { apiFetch, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { getMeta } from "../main/meta.js";
import { API_URLS } from "../main/urls.js";

function getField(id) {
  return document.getElementById(id);
}

async function updateClassicHint() {
  const hint = getField("rp-security-classic-hint");
  if (!hint) return;
  const meta = await getMeta();
  hint.hidden = meta?.auth_mode === "classic";
}

async function loadConfig() {
  const { href, method } = API_URLS.securityConfig.get();
  try {
    const res = await apiFetch(href, { method });
    const d = res.data;

    const rotationField = getField("rp-security-rotation-days");
    if (rotationField) rotationField.value = d.password_rotation_days;

    const minLengthField = getField("rp-security-min-length");
    if (minLengthField) minLengthField.value = d.password_min_length;

    const historyField = getField("rp-security-history-count");
    if (historyField) historyField.value = d.password_history_count;

    const upperField = getField("rp-security-require-uppercase");
    if (upperField) upperField.checked = d.password_require_uppercase;

    const lowerField = getField("rp-security-require-lowercase");
    if (lowerField) lowerField.checked = d.password_require_lowercase;

    const digitsField = getField("rp-security-require-digits");
    if (digitsField) digitsField.checked = d.password_require_digits;

    const specialField = getField("rp-security-require-special");
    if (specialField) specialField.checked = d.password_require_special;

    const sessionTimeoutField = getField("rp-security-session-timeout");
    if (sessionTimeoutField) sessionTimeoutField.value = d.session_timeout_minutes;
  } catch {
    toast({
      type: "error",
      title: "Load failed",
      message: "Could not load security configuration.",
    });
  }
}

function initSaveButton() {
  const btn = getField("rp-security-save-btn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const rotationField = getField("rp-security-rotation-days");
    const minLengthField = getField("rp-security-min-length");
    const historyField = getField("rp-security-history-count");
    const upperField = getField("rp-security-require-uppercase");
    const lowerField = getField("rp-security-require-lowercase");
    const digitsField = getField("rp-security-require-digits");
    const specialField = getField("rp-security-require-special");
    const sessionTimeoutField = getField("rp-security-session-timeout");

    const snap = snapshotButton(btn);
    setBusyButton(btn, "Saving…");

    const payload = {
      password_rotation_days: parseInt(rotationField?.value, 10) || 0,
      password_min_length: parseInt(minLengthField?.value, 10) || 1,
      password_history_count: parseInt(historyField?.value, 10) || 0,
      password_require_uppercase: upperField?.checked ?? false,
      password_require_lowercase: lowerField?.checked ?? false,
      password_require_digits: digitsField?.checked ?? false,
      password_require_special: specialField?.checked ?? false,
      session_timeout_minutes: parseInt(sessionTimeoutField?.value, 10) || 0,
    };

    try {
      const { href, method } = API_URLS.securityConfig.update();
      await apiFetch(href, { method, body: JSON.stringify(payload) });
      restoreButton(btn, snap);
      toast({
        type: "success",
        title: "Saved",
        message: "Security configuration updated successfully.",
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
  updateClassicHint();
  initSaveButton();
});
