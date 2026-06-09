import { BaseField } from "./base-field.js";

/* DateField  <date-field>
 *
 * Date picker field wrapping a native <input type="date">. Inherits all attributes
 * and the validation lifecycle from BaseField.
 * See base-field.js for inherited attributes.
 *
 * Additional attributes:
 *   min  – minimum selectable date (YYYY-MM-DD)
 *   max  – maximum selectable date (YYYY-MM-DD)
 *
 * Public API:
 *   field.value        – getter: current date string (YYYY-MM-DD) or ""
 *   field.value = v   – setter: sets the input value
 *
 * Validation:
 *   - required: a date must be selected
 */
export class DateField extends BaseField {
  static get observedAttributes() {
    return [...super.observedAttributes, "min", "max"];
  }

  get _value() {
    return this.querySelector(".rp-input")?.value ?? (this.getAttribute("value") || "");
  }

  get _min() {
    return this.getAttribute("min") || "";
  }

  get _max() {
    return this.getAttribute("max") || "";
  }

  _validate() {
    if (this._required && !this._value) return "This field is required.";
    return this._runCustomValidators();
  }

  _buildHTML() {
    const req = this._required ? " required" : "";
    const minAttr = this._min ? ` min="${this._esc(this._min)}"` : "";
    const maxAttr = this._max ? ` max="${this._esc(this._max)}"` : "";
    return `
      <div class="rp-field">
        ${this._labelHTML()}
        <input
          class="rp-input"
          type="date"
          id="${this._esc(this._fieldId)}-input"
          name="${this._esc(this._name)}"
          value="${this._esc(this._value)}"${req}${minAttr}${maxAttr}
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
    input.addEventListener("change", () => {
      if (this._touched) this._updateError();
    });
  }
}

customElements.define("date-field", DateField);
