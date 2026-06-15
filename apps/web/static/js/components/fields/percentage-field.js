import { NumberField } from "./number-field.js";

/* PercentageField  <percentage-field>
 *
 * Integer percentage input with a fixed "%" suffix icon.
 * Extends NumberField — all number-field and base-field attributes apply.
 *
 * Defaults applied when the attribute is absent:
 *   step  → "1"
 *
 * Additional attributes:
 *   placeholder  – input placeholder text
 *   min          – minimum allowed value (default: unrestricted)
 *   max          – maximum allowed value (default: unrestricted)
 *   step         – increment step (default "1")
 *
 * Validation:
 *   - required: value must not be empty
 *   - value must be a valid number
 *   - value must be within [min, max] when those attributes are set
 *
 * Usage:
 *   <percentage-field label="Contingency" placeholder="0" min="0" max="100"></percentage-field>
 */
class PercentageField extends NumberField {
  _buildHTML() {
    const req = this._required ? " required" : "";
    const autocomplete = this._autocomplete
      ? ` autocomplete="${this._esc(this._autocomplete)}"`
      : "";
    const min = this._min !== "" ? ` min="${this._esc(this._min)}"` : "";
    const max = this._max !== "" ? ` max="${this._esc(this._max)}"` : "";
    const step = ` step="${this._esc(this._step)}"`;
    return `
      <div class="rp-field">
        ${this._labelHTML()}
        <div class="rp-input-affix">
          <input
            class="rp-input has-suffix"
            type="number"
            id="${this._esc(this._fieldId)}-input"
            name="${this._esc(this._name)}"
            placeholder="${this._esc(this._placeholder)}"
            value="${this._esc(this._value)}"${min}${max}${step}${req}${autocomplete}
          />
          <span class="rp-suffix">%</span>
        </div>
        ${this._errorHTML()}
        ${this._hintHTML()}
      </div>
    `;
  }
}

customElements.define("percentage-field", PercentageField);
