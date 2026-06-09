import { BaseField } from "../fields/base-field.js";

/* DropdownField  <dropdown-field>
 *
 * Select/dropdown field. Options are declared as children and parsed once on connect.
 * The `value` attribute pre-selects the matching option; the `selected` attribute on an
 * <option-item> is the fallback when no `value` attribute is set. Exported for extension.
 * See base-field.js for inherited attributes and validation lifecycle.
 *
 * Declarative children (captured before first render):
 *   <values-list>
 *     <value id="…" value="…" [selected] [disabled]>Label</value>
 *   </values-list>
 *
 * Additional attributes:
 *   placeholder  – shown as the first disabled/hidden option prompting the user to select
 *
 * Validation:
 *   - required: an option with a non-empty value must be selected
 */
export class DropdownField extends BaseField {
  static get observedAttributes() {
    return [...super.observedAttributes, "placeholder"];
  }

  get _placeholder() {
    return this.getAttribute("placeholder") || "";
  }
  get _autocomplete() {
    return this.getAttribute("autocomplete") || "off";
  }
  get _value() {
    return this.querySelector(".rp-input")?.value ?? (this.getAttribute("value") || "");
  }

  get value() {
    return this._value;
  }

  set value(v) {
    const normalized = v ?? "";
    // Update the DOM select immediately (works when options are already rendered).
    const select = this.querySelector(".rp-input");
    if (select) select.value = normalized;
    // Also persist in the attribute so future _doRender() calls (e.g. after async
    // option fetch) pre-select the correct option via _buildOptions().
    // Use a silent flag to prevent attributeChangedCallback from triggering a
    // save/restore re-render cycle that would undo what we just set.
    if (this.getAttribute("value") !== normalized) {
      this._silentAttrUpdate = true;
      this.setAttribute("value", normalized);
      this._silentAttrUpdate = false;
    }
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (name === "value" && this._silentAttrUpdate) return;
    super.attributeChangedCallback(name, oldVal, newVal);
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
    // Use getAttribute directly: null means "attribute absent → honour o.selected (is_default)".
    // An explicit empty string means "no value chosen → don't pre-select any option".
    const attrVal = this.getAttribute("value");
    if (this._placeholder) {
      opts.push(
        `<option value="" disabled selected hidden>${this._esc(this._placeholder)}</option>`,
      );
    }
    opts.push(
      ...this._options.map((o) => {
        const isSelected = attrVal !== null ? o.value === attrVal : o.selected;
        const idAttr = o.id ? ` id="${this._esc(o.id)}"` : "";
        return `<option${idAttr} value="${this._esc(o.value)}"${isSelected ? " selected" : ""}${o.disabled ? " disabled" : ""}>${this._esc(o.label)}</option>`;
      }),
    );
    return opts.join("");
  }

  _buildHTML() {
    const req = this._required ? " required" : "";
    const autocomplete = this._autocomplete
      ? ` autocomplete="${this._esc(this._autocomplete)}"`
      : "";
    return `
      <div class="rp-field">
        ${this._labelHTML()}
        <select
          class="rp-input rp-select"
          id="${this._esc(this._fieldId)}-input"
          name="${this._esc(this._name)}"${req}${autocomplete}
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

customElements.define("dropdown-field", DropdownField);
