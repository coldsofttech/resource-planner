import { BaseField } from "../fields/base-field.js";

/* ChoiceGroupField  (exported base class — not registered as a custom element)
 *
 * Base class for checkbox and radio groups. Reads <option-field> children once on connect,
 * then renders a list of labelled inputs. Subclasses set `_type` and `_inputClass`.
 * See base-field.js for inherited attributes and validation lifecycle.
 *
 * Declarative children (captured before first render):
 *   <option-field label="…" value="…" [checked] [disabled]>
 *     Alternatively, text content is used as the label when the `label` attribute is absent.
 *
 * Inherited attributes (from BaseField):
 *   col, label, required, id, name, hint, hint-type, value, autocomplete
 *   The `value` attribute pre-selects options: for checkboxes, a comma-separated list;
 *   for radio groups, a single value string.
 *
 * Public API:
 *   field.value  – getter: returns currently checked value(s)
 *                  CheckboxGroupField: comma-separated string of checked values
 *                  RadioGroupField: single selected value string, or ""
 *
 * Validation:
 *   - required: at least one option must be checked (checkbox) or an option must be selected (radio)
 *
 * Inheritance:
 *   ChoiceGroupField → CheckboxGroupField
 *   ChoiceGroupField → RadioGroupField
 */
export class ChoiceGroupField extends BaseField {
  connectedCallback() {
    // Read <option-field> children synchronously before super → _doRender() replaces innerHTML.
    // Guard so re-connections (wizard move) don't overwrite the captured options.
    if (this._initialOptions === undefined) {
      this._initialOptions = Array.from(this.querySelectorAll("option-field")).map((el) => ({
        label: el.getAttribute("label") || el.textContent.trim(),
        value: el.getAttribute("value") ?? "",
        checked: el.hasAttribute("checked"),
        disabled: el.hasAttribute("disabled"),
      }));
    }
    super.connectedCallback();
  }

  get _type() {
    return "checkbox";
  }
  get _inputClass() {
    return "rp-check";
  }
  get _options() {
    return this._initialOptions || [];
  }
  get _value() {
    return this.getAttribute("value") || "";
  }

  get value() {
    return Array.from(this.querySelectorAll(`.${this._inputClass}:checked`))
      .map((cb) => cb.value)
      .join(",");
  }

  _isOptionChecked(o) {
    const val = this._value;
    if (!val) return o.checked;
    return val
      .split(",")
      .map((v) => v.trim())
      .includes(o.value);
  }

  _labelHTML() {
    const req = this._required ? ' <span class="rp-req">*</span>' : "";
    return this._label ? `<div class="rp-label">${this._esc(this._label)}${req}</div>` : "";
  }

  _savedValue() {
    return Array.from(this.querySelectorAll(`.${this._inputClass}`)).map((cb) => ({
      value: cb.value,
      checked: cb.checked,
    }));
  }
  _restoreValue(val) {
    if (!val) return;
    const inputs = Array.from(this.querySelectorAll(`.${this._inputClass}`));
    val.forEach(({ value, checked }) => {
      const inp = inputs.find((cb) => cb.value === value);
      if (inp) inp.checked = checked;
    });
  }

  _validate() {
    if (this._required) {
      const anyChecked = Array.from(this.querySelectorAll(`.${this._inputClass}`)).some(
        (cb) => cb.checked,
      );
      if (!anyChecked) return "Please select at least one option.";
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

  _buildHTML() {
    const name = this._esc(this._name || this._fieldId);
    const { _type: type, _inputClass: cls } = this;
    const itemsHTML = this._options
      .map(
        (o) => `
        <label class="rp-field-row mb-2">
          <input
            type="${type}"
            class="${cls}"
            name="${name}"
            value="${this._esc(o.value)}"
            ${this._isOptionChecked(o) ? "checked" : ""}
            ${o.disabled ? "disabled" : ""}
          />
          <span>${this._esc(o.label)}</span>
        </label>`,
      )
      .join("");
    return `
      <div class="rp-field">
        ${this._labelHTML()}
        ${itemsHTML}
        ${this._errorHTML()}
        ${this._hintHTML()}
      </div>`;
  }

  _bindEvents() {
    this.querySelectorAll(`.${this._inputClass}`).forEach((input) => {
      input.addEventListener("change", () => {
        this._touched = true;
        this._updateError();
      });
    });
  }
}
