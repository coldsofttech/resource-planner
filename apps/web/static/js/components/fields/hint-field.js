/* HintField  <hint-field>
 *
 * Standalone inline hint/callout block for use in form layouts alongside field components.
 * Inner HTML is captured once on connect and re-inserted after each render so arbitrary
 * rich content (links, bold text, etc.) is preserved. Not a BaseField subclass.
 *
 * Attributes:
 *   type   – visual variant: "info" | "warning" | "success" | "danger" (default "info")
 *   col    – Bootstrap column class applied to the host element (default "col-12")
 *   title  – optional bold heading rendered above the content inside the callout box
 */
import { esc } from "../utils.js";

class HintField extends HTMLElement {
  static get observedAttributes() {
    return ["type", "col", "title"];
  }

  connectedCallback() {
    if (this._content === undefined) {
      this._content = this.innerHTML.trim();
    }
    this._render();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this._content !== undefined && oldVal !== newVal) this._render();
  }

  get _type() {
    return this.getAttribute("type") || "info";
  }
  get _col() {
    return this.getAttribute("col") || "col-12";
  }
  get _title() {
    return this.getAttribute("title") || "";
  }

  _render() {
    const TYPES = {
      info: ["bi-info-circle", "rp-hint-info"],
      warning: ["bi-lightbulb", "rp-hint-warning"],
      success: ["bi-check-circle", "rp-hint-success"],
      danger: ["bi-exclamation-triangle", "rp-hint-danger"],
    };
    const [icon, cls] = TYPES[this._type] ?? TYPES.info;
    this.className = this._col;
    const titleHTML = this._title ? `<div class="rp-hint-title">${esc(this._title)}</div>` : "";
    this.innerHTML = `<div class="rp-hint ${cls}"><i class="bi ${icon}"></i><div>${titleHTML}${this._content}</div></div>`;
  }
}

customElements.define("hint-field", HintField);
