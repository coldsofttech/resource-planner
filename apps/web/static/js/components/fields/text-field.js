import { BaseField } from "./base-field.js";

/* TextField  <text-field>
 *
 * Single-line text input (or multi-line textarea when `cols` ≥ 2). Exported for extension.
 * See base-field.js for inherited attributes and validation lifecycle.
 *
 * Additional attributes:
 *   placeholder   – input placeholder text
 *   maxlength     – maximum character count forwarded to the input/textarea element
 *   show-counter  – boolean; when present, shows a live character count next to the label
 *   cols          – integer ≥ 2: renders a <textarea> with this number of rows instead of <input>
 *
 * Validation:
 *   - required: value must not be blank
 *   - custom validators via _customValidators array
 */
export class TextField extends BaseField {
  static get observedAttributes() {
    return [...super.observedAttributes, "placeholder", "maxlength", "show-counter", "cols"];
  }

  get _placeholder() {
    return this.getAttribute("placeholder") || "";
  }
  get _maxlength() {
    return this.getAttribute("maxlength") || "";
  }
  get _autocomplete() {
    return this.getAttribute("autocomplete") || "off";
  }
  get _showCounter() {
    return this.hasAttribute("show-counter");
  }
  get _cols() {
    const v = parseInt(this.getAttribute("cols") || "0", 10);
    if (isNaN(v) || v < 2) return 0;
    return Math.min(v, 10);
  }

  get _value() {
    return this.querySelector(".rp-input")?.value ?? (this.getAttribute("value") || "");
  }

  _validate() {
    if (this._required && !this._value.trim()) return "This field is required.";
    return this._runCustomValidators();
  }

  _counterHTML() {
    if (!this._showCounter) return "";
    const max = this._maxlength ? parseInt(this._maxlength, 10) : null;
    const maxPart = max ? `<span class="rp-counter-max">/${max}</span>` : "";
    return `<span class="rp-field-counter" data-rp-counter aria-live="polite"><span data-rp-counter-cur>0</span>${maxPart}</span>`;
  }

  _updateCounter() {
    const cur = this.querySelector("[data-rp-counter-cur]");
    const input = this.querySelector(".rp-input");
    if (cur && input) cur.textContent = input.value.length;
  }

  _restoreValue(val) {
    super._restoreValue(val);
    if (this._showCounter) this._updateCounter();
  }

  _buildHTML() {
    const maxlen = this._maxlength ? ` maxlength="${this._esc(this._maxlength)}"` : "";
    const req = this._required ? " required" : "";
    const autocomplete = this._autocomplete
      ? ` autocomplete="${this._esc(this._autocomplete)}"`
      : "";
    const labelBlock = this._showCounter
      ? `<div class="rp-field-label-row">${this._labelHTML()}${this._counterHTML()}</div>`
      : this._labelHTML();
    const inputEl = this._cols
      ? `<textarea
          class="rp-input"
          id="${this._esc(this._fieldId)}-input"
          name="${this._esc(this._name)}"
          placeholder="${this._esc(this._placeholder)}"
          rows="${this._cols}"${maxlen}${req}${autocomplete}
        >${this._esc(this._value)}</textarea>`
      : `<input
          class="rp-input"
          type="text"
          id="${this._esc(this._fieldId)}-input"
          name="${this._esc(this._name)}"
          placeholder="${this._esc(this._placeholder)}"
          value="${this._esc(this._value)}"${maxlen}${req}${autocomplete}
        />`;
    return `
      <div class="rp-field">
        ${labelBlock}
        ${inputEl}
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
      if (this._showCounter) this._updateCounter();
      if (this._touched) this._updateError();
    });
    if (this._showCounter) this._updateCounter();
  }
}

customElements.define("text-field", TextField);
