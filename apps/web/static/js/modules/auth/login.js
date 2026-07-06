import { applyMeta, clearMeta, getAppName, getAppLogo } from "../main/meta.js";
import { apiFetch, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { API_URLS, UI_URLS } from "../main/urls.js";
import { showCookieBannerIfNeeded } from "../utils/cookie.js";

function setBanner(id, message) {
  const banner = document.getElementById(id);
  if (!banner) return;
  banner.setAttribute("subtitle", message || "");
  if (message) banner.setAttribute("open", "");
  else banner.removeAttribute("open");
}

function setFormError(message) {
  setBanner("rp-login-error", message);
}

function setFormSuccess(message) {
  setBanner("rp-login-success", message);
}

function applySuccessParam() {
  const params = new URLSearchParams(window.location.search);
  if (params.get("registered") === "1") {
    setFormSuccess("Account created! Please sign in to continue.");
  } else if (params.get("password_reset") === "1") {
    setFormSuccess("Password updated! Please sign in with your new password.");
  }
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
      const json = await apiFetch(href, {
        method,
        body: JSON.stringify({ email, password }),
        skipAuth401Redirect: true,
      });
      if (json?.success) {
        const params = new URLSearchParams(window.location.search);
        const next = params.get("next");
        const safeNext = next && next.startsWith("/") && !next.startsWith("//") ? next : null;
        window.location.href = safeNext ?? json.data?.redirect ?? "/";
      } else {
        setFormError(json?.message ?? "Sign in failed. Please try again.");
        restoreButton(submitEl, snap);
      }
    } catch (err) {
      setFormError(err?.data?.message ?? "Sign in failed. Please try again.");
      restoreButton(submitEl, snap);
    }
  });
}

function applyMetaToPage(meta) {
  if (!meta) return;

  const initials = getAppLogo(meta);

  const nameEl = document.getElementById("rp-app-name");
  if (nameEl) nameEl.innerHTML = meta.app_name ?? "";

  const logoEl = document.getElementById("rp-app-logo");
  if (logoEl) logoEl.textContent = initials;

  const onboardLogoEl = document.getElementById("rp-app-logo-onboarding");
  if (onboardLogoEl) onboardLogoEl.textContent = initials;

  const footNameEl = document.getElementById("rp-auth-foot-name");
  if (footNameEl) footNameEl.textContent = getAppName(meta);

  const isClassic = meta.auth_mode === "classic";

  // Create account link: only for classic + allow_registration
  const regLink = document.getElementById("rp-create-account-link");
  if (isClassic && meta.allow_registration) {
    regLink?.removeAttribute("hidden");
  }

  // SSO button: shown for oauth (with active provider) or saml (with active provider)
  const ssoProvider =
    meta.auth_mode === "oauth"
      ? meta.oauth_provider
      : meta.auth_mode === "saml"
        ? meta.saml_provider
        : null;

  if (ssoProvider) {
    const { name, icon, code } = ssoProvider;
    const ssoSection = document.getElementById("rp-sso-section");
    const ssoBtn = document.getElementById("rp-sso-btn");

    if (ssoBtn) {
      ssoBtn.setAttribute("prefix-icon", `bi-${icon || "box-arrow-in-right"}`);
      ssoBtn.setAttribute("label", `Continue with ${name}`);
    }
    ssoSection?.removeAttribute("hidden");

    initSSOButton({ mode: meta.auth_mode, providerCode: code });
  }
}

function initSSOButton({ mode, providerCode }) {
  const btn = document.getElementById("rp-sso-btn");
  if (!btn) return;

  btn.addEventListener("click", async () => {
    const snap = snapshotButton(btn);
    setBusyButton(btn, "Redirecting…");

    try {
      let authUrl;

      if (mode === "oauth") {
        const redirectUri = `${window.location.origin}${UI_URLS.auth.login()}`;
        const { href, method } = API_URLS.auth.oauth.authorize(providerCode);
        const json = await apiFetch(`${href}?redirect_uri=${encodeURIComponent(redirectUri)}`, {
          method,
        });
        authUrl = json?.data?.authorization_url;
      } else if (mode === "saml") {
        const { href, method } = API_URLS.auth.saml.authorize(providerCode);
        const params = new URLSearchParams({ relay_state: "/dashboard/" });
        const json = await apiFetch(`${href}?${params}`, { method });
        authUrl = json?.data?.redirect_url;
      }

      if (authUrl) {
        window.location.href = authUrl;
      } else {
        restoreButton(btn, snap);
        setFormError("Failed to get authorization URL.");
      }
    } catch (err) {
      restoreButton(btn, snap);
      setFormError(err?.data?.message ?? "Could not initiate login.");
    }
  });
}

async function handleOAuthCallback(meta) {
  if (meta?.auth_mode !== "oauth") return false;

  const params = new URLSearchParams(window.location.search);
  const code = params.get("code");
  const state = params.get("state");
  if (!code || !state) return false;

  // Remove OAuth params from the URL immediately to prevent reuse on refresh.
  history.replaceState(null, "", window.location.pathname);

  try {
    const { href, method } = API_URLS.auth.oauth.callback();
    const json = await apiFetch(href, {
      method,
      body: JSON.stringify({ code, state }),
      skipAuth401Redirect: true,
    });
    if (json?.success) {
      window.location.href = json.data?.redirect ?? "/";
      return true;
    }
    setFormError(json?.message ?? "OAuth sign in failed.");
  } catch (err) {
    setFormError(err?.data?.message ?? "OAuth sign in failed. Please try again.");
  }
  return false;
}

document.addEventListener("DOMContentLoaded", async () => {
  // Footer year — set immediately, independent of meta fetch
  const yearEl = document.getElementById("rp-auth-year");
  if (yearEl) yearEl.textContent = new Date().getFullYear();

  applySuccessParam();

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

  // Handle OAuth callback redirect (?code=&state= injected by IdP into this page).
  const handledCallback = await handleOAuthCallback(meta);
  if (handledCallback) return;

  initLoginForm();
  showCookieBannerIfNeeded();
  initOnboardingStats();
});

function initOnboardingStats() {
  const statEls = document.querySelectorAll("[data-stat]");
  if (!statEls.length) return;

  const { href, method } = API_URLS.onboarding.stats();
  apiFetch(href, { method })
    .then((json) => {
      const data = json?.data ?? json ?? {};
      statEls.forEach((el) => {
        const key = el.getAttribute("data-stat");
        if (key && data[key] !== undefined) {
          el.textContent = data[key];
        }
      });
    })
    .catch(() => {});
}
