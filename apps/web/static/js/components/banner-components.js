const FLASH_TYPE_CONFIG = {
  info: { cssClass: "info", icon: "bi-info-circle-fill" },
  success: { cssClass: "success", icon: "bi-check-circle-fill" },
  warning: { cssClass: "warning", icon: "bi-exclamation-triangle-fill" },
  error: { cssClass: "danger", icon: "bi-x-circle-fill" },
};

/* FlashBanner: <rp-flash-banner> */
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

  _esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  _render() {
    const t = FLASH_TYPE_CONFIG[this._type] ?? FLASH_TYPE_CONFIG.info;
    const iconCls = this._icon || t.icon;

    this.classList.add("rp-flash");
    Object.values(FLASH_TYPE_CONFIG).forEach((c) => this.classList.remove(c.cssClass));
    this.classList.add(t.cssClass);
    this.style.display = this._isOpen ? "" : "none";

    const link = this._linkLabel
      ? `<a class="rp-link" href="${this._esc(this._linkHref)}" style="font-size:13px">${this._esc(this._linkLabel)}</a>`
      : "";

    this.innerHTML = `
      <span class="rp-flash-icon"><i class="bi ${this._esc(iconCls)}"></i></span>
      <div class="rp-flash-body">
        <strong>${this._esc(this._title)}</strong>
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

customElements.define("rp-flash-banner", FlashBanner);
