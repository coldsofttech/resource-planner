import { ChoiceField } from "./choice-field.js";

/* CheckboxField  <checkbox-field>
 * Single checkbox input. Thin wrapper over ChoiceField with type="checkbox".
 * See choice-field.js and base-field.js for full attribute and validation documentation. */
class CheckboxField extends ChoiceField {}

customElements.define("checkbox-field", CheckboxField);
