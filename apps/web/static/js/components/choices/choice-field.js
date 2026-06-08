import { BaseField } from "../fields/base-field.js";

/* ChoiceField  (exported base class — not registered as a custom element)
 *
 * Base class for single checkbox and radio inputs. Renders a label-wrapped input with optional
 * error and hint. Subclasses set `_type` ("checkbox" | "radio") and `_inputClass`.
 * See base-field.js for inherited attributes and validation lifecycle.
 *
 * Additional attributes:
 *   checked   – boolean; initial checked state
 *   disabled  – boolean; disables the input
 *   value     – submitted form value when checked (default "on")
 *
 * Public API:
 *   field.checked        – getter: returns current checked state
 *   field.checked = bool – setter: sets checked state on the underlying input
 *
 * Validation:
 *   - required: input must be checked
 *
 * Inheritance:
 *   ChoiceField → CheckboxField
 *   ChoiceField → RadioField
 */
export class ChoiceField extends BaseField {
  static get observedAttributes() {
    return [...super.observedAttributes, "checked", "disabled"];
  }

  get _type() {
    return "checkbox";
  }
  get _inputClass() {
    return "rp-check";
  }
  get _value() {
    return this.getAttribute("value") || "on";
  }
  get _checked() {
    return this.hasAttribute("checked");
  }
  get _disabled() {
    return this.hasAttribute("disabled");
  }

  _savedValue() {
    return this.querySelector(`.${this._inputClass}`)?.checked ?? null;
  }
  _restoreValue(val) {
    if (val === null) return;
    const input = this.querySelector(`.${this._inputClass}`);
    if (input) input.checked = val;
  }

  _validate() {
    if (this._required && !this.querySelector(`.${this._inputClass}`)?.checked) {
      return "This field is required.";
    }
    return "";
  }

  _updateError() {
    const err = this._validate();
    const errEl = this.querySelector("[data-rp-error]");
    if (errEl) {
      errEl.textContent = err;
      errEl.hidden = !err;
    }
  }

  get checked() {
    return this.querySelector(`.${this._inputClass}`)?.checked ?? false;
  }

  set checked(v) {
    const input = this.querySelector(`.${this._inputClass}`);
    if (input) input.checked = v;
  }

  _buildHTML() {
    return `
      <label class="rp-field-row">
        <input
          type="${this._type}"
          class="${this._inputClass}"
          ${this._fieldId ? `id="${this._esc(this._fieldId)}-input"` : ""}
          name="${this._esc(this._name)}"
          value="${this._esc(this._value)}"
          ${this._checked ? "checked" : ""}
          ${this._disabled ? "disabled" : ""}
        />
        <span>${this._esc(this._label)}</span>
      </label>
      ${this._errorHTML()}
      ${this._hintHTML()}`;
  }

  _bindEvents() {
    const input = this.querySelector(`.${this._inputClass}`);
    if (!input) return;
    input.addEventListener("change", () => {
      this._touched = true;
      this._updateError();
    });
  }
}
