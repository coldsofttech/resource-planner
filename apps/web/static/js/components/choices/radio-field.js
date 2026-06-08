import { ChoiceField } from "./choice-field.js";

/* RadioField  <radio-field>
 * Single radio input. Extends ChoiceField with type="radio".
 * See choice-field.js and base-field.js for full attribute and validation documentation. */
class RadioField extends ChoiceField {
  get _type() {
    return "radio";
  }
}

customElements.define("radio-field", RadioField);
