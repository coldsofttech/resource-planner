import { applyMeta, getAppLogo } from "../main/meta.js";
import { apiFetch, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { API_URLS, UI_URLS } from "../main/urls.js";
import { showCookieBannerIfNeeded } from "../utils/cookie.js";

const RESEND_COOLDOWN = 60;

let fpEmail = "";
let fpCode = "";
let resendTimer = null;

function showStep(n) {
  [1, 2, 3].forEach((i) => {
    const el = document.getElementById(`rp-fp-step${i}`);
    if (el) el.style.display = i === n ? "" : "none";
  });
}

function setStepBanner(id, message) {
  const banner = document.getElementById(id);
  if (!banner) return;
  banner.setAttribute("subtitle", message || "");
  if (message) banner.setAttribute("open", "");
  else banner.removeAttribute("open");
}

function setStepError(stepNum, message) {
  setStepBanner(`rp-fp-error-${stepNum}`, message);
}

function setStepSuccess(stepNum, message) {
  setStepBanner(`rp-fp-success-${stepNum}`, message);
}

function clearErrors() {
  [1, 2, 3].forEach((n) => setStepError(n, ""));
}

async function apiPost(urlEntry, body) {
  const { href, method } = urlEntry();
  return apiFetch(href, { method, body: JSON.stringify(body), skipAuth401Redirect: true });
}

function getOtpEl() {
  return document.getElementById("rp-fp-otp");
}

function getCode() {
  return getOtpEl()?.value ?? "";
}

function clearOtp() {
  const otp = getOtpEl();
  if (!otp) return;
  otp.value = "";
  otp.querySelector("[data-otp-digit]")?.focus();
}

function formatCountdown(s) {
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

function startResendCountdown() {
  const resendEl = document.getElementById("rp-fp-resend");
  if (!resendEl) return;

  let remaining = RESEND_COOLDOWN;
  resendEl.textContent = `Resend in ${formatCountdown(remaining)}`;
  resendEl.style.pointerEvents = "none";
  resendEl.style.opacity = "0.5";

  clearInterval(resendTimer);
  resendTimer = setInterval(() => {
    remaining -= 1;
    if (remaining <= 0) {
      clearInterval(resendTimer);
      resendEl.textContent = "Resend code";
      resendEl.style.pointerEvents = "";
      resendEl.style.opacity = "";
    } else {
      resendEl.textContent = `Resend in ${formatCountdown(remaining)}`;
    }
  }, 1000);
}

function initStep1() {
  const form = document.getElementById("rp-fp-form-1");
  if (!form) return;
  const btn = document.getElementById("rp-fp-send-btn");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearErrors();

    const emailEl = document.getElementById("rp-fp-email");
    emailEl?.dispatchEvent(new CustomEvent("rp:validate"));
    if (emailEl?.querySelector(".rp-input.is-invalid")) return;

    const email = emailEl?.value?.trim() ?? "";
    const snap = snapshotButton(btn);
    setBusyButton(btn, "Sending…");

    try {
      const json = await apiPost(API_URLS.auth.forgotPassword.request, { email });
      if (json?.success) {
        fpEmail = email;
        const sentToEl = document.getElementById("rp-fp-sent-to");
        if (sentToEl) sentToEl.textContent = email;
        showStep(2);
        startResendCountdown();
        clearOtp();
      } else {
        setStepError(1, json?.message ?? "Something went wrong. Please try again.");
        restoreButton(btn, snap);
      }
    } catch (err) {
      setStepError(1, err?.data?.message ?? "A network error occurred. Please try again.");
      restoreButton(btn, snap);
    }
  });
}

function initStep2() {
  const form = document.getElementById("rp-fp-form-2");
  if (!form) return;
  const btn = document.getElementById("rp-fp-verify-btn");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearErrors();

    const otpEl = getOtpEl();
    otpEl?.dispatchEvent(new CustomEvent("rp:validate"));
    if (otpEl?.querySelector(".rp-otp-digit.is-invalid")) return;

    const code = getCode();
    const snap = snapshotButton(btn);
    setBusyButton(btn, "Verifying…");

    try {
      const json = await apiPost(API_URLS.auth.forgotPassword.verify, {
        email: fpEmail,
        code,
      });
      if (json?.success) {
        fpCode = code;
        showStep(3);
      } else {
        setStepError(2, json?.message ?? "Invalid code. Please try again.");
        restoreButton(btn, snap);
      }
    } catch (err) {
      setStepError(2, err?.data?.message ?? "A network error occurred. Please try again.");
      restoreButton(btn, snap);
    }
  });

  const resendEl = document.getElementById("rp-fp-resend");
  resendEl?.addEventListener("click", async (e) => {
    e.preventDefault();
    if (resendEl.style.pointerEvents === "none") return;
    try {
      await apiPost(API_URLS.auth.forgotPassword.request, { email: fpEmail });
      clearOtp();
      startResendCountdown();
    } catch {
      // silently ignore resend errors
    }
  });
}

function initStep3() {
  const form = document.getElementById("rp-fp-form-3");
  if (!form) return;
  const btn = document.getElementById("rp-fp-reset-btn");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearErrors();

    const newPassEl = document.getElementById("rp-fp-new-password");
    const confirmPassEl = document.getElementById("rp-fp-confirm-password");
    newPassEl?.dispatchEvent(new CustomEvent("rp:validate"));
    confirmPassEl?.dispatchEvent(new CustomEvent("rp:validate"));
    if (
      newPassEl?.querySelector(".rp-input.is-invalid") ||
      confirmPassEl?.querySelector(".rp-input.is-invalid")
    )
      return;

    const new_password = newPassEl?.value ?? "";
    const confirm_password = confirmPassEl?.value ?? "";

    const snap = snapshotButton(btn);
    setBusyButton(btn, "Setting password…");

    try {
      const json = await apiPost(API_URLS.auth.forgotPassword.reset, {
        email: fpEmail,
        code: fpCode,
        new_password,
        confirm_password,
      });
      if (json?.success) {
        setStepError(3, "");
        setStepSuccess(3, json.message ?? "Password updated! Taking you to sign in…");
        restoreButton(btn, snap, { label: "Password updated", suffixIcon: "bi-check-circle-fill" });
        setTimeout(() => {
          window.location.href = UI_URLS.auth.login() + "?password_reset=1";
        }, 1800);
      } else {
        setStepError(3, json?.message ?? "Failed to reset password. Please try again.");
        restoreButton(btn, snap);
      }
    } catch (err) {
      setStepError(3, err?.data?.message ?? "A network error occurred. Please try again.");
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
  if (!document.getElementById("rp-fp-step1")) return;

  const yearEl = document.getElementById("rp-auth-year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  // Apply centralised UI_URLS to page links.
  document.getElementById("rp-fp-back-link")?.setAttribute("href", UI_URLS.auth.login());

  const meta = await applyMeta();
  applyMetaToPage(meta);

  initStep1();
  initStep2();
  initStep3();
  showCookieBannerIfNeeded();
});
