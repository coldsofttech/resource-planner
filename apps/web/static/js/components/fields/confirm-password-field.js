import { PasswordField } from "./password-field.js";

/* ConfirmPasswordField  <confirm-password-field>
 *
 * Password confirmation input that cross-validates against a sibling <password-field>.
 * Defaults: label "Confirm password", placeholder "Confirm password", required.
 * See password-field.js and base-field.js for inherited attributes.
 *
 * Additional attributes:
 *   password-field-id  – id of the sibling <password-field> element to compare against;
 *                        when set, the field shows a "Matches." success indicator and
 *                        validates that both values are equal
 *   eye-icon           – boolean; show/hide toggle (inherited from PasswordField)
 *   prefix-icon        – boolean; key icon prefix (inherited from PasswordField)
 *
 * Note: strength meter is not shown (always disabled in this subclass).
 *
 * Validation:
 *   - required: value must not be blank
 *   - match: value must equal the referenced password field's value
 */
class ConfirmPasswordField extends PasswordField {
  get _autocomplete() {
    return this.getAttribute("autocomplete") || "new-password";
  }

  connectedCallback() {
    if (!this.hasAttribute("label")) this.setAttribute("label", "Confirm password");
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "Confirm password");
    if (!this.hasAttribute("required")) this.setAttribute("required", "");
    super.connectedCallback();
  }

  get _passwordFieldId() {
    return this.getAttribute("password-field-id") || "";
  }

  // password-field-id holds the id of the sibling <password-field> element.
  // getElementById returns the custom element; .value goes through its public get value().
  get _passwordInput() {
    return this._passwordFieldId ? document.getElementById(this._passwordFieldId) : null;
  }

  get _passwordValue() {
    return this._passwordInput?.value ?? "";
  }

  get _matches() {
    return this._value !== "" && this._value === this._passwordValue;
  }

  _validate() {
    if (this._required && !this._value.trim()) return "Please confirm your password.";
    if (this._value && !this._matches) return "Passwords do not match.";
    return "";
  }

  _updateMatch() {
    const el = this.querySelector("[data-rp-match]");
    if (!el) return;
    if (this._matches) {
      el.hidden = false;
      el.className = "rp-help";
      el.innerHTML = `<i class="bi bi-check2-circle" style="color: var(--rp-success-soft-text)"></i> Matches.`;
    } else {
      el.hidden = true;
    }
  }

  _updateError() {
    super._updateError();
    this._updateMatch();
  }

  _restoreValue(val) {
    super._restoreValue(val);
    this._updateMatch();
  }

  _buildStrengthHTML() {
    return "";
  }

  _buildHTML() {
    const req = this._required ? " required" : "";
    const autocomplete = this._autocomplete
      ? ` autocomplete="${this._esc(this._autocomplete)}"`
      : "";
    const prefixIcon = this._showPrefixIcon ? `<i class="bi bi-key rp-prefix"></i>` : "";
    const eyeButton = this._showEyeIcon
      ? `<button type="button" class="rp-suffix rp-toggle-password" title="Show password">
           <i class="bi bi-eye"></i>
         </button>`
      : "";
    const inputClasses = ["rp-input"];
    if (this._showPrefixIcon) inputClasses.push("has-prefix");
    if (this._showEyeIcon) inputClasses.push("has-suffix");

    return `
      <div class="rp-field">
        ${this._labelHTML()}
        <div class="rp-input-affix">
          ${prefixIcon}
          <input
            class="${inputClasses.join(" ")}"
            type="password"
            id="${this._esc(this._fieldId)}-input"
            name="${this._esc(this._name)}"
            placeholder="${this._esc(this._placeholder)}"
            ${req}${autocomplete}
          />
          ${eyeButton}
        </div>
        <span data-rp-match hidden></span>
        ${this._errorHTML()}
        ${this._hintHTML()}
      </div>
    `;
  }

  _bindEvents() {
    super._bindEvents();

    const input = this.querySelector(".rp-input");
    const passwordInput = this._passwordInput;

    if (input) {
      input.addEventListener("input", () => this._updateMatch());
    }

    if (passwordInput) {
      passwordInput.addEventListener("input", () => {
        this._updateMatch();
        if (this._touched) this._updateError();
      });
    }
  }
}

customElements.define("confirm-password-field", ConfirmPasswordField);
