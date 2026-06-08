import { NumberField } from "./number-field.js";

/* DecimalField  <decimal-field>
 * Extends NumberField with a default step of "0.1" for decimal/floating-point inputs.
 * Override with the `step` attribute for different precision (e.g. step="0.01").
 * See number-field.js and base-field.js for full attribute and validation documentation. */
class DecimalField extends NumberField {
  get _step() {
    return this.getAttribute("step") || "0.1";
  }
}

customElements.define("decimal-field", DecimalField);
