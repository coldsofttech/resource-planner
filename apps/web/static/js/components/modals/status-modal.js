import { Modal } from "./modal.js";

const TYPE_CONFIG = {
  info: { cssClass: "info", icon: "bi-info-circle" },
  success: { cssClass: "success", icon: "bi-check-circle" },
  warning: { cssClass: "warning", icon: "bi-exclamation-triangle" },
  error: { cssClass: "danger", icon: "bi-x-circle" },
};

/* StatusModal  <status-modal>
 *
 * A centred icon + title + body modal used for status displays (progress, confirmation, result).
 * Extends Modal. Configure entirely via attributes; re-renders on any attribute change.
 * Use the `statusModal` singleton utility from `utils/modal.js` for programmatic control.
 *
 * Attributes:
 *   open              – boolean; modal is visible when present
 *   closeable         – set to "false" to remove the × close button
 *   icon-type         – "info" | "success" | "warning" | "error" (default "info")
 *   icon              – Bootstrap Icon class override (e.g. "bi-gear"); defaults to icon-type icon
 *   icon-bg-color     – custom background colour for the icon circle (CSS colour value)
 *   title             – heading text inside the modal
 *   body              – paragraph text below the title
 *   dismiss-label     – label for the muted dismiss button; omit to hide
 *   secondary-label   – label for the secondary action button; omit to hide
 *   secondary-icon    – Bootstrap Icon class for the secondary button prefix icon
 *   primary-label     – label for the primary action button; omit to hide
 *   primary-icon      – Bootstrap Icon class for the primary button prefix icon
 *   primary-href      – if set, clicking primary navigates to this URL instead of firing the event
 *   primary-disabled  – boolean; disables the primary button when present
 *
 * Public API:
 *   modal.show()                  – inherited from Modal; opens the modal
 *   modal.hide()                  – inherited from Modal; closes the modal
 *   modal.setAdditionalBody(html) – injects extra HTML into the additional-body slot in-place
 *                                   without a full re-render
 *
 * Events fired (all bubble):
 *   rp:dismiss    – dismiss button clicked (modal also hides)
 *   rp:secondary  – secondary button clicked
 *   rp:primary    – primary button clicked (navigation occurs if primary-href is set)
 */
class StatusModal extends Modal {
  static get observedAttributes() {
    return [
      ...super.observedAttributes,
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
    super.connectedCallback();
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

  get _modifierClass() {
    const t = TYPE_CONFIG[this._iconType] ?? TYPE_CONFIG.info;
    return `rp-status-modal ${t.cssClass}`;
  }

  setAdditionalBody(html) {
    this._additionalBody = html;
    const slot = this.querySelector("[data-additional]");
    if (slot) slot.innerHTML = html;
  }

  _renderContent() {
    const t = TYPE_CONFIG[this._iconType] ?? TYPE_CONFIG.info;
    const iconCls = this._icon || t.icon;
    const iconStyle = this._iconBgColor
      ? ` style="background:${this._esc(this._iconBgColor)}"`
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

    return `
      <div class="rp-status-hero">
        <div class="rp-status-icon"${iconStyle}><i class="bi ${this._esc(iconCls)}"></i></div>
        <h3>${this._esc(this._title)}</h3>
        ${this._body ? `<p>${this._esc(this._body)}</p>` : ""}
      </div>
      ${addHTML}
      ${foot}`;
  }

  _bindContent() {
    this.querySelector("[data-dismiss-modal]")?.addEventListener("click", () => {
      this.dispatchEvent(new CustomEvent("rp:dismiss", { bubbles: true }));
      this.hide();
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
}

customElements.define("status-modal", StatusModal);
