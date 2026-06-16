import { esc } from "../utils.js";

/* HistoryPanel  <history-panel>
 *
 * Sunken card container for timeline history content. Follows the same
 * slot-capture pattern as <section-panel>: all direct children are captured
 * once on connect and re-inserted into the card body after render, so inner
 * components (dropdowns, <history-items>) retain their state across re-renders.
 *
 * Typical usage:
 *   <history-panel title="Version History" icon="bi-clock-history">
 *     <dropdown-field id="picker" ...></dropdown-field>   ← header control
 *     <history-items id="list" placeholder="Select a version…"></history-items>
 *   </history-panel>
 *
 * Attributes:
 *   title  – card heading text (default "Version History")
 *   icon   – Bootstrap Icon class shown before the title (e.g. "bi-clock-history")
 *   col    – Bootstrap column class applied to the host element (default "col-12")
 */
class HistoryPanel extends HTMLElement {
  static get observedAttributes() {
    return ["title", "icon", "col"];
  }

  connectedCallback() {
    if (this._bodyNodes === undefined) {
      this._bodyNodes = Array.from(this.children);
    }
    if (!this.querySelector(".rp-card")) this._render();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this._bodyNodes !== undefined && oldVal !== newVal) this._render();
  }

  get _col() {
    return this.getAttribute("col") || "col-12";
  }
  get _title() {
    return this.getAttribute("title") || "Version History";
  }
  get _icon() {
    return this.getAttribute("icon") || "";
  }

  _render() {
    const extras = Array.from(this.classList).filter((c) => !c.startsWith("col-"));
    this.className = [this._col, ...extras].join(" ").trim();
    const iconHTML = this._icon ? `<i class="bi ${esc(this._icon)} rp-card-head-icon"></i>` : "";
    this.innerHTML = `
      <div class="rp-card rp-card-sunken">
        <div class="rp-card-head">${iconHTML}<strong>${esc(this._title)}</strong></div>
        <div class="rp-card-body" data-history-slot></div>
      </div>`;
    const slot = this.querySelector("[data-history-slot]");
    if (slot) this._bodyNodes?.forEach((n) => slot.appendChild(n));
  }
}

customElements.define("history-panel", HistoryPanel);
