/* BaseField  (exported base class — not registered as a custom element)
 *
 * Foundation for all field components. Manages the render/re-render lifecycle, attribute
 * observation, touched state, hint content, error display, and custom validator registration.
 * Subclasses implement `_buildHTML()`, `_bindEvents()`, and `_validate()`.
 *
 * Declarative children (captured before first render):
 *   <field-hint>  – raw HTML hint content; takes precedence over the `hint` attribute
 *
 * Observed attributes (inherited by all subclasses):
 *   col           – Bootstrap column class applied to the host element (default "col-md-6")
 *   label         – field label text
 *   required      – boolean; marks the field as required and enforces non-empty validation
 *   id            – id applied to the host and used to generate the input id (`{id}-input`)
 *   name          – form field name; defaults to the `id` value
 *   hint          – plain-text hint shown below the field (use <field-hint> for rich HTML)
 *   hint-type     – icon/colour variant for the hint: "info" | "warning" | "success" | "danger"
 *                   (default "info")
 *   value         – initial value; overridden by live input value once connected
 *   autocomplete  – HTML autocomplete attribute forwarded to the input element
 *
 * Public API:
 *   field.value                           – getter: current input value
 *   field.value = v                       – setter: sets the input element's value
 *   field._customValidators               – array of { fn, msg } objects added by consumers
 *                                           for additional validation rules
 *
 * Validation:
 *   - Validation runs on `rp:validate` events bubbling from the nearest [data-wiz-panel] ancestor
 *     (or from the field itself) — triggered by the wizard on "next" attempts.
 *   - Fields in hidden panels are skipped.
 *   - Errors are displayed inline below the input once the field is "touched" (after blur or validate).
 *
 * Inheritance:
 *   BaseField → TextField → PasswordField → ConfirmPasswordField
 *   BaseField → TextField → SecretField
 *   BaseField → TextField → EmailField
 *   BaseField → TextField → WebsiteField
 *   BaseField → NumberField → DecimalField
 *   BaseField → OTPField
 */
import { esc } from "../utils.js";

export class BaseField extends HTMLElement {
  constructor() {
    super();
    this._touched = false;
    this._connected = false;
    this._hintContent = undefined; // undefined = not yet read; null = no <field-hint> found
    this._customValidators = [];
  }

  static get observedAttributes() {
    return [
      "col",
      "label",
      "required",
      "id",
      "name",
      "hint",
      "hint-type",
      "value",
      "autocomplete",
      "readonly",
    ];
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

  get value() {
    return this._value;
  }

  set value(v) {
    const input = this.querySelector(".rp-input");
    if (input) input.value = v;
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
    this.querySelectorAll("input, select, textarea").forEach((el) => {
      el.addEventListener("invalid", (e) => e.preventDefault());
    });
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
    return this.id || "";
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
  get _autocomplete() {
    return this.getAttribute("autocomplete") || "";
  }
  get _readonly() {
    return this.hasAttribute("readonly");
  }

  _buildHTML() {
    return "";
  }
  _bindEvents() {}
  _validate() {
    return "";
  }

  _runCustomValidators() {
    if (!this._customValidators.length) return "";
    const val = this._value;
    for (const { fn, msg } of this._customValidators) {
      if (val && !fn(val)) return msg;
    }
    return "";
  }

  _onValidate() {
    if (this.closest("[hidden]")) return;
    if (this._readonly) return;
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
    if (input) {
      input.classList.toggle("is-invalid", !!err);
      if (typeof input.setCustomValidity === "function") input.setCustomValidity(err);
    }
  }

  _labelHTML() {
    const req = this._required ? ' <span class="rp-req">*</span>' : "";
    return `<label class="rp-label" for="${this._esc(this._fieldId)}-input">${this._esc(this._label)}${req}</label>`;
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
    return esc(s);
  }
}
