"use strict";

import { applyMeta } from "./meta.js";
import { apiFetch } from "../utils/utils.js";
import { API_URLS } from "./urls.js";

export { getMeta, getAppName, getAppLogo, clearMeta, applyMeta } from "./meta.js";

function showFyBanner(fy) {
  const banner = document.getElementById("fy-banner");
  if (!banner || !fy?.in_threshold) return;

  const daysLeft = fy.days_remaining ?? 0;
  const longFy = String(fy.long_fy ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  const daysLabel =
    daysLeft <= 0
      ? `Financial Year <strong>${longFy}</strong> ends today.`
      : `Financial Year <strong>${longFy}</strong> ends in <strong>${daysLeft === 1 ? "1 day" : `${daysLeft} days`}</strong>.`;

  banner._msgContent = daysLabel;
  banner.setAttribute("open", "");
}

async function initFyBanner() {
  const banner = document.getElementById("fy-banner");
  if (!banner) return;

  try {
    const response = await apiFetch(API_URLS.fy.active().href);
    showFyBanner(response?.data);
  } catch {
    return;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  applyMeta();
  initFyBanner();
});
