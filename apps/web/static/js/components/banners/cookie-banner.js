/* CookieBanner  <cookie-banner>
 *
 * Cookie-consent banner strip. Provides accept, reject, and optional "more info"
 * actions. Hides itself when the `open` attribute is removed.
 *
 * Attributes:
 *   open             – boolean; show the banner
 *   icon             – Bootstrap Icons class (default "bi-cookie")
 *   title            – heading text (default "Cookies")
 *   body             – body/description text
 *   accept-label     – accept button label (default "Accept all")
 *   reject-label     – reject button label (default "Reject")
 *   more-info-label  – optional third-button label; omit to hide the button
 *   more-info-href   – URL opened in a new tab when more-info button is clicked
 *
 * Events fired:
 *   rp:accept    (bubbles) – when the user clicks the accept button
 *   rp:reject    (bubbles) – when the user clicks the reject button
 *   rp:more-info (bubbles) – when the user clicks the more-info button
 *   All three also remove the `open` attribute (hiding the banner).
 *
 * Example:
 *   <cookie-banner open
 *     title="We use cookies"
 *     body="We use cookies to improve your experience."
 *     more-info-label="Learn more"
 *     more-info-href="/privacy">
 *   </cookie-banner>
 */
import { esc } from "../utils.js";

class CookieBanner extends HTMLElement {
  static get observedAttributes() {
    return [
      "open",
      "icon",
      "title",
      "body",
      "accept-label",
      "reject-label",
      "more-info-label",
      "more-info-href",
    ];
  }

  connectedCallback() {
    this._render();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this.isConnected && oldVal !== newVal) this._render();
  }

  get _isOpen() {
    return this.hasAttribute("open");
  }
  get _icon() {
    return this.getAttribute("icon") || "bi-cookie";
  }
  get _title() {
    return this.getAttribute("title") || "Cookies";
  }
  get _body() {
    return this.getAttribute("body") || "";
  }
  get _acceptLabel() {
    return this.getAttribute("accept-label") || "Accept all";
  }
  get _rejectLabel() {
    return this.getAttribute("reject-label") || "Reject";
  }
  get _moreInfoLabel() {
    return this.getAttribute("more-info-label") || "";
  }
  get _moreInfoHref() {
    return this.getAttribute("more-info-href") || "";
  }

  _dismiss(eventName) {
    this.dispatchEvent(new CustomEvent(eventName, { bubbles: true }));
    this.removeAttribute("open");
  }

  _render() {
    this.className = "rp-cookie";
    this.style.display = this._isOpen ? "" : "none";

    const moreInfoBtn = this._moreInfoLabel
      ? `<button class="rp-btn rp-btn-muted rp-btn-sm" data-more-info>${esc(this._moreInfoLabel)}</button>`
      : "";

    this.innerHTML = `
      <i class="bi ${esc(this._icon)}" style="font-size:24px;color:var(--rp-warning-soft-text)"></i>
      <div>
        <strong style="font-size:14px">${esc(this._title)}</strong>
        ${this._body ? `<div class="rp-muted" style="font-size:13px">${this._body}</div>` : ""}
      </div>
      <div class="d-flex gap-2 ms-auto">
        ${moreInfoBtn}
        <button class="rp-btn rp-btn-muted rp-btn-sm" data-reject>${esc(this._rejectLabel)}</button>
        <button class="rp-btn rp-btn-primary rp-btn-sm" data-accept>${esc(this._acceptLabel)}</button>
      </div>`;

    this.querySelector("[data-reject]").addEventListener("click", () => this._dismiss("rp:reject"));
    this.querySelector("[data-accept]").addEventListener("click", () => this._dismiss("rp:accept"));
    this.querySelector("[data-more-info]")?.addEventListener("click", () => {
      this.dispatchEvent(new CustomEvent("rp:more-info", { bubbles: true }));
      if (this._moreInfoHref) window.open(this._moreInfoHref, "_blank", "noopener");
    });
  }
}

customElements.define("cookie-banner", CookieBanner);
