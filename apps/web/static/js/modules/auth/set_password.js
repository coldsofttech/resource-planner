"use strict";

import { applyMeta, getAppLogo } from "../main/meta.js";
import { apiFetch, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { API_URLS, UI_URLS } from "../main/urls.js";
import { showCookieBannerIfNeeded } from "../utils/cookie.js";

const FIELD_IDS = ["rp-set-password-new", "rp-set-password-confirm"];

function setBanner(id, message) {
  const banner = document.getElementById(id);
  if (!banner) return;
  banner.setAttribute("subtitle", message || "");
  if (message) banner.setAttribute("open", "");
  else banner.removeAttribute("open");
}

function setFormError(message) {
  setBanner("rp-set-password-error", message);
}

function setFormSuccess() {
  setBanner("rp-set-password-success", "");
  document.getElementById("rp-set-password-success")?.setAttribute("open", "");
}

function getTokenFromUrl() {
  return new URLSearchParams(window.location.search).get("token") || "";
}

function initSetPasswordForm() {
  const form = document.getElementById("rp-set-password-form");
  if (!form) return;

  const tokenInput = document.getElementById("rp-set-password-token");
  const token = getTokenFromUrl();
  if (tokenInput) tokenInput.value = token;

  const btn = document.getElementById("rp-set-password-btn");

  FIELD_IDS.forEach((id) => {
    document.getElementById(id)?.addEventListener("input", () => setFormError(""));
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    setFormError("");

    FIELD_IDS.forEach((id) =>
      document.getElementById(id)?.dispatchEvent(new CustomEvent("rp:validate")),
    );

    const hasError = FIELD_IDS.some(
      (id) => !!document.getElementById(id)?.querySelector(".rp-input.is-invalid"),
    );
    if (hasError) return;

    const new_password = document.getElementById("rp-set-password-new")?.value ?? "";
    const confirm_password = document.getElementById("rp-set-password-confirm")?.value ?? "";

    const snap = snapshotButton(btn);
    setBusyButton(btn, "Setting password…");

    try {
      const { href, method } = API_URLS.users.setPassword();
      const json = await apiFetch(href, {
        method,
        body: JSON.stringify({ token, new_password, confirm_password }),
        skipAuth401Redirect: true,
      });
      if (json?.success) {
        setFormSuccess();
        restoreButton(btn, snap, { label: "Password set", suffixIcon: "bi-check-circle-fill" });
        setTimeout(() => {
          window.location.href = UI_URLS.auth.login();
        }, 1800);
      } else {
        setFormError(json?.message ?? "Failed to set password. Please try again.");
        restoreButton(btn, snap);
      }
    } catch (err) {
      const msg = err?.data?.message ?? "Failed to set password. Please try again.";
      setFormError(msg);
      restoreButton(btn, snap);
    }
  });
}

function applyMetaToPage(meta) {
  if (!meta) return;
  const nameEl = document.getElementById("rp-app-name");
  if (nameEl) nameEl.innerHTML = meta.app_name ?? "";
  const logoEl = document.getElementById("rp-app-logo");
  if (logoEl) logoEl.textContent = getAppLogo(meta);
}

document.addEventListener("DOMContentLoaded", async () => {
  if (!document.getElementById("rp-set-password-form")) return;

  const meta = await applyMeta();
  applyMetaToPage(meta);
  initSetPasswordForm();
  showCookieBannerIfNeeded();
});
