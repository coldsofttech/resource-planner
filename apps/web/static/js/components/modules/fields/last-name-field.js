import { TextField } from "../../fields/text-field.js";

/* LastNameField  <last-name-field>
 * Pre-configured text input for a person's family name.
 * Defaults: label "Last name", required, maxlength 100, placeholder "Doe",
 * autocomplete "family-name".
 * See text-field.js and base-field.js for full attribute documentation. */
class LastNameField extends TextField {
  get _autocomplete() {
    return this.getAttribute("autocomplete") || "family-name";
  }

  connectedCallback() {
    if (!this.hasAttribute("label")) {
      this.setAttribute("label", "Last name");
    }

    if (!this.hasAttribute("required")) {
      this.setAttribute("required", "");
    }

    if (!this.hasAttribute("maxlength")) {
      this.setAttribute("maxlength", "100");
    }

    if (!this.hasAttribute("placeholder")) {
      this.setAttribute("placeholder", "Doe");
    }

    super.connectedCallback();
  }

  _validate() {
    const value = this._value.trim();

    if (!value) {
      return "Last name is required.";
    }

    if (value.length > 100) {
      return "Last name cannot exceed 100 characters.";
    }

    return "";
  }
}

customElements.define("last-name-field", LastNameField);
