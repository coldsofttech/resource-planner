import { esc } from "../../utils.js";

/* FYFlashBanner  <fy-flash-banner>
 *
 * System-wide top-strip banner for fiscal-year or platform-wide announcements
 * (e.g. "FY expires in 14 days"). Rendered above the main layout.
 * Supports rich HTML content via a `<banner-message>` declarative child.
 *
 * Attributes:
 *   open          – boolean; show the banner (absent = hidden)
 *   type          – "warning" (default) | "info" | "danger" | "success"
 *   icon          – Bootstrap Icons class override (e.g. "bi-bell")
 *   link-label    – CTA anchor text (requires link-href)
 *   link-href     – CTA anchor href (default "#")
 *   dismissable   – boolean; show the dismiss (×) button
 *
 * Declarative child:
 *   <banner-message>Rich HTML content here</banner-message>
 *   Content is captured once on first connect; subsequent re-connections
 *   reuse the same HTML so it survives wizard step navigation.
 *
 * Events fired:
 *   rp:dismiss (bubbles) – when the user clicks the dismiss button; the banner
 *                          also removes its own `open` attribute after firing
 *
 * Example:
 *   <fy-flash-banner type="warning" link-label="Fix it" link-href="/fy" dismissable open>
 *     <banner-message>FY25-26 expires in <strong>14 days</strong>.</banner-message>
 *   </fy-flash-banner>
 *
 * Notes:
 *   - Use `flash-banner` for inline per-page alerts.
 *   - Only one `fy-flash-banner` should be present per page (already mounted in base.html).
 */
const FY_BANNER_CONFIG = {
  warning: {
    bg: "var(--rp-warning-soft)",
    color: "var(--rp-warning-soft-text)",
    border: "oklch(0.85 0.1 75 / 0.5)",
    icon: "bi-exclamation-triangle-fill",
  },
  info: {
    bg: "var(--rp-info-soft)",
    color: "var(--rp-info-soft-text)",
    border: "oklch(0.75 0.1 230 / 0.6)",
    icon: "bi-info-circle-fill",
  },
  danger: {
    bg: "var(--rp-danger-soft)",
    color: "var(--rp-danger-soft-text)",
    border: "oklch(0.75 0.13 25 / 0.6)",
    icon: "bi-x-circle-fill",
  },
  success: {
    bg: "var(--rp-success-soft)",
    color: "var(--rp-success-soft-text)",
    border: "oklch(0.75 0.12 150 / 0.6)",
    icon: "bi-check-circle-fill",
  },
};

class FYFlashBanner extends HTMLElement {
  static get observedAttributes() {
    return ["open", "type", "icon", "link-label", "link-href", "dismissable"];
  }

  connectedCallback() {
    this._connected = true;
    this.classList.add("rp-banner");
    if (this._msgContent === undefined) {
      const msgEl = this.querySelector("banner-message");
      this._msgContent = msgEl ? msgEl.innerHTML.trim() : "";
    }
    this._render();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this._connected && oldVal !== newVal) this._render();
  }

  get _isOpen() {
    return this.hasAttribute("open");
  }
  get _type() {
    return this.getAttribute("type") || "warning";
  }
  get _icon() {
    return this.getAttribute("icon") || "";
  }
  get _linkLabel() {
    return this.getAttribute("link-label") || "";
  }
  get _linkHref() {
    return this.getAttribute("link-href") || "#";
  }
  get _dismissable() {
    return this.hasAttribute("dismissable");
  }

  _render() {
    const t = FY_BANNER_CONFIG[this._type] ?? FY_BANNER_CONFIG.warning;
    const iconCls = this._icon || t.icon;

    this.style.background = t.bg;
    this.style.color = t.color;
    this.style.borderBottomColor = t.border;
    this.style.display = this._isOpen ? "" : "none";

    if (!this._isOpen) {
      this.innerHTML = "";
      return;
    }

    const ctaHTML =
      this._linkLabel || this._dismissable
        ? `<div class="rp-banner-cta">
            ${this._linkLabel ? `<a class="rp-link" href="${esc(this._linkHref)}">${esc(this._linkLabel)}</a>` : ""}
            ${this._dismissable ? `<button class="rp-iconbtn" title="Dismiss" data-dismiss><i class="bi bi-x-lg"></i></button>` : ""}
          </div>`
        : "";

    this.innerHTML = `
      <i class="bi ${esc(iconCls)}"></i>
      <span>${this._msgContent || ""}</span>
      ${ctaHTML}
    `;

    this.querySelector("[data-dismiss]")?.addEventListener("click", () => {
      this.removeAttribute("open");
      this.dispatchEvent(new CustomEvent("rp:dismiss", { bubbles: true }));
    });
  }
}

customElements.define("fy-flash-banner", FYFlashBanner);
