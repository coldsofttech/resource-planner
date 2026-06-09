import { BaseField } from "./base-field.js";

/* MultiSelectField  <multi-select-field>
 *
 * Chip-based multi-value select field. Options are declared as children and parsed once on
 * connect. Pre-selected values are set via the `value` attribute (JSON array) or the
 * `selected` attribute on individual <value> children.
 * See base-field.js for inherited attributes and validation lifecycle.
 *
 * Declarative children (captured before first render):
 *   <values-list>
 *     <value id="…" [value="…"] [selected]>Label</value>
 *   </values-list>
 *
 * Additional attributes:
 *   placeholder  – input placeholder text
 *   max          – maximum number of chips (omit for unlimited)
 *   free-form    – boolean; when present, allows custom values not in the list (Enter to add)
 *
 * Public API:
 *   field.value           – getter: JSON array string of selected values e.g. '["a","b"]'
 *   field.value = v       – setter: accepts JSON array string or comma-separated string
 *   field.values          – getter: array of { id, label, value } chip objects
 *
 * Validation:
 *   required – at least one chip must be selected
 */
export class MultiSelectField extends BaseField {
  static get observedAttributes() {
    return [...super.observedAttributes, "placeholder", "max", "free-form"];
  }

  connectedCallback() {
    // Read declarative <values-list><value> children once before super replaces innerHTML.
    if (this._initialOptions === undefined) {
      this._initialOptions = Array.from(this.querySelectorAll("values-list value")).map((el) => ({
        id: el.getAttribute("id") || "",
        label: el.textContent.trim(),
        value: el.getAttribute("value") ?? el.textContent.trim(),
        selected: el.hasAttribute("selected"),
      }));
    }
    // Initialise selected chips from `value` attr (JSON/CSV) or `selected` on children.
    if (this._selectedValues === undefined) {
      const attrVal = this.getAttribute("value") || "";
      let preSelected = [];
      if (attrVal) {
        try {
          preSelected = JSON.parse(attrVal);
        } catch {
          preSelected = attrVal
            .split(",")
            .map((v) => v.trim())
            .filter(Boolean);
        }
      } else {
        preSelected = this._initialOptions.filter((o) => o.selected).map((o) => o.value);
      }
      this._selectedValues = this._initialOptions
        .filter((o) => preSelected.includes(o.value))
        .map((o) => ({ ...o }));
      if (this._freeForm) {
        preSelected.forEach((v) => {
          if (!this._selectedValues.find((s) => s.value === v)) {
            this._selectedValues.push({ id: "", label: v, value: v });
          }
        });
      }
    }
    this._highlightedIdx = -1;
    super.connectedCallback();
  }

  disconnectedCallback() {
    if (this._docClickHandler) {
      document.removeEventListener("click", this._docClickHandler);
      this._docClickHandler = null;
    }
  }

  // ── Attribute helpers ────────────────────────────────────────────────────

  get _placeholder() {
    return this.getAttribute("placeholder") || "";
  }
  get _max() {
    const v = parseInt(this.getAttribute("max") || "0", 10);
    return isNaN(v) || v <= 0 ? null : v;
  }
  get _freeForm() {
    return this.hasAttribute("free-form");
  }

  // ── Value API ────────────────────────────────────────────────────────────

  get _value() {
    const vals = (this._selectedValues || []).map((v) => v.value);
    return vals.length ? JSON.stringify(vals) : "";
  }

  get values() {
    return (this._selectedValues || []).map((v) => ({ ...v }));
  }

  set value(v) {
    let vals = [];
    if (Array.isArray(v)) {
      vals = v;
    } else if (typeof v === "string" && v) {
      if (v.startsWith("[")) {
        try {
          vals = JSON.parse(v);
        } catch {
          vals = [];
        }
      } else {
        vals = v
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean);
      }
    }
    this._selectedValues = vals.map((val) => {
      const opt = (this._initialOptions || []).find((o) => o.value === val);
      return opt ? { ...opt } : { id: "", label: val, value: val };
    });
    this._refreshChipsAndInput();
    if (this._touched) this._updateError();
  }

  // Intercept `value` attr changes so they update chip state instead of causing a full re-render.
  attributeChangedCallback(name, oldVal, newVal) {
    if (name === "value" && this._connected && oldVal !== newVal) {
      this.value = newVal || "";
    } else {
      super.attributeChangedCallback(name, oldVal, newVal);
    }
  }

  // No need to save/restore via the input element — _selectedValues is maintained in memory.
  _savedValue() {
    return null;
  }
  _restoreValue(_) {}

  // ── State helpers ────────────────────────────────────────────────────────

  _isAtMax() {
    return this._max !== null && (this._selectedValues || []).length >= this._max;
  }

  _options() {
    return this._initialOptions || [];
  }

  _unselected() {
    return this._options().filter((o) => !this._selectedValues.find((s) => s.value === o.value));
  }

  // ── Rendering ────────────────────────────────────────────────────────────

  _buildChipsHTML() {
    return (this._selectedValues || [])
      .map(
        (v, i) =>
          `<span class="rp-ms-chip" data-ms-idx="${i}">${this._esc(v.label)}<button type="button" data-ms-remove="${i}" aria-label="Remove ${this._esc(v.label)}">×</button></span>`,
      )
      .join("");
  }

  _buildHTML() {
    const inputAttrs = this._isAtMax() ? " hidden" : "";
    return `
      <div class="rp-field">
        ${this._labelHTML()}
        <div class="rp-multiselect" role="group" aria-label="${this._esc(this._label)}">
          ${this._buildChipsHTML()}
          <input
            class="rp-ms-input"
            type="text"
            id="${this._esc(this._fieldId)}-input"
            placeholder="${this._isAtMax() ? "" : this._esc(this._placeholder)}"
            autocomplete="off"
            aria-autocomplete="list"
            aria-expanded="false"${inputAttrs}
          />
          <div class="rp-ms-dropdown" role="listbox" hidden></div>
        </div>
        ${this._errorHTML()}
        ${this._hintHTML()}
      </div>
    `;
  }

  // ── Events ───────────────────────────────────────────────────────────────

  _bindEvents() {
    const ms = this.querySelector(".rp-multiselect");
    const input = this.querySelector(".rp-ms-input");
    const dropdown = this.querySelector(".rp-ms-dropdown");
    if (!ms || !input || !dropdown) return;

    // Prevent blur when clicking within the container (avoids flicker caused by blur → timer → close)
    ms.addEventListener("mousedown", (e) => {
      if (e.target !== input) e.preventDefault();
    });

    // Click on the container area (not chip buttons / options) → focus input
    ms.addEventListener("click", (e) => {
      if (!e.target.closest("[data-ms-remove]") && !e.target.closest(".rp-ms-option")) {
        input.focus();
      }
    });

    // Remove chip via × button (event delegation)
    ms.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-ms-remove]");
      if (!btn) return;
      this._removeChip(parseInt(btn.getAttribute("data-ms-remove"), 10));
    });

    // Input → filter dropdown
    input.addEventListener("input", () => this._updateDropdown());
    input.addEventListener("focus", () => this._updateDropdown());
    input.addEventListener("keydown", (e) => this._onKeydown(e));
    input.addEventListener("blur", () => {
      // Delay allows mousedown on dropdown options to fire first
      setTimeout(() => {
        this._closeDropdown();
        this._touched = true;
        this._updateError();
      }, 160);
    });

    // Dropdown option click (mousedown to fire before blur)
    dropdown.addEventListener("mousedown", (e) => {
      e.preventDefault();
      const opt = e.target.closest(".rp-ms-option");
      if (!opt) return;
      this._addChip({
        id: opt.getAttribute("data-ms-id") || "",
        label: opt.getAttribute("data-ms-label"),
        value: opt.getAttribute("data-ms-val"),
      });
    });

    // Outside click closes dropdown
    if (this._docClickHandler) document.removeEventListener("click", this._docClickHandler);
    this._docClickHandler = (e) => {
      if (!this.contains(e.target)) this._closeDropdown();
    };
    document.addEventListener("click", this._docClickHandler);
  }

  _onKeydown(e) {
    const input = this.querySelector(".rp-ms-input");
    const dropdown = this.querySelector(".rp-ms-dropdown");
    const options = dropdown ? Array.from(dropdown.querySelectorAll(".rp-ms-option")) : [];

    // Backspace on empty input removes the last chip
    if (e.key === "Backspace" && input.value === "" && (this._selectedValues || []).length) {
      this._removeChip(this._selectedValues.length - 1);
      return;
    }

    if (e.key === "Escape") {
      this._closeDropdown();
      return;
    }

    if (dropdown && !dropdown.hidden && options.length) {
      if (e.key === "ArrowDown") {
        e.preventDefault();
        this._highlightedIdx = Math.min(this._highlightedIdx + 1, options.length - 1);
        this._applyHighlight(options);
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        this._highlightedIdx = Math.max(this._highlightedIdx - 1, 0);
        this._applyHighlight(options);
        return;
      }
    }

    if (e.key === "Enter") {
      e.preventDefault();
      if (options.length && this._highlightedIdx >= 0 && options[this._highlightedIdx]) {
        const opt = options[this._highlightedIdx];
        this._addChip({
          id: opt.getAttribute("data-ms-id") || "",
          label: opt.getAttribute("data-ms-label"),
          value: opt.getAttribute("data-ms-val"),
        });
      } else if (this._freeForm && input.value.trim()) {
        const val = input.value.trim();
        this._addChip({ id: "", label: val, value: val });
      }
    }
  }

  _applyHighlight(options) {
    options.forEach((o, i) => {
      const active = i === this._highlightedIdx;
      o.classList.toggle("is-highlighted", active);
      if (active) o.scrollIntoView({ block: "nearest" });
    });
  }

  // ── Dropdown ─────────────────────────────────────────────────────────────

  _updateDropdown() {
    if (this._isAtMax()) {
      this._closeDropdown();
      return;
    }
    const input = this.querySelector(".rp-ms-input");
    const dropdown = this.querySelector(".rp-ms-dropdown");
    if (!input || !dropdown) return;

    const query = input.value.trim().toLowerCase();
    const unselected = this._unselected();
    const filtered = query
      ? unselected.filter((o) => o.label.toLowerCase().includes(query))
      : unselected;

    const items = filtered.map(
      (o) =>
        `<div class="rp-ms-option" role="option" data-ms-val="${this._esc(o.value)}" data-ms-label="${this._esc(o.label)}" data-ms-id="${this._esc(o.id)}">${this._esc(o.label)}</div>`,
    );

    // Free-form: offer to create if query doesn't exactly match an unselected option
    if (
      this._freeForm &&
      query &&
      !unselected.find((o) => o.value.toLowerCase() === query) &&
      !(this._selectedValues || []).find((s) => s.value.toLowerCase() === query)
    ) {
      items.unshift(
        `<div class="rp-ms-option rp-ms-option--create" role="option" data-ms-val="${this._esc(query)}" data-ms-label="${this._esc(query)}" data-ms-id="">Add &ldquo;${this._esc(query)}&rdquo;</div>`,
      );
    }

    if (!items.length) {
      dropdown.innerHTML = `<div class="rp-ms-empty">No options found</div>`;
      dropdown.hidden = false;
    } else {
      dropdown.innerHTML = items.join("");
      dropdown.hidden = false;
    }
    this._highlightedIdx = -1;

    const inp = this.querySelector(".rp-ms-input");
    if (inp) inp.setAttribute("aria-expanded", "true");
  }

  _closeDropdown() {
    const dropdown = this.querySelector(".rp-ms-dropdown");
    if (dropdown) dropdown.hidden = true;
    const input = this.querySelector(".rp-ms-input");
    if (input) input.setAttribute("aria-expanded", "false");
    this._highlightedIdx = -1;
  }

  // ── Chip mutations ───────────────────────────────────────────────────────

  _addChip(opt) {
    if (this._isAtMax()) return;
    if (!this._selectedValues) this._selectedValues = [];
    if (this._selectedValues.find((s) => s.value === opt.value)) return;
    this._selectedValues.push({ id: opt.id || "", label: opt.label, value: opt.value });
    const input = this.querySelector(".rp-ms-input");
    if (input) input.value = "";
    this._refreshChipsAndInput();
    this._closeDropdown();
    input?.focus();
    this._updateDropdown();
    if (this._touched) this._updateError();
  }

  _removeChip(idx) {
    if (!this._selectedValues || idx < 0 || idx >= this._selectedValues.length) return;
    this._selectedValues.splice(idx, 1);
    this._refreshChipsAndInput();
    this.querySelector(".rp-ms-input")?.focus();
    if (this._touched) this._updateError();
  }

  // Re-render only the chips and input state (no full innerHTML replace).
  _refreshChipsAndInput() {
    const ms = this.querySelector(".rp-multiselect");
    const input = ms?.querySelector(".rp-ms-input");
    if (!ms || !input) return;
    ms.querySelectorAll(".rp-ms-chip").forEach((c) => c.remove());
    input.insertAdjacentHTML("beforebegin", this._buildChipsHTML());
    const atMax = this._isAtMax();
    input.hidden = atMax;
    input.placeholder = atMax ? "" : this._placeholder;
  }

  // ── Validation ───────────────────────────────────────────────────────────

  _validate() {
    if (this._required && !(this._selectedValues || []).length) return "This field is required.";
    return "";
  }

  _updateError() {
    const err = this._validate();
    const errEl = this.querySelector("[data-rp-error]");
    const ms = this.querySelector(".rp-multiselect");
    if (errEl) {
      errEl.textContent = err;
      errEl.hidden = !err;
    }
    if (ms) ms.classList.toggle("is-invalid", !!err);
  }
}

customElements.define("multi-select-field", MultiSelectField);
