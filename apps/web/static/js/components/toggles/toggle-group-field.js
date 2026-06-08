import { ChoiceGroupField } from "../choices/choice-group-field.js";

/* ToggleGroupField  <toggle-group-field>
 * Group of toggle switch inputs. Extends ChoiceGroupField using the `rp-toggle` CSS class.
 * Each option is rendered as a pill switch rather than a standard checkbox.
 * See choice-group-field.js and base-field.js for full attribute and validation documentation. */
class ToggleGroupField extends ChoiceGroupField {
  get _inputClass() {
    return "rp-toggle";
  }
}

customElements.define("toggle-group-field", ToggleGroupField);
