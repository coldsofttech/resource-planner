import { TextField } from "./text-field.js";

/* EmailField  <email-field>
 *
 * Email address input with built-in format validation.
 * Defaults: label "Email address", maxlength 255, placeholder "john.doe@example.com".
 * See text-field.js and base-field.js for inherited attributes.
 *
 * Additional attributes:
 *   prefix-icon  – boolean; adds an envelope icon (bi-envelope) to the left of the input
 *
 * Validation (always enforced regardless of `required`):
 *   - value must not be empty
 *   - value must not exceed 255 characters
 *   - value must match email format (user@domain.tld)
 */
class EmailField extends TextField {
  get _autocomplete() {
    return this.getAttribute("autocomplete") || "email";
  }

  connectedCallback() {
    if (!this.hasAttribute("label")) {
      this.setAttribute("label", "Email address");
    }

    if (!this.hasAttribute("maxlength")) {
      this.setAttribute("maxlength", "255");
    }

    if (!this.hasAttribute("placeholder")) {
      this.setAttribute("placeholder", "john.doe@example.com");
    }

    super.connectedCallback();
  }

  get _showPrefixIcon() {
    return this.hasAttribute("prefix-icon");
  }

  get _validEmail() {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(this._value.trim());
  }

  _validate() {
    if (this._readonly) return "";
    const value = this._value.trim();

    if (!value) {
      return "Email address is required.";
    }

    if (value.length > 255) {
      return "Email address cannot exceed 255 characters.";
    }

    if (value && !this._validEmail) {
      return "Enter a valid email address.";
    }

    return "";
  }

  _buildHTML() {
    const maxlen = this._maxlength ? ` maxlength="${this._esc(this._maxlength)}"` : "";
    const req = this._required ? " required" : "";
    const autocomplete = this._autocomplete
      ? ` autocomplete="${this._esc(this._autocomplete)}"`
      : "";
    const readonlyAttr = this._readonly ? " readonly" : "";
    const prefixIcon = this._showPrefixIcon ? `<i class="bi bi-envelope rp-prefix"></i>` : "";

    const inputClasses = ["rp-input"];
    if (this._showPrefixIcon) {
      inputClasses.push("has-prefix");
    }

    return `
      <div class="rp-field">
        ${this._labelHTML()}
        <div class="rp-input-affix">
          ${prefixIcon}
          <input
            class="${inputClasses.join(" ")}"
            type="email"
            id="${this._esc(this._fieldId)}-input"
            name="${this._esc(this._name)}"
            placeholder="${this._esc(this._placeholder)}"
            value="${this._esc(this._value)}"
            ${maxlen}
            ${req}
            ${autocomplete}
            ${readonlyAttr}
          />
        </div>
        ${this._errorHTML()}
        ${this._hintHTML()}
      </div>
    `;
  }
}

customElements.define("email-field", EmailField);
