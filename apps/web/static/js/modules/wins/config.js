"use strict";

import { apiFetch, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { toast } from "../utils/toast.js";
import { isEmail } from "../utils/validators.js";
import { API_URLS } from "../main/urls.js";

async function loadConfig() {
  const { href, method } = API_URLS.winsConfig.get();
  try {
    const res = await apiFetch(href, { method });
    const d = res.data;

    const startNumberField = document.getElementById("rp-wins-config-start-number");
    if (startNumberField) startNumberField.value = String(d.win_start_number);
    const startNumberView = document.getElementById("rp-wins-config-start-number-view");
    if (startNumberView) startNumberView.textContent = String(d.win_start_number);

    const recipientsField = document.getElementById("rp-wins-config-review-recipients");
    if (recipientsField) recipientsField.value = d.wins_review_email_recipients || "";
    const recipientsView = document.getElementById("rp-wins-config-review-recipients-view");
    if (recipientsView) {
      recipientsView.textContent = d.wins_review_email_recipients || "—";
    }
  } catch {
    toast({
      type: "error",
      title: "Load failed",
      message: "Could not load Wins configuration.",
    });
  }
}

function initSaveButton() {
  const btn = document.getElementById("rp-wins-config-save-btn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const startNumberField = document.getElementById("rp-wins-config-start-number");
    const recipientsField = document.getElementById("rp-wins-config-review-recipients");

    startNumberField?.dispatchEvent(new Event("rp:validate", { bubbles: false }));
    if (document.querySelector("[data-rp-error]:not([hidden])")) return;

    const recipients = (recipientsField?.value || "").trim();
    if (recipients) {
      const invalid = recipients
        .split(",")
        .map((addr) => addr.trim())
        .filter((addr) => addr && !isEmail(addr));
      if (invalid.length) {
        toast({
          type: "error",
          title: "Invalid email",
          message: `'${invalid[0]}' is not a valid email address.`,
        });
        return;
      }
    }

    const snap = snapshotButton(btn);
    setBusyButton(btn, "Saving…");

    try {
      const { href, method } = API_URLS.winsConfig.update();
      await apiFetch(href, {
        method,
        body: JSON.stringify({
          win_start_number: parseInt(startNumberField?.value || "1", 10) || 1,
          wins_review_email_recipients: recipients,
        }),
      });
      restoreButton(btn, snap);
      toast({
        type: "success",
        title: "Saved",
        message: "Wins configuration updated successfully.",
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
  const panel =
    document.getElementById("rp-wins-config-start-number") ||
    document.getElementById("rp-wins-config-start-number-view");
  if (!panel) return;

  loadConfig();
  initSaveButton();
});
