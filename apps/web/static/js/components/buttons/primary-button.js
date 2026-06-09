/* PrimaryButton  <primary-button>
 *
 * Base button component. Renders a single `<button>` inside the host element.
 * Subclasses override `_variant` to produce different visual styles.
 *
 * Attributes:
 *   label        – button text
 *   prefix-icon  – Bootstrap Icons class shown before the label (e.g. "bi-plus")
 *   suffix-icon  – Bootstrap Icons class shown after the label (e.g. "bi-arrow-right")
 *   disabled     – boolean; disables the button
 *   type         – HTML button type: "button" (default) | "submit" | "reset"
 *
 * Variants (subclasses):
 *   <primary-button>    → rp-btn-primary  (blue, call-to-action)
 *   <secondary-button>  → rp-btn-secondary
 *   <muted-button>      → rp-btn-muted    (neutral, cancel/back)
 *   <engine-button>     → rp-btn-engine   (processing/run actions)
 *   <delete-button>     → rp-btn-delete   (destructive, red)
 *   <activate-button>   → rp-btn-activate
 *   <deactivate-button> → rp-btn-deactivate
 *
 * Use `snapshotButton` / `setBusyButton` / `restoreButton` from utils.js to
 * manage loading states on async actions.
 *
 * Example:
 *   <primary-button label="Save" suffix-icon="bi-check2"></primary-button>
 *   <muted-button label="Cancel"></muted-button>
 */
import { esc } from "../utils.js";

export class PrimaryButton extends HTMLElement {
  static get observedAttributes() {
    return ["label", "prefix-icon", "suffix-icon", "disabled", "type"];
  }

  connectedCallback() {
    this._rendered = false;
    this._render();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this._rendered && oldVal !== newVal) this._render();
  }

  get _label() {
    return this.getAttribute("label") || "";
  }
  get _prefixIcon() {
    return this.getAttribute("prefix-icon") || "";
  }
  get _suffixIcon() {
    return this.getAttribute("suffix-icon") || "";
  }
  get _disabled() {
    return this.hasAttribute("disabled");
  }
  get _type() {
    return this.getAttribute("type") || "button";
  }
  get _variant() {
    return "rp-btn-primary";
  }

  _render() {
    const prefix = this._prefixIcon ? `<i class="bi ${esc(this._prefixIcon)}"></i>` : "";
    const suffix = this._suffixIcon ? `<i class="bi ${esc(this._suffixIcon)}"></i>` : "";
    const label = this._label ? esc(this._label) : "";
    this.innerHTML = `<button type="${esc(this._type)}" class="rp-btn ${this._variant}"${this._disabled ? " disabled" : ""}>${prefix}${label}${suffix}</button>`;
    this._rendered = true;
  }
}

customElements.define("primary-button", PrimaryButton);
