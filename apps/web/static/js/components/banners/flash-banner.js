/* FlashBanner  <flash-banner>
 *
 * Inline page-level alert banner for status messages, warnings, and errors.
 * Renders a coloured strip with icon, title, optional subtitle, optional link,
 * and a dismiss (×) button.
 *
 * Attributes:
 *   open          – boolean; show the banner (absent = hidden)
 *   type          – "info" (default) | "success" | "warning" | "error"
 *   icon          – Bootstrap Icons class override (e.g. "bi-bell"); falls back to type default
 *   title         – bold heading text
 *   subtitle      – secondary text below the title
 *   link-label    – CTA anchor text (requires link-href)
 *   link-href     – CTA anchor href (default "#")
 *
 * Events fired:
 *   rp:dismiss (bubbles) – when the user clicks the dismiss button; the banner
 *                          also removes its own `open` attribute after firing
 *
 * Example:
 *   <flash-banner type="warning" title="Heads up" subtitle="Your plan expires soon" open>
 *   </flash-banner>
 *
 * Notes:
 *   - The `open` attribute controls visibility; set/remove it via JS or HTML.
 *   - Use `flash-banner` for per-page inline alerts.
 *   - For system-wide top-strip banners use `fy-flash-banner` instead.
 */
import { esc } from "../utils.js";

const FLASH_TYPE_CONFIG = {
  info: { cssClass: "info", icon: "bi-info-circle-fill" },
  success: { cssClass: "success", icon: "bi-check-circle-fill" },
  warning: { cssClass: "warning", icon: "bi-exclamation-triangle-fill" },
  error: { cssClass: "danger", icon: "bi-x-circle-fill" },
};

class FlashBanner extends HTMLElement {
  static get observedAttributes() {
    return ["open", "type", "icon", "title", "subtitle", "link-label", "link-href"];
  }

  connectedCallback() {
    this.setAttribute("role", "alert");
    this._render();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this.isConnected && oldVal !== newVal) this._render();
  }

  get _isOpen() {
    return this.hasAttribute("open");
  }
  get _type() {
    return this.getAttribute("type") || "info";
  }
  get _icon() {
    return this.getAttribute("icon") || "";
  }
  get _title() {
    return this.getAttribute("title") || "";
  }
  get _subtitle() {
    return this.getAttribute("subtitle") || "";
  }
  get _linkLabel() {
    return this.getAttribute("link-label") || "";
  }
  get _linkHref() {
    return this.getAttribute("link-href") || "#";
  }

  _render() {
    const t = FLASH_TYPE_CONFIG[this._type] ?? FLASH_TYPE_CONFIG.info;
    const iconCls = this._icon || t.icon;

    this.classList.add("rp-flash");
    Object.values(FLASH_TYPE_CONFIG).forEach((c) => this.classList.remove(c.cssClass));
    this.classList.add(t.cssClass);
    this.style.display = this._isOpen ? "" : "none";

    const link = this._linkLabel
      ? `<a class="rp-link" href="${esc(this._linkHref)}" style="font-size:13px">${esc(this._linkLabel)}</a>`
      : "";

    this.innerHTML = `
      <span class="rp-flash-icon"><i class="bi ${esc(iconCls)}"></i></span>
      <div class="rp-flash-body">
        <strong>${esc(this._title)}</strong>
        ${this._subtitle ? `<div class="rp-flash-sub">${this._subtitle}</div>` : ""}
      </div>
      <div class="rp-flash-actions">
        ${link}
        <button class="rp-flash-close" aria-label="Dismiss" data-dismiss><i class="bi bi-x-lg"></i></button>
      </div>`;

    this.querySelector("[data-dismiss]").addEventListener("click", () => {
      this.dispatchEvent(new CustomEvent("rp:dismiss", { bubbles: true }));
      this.removeAttribute("open");
    });
  }
}

customElements.define("flash-banner", FlashBanner);
