import { getTheme, setTheme } from "../../modules/utils/theme.js";

/* ThemeToggle  <theme-toggle>
 *
 * Icon button that cycles through light → dark → system themes. The current
 * theme is persisted via `setTheme()` (localStorage) and applied to
 * `document.documentElement[data-theme]`. Multiple instances stay in sync via
 * the `rp-theme-changed` window event.
 *
 * "system" follows the OS preference (prefers-color-scheme) and reacts to OS
 * changes dynamically without a page reload.
 *
 * No public attributes. No public API. Place anywhere in the page layout.
 * A single instance is pre-mounted in `templates/base.html` — do not add
 * additional instances.
 *
 * Window events listened (internal sync):
 *   rp-theme-changed  – fired by `setTheme()` when any instance changes the
 *                       theme; all instances update their icon in response.
 */

const ICONS = { light: "bi-sun", dark: "bi-moon", system: "bi-circle-half" };
const NEXT = { light: "dark", dark: "system", system: "light" };
const TITLES = {
  light: "Switch to dark mode",
  dark: "Switch to system theme",
  system: "Switch to light mode",
};

class ThemeToggle extends HTMLElement {
  constructor() {
    super();
    this._theme = "light";
    this._onThemeChanged = (e) => {
      if (e.detail.theme !== this._theme) {
        this._theme = e.detail.theme;
        this._updateIcon();
      }
    };
  }

  connectedCallback() {
    this._theme = getTheme();
    document.documentElement.setAttribute("data-theme", this._resolveEffective());

    this.innerHTML = `
      <button class="rp-iconbtn" type="button" title="${TITLES[this._theme] ?? "Toggle theme"}">
        <i class="bi" data-theme-icon></i>
      </button>
    `;

    this._updateIcon();
    this.querySelector("button").addEventListener("click", () => this._toggle());
    window.addEventListener("rp-theme-changed", this._onThemeChanged);
  }

  disconnectedCallback() {
    window.removeEventListener("rp-theme-changed", this._onThemeChanged);
  }

  _resolveEffective() {
    if (this._theme === "system") {
      return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    }
    return this._theme;
  }

  _toggle() {
    this._theme = NEXT[this._theme] ?? "light";
    setTheme(this._theme);
    this._updateIcon();
  }

  _updateIcon() {
    const icon = this.querySelector("[data-theme-icon]");
    const btn = this.querySelector("button");
    if (icon) icon.className = `bi ${ICONS[this._theme] ?? "bi-moon"}`;
    if (btn) btn.title = TITLES[this._theme] ?? "Toggle theme";
  }
}

customElements.define("theme-toggle", ThemeToggle);
