import { TextField } from "./text-field.js";

/* SecretField  <secret-field>
 *
 * Password-style input for sensitive values (API keys, tokens, credentials).
 * Renders an "Encrypted" badge next to the label to signal at-rest encryption.
 * Defaults: label "Secret", placeholder "Enter secret value".
 * See text-field.js and base-field.js for inherited attributes.
 *
 * Additional attributes:
 *   eye-icon    – boolean; adds a show/hide secret toggle button
 *   prefix-icon – boolean; adds a shield-lock icon (bi-shield-lock) to the left of the input
 *   required    – boolean (inherited); marks the field as required
 */
class SecretField extends TextField {
  connectedCallback() {
    if (!this.hasAttribute("label")) this.setAttribute("label", "Secret");
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "Enter secret value");
    this._showPassword = false;
    super.connectedCallback();
  }

  get _showEyeIcon() {
    return this.hasAttribute("eye-icon");
  }
  get _showPrefixIcon() {
    return this.hasAttribute("prefix-icon");
  }

  _labelHTML() {
    const req = this._required ? ' <span class="rp-req">*</span>' : "";
    const badge = `<span class="rp-badge rp-badge-soft rp-badge-warning"><i class="bi bi-lock-fill"></i> Encrypted</span>`;
    return `<label class="rp-label" for="${this._esc(this._fieldId)}-input">${this._esc(this._label)} ${badge}${req}</label>`;
  }

  _buildHTML() {
    const req = this._required ? " required" : "";
    const autocomplete = this._autocomplete
      ? ` autocomplete="${this._esc(this._autocomplete)}"`
      : "";
    const prefixIcon = this._showPrefixIcon ? `<i class="bi bi-shield-lock rp-prefix"></i>` : "";
    const eyeButton = this._showEyeIcon
      ? `<button type="button" class="rp-suffix rp-toggle-password" title="Show secret">
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

  _bindEvents() {
    super._bindEvents();
    const input = this.querySelector(".rp-input");
    const toggleBtn = this.querySelector(".rp-toggle-password");
    if (toggleBtn) {
      toggleBtn.addEventListener("click", () => {
        this._showPassword = !this._showPassword;
        if (input) input.type = this._showPassword ? "text" : "password";
        const icon = toggleBtn.querySelector("i");
        if (icon) icon.className = `bi ${this._showPassword ? "bi-eye-slash" : "bi-eye"}`;
        toggleBtn.title = this._showPassword ? "Hide secret" : "Show secret";
      });
    }
  }
}

customElements.define("secret-field", SecretField);
