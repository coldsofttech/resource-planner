import { esc } from "../utils.js";

/* HistoryItem  <history-item>
 *
 * Single entry in a timeline history list. Renders an icon column (with an
 * optional vertical connector line to the next item) and a text body column.
 *
 * Attributes:
 *   label       – action label text   (e.g. "Created", "Updated")
 *   icon        – Bootstrap Icon class (e.g. "bi-plus-circle-fill")
 *   icon-color  – named colour token or raw CSS colour value:
 *                   accent | success | muted | danger | warning | info
 *   status      – status transition text (e.g. "Draft → Approved")
 *   note        – optional italic note beneath the status line
 *   meta        – small footer text   (e.g. "12 May 2025 · alice@example.com")
 *   connector   – boolean; draws a vertical line below the icon to connect
 *                 this item to the next one — set on all items except the last
 */
class HistoryItem extends HTMLElement {
  static get observedAttributes() {
    return ["label", "icon", "icon-color", "status", "note", "meta", "connector"];
  }

  connectedCallback() {
    this._render();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (oldVal !== newVal) this._render();
  }

  static _colors = {
    accent: "var(--rp-accent)",
    success: "var(--rp-success-soft-text, #198754)",
    muted: "var(--rp-text-muted)",
    danger: "var(--rp-danger-soft-text, #dc3545)",
    warning: "var(--rp-warning-soft-text, #856404)",
    info: "var(--rp-info-soft-text)",
  };

  _resolveColor(token) {
    return HistoryItem._colors[token] || token || "var(--rp-text-muted)";
  }

  _render() {
    const label = this.getAttribute("label") || "";
    const icon = this.getAttribute("icon") || "bi-circle-fill";
    const color = this._resolveColor(this.getAttribute("icon-color") || "muted");
    const status = this.getAttribute("status") || "";
    const note = this.getAttribute("note") || "";
    const meta = this.getAttribute("meta") || "";
    const connector = this.hasAttribute("connector");

    const lineHTML = connector
      ? `<div style="width:1px;flex:1;min-height:20px;background:var(--rp-border);margin-top:4px;"></div>`
      : "";

    this.innerHTML = `
      <div class="d-flex gap-2 align-items-start${connector ? " pb-3" : ""}">
        <div class="d-flex flex-column align-items-center flex-shrink-0" style="width:20px;">
          <i class="bi ${esc(icon)}" style="color:${color};font-size:14px;"></i>
          ${lineHTML}
        </div>
        <div class="flex-grow-1">
          <div class="rp-fs-13 fw-medium" data-hi-label></div>
          <div class="rp-fs-12 text-muted" data-hi-status></div>
          ${note ? `<div class="rp-fs-12 text-muted fst-italic mt-1" data-hi-note></div>` : ""}
          ${meta ? `<div class="rp-fs-11 text-muted mt-1" data-hi-meta></div>` : ""}
        </div>
      </div>`;

    // Use textContent for all user-supplied values — never flow API data into innerHTML
    this.querySelector("[data-hi-label]").textContent = label;
    this.querySelector("[data-hi-status]").textContent = status;
    if (note) this.querySelector("[data-hi-note]").textContent = note;
    if (meta) this.querySelector("[data-hi-meta]").textContent = meta;
  }
}

customElements.define("history-item", HistoryItem);
