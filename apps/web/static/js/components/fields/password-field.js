import { TextField } from "./text-field.js";

/* PasswordField  <password-field>
 *
 * Password input with optional eye-icon toggle, prefix icon, and strength indicator.
 * Defaults: label "Password", placeholder "Enter password", required.
 * Exported for extension (e.g. ConfirmPasswordField, SecretField).
 * See base-field.js and text-field.js for inherited attributes.
 *
 * Additional attributes:
 *   eye-icon   – boolean; when present, adds a show/hide password toggle button
 *   prefix-icon – boolean; when present, adds a key icon (bi-key) to the left of the input
 *   strength   – boolean; when present, enables the 4-segment strength meter and enforces
 *                strong-password validation (12+ chars, upper, lower, digit, symbol)
 *
 * Public API:
 *   field.strength  – getter: current strength score 0–4 (derived from live value)
 *
 * Validation (when `strength` attribute is present):
 *   - minimum 12 characters
 *   - at least one uppercase letter
 *   - at least one lowercase letter
 *   - at least one digit
 *   - at least one symbol
 */
export class PasswordField extends TextField {
  get _autocomplete() {
    return this.getAttribute("autocomplete") || "new-password";
  }

  connectedCallback() {
    if (!this.hasAttribute("label")) this.setAttribute("label", "Password");
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "Enter password");
    if (!this.hasAttribute("required")) this.setAttribute("required", "");
    this._showPassword = false;
    super.connectedCallback();
  }

  get strength() {
    return this._strength;
  }

  get _showEyeIcon() {
    return this.hasAttribute("eye-icon");
  }
  get _showPrefixIcon() {
    return this.hasAttribute("prefix-icon");
  }
  get _showStrength() {
    return this.hasAttribute("strength");
  }

  get _strength() {
    const v = this._value;
    let s = 0;
    if (v.length >= 12) s++;
    if (/[A-Z]/.test(v) && /[a-z]/.test(v)) s++;
    if (/\d/.test(v)) s++;
    if (/[^A-Za-z0-9]/.test(v)) s++;
    return s;
  }

  get _strengthClass() {
    return ["", "d", "w", "f", "s"][this._strength] || "";
  }

  get _strengthLabel() {
    return (
      { 1: "Weak", 2: "Fair", 3: "Good", 4: "Strong · 12+ chars, mixed case, number, symbol." }[
        this._strength
      ] || ""
    );
  }

  _validate() {
    if (this._required && !this._value.trim()) return "Password is required.";
    if (this._showStrength && this._value) {
      const v = this._value;
      if (v.length < 12) return "Password must be at least 12 characters.";
      if (!/[A-Z]/.test(v)) return "Must contain at least one uppercase letter.";
      if (!/[a-z]/.test(v)) return "Must contain at least one lowercase letter.";
      if (!/\d/.test(v)) return "Must contain at least one number.";
      if (!/[^A-Za-z0-9]/.test(v)) return "Must contain at least one symbol.";
    }
    return "";
  }

  _updateStrength() {
    const segments = this.querySelectorAll(".rp-progress-segmented span");
    const label = this.querySelector("[data-rp-strength-label]");
    const score = this._strength;
    const cls = this._strengthClass;
    segments.forEach((seg, i) => {
      seg.className = score >= i + 1 ? cls : "";
    });
    if (label) {
      label.textContent = this._value ? this._strengthLabel : "";
      label.hidden = !this._value;
    }
  }

  _buildStrengthHTML() {
    if (!this._showStrength) return "";
    return `
      <div>
        <div class="rp-progress-segmented mt-2" style="height: 4px">
          <span></span><span></span><span></span><span></span>
        </div>
        <span class="rp-help" data-rp-strength-label hidden></span>
      </div>
    `;
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
        ${this._buildStrengthHTML()}
        ${this._errorHTML()}
        ${this._hintHTML()}
      </div>
    `;
  }

  _doRender() {
    super._doRender();
    if (this._showPassword) {
      const input = this.querySelector(".rp-input");
      if (input) input.type = "text";
    }
  }

  _restoreValue(val) {
    super._restoreValue(val);
    if (this._showStrength) this._updateStrength();
  }

  _bindEvents() {
    super._bindEvents();

    const input = this.querySelector(".rp-input");
    const toggleBtn = this.querySelector(".rp-toggle-password");

    if (input && this._showStrength) {
      input.addEventListener("input", () => this._updateStrength());
    }

    if (toggleBtn) {
      toggleBtn.addEventListener("click", () => {
        this._showPassword = !this._showPassword;
        if (input) input.type = this._showPassword ? "text" : "password";
        const icon = toggleBtn.querySelector("i");
        if (icon) icon.className = `bi ${this._showPassword ? "bi-eye-slash" : "bi-eye"}`;
        toggleBtn.title = this._showPassword ? "Hide password" : "Show password";
      });
    }
  }
}

customElements.define("password-field", PasswordField);
