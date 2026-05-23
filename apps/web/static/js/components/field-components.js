class BaseField extends HTMLElement {
  constructor() {
    super();
    this._touched = false;
    this._connected = false;
    this._hintContent = undefined; // undefined = not yet read; null = no <field-hint> found
  }

  static get observedAttributes() {
    return ["col", "label", "required", "field-id", "name", "hint", "hint-type", "value"];
  }

  connectedCallback() {
    this._connected = true;
    // Read <field-hint> innerHTML once, before _doRender() destroys declarative children.
    // Guard with === undefined so re-connections (e.g. wizard moving the element) don't
    // overwrite the value that was captured on the first connect.
    if (this._hintContent === undefined) {
      const el = this.querySelector("field-hint");
      this._hintContent = el ? el.innerHTML.trim() : null;
    }
    this._doRender();
    const panel = this.closest("[data-wiz-panel]");
    (panel || this).addEventListener("rp:validate", () => this._onValidate());
  }

  attributeChangedCallback(name, oldVal, newVal) {
    // _connected guards against spurious calls during element upgrade: the browser
    // fires attributeChangedCallback for every pre-existing attribute before
    // connectedCallback, at which point innerHTML would destroy declarative children
    // (e.g. <scheme-list>) before connectedCallback has a chance to read them.
    if (this._connected && oldVal !== newVal) {
      const saved = this._savedValue();
      this._doRender();
      this._restoreValue(saved);
    }
  }

  _savedValue() {
    return this.querySelector(".rp-input")?.value ?? null;
  }

  _restoreValue(val) {
    if (val === null) return;
    const input = this.querySelector(".rp-input");
    if (input) input.value = val;
  }

  _doRender() {
    this.className = this._col;
    this.innerHTML = this._buildHTML();
    this._bindEvents();
    if (this._touched) this._updateError();
  }

  get _col() {
    return this.getAttribute("col") || "col-md-6";
  }
  get _label() {
    return this.getAttribute("label") || "";
  }
  get _required() {
    return this.hasAttribute("required");
  }
  get _fieldId() {
    return this.getAttribute("field-id") || "";
  }
  get _name() {
    return this.getAttribute("name") || this._fieldId;
  }
  get _hint() {
    return this.getAttribute("hint") || "";
  }
  get _hintType() {
    return this.getAttribute("hint-type") || "info";
  }

  _buildHTML() {
    return "";
  }
  _bindEvents() {}
  _validate() {
    return "";
  }

  _onValidate() {
    this._touched = true;
    this._updateError();
  }

  _updateError() {
    const err = this._validate();
    const errEl = this.querySelector("[data-rp-error]");
    const input = this.querySelector(".rp-input");
    if (errEl) {
      errEl.textContent = err;
      errEl.hidden = !err;
    }
    if (input) input.classList.toggle("is-invalid", !!err);
  }

  _labelHTML() {
    const req = this._required ? ' <span class="rp-req">*</span>' : "";
    return `<label class="rp-label" for="${this._esc(this._fieldId)}">${this._esc(this._label)}${req}</label>`;
  }

  _hintHTML() {
    // <field-hint> child (raw HTML) takes precedence over the hint="" attribute (escaped text).
    const content = this._hintContent ?? (this._hint ? this._esc(this._hint) : "");
    if (!content) return "";
    const TYPES = {
      info: ["bi-info-circle", "var(--rp-info)"],
      warning: ["bi-lightbulb", "var(--rp-warning-soft-text)"],
      success: ["bi-check-circle", "var(--rp-success-soft-text)"],
      danger: ["bi-exclamation-triangle", "var(--rp-danger-soft-text)"],
    };
    const [icon, color] = TYPES[this._hintType] ?? TYPES.info;
    return `<span class="rp-help"><i class="bi ${icon}" style="color:${color}"></i> ${content}</span>`;
  }

  _errorHTML() {
    return `<span class="rp-help is-error" data-rp-error hidden></span>`;
  }

  _esc(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
}

/* TextField: <field-text> */
class TextField extends BaseField {
  static get observedAttributes() {
    return [...super.observedAttributes, "placeholder", "maxlength"];
  }

  get _placeholder() {
    return this.getAttribute("placeholder") || "";
  }
  get _maxlength() {
    return this.getAttribute("maxlength") || "";
  }

  get _value() {
    return this.querySelector(".rp-input")?.value ?? (this.getAttribute("value") || "");
  }

  _validate() {
    if (this._required && !this._value.trim()) return "This field is required.";
    return "";
  }

  _buildHTML() {
    const maxlen = this._maxlength ? ` maxlength="${this._esc(this._maxlength)}"` : "";
    const req = this._required ? " required" : "";
    return `
      <div class="rp-field">
        ${this._labelHTML()}
        <input
          class="rp-input"
          type="text"
          id="${this._esc(this._fieldId)}"
          name="${this._esc(this._name)}"
          placeholder="${this._esc(this._placeholder)}"
          value="${this._esc(this._value)}"${maxlen}${req}
        />
        ${this._errorHTML()}
        ${this._hintHTML()}
      </div>
    `;
  }

  _bindEvents() {
    const input = this.querySelector(".rp-input");
    if (!input) return;
    input.addEventListener("blur", () => {
      this._touched = true;
      this._updateError();
    });
    input.addEventListener("input", () => {
      if (this._touched) this._updateError();
    });
  }
}

customElements.define("rp-field-text", TextField);

/* FirstNameField: <field-first-name> */
class FirstNameField extends TextField {
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

customElements.define("rp-field-first-name", FirstNameField);

/* LastNameField: <field-last-name> */
class LastNameField extends TextField {
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

customElements.define("rp-field-last-name", LastNameField);

/* EmailField: <field-email> */
class EmailField extends TextField {
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
            id="${this._esc(this._fieldId)}"
            name="${this._esc(this._name)}"
            placeholder="${this._esc(this._placeholder)}"
            value="${this._esc(this._value)}"
            ${maxlen}
            ${req}
          />
        </div>
        ${this._errorHTML()}
        ${this._hintHTML()}
      </div>
    `;
  }
}

customElements.define("rp-field-email", EmailField);

/* WebsiteField: <field-website> */
class WebsiteField extends TextField {
  connectedCallback() {
    if (this._initialSchemes === undefined) {
      this._initialSchemes = Array.from(this.querySelectorAll("scheme-list scheme"))
        .map((el) => el.textContent.trim())
        .filter(Boolean);
    }
    if (this._pasteError === undefined) this._pasteError = "";

    if (!this.hasAttribute("label")) this.setAttribute("label", "Website");
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "example.com");

    super.connectedCallback();
  }

  get _schemes() {
    if (this._initialSchemes && this._initialSchemes.length) {
      return this._initialSchemes;
    }

    return ["https://"];
  }

  get _scheme() {
    return this.getAttribute("scheme") || this._schemes[0];
  }

  get _showPrefixIcon() {
    return this.hasAttribute("prefix-icon");
  }

  get _showOpenButton() {
    return this.hasAttribute("open-button");
  }

  get _fullUrl() {
    const value = this._value.trim();

    if (!value) return "";

    return this._scheme + value;
  }

  get _validUrl() {
    if (!this._value.trim()) {
      return false;
    }

    try {
      new URL(this._fullUrl);

      return true;
    } catch {
      return false;
    }
  }

  _validate() {
    if (this._pasteError) return this._pasteError;
    const value = this._value.trim();

    if (this._required && !value) {
      return "Website is required.";
    }

    if (value && !this._validUrl) {
      return "Enter a valid URL.";
    }

    return "";
  }

  _openWebsite() {
    if (!this._fullUrl) return;

    window.open(this._fullUrl, "_blank", "noopener");
  }

  _buildSchemeOptions() {
    return this._schemes
      .map(
        (scheme) => `<option
            value="${this._esc(scheme)}"
            ${scheme === this._scheme ? "selected" : ""}>
            ${this._esc(scheme)}
          </option>`,
      )
      .join("");
  }

  _buildHTML() {
    const maxlen = this._maxlength ? ` maxlength="${this._esc(this._maxlength)}"` : "";
    const req = this._required ? " required" : "";
    const prefixIcon = this._showPrefixIcon ? `<i class="bi bi-globe2 rp-prefix"></i>` : "";
    const openButton = this._showOpenButton
      ? `<button
          type="button"
          class="rp-website-open"
          title="Open in new tab">
          <i class="bi bi-box-arrow-up-right"></i>
        </button>`
      : "";

    const inputClasses = ["rp-input"];
    if (this._showPrefixIcon) {
      inputClasses.push("has-prefix");
    }

    return `
      <div class="rp-field">
        ${this._labelHTML()}
        <div class="rp-website">
          <label class="rp-website-scheme">
            ${prefixIcon}
            <select
              class="rp-scheme-select"
              id="${this._esc(this._fieldId)}-scheme">
              ${this._buildSchemeOptions()}
            </select>
          </label>
          <input
            class="${inputClasses.join(" ")}"
            type="url"
            id="${this._esc(this._fieldId)}"
            name="${this._esc(this._name)}"
            placeholder="${this._esc(this._placeholder)}"
            value="${this._esc(this._value)}"
            ${maxlen}
            ${req}
          />
          ${openButton}
        </div>
        ${this._errorHTML()}
        ${this._hintHTML()}
      </div>
    `;
  }

  _bindEvents() {
    super._bindEvents();

    const input = this.querySelector(".rp-input");
    const select = this.querySelector(".rp-scheme-select");
    const openBtn = this.querySelector(".rp-website-open");

    if (select) {
      select.addEventListener("change", () => {
        this.setAttribute("scheme", select.value);
        if (this._touched) this._updateError();
      });
    }

    if (openBtn) {
      openBtn.addEventListener("click", () => this._openWebsite());
    }

    if (input) {
      input.addEventListener("input", () => {
        if (this._pasteError) {
          this._pasteError = "";
          this._updateError();
        }
      });

      input.addEventListener("paste", (e) => {
        const raw = (e.clipboardData || window.clipboardData).getData("text").trim();

        // Only intercept if the pasted text starts with a scheme (e.g. https://)
        const schemeMatch = raw.match(/^([a-zA-Z][a-zA-Z0-9+\-.]*:\/\/)/);
        if (!schemeMatch) return;

        e.preventDefault();
        this._pasteError = "";

        const pastedScheme = schemeMatch[1].toLowerCase();
        const rest = raw.slice(schemeMatch[1].length);

        const matched = this._schemes.find((s) => s.toLowerCase() === pastedScheme);

        if (matched) {
          if (select) {
            select.value = matched;
            this.setAttribute("scheme", matched);
          }
          input.value = rest;
        } else {
          input.value = rest;
          this._pasteError = `"${pastedScheme}" is not supported. Accepted: ${this._schemes.join(", ")}`;
        }

        this._touched = true;
        this._updateError();
      });
    }
  }
}

customElements.define("rp-field-website", WebsiteField);

/* PasswordField: <field-password> */
class PasswordField extends TextField {
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
            id="${this._esc(this._fieldId)}"
            name="${this._esc(this._name)}"
            placeholder="${this._esc(this._placeholder)}"
            ${req}
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

customElements.define("rp-field-password", PasswordField);

/* ConfirmPasswordField: <field-confirm-password> */
class ConfirmPasswordField extends PasswordField {
  connectedCallback() {
    if (!this.hasAttribute("label")) this.setAttribute("label", "Confirm password");
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "Confirm password");
    if (!this.hasAttribute("required")) this.setAttribute("required", "");
    super.connectedCallback();
  }

  get _passwordFieldId() {
    return this.getAttribute("password-field-id") || "";
  }

  // password-field-id is the field-id value of <field-password>, which becomes
  // the id on that element's inner <input> — so getElementById gives us the input directly
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
    return "";
  }

  _updateMatch() {
    const el = this.querySelector("[data-rp-match]");
    if (!el) return;
    const val = this._value;
    if (!val) {
      el.hidden = true;
      return;
    }
    if (this._matches) {
      el.hidden = false;
      el.className = "rp-help";
      el.innerHTML = `<i class="bi bi-check2-circle" style="color: var(--rp-success-soft-text)"></i> Matches.`;
    } else if (this._touched) {
      el.hidden = false;
      el.className = "rp-help is-error";
      el.innerHTML = `<i class="bi bi-x-circle"></i> Passwords do not match.`;
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
            id="${this._esc(this._fieldId)}"
            name="${this._esc(this._name)}"
            placeholder="${this._esc(this._placeholder)}"
            ${req}
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

customElements.define("rp-field-confirm-password", ConfirmPasswordField);

/* SecretField: <rp-field-secret> */
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
    return `<label class="rp-label" for="${this._esc(this._fieldId)}">${this._esc(this._label)} ${badge}${req}</label>`;
  }

  _buildHTML() {
    const req = this._required ? " required" : "";
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
            id="${this._esc(this._fieldId)}"
            name="${this._esc(this._name)}"
            placeholder="${this._esc(this._placeholder)}"
            ${req}
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

customElements.define("rp-field-secret", SecretField);

/* DropdownField: <rp-field-dropdown> */
class DropdownField extends BaseField {
  static get observedAttributes() {
    return [...super.observedAttributes, "placeholder"];
  }

  get _placeholder() {
    return this.getAttribute("placeholder") || "";
  }
  get _value() {
    return this.getAttribute("value") || "";
  }

  connectedCallback() {
    // Read declarative <values-list><value> children synchronously before
    // super.connectedCallback() → _doRender() replaces innerHTML.
    // Guard with === undefined so re-connections (e.g. wizard moving the element)
    // don't overwrite the options captured on the first connect.
    if (this._initialOptions === undefined) {
      this._initialOptions = Array.from(this.querySelectorAll("values-list value")).map((el) => ({
        id: el.getAttribute("id") || "",
        label: el.textContent.trim(),
        value: el.getAttribute("value") ?? el.textContent.trim(),
        selected: el.hasAttribute("selected"),
        disabled: el.hasAttribute("disabled"),
      }));
    }
    super.connectedCallback();
  }

  get _options() {
    return this._initialOptions || [];
  }

  _validate() {
    const val = this.querySelector(".rp-input")?.value ?? "";
    if (this._required && !val) return "Please select an option.";
    return "";
  }

  _buildOptions() {
    const opts = [];
    const attrVal = this._value;
    if (this._placeholder) {
      opts.push(
        `<option value="" disabled selected hidden>${this._esc(this._placeholder)}</option>`,
      );
    }
    opts.push(
      ...this._options.map((o) => {
        const isSelected = attrVal ? o.value === attrVal : o.selected;
        const idAttr = o.id ? ` id="${this._esc(o.id)}"` : "";
        return `<option${idAttr} value="${this._esc(o.value)}"${isSelected ? " selected" : ""}${o.disabled ? " disabled" : ""}>${this._esc(o.label)}</option>`;
      }),
    );
    return opts.join("");
  }

  _buildHTML() {
    const req = this._required ? " required" : "";
    return `
      <div class="rp-field">
        ${this._labelHTML()}
        <select
          class="rp-input rp-select"
          id="${this._esc(this._fieldId)}"
          name="${this._esc(this._name)}"${req}
        >
          ${this._buildOptions()}
        </select>
        ${this._errorHTML()}
        ${this._hintHTML()}
      </div>
    `;
  }

  _bindEvents() {
    const select = this.querySelector(".rp-input");
    if (!select) return;
    select.addEventListener("change", () => {
      this._touched = true;
      this._updateError();
    });
    select.addEventListener("blur", () => {
      this._touched = true;
      this._updateError();
    });
  }
}

customElements.define("rp-field-dropdown", DropdownField);

/* NumberField: <rp-field-number> */
class NumberField extends BaseField {
  static get observedAttributes() {
    return [...super.observedAttributes, "placeholder", "min", "max", "step"];
  }

  get _placeholder() {
    return this.getAttribute("placeholder") || "";
  }
  get _min() {
    return this.getAttribute("min") || "";
  }
  get _max() {
    return this.getAttribute("max") || "";
  }
  get _step() {
    return this.getAttribute("step") || "1";
  }

  get _value() {
    return this.querySelector(".rp-input")?.value ?? (this.getAttribute("value") || "");
  }

  _validate() {
    const raw = this._value;
    if (this._required && raw === "") return "This field is required.";
    const num = Number(raw);
    if (raw !== "" && isNaN(num)) return "Enter a valid number.";
    if (raw !== "" && this._min !== "" && num < Number(this._min))
      return `Value must be at least ${this._min}.`;
    if (raw !== "" && this._max !== "" && num > Number(this._max))
      return `Value must be at most ${this._max}.`;
    return "";
  }

  _buildHTML() {
    const req = this._required ? " required" : "";
    const min = this._min !== "" ? ` min="${this._esc(this._min)}"` : "";
    const max = this._max !== "" ? ` max="${this._esc(this._max)}"` : "";
    const step = ` step="${this._esc(this._step)}"`;
    return `
      <div class="rp-field">
        ${this._labelHTML()}
        <input
          class="rp-input"
          type="number"
          id="${this._esc(this._fieldId)}"
          name="${this._esc(this._name)}"
          placeholder="${this._esc(this._placeholder)}"
          value="${this._esc(this._value)}"${min}${max}${step}${req}
        />
        ${this._errorHTML()}
        ${this._hintHTML()}
      </div>
    `;
  }

  _bindEvents() {
    const input = this.querySelector(".rp-input");
    if (!input) return;
    input.addEventListener("blur", () => {
      this._touched = true;
      this._updateError();
    });
    input.addEventListener("input", () => {
      if (this._touched) this._updateError();
    });
  }
}

customElements.define("rp-field-number", NumberField);

/* DecimalField: <rp-field-decimal> */
class DecimalField extends NumberField {
  get _step() {
    return this.getAttribute("step") || "0.1";
  }
}

customElements.define("rp-field-decimal", DecimalField);

/* ChoiceField */
class ChoiceField extends BaseField {
  static get observedAttributes() {
    return [...super.observedAttributes, "checked", "disabled"];
  }

  get _type() {
    return "checkbox";
  }
  get _inputClass() {
    return "rp-check";
  }
  get _value() {
    return this.getAttribute("value") || "on";
  }
  get _checked() {
    return this.hasAttribute("checked");
  }
  get _disabled() {
    return this.hasAttribute("disabled");
  }

  _savedValue() {
    return this.querySelector(`.${this._inputClass}`)?.checked ?? null;
  }
  _restoreValue(val) {
    if (val === null) return;
    const input = this.querySelector(`.${this._inputClass}`);
    if (input) input.checked = val;
  }

  _validate() {
    if (this._required && !this.querySelector(`.${this._inputClass}`)?.checked) {
      return "This field is required.";
    }
    return "";
  }

  _updateError() {
    const err = this._validate();
    const errEl = this.querySelector("[data-rp-error]");
    if (errEl) {
      errEl.textContent = err;
      errEl.hidden = !err;
    }
  }

  _buildHTML() {
    return `
      <label class="rp-field-row">
        <input
          type="${this._type}"
          class="${this._inputClass}"
          ${this._fieldId ? `id="${this._esc(this._fieldId)}"` : ""}
          name="${this._esc(this._name)}"
          value="${this._esc(this._value)}"
          ${this._checked ? "checked" : ""}
          ${this._disabled ? "disabled" : ""}
        />
        <span>${this._esc(this._label)}</span>
      </label>
      ${this._errorHTML()}
      ${this._hintHTML()}`;
  }

  _bindEvents() {
    const input = this.querySelector(`.${this._inputClass}`);
    if (!input) return;
    input.addEventListener("change", () => {
      this._touched = true;
      this._updateError();
    });
  }
}

/* ChoiceGroupField */
class ChoiceGroupField extends BaseField {
  connectedCallback() {
    // Read <rp-option> children synchronously before super → _doRender() replaces innerHTML.
    // Guard so re-connections (wizard move) don't overwrite the captured options.
    if (this._initialOptions === undefined) {
      this._initialOptions = Array.from(this.querySelectorAll("rp-option")).map((el) => ({
        label: el.getAttribute("label") || el.textContent.trim(),
        value: el.getAttribute("value") ?? "",
        checked: el.hasAttribute("checked"),
        disabled: el.hasAttribute("disabled"),
      }));
    }
    super.connectedCallback();
  }

  get _type() {
    return "checkbox";
  }
  get _inputClass() {
    return "rp-check";
  }
  get _options() {
    return this._initialOptions || [];
  }
  get _value() {
    return this.getAttribute("value") || "";
  }

  _isOptionChecked(o) {
    const val = this._value;
    if (!val) return o.checked;
    return val
      .split(",")
      .map((v) => v.trim())
      .includes(o.value);
  }

  _labelHTML() {
    const req = this._required ? ' <span class="rp-req">*</span>' : "";
    return this._label ? `<div class="rp-label">${this._esc(this._label)}${req}</div>` : "";
  }

  _savedValue() {
    return Array.from(this.querySelectorAll(`.${this._inputClass}`)).map((cb) => ({
      value: cb.value,
      checked: cb.checked,
    }));
  }
  _restoreValue(val) {
    if (!val) return;
    const inputs = Array.from(this.querySelectorAll(`.${this._inputClass}`));
    val.forEach(({ value, checked }) => {
      const inp = inputs.find((cb) => cb.value === value);
      if (inp) inp.checked = checked;
    });
  }

  _validate() {
    if (this._required) {
      const anyChecked = Array.from(this.querySelectorAll(`.${this._inputClass}`)).some(
        (cb) => cb.checked,
      );
      if (!anyChecked) return "Please select at least one option.";
    }
    return "";
  }

  _updateError() {
    const err = this._validate();
    const errEl = this.querySelector("[data-rp-error]");
    if (errEl) {
      errEl.textContent = err;
      errEl.hidden = !err;
    }
  }

  _buildHTML() {
    const name = this._esc(this._name || this._fieldId);
    const { _type: type, _inputClass: cls } = this;
    const itemsHTML = this._options
      .map(
        (o) => `
        <label class="rp-field-row mb-2">
          <input
            type="${type}"
            class="${cls}"
            name="${name}"
            value="${this._esc(o.value)}"
            ${this._isOptionChecked(o) ? "checked" : ""}
            ${o.disabled ? "disabled" : ""}
          />
          <span>${this._esc(o.label)}</span>
        </label>`,
      )
      .join("");
    return `
      <div class="rp-field">
        ${this._labelHTML()}
        ${itemsHTML}
        ${this._errorHTML()}
        ${this._hintHTML()}
      </div>`;
  }

  _bindEvents() {
    this.querySelectorAll(`.${this._inputClass}`).forEach((input) => {
      input.addEventListener("change", () => {
        this._touched = true;
        this._updateError();
      });
    });
  }
}

/* CheckboxField: <rp-field-checkbox> */
class CheckboxField extends ChoiceField {}

customElements.define("rp-field-checkbox", CheckboxField);

/* CheckboxGroupField: <rp-field-checkbox-group> */
class CheckboxGroupField extends ChoiceGroupField {}

customElements.define("rp-field-checkbox-group", CheckboxGroupField);

/* RadioField: <rp-field-radio> */
class RadioField extends ChoiceField {
  get _type() {
    return "radio";
  }
}

customElements.define("rp-field-radio", RadioField);

/* RadioGroupField: <rp-field-radio-group> */
class RadioGroupField extends ChoiceGroupField {
  get _type() {
    return "radio";
  }

  _isOptionChecked(o) {
    const val = this._value;
    return val ? o.value === val : o.checked;
  }

  _savedValue() {
    return this.querySelector(`.${this._inputClass}:checked`)?.value ?? null;
  }
  _restoreValue(val) {
    if (val === null) return;
    this.querySelectorAll(`.${this._inputClass}`).forEach((r) => {
      r.checked = r.value === val;
    });
  }
  _validate() {
    if (this._required && !this.querySelector(`.${this._inputClass}:checked`)) {
      return "Please select an option.";
    }
    return "";
  }
}

customElements.define("rp-field-radio-group", RadioGroupField);

/* ToggleField: <rp-field-toggle> */
class ToggleField extends ChoiceField {
  get _inputClass() {
    return "rp-toggle";
  }
}

customElements.define("rp-field-toggle", ToggleField);

/* ToggleGroupField: <rp-field-toggle-group> */
class ToggleGroupField extends ChoiceGroupField {
  get _inputClass() {
    return "rp-toggle";
  }
}

customElements.define("rp-field-toggle-group", ToggleGroupField);

/* HintField: <rp-field-hint> */
class HintField extends HTMLElement {
  static get observedAttributes() {
    return ["type", "col", "title"];
  }

  connectedCallback() {
    if (this._content === undefined) {
      this._content = this.innerHTML.trim();
    }
    this._render();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this._content !== undefined && oldVal !== newVal) this._render();
  }

  get _type() {
    return this.getAttribute("type") || "info";
  }
  get _col() {
    return this.getAttribute("col") || "col-12";
  }
  get _title() {
    return this.getAttribute("title") || "";
  }

  _render() {
    const TYPES = {
      info: ["bi-info-circle", "rp-hint-info"],
      warning: ["bi-lightbulb", "rp-hint-warning"],
      success: ["bi-check-circle", "rp-hint-success"],
      danger: ["bi-exclamation-triangle", "rp-hint-danger"],
    };
    const [icon, cls] = TYPES[this._type] ?? TYPES.info;
    this.className = this._col;
    const titleHTML = this._title
      ? `<div class="rp-hint-title">${this._esc(this._title)}</div>`
      : "";
    this.innerHTML = `<div class="rp-hint ${cls}"><i class="bi ${icon}"></i><div>${titleHTML}${this._content}</div></div>`;
  }

  _esc(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
}

customElements.define("rp-field-hint", HintField);

/* OptionField: <rp-option> data-container for group items */
class OptionField extends HTMLElement {}

customElements.define("rp-option", OptionField);
