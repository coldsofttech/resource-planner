"use strict";

import { applyMeta, getAppLogo } from "../main/meta.js";
import { apiFetch, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { API_URLS, UI_URLS } from "../main/urls.js";

const FIELD_IDS = ["rp-force-change-password-new", "rp-force-change-password-confirm"];

function setBanner(id, message) {
  const banner = document.getElementById(id);
  if (!banner) return;
  banner.setAttribute("subtitle", message || "");
  if (message) banner.setAttribute("open", "");
  else banner.removeAttribute("open");
}

function setFormError(message) {
  setBanner("rp-force-change-password-error", message);
}

function setFormSuccess() {
  document.getElementById("rp-force-change-password-success")?.setAttribute("open", "");
}

function initSignOutLink() {
  const link = document.getElementById("rp-force-change-password-sign-out-link");
  if (!link) return;
  link.addEventListener("click", async (e) => {
    e.preventDefault();
    try {
      const { href, method } = API_URLS.auth.logout();
      await apiFetch(href, { method, skipAuth401Redirect: true });
    } catch {
      // Proceed to redirect regardless of API response.
    }
    window.location.href = UI_URLS.auth.login();
  });
}

function initForm() {
  const form = document.getElementById("rp-force-change-password-form");
  if (!form) return;

  const btn = document.getElementById("rp-force-change-password-btn");

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

    const new_password = document.getElementById("rp-force-change-password-new")?.value ?? "";
    const confirm_password =
      document.getElementById("rp-force-change-password-confirm")?.value ?? "";

    const snap = snapshotButton(btn);
    setBusyButton(btn, "Updating…");

    try {
      const { href, method } = API_URLS.auth.forceChangePassword();
      await apiFetch(href, {
        method,
        body: JSON.stringify({ new_password, confirm_password }),
      });
      setFormSuccess();
      restoreButton(btn, snap, { label: "Password updated", suffixIcon: "bi-check-circle-fill" });
      setTimeout(() => {
        window.location.href = "/dashboard/";
      }, 1200);
    } catch (err) {
      const msg = err?.data?.error?.message ?? "Failed to update password. Please try again.";
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
  if (!document.getElementById("rp-force-change-password-form")) return;

  const meta = await applyMeta();
  applyMetaToPage(meta);
  initForm();
  initSignOutLink();
});
