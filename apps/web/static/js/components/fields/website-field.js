import { TextField } from "./text-field.js";

/* WebsiteField  <website-field>
 *
 * URL input with a configurable scheme selector (e.g. https://, http://). Defaults: label
 * "Website", placeholder "example.com". Scheme options are declared as children and parsed once
 * on connect. Smart paste automatically splits pasted full URLs into scheme + path.
 * See text-field.js and base-field.js for inherited attributes.
 *
 * Declarative children (captured before first render):
 *   <scheme-list>
 *     <scheme id="…" value="https://" [selected] [disabled]>Label</scheme>
 *   </scheme-list>
 *   Default scheme is "https://" when no <scheme-list> is provided.
 *
 * Additional attributes:
 *   accept-trailing-slash  – boolean; when absent, trailing slashes are stripped on blur
 *   prefix-icon            – boolean; adds a globe icon (bi-globe2) to the left of the scheme select
 *   open-button            – boolean; adds an external-link button that opens the current URL
 *                            in a new tab
 *
 * Public API:
 *   field.value      – getter/setter: full URL including scheme (e.g. "https://example.com")
 *   field.rawValue   – getter: path-only portion without scheme (e.g. "example.com")
 *   field.scheme     – getter: currently selected scheme string (e.g. "https://")
 *
 * Validation:
 *   - required: full URL must not be blank
 *   - value must be a parseable URL with a valid hostname (dotted domain, localhost, or IPv6)
 *   - paste error: shown when pasted scheme is not in the allowed scheme list
 */
class WebsiteField extends TextField {
  static get observedAttributes() {
    return [...super.observedAttributes, "accept-trailing-slash"];
  }

  get _autocomplete() {
    return this.getAttribute("autocomplete") || "url";
  }

  get _acceptTrailingSlash() {
    return this.hasAttribute("accept-trailing-slash");
  }

  connectedCallback() {
    if (this._initialSchemes === undefined) {
      this._initialSchemes = Array.from(this.querySelectorAll("scheme-list scheme"))
        .map((el) => ({
          id: el.getAttribute("id") || "",
          label: el.textContent.trim(),
          value: el.getAttribute("value") ?? el.textContent.trim(),
          selected: el.hasAttribute("selected"),
          disabled: el.hasAttribute("disabled"),
        }))
        .filter((s) => s.value);
    }
    if (this._pasteError === undefined) this._pasteError = "";

    if (!this.hasAttribute("label")) this.setAttribute("label", "Website");
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "example.com");

    super.connectedCallback();
  }

  get _schemes() {
    if (this._initialSchemes && this._initialSchemes.length) {
      return this._initialSchemes.map((s) => s.value);
    }

    return ["https://"];
  }

  get _scheme() {
    if (this.hasAttribute("scheme")) return this.getAttribute("scheme");
    const preselected = this._initialSchemes?.find((s) => s.selected);
    return preselected?.value ?? this._schemes[0] ?? "";
  }

  get _rawValue() {
    return this.querySelector(".rp-input")?.value ?? (this.getAttribute("value") || "");
  }

  get _value() {
    return this._fullUrl;
  }

  get _showPrefixIcon() {
    return this.hasAttribute("prefix-icon");
  }

  get _showOpenButton() {
    return this.hasAttribute("open-button");
  }

  get scheme() {
    return this._scheme;
  }

  get rawValue() {
    return this._rawValue;
  }

  get value() {
    return this._fullUrl;
  }

  set value(v) {
    const input = this.querySelector(".rp-input");
    const select = this.querySelector(".rp-scheme-select");
    if (!input) return;
    const match = this._schemes.find((s) => v.toLowerCase().startsWith(s.toLowerCase()));
    if (match) {
      if (select) {
        select.value = match;
        this.setAttribute("scheme", match);
      }
      input.value = v.slice(match.length);
    } else {
      input.value = v;
    }
  }

  get _fullUrl() {
    const value = this._rawValue.trim();

    if (!value) return "";

    return this._scheme + value;
  }

  get _validUrl() {
    if (!this._rawValue.trim()) return false;
    try {
      const url = new URL(this._fullUrl);
      const h = url.hostname;
      // Accept dotted hostnames (domains, IPv4), localhost, and IPv6 addresses.
      // Reject bare words like "notaurl" that have no dot and are not known local hosts.
      return h.includes(".") || h === "localhost" || h.startsWith("[");
    } catch {
      return false;
    }
  }

  _validate() {
    if (this._pasteError) return this._pasteError;
    const value = this._rawValue.trim();

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
    const current = this._scheme;
    return (this._initialSchemes || [])
      .map((s) => {
        const idAttr = s.id ? ` id="${this._esc(s.id)}"` : "";
        const selectedAttr = s.value === current ? " selected" : "";
        const disabledAttr = s.disabled ? " disabled" : "";
        return `<option${idAttr} value="${this._esc(s.value)}"${selectedAttr}${disabledAttr}>${this._esc(s.label)}</option>`;
      })
      .join("");
  }

  _buildHTML() {
    const maxlen = this._maxlength ? ` maxlength="${this._esc(this._maxlength)}"` : "";
    const req = this._required ? " required" : "";
    const autocomplete = this._autocomplete
      ? ` autocomplete="${this._esc(this._autocomplete)}"`
      : "";
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
            type="text"
            id="${this._esc(this._fieldId)}-input"
            name="${this._esc(this._name)}"
            placeholder="${this._esc(this._placeholder)}"
            value="${this._esc(this._rawValue)}"
            ${maxlen}
            ${req}
            ${autocomplete}
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
      if (!this._acceptTrailingSlash) {
        input.addEventListener("blur", () => {
          const stripped = input.value.replace(/\/+$/, "");
          if (input.value !== stripped) {
            input.value = stripped;
            if (this._touched) this._updateError();
          }
        });
      }

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

customElements.define("website-field", WebsiteField);
