"use strict";

import { esc } from "../../utils.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { setTheme } from "../../../modules/utils/theme.js";
import { API_URLS, UI_URLS } from "../../../modules/main/urls.js";

/* UserProfile  <user-profile>
 *
 * Top-bar account dropdown. Renders an avatar trigger button and a dropdown
 * panel populated from GET /api/v1/auth/me/ on first open.
 *
 * Responsibilities:
 *   - Displays user avatar (or identicon fallback) in the trigger button and panel.
 *   - Displays user name and email in the panel header.
 *   - Syncs the server-stored theme to localStorage on first load (server wins).
 *   - Listens for `rp-theme-changed` and PATCHes /users/me/preferences/ to persist
 *     theme changes made via <theme-toggle> (logged-in pages only).
 *   - Handles Ctrl+, / ⌘+, shortcut to navigate to /profile/.
 *   - Handles sign-out via POST /auth/logout/.
 *
 * Pre-mounted in templates/base.html. Do not add additional instances.
 */

// ⌘ + thin space + comma — matches the search-field shortcut hint convention.
const SHORTCUT_LABEL = "⌘ ,";

class UserProfile extends HTMLElement {
  constructor() {
    super();
    this._data = null;
    this._open = false;
    this._syncingFromServer = false;

    this._onDocClick = (e) => {
      if (this._open && !this.contains(e.target)) this._closePanel();
    };
    this._onKeydown = (e) => {
      if (e.key === "," && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        window.location.href = "/profile/";
      }
      if (e.key === "Escape" && this._open) this._closePanel();
    };
    this._onThemeChanged = (e) => {
      if (this._syncingFromServer) return;
      this._persistTheme(e.detail.theme);
    };
  }

  connectedCallback() {
    this.style.position = "relative";
    this._render();
    document.addEventListener("keydown", this._onKeydown);
    window.addEventListener("rp-theme-changed", this._onThemeChanged);
    this._loadData();
  }

  disconnectedCallback() {
    document.removeEventListener("keydown", this._onKeydown);
    document.removeEventListener("click", this._onDocClick);
    window.removeEventListener("rp-theme-changed", this._onThemeChanged);
  }

  _render() {
    this.innerHTML = `
      <div class="rp-iconbtn-wrap">
        <button class="rp-profile-trigger" title="Account" data-trigger>
          <div class="rp-avatar" data-trigger-avatar>?</div>
          <i class="bi bi-chevron-down" style="font-size:10px;color:var(--rp-text-muted)"></i>
        </button>
      </div>
      <div class="rp-dd-panel dd-right rp-profile-panel" data-panel>
        <div class="rp-pop-head">
          <div class="rp-avatar rp-avatar--lg" data-panel-avatar>?</div>
          <div>
            <strong data-panel-name>&nbsp;</strong>
            <small data-panel-email class="mt-1">&nbsp;</small>
          </div>
        </div>
        <div class="rp-dd-label">Account</div>
        <a href="/profile/" data-profile-link>
          <i class="bi bi-person"></i>
          Profile
          <span class="rp-dd-shortcut">${esc(SHORTCUT_LABEL)}</span>
        </a>
        <a href="/notifications/preferences/">
          <i class="bi bi-bell"></i>
          Notification preferences
        </a>
        <hr />
        <button type="button" class="rp-dd-link rp-dd-danger" data-signout>
          <i class="bi bi-box-arrow-right"></i>
          Sign out
        </button>
      </div>
    `;

    this.querySelector("[data-trigger]").addEventListener("click", (e) => {
      e.stopPropagation();
      this._togglePanel();
    });

    this.querySelector("[data-signout]").addEventListener("click", () => this._signOut());
  }

  _togglePanel() {
    this._open ? this._closePanel() : this._openPanel();
  }

  _openPanel() {
    this._open = true;
    this.querySelector("[data-panel]").classList.add("rp-dd-open");
    document.addEventListener("click", this._onDocClick);
    if (!this._data) this._loadData();
  }

  _closePanel() {
    this._open = false;
    this.querySelector("[data-panel]")?.classList.remove("rp-dd-open");
    document.removeEventListener("click", this._onDocClick);
  }

  async _loadData() {
    try {
      const { href, method } = API_URLS.auth.me();
      const resp = await apiFetch(href, { method });
      this._data = resp?.data ?? null;
      if (this._data) {
        this._updateDisplay();
        this._syncTheme(this._data.theme);
      }
    } catch {
      // Panel remains open with placeholder values; non-critical failure.
    }
  }

  _updateDisplay() {
    const { first_name, last_name, email, avatar_url, is_sso, display_name } = this._data;
    const fullName = display_name || [first_name, last_name].filter(Boolean).join(" ") || email;

    this.querySelector("[data-panel-name]").textContent = fullName;
    this.querySelector("[data-panel-email]").textContent = email;

    this._applyAvatar(this.querySelector("[data-trigger-avatar]"), avatar_url, email, "sm");
    this._applyAvatar(this.querySelector("[data-panel-avatar]"), avatar_url, email, "lg");
  }

  _applyAvatar(el, avatarUrl, seed, size) {
    if (!el) return;

    if (avatarUrl) {
      // Show real avatar image; fall back to identicon on error.
      el.innerHTML = `<img src="${avatarUrl}" alt="Avatar" style="width:100%;height:100%;object-fit:cover;border-radius:inherit;" onerror="this.parentElement._fallback && this.parentElement._fallback()" />`;
      el._fallback = () => this._renderIdenticon(el, seed, size);
    } else {
      this._renderIdenticon(el, seed, size);
    }
  }

  _renderIdenticon(el, seed, size) {
    if (typeof window.rpIdenticon === "function") {
      const svg = window.rpIdenticon(seed, { style: "initials", name: seed });
      el.style.overflow = "hidden";
      el.innerHTML = svg;
    } else {
      el.textContent = this._initials(seed);
    }
  }

  _initials(seed) {
    const parts = String(seed || "")
      .trim()
      .split(/[\s@._-]+/)
      .filter(Boolean);
    if (!parts.length) return "?";
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }

  _syncTheme(theme) {
    if (!theme) return;
    const stored = localStorage.getItem("rp-theme");
    if (stored === theme) return;
    this._syncingFromServer = true;
    setTheme(theme);
    this._syncingFromServer = false;
  }

  refresh(avatarUrl) {
    if (!this._data) return;
    this._data.avatar_url = avatarUrl;
    this._updateDisplay();
  }

  async _persistTheme(theme) {
    try {
      const { href, method } = API_URLS.users.updatePreferences();
      await apiFetch(href, { method, body: JSON.stringify({ theme }) });
    } catch {
      // Local theme already applied — silent failure is acceptable.
    }
  }

  async _signOut() {
    const btn = this.querySelector("[data-signout]");
    if (btn) btn.disabled = true;
    try {
      const { href, method } = API_URLS.auth.logout();
      await apiFetch(href, { method, skipAuth401Redirect: true });
    } catch {
      // Proceed to redirect regardless of API response.
    }
    window.dispatchEvent(new CustomEvent("rp:signout"));
    window.location.href = UI_URLS.auth.login();
  }
}

customElements.define("user-profile", UserProfile);
