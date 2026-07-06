import { esc } from "../utils.js";

/* SectionPanel  <section-panel>
 *
 * Sunken card container with an optional titled header and a body slot. Body child nodes are
 * captured once on connect and re-inserted into a slot div after render, preserving component
 * state when the panel is moved by the wizard. Re-connection is safe: the render is skipped if
 * the card shell already exists (wizard-safe guard).
 *
 * Declarative children (captured before first render):
 *   <panel-title>    – raw HTML content used as the card heading; takes precedence over `title`
 *   <panel-actions>  – child nodes placed in the right side of the card header (e.g. icon buttons)
 *   <panel-body>     – child elements placed inside the card body slot
 *
 * Attributes:
 *   col    – Bootstrap column class applied to the host element (default "col-12")
 *   title  – plain-text card heading (used when <panel-title> is absent)
 *   icon   – Bootstrap Icon class shown before the title (e.g. "bi-person")
 *   id     – element id; also used as `name` fallback
 *   name   – logical name for the panel
 */
class SectionPanel extends HTMLElement {
  static get observedAttributes() {
    return ["col", "title", "icon", "id", "name"];
  }

  connectedCallback() {
    if (this._bodyNodes === undefined) {
      // <panel-title> innerHTML takes precedence over the title="" attribute.
      // Captured once here (=== undefined guard) before _render() replaces innerHTML.
      const titleEl = this.querySelector("panel-title");
      this._titleContent = titleEl ? titleEl.innerHTML.trim() : null;

      const actionsEl = this.querySelector("panel-actions");
      this._actionsNodes = actionsEl ? Array.from(actionsEl.childNodes) : null;

      const body = this.querySelector("panel-body");
      this._bodyNodes = body ? Array.from(body.children) : [];
    }
    // When the wizard moves this element the .rp-card shell is still intact —
    // skip the full re-render to avoid detaching/reattaching body nodes.
    if (!this.querySelector(":scope > .rp-card")) this._render();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this._bodyNodes !== undefined && oldVal !== newVal) this._render();
  }

  get _col() {
    return this.getAttribute("col") || "col-12";
  }
  get _title() {
    return this.getAttribute("title") || "";
  }
  get _icon() {
    return this.getAttribute("icon") || "";
  }
  get _fieldId() {
    return this.id || "";
  }
  get _name() {
    return this.getAttribute("name") || this._fieldId;
  }

  _render() {
    const extras = Array.from(this.classList).filter((c) => !c.startsWith("col-"));
    this.className = [this._col, ...extras].join(" ").trim();
    const headContent = this._titleContent ?? (this._title ? esc(this._title) : "");
    const iconHTML = this._icon ? `<i class="bi ${esc(this._icon)} rp-card-head-icon"></i>` : "";
    const actionsSlot = this._actionsNodes ? `<div data-panel-actions></div>` : "";
    const headHTML =
      headContent || iconHTML || this._actionsNodes
        ? `<div class="rp-card-head">${iconHTML}<strong>${headContent}</strong>${actionsSlot}</div>`
        : "";
    this.innerHTML = `<div class="rp-card rp-card-sunken">${headHTML}<div class="rp-card-body" data-panel-body></div></div>`;
    const actionsSlotEl = this.querySelector("[data-panel-actions]");
    if (actionsSlotEl && this._actionsNodes)
      this._actionsNodes.forEach((node) => actionsSlotEl.appendChild(node));
    const slot = this.querySelector("[data-panel-body]");
    if (slot && this._bodyNodes) this._bodyNodes.forEach((node) => slot.appendChild(node));
  }
}

customElements.define("section-panel", SectionPanel);
