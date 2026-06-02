import { applyMeta, getAppLogo } from "../main/meta.js";
import { apiFetch, snapshotButton, setBusyButton, restoreButton } from "../utils/utils.js";
import { API_URLS, UI_URLS } from "../main/urls.js";
import { showCookieBannerIfNeeded } from "../utils/cookie.js";

const FIELD_IDS = [
  "rp-register-first-name",
  "rp-register-last-name",
  "rp-register-email",
  "rp-register-password",
  "rp-register-confirm-password",
];

function setBanner(id, message) {
  const banner = document.getElementById(id);
  if (!banner) return;
  banner.setAttribute("subtitle", message || "");
  if (message) banner.setAttribute("open", "");
  else banner.removeAttribute("open");
}

function setFormError(message) {
  setBanner("rp-register-error", message);
}

function setFormSuccess(message) {
  setBanner("rp-register-success", message);
}

function initRegisterForm() {
  const form = document.getElementById("rp-register-form");
  if (!form) return;
  const btn = document.getElementById("rp-register-btn");

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

    const first_name = document.getElementById("rp-register-first-name")?.value?.trim() ?? "";
    const last_name = document.getElementById("rp-register-last-name")?.value?.trim() ?? "";
    const email = document.getElementById("rp-register-email")?.value?.trim() ?? "";
    const password = document.getElementById("rp-register-password")?.value ?? "";
    const confirm_password = document.getElementById("rp-register-confirm-password")?.value ?? "";

    const snap = snapshotButton(btn);
    setBusyButton(btn, "Creating account…");

    try {
      const { href, method } = API_URLS.auth.register();
      const json = await apiFetch(href, {
        method,
        body: JSON.stringify({ first_name, last_name, email, password, confirm_password }),
        skipAuth401Redirect: true,
      });
      if (json?.success) {
        setFormError("");
        setFormSuccess(json.message ?? "Account created! Taking you to sign in…");
        restoreButton(btn, snap, { label: "Account created", suffixIcon: "bi-check-circle-fill" });
        setTimeout(() => {
          window.location.href = UI_URLS.auth.login() + "?registered=1";
        }, 1800);
      } else {
        setFormError(json?.message ?? "Registration failed. Please try again.");
        restoreButton(btn, snap);
      }
    } catch (err) {
      const msg = err?.data?.message ?? "Registration failed. Please try again.";
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
  if (!document.getElementById("rp-register-form")) return;

  document.getElementById("rp-register-sign-in-link")?.setAttribute("href", UI_URLS.auth.login());

  const meta = await applyMeta();

  if (meta?.setup_complete === false) {
    window.location.href = UI_URLS.setup.wizard();
    return;
  }

  if (!meta?.allow_registration) {
    window.location.href = UI_URLS.auth.login();
    return;
  }

  applyMetaToPage(meta);
  initRegisterForm();
  showCookieBannerIfNeeded();
});
