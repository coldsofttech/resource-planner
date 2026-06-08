import { ChoiceGroupField } from "./choice-group-field.js";

/* CheckboxGroupField  <checkbox-group-field>
 * Group of checkbox inputs. Thin wrapper over ChoiceGroupField with type="checkbox".
 * `field.value` returns a comma-separated string of all checked values.
 * See choice-group-field.js and base-field.js for full attribute and validation documentation. */
class CheckboxGroupField extends ChoiceGroupField {}

customElements.define("checkbox-group-field", CheckboxGroupField);
