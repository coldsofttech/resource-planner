import { ChoiceField } from "../choices/choice-field.js";

/* ToggleField  <toggle-field>
 * Single toggle switch input. Extends ChoiceField using the `rp-toggle` CSS class.
 * Visually styled as a pill switch rather than a standard checkbox.
 * See choice-field.js and base-field.js for full attribute and validation documentation. */
class ToggleField extends ChoiceField {
  get _inputClass() {
    return "rp-toggle";
  }
}

customElements.define("toggle-field", ToggleField);
