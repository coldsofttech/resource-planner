import { BaseField } from "./base-field.js";

/* OTPField  <otp-field>
 *
 * N-digit one-time-password input rendered as N individual single-character inputs.
 * Sequential focus advances automatically on digit entry; backspace moves focus back.
 * Paste handling distributes pasted digits across inputs starting from the focused position.
 * A hidden input aggregates the full code for form submission.
 * See base-field.js for inherited attributes and validation lifecycle.
 *
 * Additional attributes:
 *   digits  – number of digit inputs to render (default 6)
 *
 * Public API:
 *   field.value = "123456"  – setter: distributes digits across inputs and syncs hidden field
 *   field.value             – getter: returns the concatenated digit string
 *
 * Validation:
 *   - required (via `required` attribute): all digits must be filled
 */
class OTPField extends BaseField {
  static get observedAttributes() {
    return [...super.observedAttributes, "digits"];
  }

  get _digits() {
    return parseInt(this.getAttribute("digits") || "6", 10);
  }

  get _value() {
    return Array.from(this.querySelectorAll("[data-otp-digit]"))
      .map((i) => i.value)
      .join("");
  }

  // Explicitly re-declare the getter so the setter below does not shadow
  // BaseField's get value() → without this, defining only set value() here
  // would make otpEl.value return undefined on OTPField instances.
  get value() {
    return this._value;
  }

  set value(v) {
    const inputs = Array.from(this.querySelectorAll("[data-otp-digit]"));
    const chars = String(v || "")
      .replace(/\D/g, "")
      .slice(0, this._digits)
      .split("");
    inputs.forEach((inp, i) => {
      inp.value = chars[i] || "";
      inp.classList.toggle("is-filled", !!inp.value);
    });
    this._syncHidden();
  }

  _savedValue() {
    return this._value;
  }

  _restoreValue(val) {
    if (val === null) return;
    this.value = val;
  }

  _syncHidden() {
    const hidden = this.querySelector("[data-otp-hidden]");
    if (hidden) hidden.value = this._value;
  }

  _buildHTML() {
    const n = this._digits;
    const baseId = this._fieldId;
    const baseName = this._name;
    let digitInputs = "";
    for (let i = 0; i < n; i++) {
      const pos = i + 1;
      const digitId = baseId ? ` id="${this._esc(baseId)}-${pos}"` : "";
      const digitName = baseName ? ` name="${this._esc(baseName)}_${pos}"` : "";
      digitInputs += `<input
        class="rp-otp-digit"
        data-otp-digit
        type="text"
        inputmode="numeric"
        maxlength="1"${digitId}${digitName}
        ${i === 0 ? 'autocomplete="one-time-code"' : 'autocomplete="off"'}
        aria-label="Digit ${pos} of ${n}"
      />`;
    }
    return `
      <div class="rp-field">
        ${this._label ? this._labelHTML() : ""}
        <div class="rp-otp-inputs" data-otp-container role="group" aria-label="One-time password">
          ${digitInputs}
          <input type="hidden" data-otp-hidden name="${this._esc(baseName)}" />
        </div>
        ${this._errorHTML()}
        ${this._hintHTML()}
      </div>
    `;
  }

  _bindEvents() {
    const container = this.querySelector("[data-otp-container]");
    if (!container) return;
    const inputs = Array.from(container.querySelectorAll("[data-otp-digit]"));

    inputs.forEach((inp, idx) => {
      inp.addEventListener("input", () => {
        const val = inp.value.replace(/\D/g, "");
        inp.value = val ? val[0] : "";
        inp.classList.toggle("is-filled", !!inp.value);
        this._syncHidden();
        if (val && idx < inputs.length - 1) inputs[idx + 1].focus();
        if (this._touched) this._updateError();
      });

      inp.addEventListener("keydown", (e) => {
        if (e.key === "Backspace" && !inp.value && idx > 0) {
          inputs[idx - 1].focus();
        }
      });

      inp.addEventListener("paste", (e) => {
        e.preventDefault();
        const pasted = (e.clipboardData || window.clipboardData).getData("text").replace(/\D/g, "");
        const chars = pasted.slice(0, inputs.length - idx).split("");
        chars.forEach((ch, i) => {
          if (inputs[idx + i]) {
            inputs[idx + i].value = ch;
            inputs[idx + i].classList.toggle("is-filled", !!ch);
          }
        });
        this._syncHidden();
        const lastFilled = Math.min(idx + chars.length, inputs.length - 1);
        inputs[lastFilled].focus();
        if (this._touched) this._updateError();
      });

      inp.addEventListener("blur", () => {
        this._touched = true;
        this._updateError();
      });
    });
  }

  _validate() {
    if (this._required && this._value.length < this._digits) {
      return `Please enter the full ${this._digits}-digit code.`;
    }
    return "";
  }

  _updateError() {
    const err = this._validate();
    const errEl = this.querySelector("[data-rp-error]");
    const hidden = this.querySelector("[data-otp-hidden]");

    if (errEl) {
      errEl.textContent = err;
      errEl.hidden = !err;
    }
    if (hidden && typeof hidden.setCustomValidity === "function") {
      hidden.setCustomValidity(err);
    }
    this.querySelectorAll("[data-otp-digit]").forEach((inp) => {
      inp.classList.toggle("is-invalid", !!err);
    });
  }
}

customElements.define("otp-field", OTPField);
