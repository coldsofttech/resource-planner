/* DiffCompare  <diff-compare>
 *
 * Git-like diff/compare table — renders a set of typed rows (added/removed)
 * across configurable columns, reusing the green/red add/del color
 * language of a unified text diff, generalized to tabular data instead of
 * text lines. No "changed" state: a modified value is represented as an
 * adjacent del row (old value) followed by an add row (new value).
 *
 * Attributes:
 *   title  – card heading text
 *
 * Public API:
 *   diffEl.columns = [{ key, label }, ...]   — column definitions, in order
 *   diffEl.data = { rows: [{ type: "add" | "del", cells: { [key]: value } }] }
 *
 * Empty state: renders a muted "No differences found." message when
 * `data.rows` is an empty array (distinguish from `columns`/`data` never
 * having been set, which renders nothing).
 */
import { esc } from "../utils.js";

class DiffCompare extends HTMLElement {
  static get observedAttributes() {
    return ["title"];
  }

  connectedCallback() {
    this._render();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (oldVal !== newVal && this.isConnected) this._render();
  }

  get _title() {
    return this.getAttribute("title") || "";
  }

  set columns(cols) {
    this._columns = Array.isArray(cols) ? cols : [];
    if (this.isConnected) this._render();
  }

  get columns() {
    return this._columns || [];
  }

  set data(payload) {
    this._data = payload;
    if (this.isConnected) this._render();
  }

  get data() {
    return this._data;
  }

  _gridTemplate() {
    return `32px repeat(${this.columns.length}, 1fr)`;
  }

  _headerHTML() {
    if (!this.columns.length) return "";
    const cells = this.columns
      .map((c) => `<div class="rp-diff-cell rp-diff-head-cell">${esc(c.label)}</div>`)
      .join("");
    return `
      <div class="rp-diff-row rp-diff-header-row" style="grid-template-columns:${this._gridTemplate()}">
        <div class="rp-diff-ln"></div>
        ${cells}
      </div>
    `;
  }

  _rowHTML(row) {
    const glyph = row.type === "add" ? "+" : "-";
    const cells = this.columns
      .map((c) => `<div class="rp-diff-cell">${esc(row.cells?.[c.key] ?? "")}</div>`)
      .join("");
    return `
      <div class="rp-diff-row ${esc(row.type)}" style="grid-template-columns:${this._gridTemplate()}">
        <div class="rp-diff-ln">${glyph}</div>
        ${cells}
      </div>
    `;
  }

  _render() {
    const headHTML = this._title
      ? `<div class="rp-chart-head"><h4>${esc(this._title)}</h4></div>`
      : "";

    const rows = this._data?.rows;
    if (!rows) {
      this.innerHTML = headHTML;
      return;
    }

    if (!rows.length) {
      this.innerHTML = `${headHTML}<p class="small mb-0" style="color:var(--rp-text-muted)">No differences found.</p>`;
      return;
    }

    this.innerHTML = `
      ${headHTML}
      <div class="rp-diff">
        ${this._headerHTML()}
        ${rows.map((r) => this._rowHTML(r)).join("")}
      </div>
    `;
  }
}

customElements.define("diff-compare", DiffCompare);
