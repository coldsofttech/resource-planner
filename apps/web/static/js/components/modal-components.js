const TYPE_CONFIG = {
  info: { cssClass: "info", icon: "bi-info-circle" },
  success: { cssClass: "success", icon: "bi-check-circle" },
  warning: { cssClass: "warning", icon: "bi-exclamation-triangle" },
  error: { cssClass: "danger", icon: "bi-x-circle" },
};

/* StatusModal: <rp-modal-status> */
class StatusModal extends HTMLElement {
  static get observedAttributes() {
    return [
      "open",
      "closeable",
      "icon-type",
      "icon",
      "icon-bg-color",
      "title",
      "body",
      "dismiss-label",
      "secondary-label",
      "secondary-icon",
      "primary-label",
      "primary-icon",
      "primary-href",
      "primary-disabled",
    ];
  }

  connectedCallback() {
    this._additionalBody = null;
    this._render();
    this._bindGlobal();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this.isConnected && oldVal !== newVal) this._render();
  }

  get _isOpen() {
    return this.hasAttribute("open");
  }
  get _closeable() {
    return !this.hasAttribute("closeable") || this.getAttribute("closeable") !== "false";
  }
  get _iconType() {
    return this.getAttribute("icon-type") || "info";
  }
  get _icon() {
    return this.getAttribute("icon") || "";
  }
  get _iconBgColor() {
    return this.getAttribute("icon-bg-color") || "";
  }
  get _title() {
    return this.getAttribute("title") || "";
  }
  get _body() {
    return this.getAttribute("body") || "";
  }
  get _dismissLabel() {
    return this.getAttribute("dismiss-label") || "";
  }
  get _secLabel() {
    return this.getAttribute("secondary-label") || "";
  }
  get _secIcon() {
    return this.getAttribute("secondary-icon") || "";
  }
  get _primLabel() {
    return this.getAttribute("primary-label") || "";
  }
  get _primIcon() {
    return this.getAttribute("primary-icon") || "";
  }
  get _primHref() {
    return this.getAttribute("primary-href") || "";
  }
  get _primDisabled() {
    return this.hasAttribute("primary-disabled");
  }

  setAdditionalBody(html) {
    this._additionalBody = html;
    const slot = this.querySelector("[data-additional]");
    if (slot) slot.innerHTML = html;
  }

  _esc(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  _render() {
    const t = TYPE_CONFIG[this._iconType] ?? TYPE_CONFIG.info;
    const iconCls = this._icon || t.icon;
    const iconStyle = this._iconBgColor
      ? ` style="background:${this._esc(this._iconBgColor)}"`
      : "";

    const closeBtn = this._closeable
      ? `<button class="rp-iconbtn" data-close-modal style="position:absolute;top:10px;right:10px;z-index:1"><i class="bi bi-x-lg"></i></button>`
      : "";

    const dismissBtn = this._dismissLabel
      ? `<button class="rp-btn rp-btn-muted" data-dismiss-modal>${this._esc(this._dismissLabel)}</button>`
      : "";

    const secBtn = this._secLabel
      ? `<button class="rp-btn rp-btn-secondary" data-secondary-modal>
          ${this._secIcon ? `<i class="bi ${this._esc(this._secIcon)}"></i>` : ""}
          ${this._esc(this._secLabel)}
        </button>`
      : "";

    const primBtn = this._primLabel
      ? `<button class="rp-btn rp-btn-primary" data-primary-modal${this._primDisabled ? " disabled" : ""}>
          ${this._primIcon ? `<i class="bi ${this._esc(this._primIcon)}"></i>` : ""}
          ${this._esc(this._primLabel)}
        </button>`
      : "";

    const foot =
      dismissBtn || secBtn || primBtn
        ? `<div class="rp-modal-foot">${dismissBtn}${secBtn}${primBtn}</div>`
        : "";

    const addHTML = this._additionalBody
      ? `<div class="rp-status-additional" data-additional>${this._additionalBody}</div>`
      : `<div class="rp-status-additional" data-additional style="display:none"></div>`;

    this.className = `rp-modal-back rp-status-modal ${t.cssClass}`;
    this.style.display = this._isOpen ? "grid" : "none";

    this.innerHTML = `
      <div class="rp-modal" style="position:relative">
        ${closeBtn}
        <div class="rp-status-hero">
          <div class="rp-status-icon"${iconStyle}><i class="bi ${this._esc(iconCls)}"></i></div>
          <h3>${this._esc(this._title)}</h3>
          ${this._body ? `<p>${this._esc(this._body)}</p>` : ""}
        </div>
        ${addHTML}
        ${foot}
      </div>`;

    this.querySelector("[data-close-modal]")?.addEventListener("click", () =>
      this.removeAttribute("open"),
    );

    this.querySelector("[data-dismiss-modal]")?.addEventListener("click", () => {
      this.dispatchEvent(new CustomEvent("rp:dismiss", { bubbles: true }));
      this.removeAttribute("open");
    });

    this.querySelector("[data-secondary-modal]")?.addEventListener("click", () => {
      this.dispatchEvent(new CustomEvent("rp:secondary", { bubbles: true }));
    });

    const primEl = this.querySelector("[data-primary-modal]");
    if (primEl) {
      primEl.addEventListener("click", () => {
        this.dispatchEvent(new CustomEvent("rp:primary", { bubbles: true }));
        if (this._primHref && !this._primDisabled) window.location.href = this._primHref;
      });
    }
  }

  _bindGlobal() {
    this.addEventListener("click", (e) => {
      if (e.target === this && this._closeable) this.removeAttribute("open");
    });
  }
}

customElements.define("rp-modal-status", StatusModal);
