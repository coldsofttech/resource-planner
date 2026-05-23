/* ThemeToggle: <rp-theme-toggle> */
class ThemeToggle extends HTMLElement {
  constructor() {
    super();
    this._theme = "light";
    // Stored as a bound reference so disconnectedCallback can remove the exact listener
    this._onThemeChanged = (e) => {
      if (e.detail.theme !== this._theme) {
        this._theme = e.detail.theme;
        this._updateIcon();
      }
    };
  }

  connectedCallback() {
    this._theme =
      localStorage.getItem("rp-theme") ||
      (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");

    document.documentElement.setAttribute("data-theme", this._theme);

    this.innerHTML = `
      <button class="rp-iconbtn" type="button" title="Toggle theme">
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

  _toggle() {
    this._theme = this._theme === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", this._theme);
    localStorage.setItem("rp-theme", this._theme);
    window.dispatchEvent(new CustomEvent("rp-theme-changed", { detail: { theme: this._theme } }));
    this._updateIcon();
  }

  _updateIcon() {
    const icon = this.querySelector("[data-theme-icon]");
    if (icon) icon.className = `bi ${this._theme === "dark" ? "bi-sun" : "bi-moon"}`;
  }
}

customElements.define("rp-theme-toggle", ThemeToggle);
