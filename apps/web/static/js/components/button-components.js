/* ButtonPrimary: <rp-button-primary> */
class ButtonPrimary extends HTMLElement {
  static get observedAttributes() {
    return ["label", "prefix-icon", "suffix-icon", "disabled", "type"];
  }

  connectedCallback() {
    this._rendered = false;
    this._render();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this._rendered && oldVal !== newVal) this._render();
  }

  get _label() {
    return this.getAttribute("label") || "";
  }
  get _prefixIcon() {
    return this.getAttribute("prefix-icon") || "";
  }
  get _suffixIcon() {
    return this.getAttribute("suffix-icon") || "";
  }
  get _disabled() {
    return this.hasAttribute("disabled");
  }
  get _type() {
    return this.getAttribute("type") || "button";
  }
  get _variant() {
    return "rp-btn-primary";
  }

  _render() {
    const prefix = this._prefixIcon ? `<i class="bi ${this._esc(this._prefixIcon)}"></i>` : "";
    const suffix = this._suffixIcon ? `<i class="bi ${this._esc(this._suffixIcon)}"></i>` : "";
    const label = this._label ? this._esc(this._label) : "";
    this.innerHTML = `<button type="${this._esc(this._type)}" class="rp-btn ${this._variant}"${this._disabled ? " disabled" : ""}>${prefix}${label}${suffix}</button>`;
    this._rendered = true;
  }

  _esc(s) {
    return String(s || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
}

customElements.define("rp-button-primary", ButtonPrimary);

/* ButtonMuted: <rp-button-muted> */
class ButtonMuted extends ButtonPrimary {
  get _variant() {
    return "rp-btn-muted";
  }
}

customElements.define("rp-button-muted", ButtonMuted);

/* ButtonEngine: <rp-button-engine> */
class ButtonEngine extends ButtonPrimary {
  get _variant() {
    return "rp-btn-engine";
  }
}

customElements.define("rp-button-engine", ButtonEngine);
