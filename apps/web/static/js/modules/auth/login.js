import { applyMeta, clearMeta, getAppName, getAppLogo } from "../main/meta.js";
import { getCsrfToken, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { API_URLS, UI_URLS } from "../main/urls.js";
import { showCookieBannerIfNeeded } from "../utils/cookie.js";

function setFormError(message) {
  const banner = document.getElementById("rp-login-error");
  if (!banner) return;
  banner.setAttribute("subtitle", message || "");
  if (message) banner.setAttribute("open", "");
  else banner.removeAttribute("open");
}

/** Trigger the web component's own built-in validation (marks is-invalid). */
function triggerValidation(componentId) {
  document.getElementById(componentId)?.dispatchEvent(new CustomEvent("rp:validate"));
}

/** Returns true if the component's inner input carries the is-invalid class. */
function hasComponentError(componentId) {
  return !!document.getElementById(componentId)?.querySelector(".rp-input.is-invalid");
}

function initLoginForm() {
  const form = document.getElementById("rp-login-form");
  if (!form) return;

  const emailEl = document.getElementById("rp-login-email");
  const passEl = document.getElementById("rp-login-password");
  const submitEl = document.getElementById("rp-login-submit");

  // Clear the flash banner whenever the user edits either field.
  // The input event on the inner <input> bubbles up through the custom element.
  [emailEl, passEl].forEach((el) => {
    el?.addEventListener("input", () => setFormError(""));
  });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    setFormError("");

    // Delegate client-side validation to the web components.
    triggerValidation("rp-login-email");
    triggerValidation("rp-login-password");
    if (hasComponentError("rp-login-email") || hasComponentError("rp-login-password")) return;

    const email = emailEl?.value?.trim() ?? "";
    const password = passEl?.value ?? "";

    const snap = snapshotButton(submitEl);
    setBusyButton(submitEl, "Signing in…");

    try {
      const { href, method } = API_URLS.auth.login();
      const res = await fetch(href, {
        method,
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({ email, password }),
      });
      const json = await res.json();
      if (json?.success) {
        window.location.href = json.data?.redirect ?? "/";
      } else {
        setFormError(json?.message ?? "Sign in failed. Please try again.");
        restoreButton(submitEl, snap);
      }
    } catch {
      setFormError("A network error occurred. Please try again.");
      restoreButton(submitEl, snap);
    }
  });
}

function applyMetaToPage(meta) {
  if (!meta) return;

  const initials = getAppLogo(meta);

  // App name (preserves HTML tags like <b>)
  const nameEl = document.getElementById("rp-app-name");
  if (nameEl) nameEl.innerHTML = meta.app_name ?? "";

  // Logo initials — main bar
  const logoEl = document.getElementById("rp-app-logo");
  if (logoEl) logoEl.textContent = initials;

  // Logo initials — onboarding side panel
  const onboardLogoEl = document.getElementById("rp-app-logo-onboarding");
  if (onboardLogoEl) onboardLogoEl.textContent = initials;

  // Create-account link visibility
  const regLink = document.getElementById("rp-create-account-link");
  if (regLink) regLink.style.display = meta.allow_registration ? "" : "none";

  // Footer app name
  const footNameEl = document.getElementById("rp-auth-foot-name");
  if (footNameEl) footNameEl.textContent = getAppName(meta);
}

document.addEventListener("DOMContentLoaded", async () => {
  // Footer year — set immediately, independent of meta fetch
  const yearEl = document.getElementById("rp-auth-year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  clearMeta();
  const meta = await applyMeta();

  // Redirect to setup wizard if initial setup has not been completed.
  if (meta?.setup_complete === false) {
    window.location.href = UI_URLS.setup.wizard();
    return;
  }

  applyMetaToPage(meta);

  // Apply centralised UI_URLS to auth page links.
  document
    .getElementById("rp-login-forgot-link")
    ?.setAttribute("href", UI_URLS.auth.forgotPassword());
  document.getElementById("rp-create-account-link")?.setAttribute("href", UI_URLS.auth.register());

  initLoginForm();
  showCookieBannerIfNeeded();
});
