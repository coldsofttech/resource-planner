import { TextField } from "../../fields/text-field.js";

/* FirstNameField  <first-name-field>
 * Pre-configured text input for a person's given name.
 * Defaults: label "First name", required, maxlength 100, placeholder "John",
 * autocomplete "given-name".
 * See text-field.js and base-field.js for full attribute documentation. */
class FirstNameField extends TextField {
  get _autocomplete() {
    return this.getAttribute("autocomplete") || "given-name";
  }

  connectedCallback() {
    if (!this.hasAttribute("label")) {
      this.setAttribute("label", "First name");
    }

    if (!this.hasAttribute("required")) {
      this.setAttribute("required", "");
    }

    if (!this.hasAttribute("maxlength")) {
      this.setAttribute("maxlength", "100");
    }

    if (!this.hasAttribute("placeholder")) {
      this.setAttribute("placeholder", "John");
    }

    super.connectedCallback();
  }

  _validate() {
    const value = this._value.trim();

    if (!value) {
      return "First name is required.";
    }

    if (value.length > 100) {
      return "First name cannot exceed 100 characters.";
    }

    return "";
  }
}

customElements.define("first-name-field", FirstNameField);
