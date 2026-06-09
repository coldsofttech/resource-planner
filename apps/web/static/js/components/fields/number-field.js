import { BaseField } from "./base-field.js";

/* NumberField  <number-field>
 *
 * Integer numeric input. Exported for extension (DecimalField).
 * See base-field.js for inherited attributes and validation lifecycle.
 *
 * Additional attributes:
 *   placeholder  – input placeholder text
 *   min          – minimum allowed value (forwarded to <input type="number">)
 *   max          – maximum allowed value (forwarded to <input type="number">)
 *   step         – increment step (default "1")
 *
 * Validation:
 *   - required: value must not be empty
 *   - value must be a valid number
 *   - value must be within [min, max] when those attributes are set
 */
export class NumberField extends BaseField {
  static get observedAttributes() {
    return [...super.observedAttributes, "placeholder", "min", "max", "step"];
  }

  get _placeholder() {
    return this.getAttribute("placeholder") || "";
  }
  get _autocomplete() {
    return this.getAttribute("autocomplete") || "off";
  }
  get _min() {
    return this.getAttribute("min") || "";
  }
  get _max() {
    return this.getAttribute("max") || "";
  }
  get _step() {
    return this.getAttribute("step") || "1";
  }

  get _value() {
    return this.querySelector(".rp-input")?.value ?? (this.getAttribute("value") || "");
  }

  _validate() {
    const raw = this._value;
    if (this._required && raw === "") return "This field is required.";
    const num = Number(raw);
    if (raw !== "" && isNaN(num)) return "Enter a valid number.";
    if (raw !== "" && this._min !== "" && num < Number(this._min))
      return `Value must be at least ${this._min}.`;
    if (raw !== "" && this._max !== "" && num > Number(this._max))
      return `Value must be at most ${this._max}.`;
    return "";
  }

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
        <input
          class="rp-input"
          type="number"
          id="${this._esc(this._fieldId)}-input"
          name="${this._esc(this._name)}"
          placeholder="${this._esc(this._placeholder)}"
          value="${this._esc(this._value)}"${min}${max}${step}${req}${autocomplete}
        />
        ${this._errorHTML()}
        ${this._hintHTML()}
      </div>
    `;
  }

  _bindEvents() {
    const input = this.querySelector(".rp-input");
    if (!input) return;
    input.addEventListener("blur", () => {
      this._touched = true;
      this._updateError();
    });
    input.addEventListener("input", () => {
      if (this._touched) this._updateError();
    });
  }
}

customElements.define("number-field", NumberField);
