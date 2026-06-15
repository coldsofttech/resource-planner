import { apiFetch } from "../utils/utils.js";
import { API_URLS } from "./urls.js";

const META_KEY = "rp-meta";

function htmlToText(html) {
  const doc = new DOMParser().parseFromString(html, "text/html");
  return (doc.body.textContent || "").replace(/\s+/g, " ").trim();
}

function toInitials(name) {
  const text = htmlToText(name).replace(/([a-z])([A-Z])/g, "$1 $2");

  return text
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join("");
}

/**
 * Fetch app meta from the API. Result is cached indefinitely in localStorage;
 * cleared on logout via clearMeta().
 */
export async function getMeta() {
  const cached = localStorage.getItem(META_KEY);
  if (cached) {
    try {
      const parsed = JSON.parse(cached);
      // Don't trust a cached snapshot that says setup is incomplete — always
      // re-fetch so the login page gets the latest setup_complete flag.
      if (parsed?.setup_complete !== false) return parsed;
    } catch {}
  }
  try {
    const { href } = API_URLS.meta.get();
    const json = await apiFetch(href);
    if (json?.success && json?.data) {
      // Only persist the cache once setup is complete; pre-setup data must
      // always be fetched fresh so the redirect logic stays correct.
      if (json.data.setup_complete !== false) {
        localStorage.setItem(META_KEY, JSON.stringify(json.data));
      }
      return json.data;
    }
  } catch {}
  return null;
}

/** Strip HTML tags and normalise whitespace to get a plain-text app name. */
export function getAppName(meta) {
  if (!meta?.app_name) return "Resource<b>Planner</b>";
  return htmlToText(meta.app_name);
}

/** Convert plain-text app name to two-letter initials (e.g. "Resource Planner" → "RP"). */
export function getAppLogo(meta) {
  return toInitials(getAppName(meta));
}

/** Remove the cached meta entry (call on logout). */
export function clearMeta() {
  localStorage.removeItem(META_KEY);
}

/**
 * Fetch meta and apply it to the current page:
 *   - Updates document.title suffix with the app name
 *   - Sets innerHTML of #bar-app-name (preserves HTML like <b>)
 *   - Sets textContent of every [data-app-logo] element to the initials
 *   - Shows/hides #create-account-link based on allow_registration
 */
export async function applyMeta() {
  const meta = await getMeta();
  if (!meta) return null;

  // Title: "Sign in" → "Sign in — Resource Planner"
  const appName = getAppName(meta);
  const titleBase = document.title.split(/\s*[—\-–]\s*/)[0].trim();
  if (titleBase && appName && !document.title.includes(appName)) {
    document.title = `${titleBase} — ${appName}`;
  }

  // Top-bar name (innerHTML preserves <b>, etc.) — shared across layouts
  const nameEl = document.getElementById("bar-app-name");
  if (nameEl) nameEl.innerHTML = meta.app_name;
  const rpNameEl = document.getElementById("rp-app-name");
  if (rpNameEl) rpNameEl.innerHTML = meta.app_name;

  // All logo badge elements
  const initials = getAppLogo(meta);
  document.querySelectorAll("[data-app-logo]").forEach((el) => {
    el.textContent = initials;
  });

  // Create-account link visibility
  const regLink = document.getElementById("create-account-link");
  if (regLink) regLink.style.display = meta.allow_registration ? "" : "none";

  return meta;
}
