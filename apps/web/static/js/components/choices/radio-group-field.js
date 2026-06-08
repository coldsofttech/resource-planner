import { ChoiceGroupField } from "./choice-group-field.js";

/* RadioGroupField  <radio-group-field>
 * Group of radio inputs; only one option can be selected at a time. Extends ChoiceGroupField
 * with type="radio". `field.value` returns the single selected value string, or "".
 * See choice-group-field.js and base-field.js for full attribute and validation documentation. */
class RadioGroupField extends ChoiceGroupField {
  get _type() {
    return "radio";
  }

  get value() {
    return this.querySelector(`.${this._inputClass}:checked`)?.value ?? "";
  }

  _isOptionChecked(o) {
    const val = this._value;
    return val ? o.value === val : o.checked;
  }

  _savedValue() {
    return this.querySelector(`.${this._inputClass}:checked`)?.value ?? null;
  }
  _restoreValue(val) {
    if (val === null) return;
    this.querySelectorAll(`.${this._inputClass}`).forEach((r) => {
      r.checked = r.value === val;
    });
  }
  _validate() {
    if (this._required && !this.querySelector(`.${this._inputClass}:checked`)) {
      return "Please select an option.";
    }
    return "";
  }
}

customElements.define("radio-group-field", RadioGroupField);
