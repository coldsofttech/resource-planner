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
 *   searchable   – when present, renders a combobox (text input + filtered dropdown list)
 *                  instead of a native <select>; supports keyboard navigation and filtering
 *
 * Validation:
 *   - required: an option with a non-empty value must be selected
 */
export class DropdownField extends BaseField {
  static get observedAttributes() {
    return [...super.observedAttributes, "placeholder", "searchable"];
  }

  get _placeholder() {
    return this.getAttribute("placeholder") || "";
  }
  get _autocomplete() {
    return this.getAttribute("autocomplete") || "off";
  }
  get _searchable() {
    return this.hasAttribute("searchable");
  }

  get _value() {
    if (this._searchable) return this._comboValue ?? "";
    return this.querySelector(".rp-input")?.value ?? (this.getAttribute("value") || "");
  }

  get value() {
    return this._value;
  }

  set value(v) {
    const normalized = v ?? "";
    if (this._searchable) {
      this._comboValue = normalized;
      this._comboLabel =
        this._options.find((o) => o.value === normalized)?.label ?? this._comboLabel ?? "";
      const input = this.querySelector(".rp-combobox-search");
      if (input) input.value = this._comboLabel;
    } else {
      const select = this.querySelector(".rp-input");
      if (select) select.value = normalized;
    }
    if (this.getAttribute("value") !== normalized) {
      this._silentAttrUpdate = true;
      this.setAttribute("value", normalized);
      this._silentAttrUpdate = false;
    }
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (name === "value" && this._silentAttrUpdate) return;
    // For searchable mode, handle value attribute changes without a full re-render.
    if (name === "value" && this._searchable && this._connected && oldVal !== newVal) {
      this._comboValue = newVal || "";
      const opt = this._options.find((o) => o.value === this._comboValue);
      this._comboLabel = opt?.label ?? this._comboLabel ?? "";
      const input = this.querySelector(".rp-combobox-search");
      if (input) input.value = this._comboLabel;
      return;
    }
    super.attributeChangedCallback(name, oldVal, newVal);
  }

  connectedCallback() {
    // Read declarative <values-list><value> children synchronously before
    // super.connectedCallback() → _doRender() replaces innerHTML.
    if (this._initialOptions === undefined) {
      this._initialOptions = Array.from(this.querySelectorAll("values-list value")).map((el) => ({
        id: el.getAttribute("id") || "",
        label: el.textContent.trim(),
        value: el.getAttribute("value") ?? el.textContent.trim(),
        selected: el.hasAttribute("selected"),
        disabled: el.hasAttribute("disabled"),
      }));
    }
    // Initialise combobox value state from the attribute before first render.
    if (this._searchable && this._comboValue === undefined) {
      this._comboValue = this.getAttribute("value") || "";
    }
    super.connectedCallback();
  }

  disconnectedCallback() {
    if (this._comboDocClick) {
      document.removeEventListener("click", this._comboDocClick);
      this._comboDocClick = null;
    }
  }

  get _options() {
    return this._initialOptions || [];
  }

  _savedValue() {
    if (this._searchable) return this._comboValue ?? null;
    return this.querySelector(".rp-input")?.value ?? null;
  }

  _restoreValue(val) {
    if (val === null) return;
    if (this._searchable) {
      this._comboValue = val;
      const opt = this._options.find((o) => o.value === val);
      if (opt) this._comboLabel = opt.label;
      const input = this.querySelector(".rp-combobox-search");
      if (input) input.value = this._comboLabel || "";
      return;
    }
    const input = this.querySelector(".rp-input");
    if (input) input.value = val;
  }

  _validate() {
    const val = this._searchable
      ? (this._comboValue ?? "")
      : (this.querySelector(".rp-input")?.value ?? "");
    if (this._required && !val) return "Please select an option.";
    return "";
  }

  // Returns the display label for the current comboValue, refreshing _comboLabel from options.
  _getComboDisplayLabel() {
    if (!(this._comboValue ?? "")) return "";
    const opt = this._options.find((o) => o.value === this._comboValue);
    if (opt) {
      this._comboLabel = opt.label;
      return opt.label;
    }
    return this._comboLabel || "";
  }

  // Returns the typed text inside the combobox input (searchable mode only).
  get inputText() {
    if (this._searchable) return this.querySelector(".rp-combobox-search")?.value?.trim() || "";
    return "";
  }

  _buildOptions() {
    const opts = [];
    const attrVal = this.getAttribute("value");
    // Suppress placeholder when an explicit empty-value option is already in the list
    // (e.g. "Not Set" injected by confidence-field / priority-field with not-set attribute).
    const hasExplicitEmpty = this._options.some((o) => o.value === "" && o.selected && !o.disabled);
    if (this._placeholder && !hasExplicitEmpty) {
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

  _buildComboItems(query) {
    const q = (query || "").toLowerCase();
    const filtered = q
      ? this._options.filter((o) => o.label.toLowerCase().includes(q))
      : this._options;
    if (!filtered.length) {
      return `<div class="rp-ms-empty">No options found</div>`;
    }
    return filtered
      .map((o) => {
        const isSel = o.value === this._comboValue;
        return `<div class="rp-ms-option${isSel ? " is-highlighted" : ""}" role="option" data-combo-val="${this._esc(o.value)}" data-combo-label="${this._esc(o.label)}">${this._esc(o.label)}</div>`;
      })
      .join("");
  }

  _buildHTML() {
    if (this._searchable) {
      const selectedLabel = this._getComboDisplayLabel();
      const placeholder = this._placeholder || "Search…";
      return `
        <div class="rp-field">
          ${this._labelHTML()}
          <div class="rp-combobox">
            <div class="rp-input-affix">
              <input
                type="text"
                class="rp-input has-suffix rp-combobox-search"
                id="${this._esc(this._fieldId)}-input"
                placeholder="${this._esc(placeholder)}"
                autocomplete="off"
                role="combobox"
                aria-expanded="false"
                aria-autocomplete="list"
                value="${this._esc(selectedLabel)}"
              >
              <span class="rp-suffix" aria-hidden="true"><i class="bi bi-chevron-expand"></i></span>
            </div>
            <div class="rp-ms-dropdown" role="listbox" hidden></div>
          </div>
          ${this._errorHTML()}
          ${this._hintHTML()}
        </div>
      `;
    }

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
    if (this._searchable) {
      this._bindComboEvents();
      return;
    }
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

  _bindComboEvents() {
    const input = this.querySelector(".rp-combobox-search");
    const dropdown = this.querySelector(".rp-ms-dropdown");
    if (!input || !dropdown) return;

    this._comboHighlightIdx = -1;

    // On focus: select all text so the user can immediately type a filter query.
    input.addEventListener("focus", () => {
      input.select();
      this._showComboDropdown(input.value);
    });

    // Typing filters the list and clears the current selection.
    input.addEventListener("input", () => {
      this._comboValue = "";
      this._comboLabel = "";
      this._showComboDropdown(input.value);
    });

    input.addEventListener("keydown", (e) => this._onComboKeydown(e));

    // On blur: close dropdown and restore the selected label (or clear if nothing selected).
    // Delay allows the mousedown on a dropdown option to fire first.
    input.addEventListener("blur", () => {
      setTimeout(() => this._doComboBlur(input), 160);
    });

    // Option selection via click (mousedown fires before blur).
    dropdown.addEventListener("mousedown", (e) => {
      e.preventDefault();
      const opt = e.target.closest(".rp-ms-option");
      if (!opt) return;
      this._selectComboOption(
        opt.getAttribute("data-combo-val"),
        opt.getAttribute("data-combo-label"),
        input,
        dropdown,
      );
    });

    // Close dropdown when clicking outside the component.
    if (this._comboDocClick) document.removeEventListener("click", this._comboDocClick);
    this._comboDocClick = (e) => {
      if (!this.contains(e.target)) this._closeComboDropdown();
    };
    document.addEventListener("click", this._comboDocClick);
  }

  _showComboDropdown(query) {
    const dropdown = this.querySelector(".rp-ms-dropdown");
    const input = this.querySelector(".rp-combobox-search");
    if (!dropdown || !input) return;
    dropdown.innerHTML = this._buildComboItems(query);
    dropdown.hidden = false;
    input.setAttribute("aria-expanded", "true");
    this._comboHighlightIdx = -1;
  }

  _closeComboDropdown() {
    const dropdown = this.querySelector(".rp-ms-dropdown");
    const input = this.querySelector(".rp-combobox-search");
    if (dropdown) dropdown.hidden = true;
    if (input) input.setAttribute("aria-expanded", "false");
    this._comboHighlightIdx = -1;
  }

  _selectComboOption(val, label, input, dropdown) {
    this._comboValue = val;
    this._comboLabel = label;
    if (input) input.value = label;
    this._closeComboDropdown();
    this._touched = true;
    this._updateError();
    if (this.getAttribute("value") !== val) {
      this._silentAttrUpdate = true;
      this.setAttribute("value", val);
      this._silentAttrUpdate = false;
    }
  }

  _onComboKeydown(e) {
    const dropdown = this.querySelector(".rp-ms-dropdown");
    const input = this.querySelector(".rp-combobox-search");
    if (!dropdown || dropdown.hidden) {
      if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        this._showComboDropdown(input?.value || "");
      }
      return;
    }
    const options = Array.from(dropdown.querySelectorAll(".rp-ms-option"));
    if (e.key === "Escape") {
      this._closeComboDropdown();
      if (input) input.value = this._comboLabel || "";
      return;
    }
    if (e.key === "ArrowDown") {
      e.preventDefault();
      this._comboHighlightIdx = Math.min(this._comboHighlightIdx + 1, options.length - 1);
      this._applyComboHighlight(options);
      return;
    }
    if (e.key === "ArrowUp") {
      e.preventDefault();
      this._comboHighlightIdx = Math.max(this._comboHighlightIdx - 1, 0);
      this._applyComboHighlight(options);
      return;
    }
    if (e.key === "Enter" && options.length && this._comboHighlightIdx >= 0) {
      e.preventDefault();
      const opt = options[this._comboHighlightIdx];
      if (opt) {
        this._selectComboOption(
          opt.getAttribute("data-combo-val"),
          opt.getAttribute("data-combo-label"),
          input,
          dropdown,
        );
      }
    }
  }

  _doComboBlur(input) {
    this._closeComboDropdown();
    input.value = this._comboLabel || "";
    this._touched = true;
    this._updateError();
  }

  _applyComboHighlight(options) {
    options.forEach((o, i) => {
      const active = i === this._comboHighlightIdx;
      o.classList.toggle("is-highlighted", active);
      if (active) o.scrollIntoView({ block: "nearest" });
    });
  }
}

customElements.define("dropdown-field", DropdownField);
