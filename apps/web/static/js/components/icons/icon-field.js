/* IconField  <icon-field>
 *
 * Inline icon display component backed by Bootstrap Icons. Replaces raw
 * `<i class="bi bi-*">` tags with a semantic, accessible element whose
 * appearance is fully driven by HTML attributes.
 *
 * Attributes:
 *   icon    – Bootstrap Icons class, with or without the "bi-" prefix
 *             (e.g. "bi-arrow-right" or "arrow-right"). Required.
 *   size    – Named size: "xs" | "sm" | "md" (default) | "lg" | "xl" | "2x"
 *             OR any valid CSS font-size value (e.g. "1.25rem", "20px").
 *   color   – Named colour token: "info" | "success" | "warning" | "danger" | "muted" | "primary"
 *             OR any valid CSS color value (e.g. "var(--rp-info)", "#ff0000").
 *   label   – Accessible text label. When set, the <i> receives aria-hidden="true" and a
 *             visually-hidden <span> carries the text for screen readers.
 *             When absent, the <i> receives role="img" and aria-label derived from the icon name.
 *   title   – Native tooltip text shown on hover.
 *
 * Example:
 *   <icon-field icon="bi-check-circle" color="success" size="lg" label="Completed"></icon-field>
 *   <icon-field icon="bi-exclamation-triangle" color="warning" title="Needs attention"></icon-field>
 *   <icon-field icon="arrow-right" size="1.5rem"></icon-field>
 */
import { esc } from "../utils.js";

const NAMED_SIZES = {
  xs: "0.75rem",
  sm: "0.875rem",
  md: "1rem",
  lg: "1.25rem",
  xl: "1.5rem",
  "2x": "2rem",
};

const NAMED_COLORS = {
  info: "var(--rp-info)",
  success: "var(--rp-success-soft-text)",
  warning: "var(--rp-warning-soft-text)",
  danger: "var(--rp-danger-soft-text)",
  muted: "var(--rp-text-muted)",
  primary: "var(--rp-primary)",
};

export class IconField extends HTMLElement {
  static get observedAttributes() {
    return ["icon", "size", "color", "label", "title"];
  }

  connectedCallback() {
    this._rendered = false;
    this._render();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this._rendered && oldVal !== newVal) this._render();
  }

  get _icon() {
    const raw = this.getAttribute("icon") || "";
    if (!raw) return "";
    return raw.startsWith("bi-") ? raw : `bi-${raw}`;
  }

  get _size() {
    const val = this.getAttribute("size") || "";
    return NAMED_SIZES[val] ?? val;
  }

  get _color() {
    const val = this.getAttribute("color") || "";
    return NAMED_COLORS[val] ?? val;
  }

  get _label() {
    return this.getAttribute("label") || "";
  }

  get _title() {
    return this.getAttribute("title") || "";
  }

  _render() {
    const icon = this._icon;
    if (!icon) {
      this.innerHTML = "";
      this._rendered = true;
      return;
    }

    const styles = [
      this._size ? `font-size:${this._size}` : "",
      this._color ? `color:${this._color}` : "",
    ]
      .filter(Boolean)
      .join(";");

    const styleAttr = styles ? ` style="${esc(styles)}"` : "";
    const titleAttr = this._title ? ` title="${esc(this._title)}"` : "";
    const label = this._label;

    let html;
    if (label) {
      html =
        `<i class="bi ${esc(icon)}" aria-hidden="true"${styleAttr}${titleAttr}></i>` +
        `<span class="visually-hidden">${esc(label)}</span>`;
    } else {
      const ariaLabel = icon.replace(/^bi-/, "").replace(/-/g, " ");
      html = `<i class="bi ${esc(icon)}" role="img" aria-label="${esc(ariaLabel)}"${styleAttr}${titleAttr}></i>`;
    }

    this.innerHTML = html;
    this._rendered = true;
  }
}

customElements.define("icon-field", IconField);
