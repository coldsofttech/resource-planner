import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* WinsWeekField  <wins-week-field>
 *
 * Dropdown (or chip-based multi-select) field pre-wired to the Weekly Wins
 * options API. Weeks are fetched from GET /api/v1/wins/options/ on first
 * connect. Inherits all attributes and public API from DropdownField / BaseField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Week"
 *   placeholder → "Select week…"
 *
 * Attributes:
 *   show-label   – when present, renders "Week" as the visible field label.
 *   multi-select – when present, renders as a chip-based multi-select instead of a
 *                  dropdown. value getter returns a JSON array string; setter accepts
 *                  a JSON array string, comma-separated string, or Array.
 *
 * Usage (single-select):
 *   <wins-week-field id="win-week" required col="col-md-6"></wins-week-field>
 *
 * Usage (multi-select):
 *   <wins-week-field id="monthly-win-weeks" multi-select required col="col-12" show-label></wins-week-field>
 *
 * Reading the multi-select value in JS:
 *   JSON.parse(field.value)  // → ["WIN-3", "WIN-4"]
 *   field.values             // → [{id, label, value}, …]
 */
class WinsWeekField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label", "multi-select"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Week";
    return super._label;
  }

  get _isMultiSelect() {
    return this.hasAttribute("multi-select");
  }

  get _value() {
    if (this._isMultiSelect) {
      const vals = (this._selectedValues || []).map((v) => v.value);
      return vals.length ? JSON.stringify(vals) : "";
    }
    return super._value;
  }

  get value() {
    return this._value;
  }

  // Returns selected chip objects — only meaningful in multi-select mode.
  get values() {
    return this._isMultiSelect ? (this._selectedValues || []).map((v) => ({ ...v })) : [];
  }

  set value(v) {
    if (this._isMultiSelect) {
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
    } else {
      super.value = v;
    }
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this._isMultiSelect && name === "value" && this._connected && oldVal !== newVal) {
      this.value = newVal || "";
    } else {
      super.attributeChangedCallback(name, oldVal, newVal);
    }
  }

  // In multi-select mode _selectedValues are maintained in memory — no DOM value to save/restore.
  _savedValue() {
    if (this._isMultiSelect) return null;
    return super._savedValue();
  }

  _restoreValue(val) {
    if (this._isMultiSelect) return;
    super._restoreValue(val);
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "Select week…");

    const firstConnect = this._initialOptions === undefined;

    if (firstConnect) {
      this._initialOptions = [];
      this._loadId = Symbol();

      if (this._isMultiSelect) {
        const pending = this._parseValueCodes(this.getAttribute("value") || "");
        this._selectedValues = pending.map((code) => ({ id: code, label: code, value: code }));
        this._highlightedIdx = -1;
      }
    }

    super.connectedCallback();

    if (firstConnect) {
      if (this._isMultiSelect) {
        this._setLoadingState(true);
      } else {
        const select = this.querySelector(".rp-input");
        if (select) select.disabled = true;
      }
      this._fetchOptions(this._loadId);
    } else if (!this._isMultiSelect && this._weekOptions === undefined) {
      this._loadId = Symbol();
      const select = this.querySelector(".rp-input");
      if (select) select.disabled = true;
      this._fetchOptions(this._loadId);
    }
  }

  disconnectedCallback() {
    this._loadId = Symbol();
    if (this._isMultiSelect && this._docClickHandler) {
      document.removeEventListener("click", this._docClickHandler);
      this._docClickHandler = null;
    }
  }

  async _fetchOptions(id) {
    try {
      const { href, method } = API_URLS.wins.options();
      const res = await apiFetch(href, { method });
      if (this._loadId !== id) return;

      const weeks = res?.data ?? [];

      if (this._isMultiSelect) {
        this._initialOptions = weeks.map((w) => ({
          id: w.code,
          label: w.name,
          value: w.code,
          selected: false,
          disabled: false,
        }));

        if (this._selectedValues && this._selectedValues.length > 0) {
          this._selectedValues = this._selectedValues.map((sv) => {
            const opt = this._initialOptions.find((o) => o.value === sv.value);
            return opt ? { ...opt } : sv;
          });
          this._refreshChipsAndInput();
        }

        const dropdown = this.querySelector(".rp-ms-dropdown");
        if (dropdown && !dropdown.hidden) this._updateDropdown();
      } else {
        this._weekOptions = weeks.map((w) => ({
          id: w.code,
          label: w.name,
          value: w.code,
          selected: false,
          disabled: false,
        }));
        this._initialOptions = this._weekOptions;
        this._doRender();
      }
    } catch {
      if (this._loadId !== id) return;
      this._setFetchError();
    } finally {
      if (this._loadId === id && this._isMultiSelect) this._setLoadingState(false);
    }
  }

  _setFetchError() {
    if (this._isMultiSelect) {
      const input = this.querySelector(".rp-ms-input");
      const errEl = this.querySelector("[data-rp-error]");
      const ms = this.querySelector(".rp-multiselect");
      if (input) {
        input.disabled = true;
        input.placeholder = "";
      }
      if (errEl) {
        errEl.textContent = "Could not load weeks. Refresh the page to retry.";
        errEl.hidden = false;
      }
      if (ms) ms.classList.add("is-invalid");
    } else {
      const select = this.querySelector(".rp-input");
      const errEl = this.querySelector("[data-rp-error]");
      if (select) {
        select.disabled = true;
        select.innerHTML = '<option value="" disabled selected>Could not load weeks</option>';
      }
      if (errEl) {
        errEl.textContent = "Could not load weeks. Refresh the page to retry.";
        errEl.hidden = false;
      }
    }
  }

  _buildHTML() {
    if (this._isMultiSelect) return this._buildMultiSelectHTML();
    return super._buildHTML();
  }

  _bindEvents() {
    if (this._isMultiSelect) return this._bindMultiSelectEvents();
    return super._bindEvents();
  }

  _validate() {
    if (this._isMultiSelect) {
      if (this._required && !(this._selectedValues || []).length) return "This field is required.";
      return "";
    }
    return super._validate();
  }

  _updateError() {
    if (this._isMultiSelect) {
      const err = this._validate();
      const errEl = this.querySelector("[data-rp-error]");
      const ms = this.querySelector(".rp-multiselect");
      if (errEl) {
        errEl.textContent = err;
        errEl.hidden = !err;
      }
      if (ms) ms.classList.toggle("is-invalid", !!err);
      return;
    }
    super._updateError();
  }

  _buildChipsHTML() {
    return (this._selectedValues || [])
      .map(
        (v, i) =>
          `<span class="rp-ms-chip" data-ms-idx="${i}">${this._esc(v.label)}<button type="button" data-ms-remove="${i}" aria-label="Remove ${this._esc(v.label)}">×</button></span>`,
      )
      .join("");
  }

  _buildMultiSelectHTML() {
    const atMax = this._isAtMax();
    return `
      <div class="rp-field">
        ${this._labelHTML()}
        <div class="rp-multiselect" role="group" aria-label="${this._esc(this._label)}">
          ${this._buildChipsHTML()}
          <input
            class="rp-ms-input"
            type="text"
            id="${this._esc(this._fieldId)}-input"
            placeholder="${atMax ? "" : this._esc(this._placeholder)}"
            autocomplete="off"
            aria-autocomplete="list"
            aria-expanded="false"${atMax ? " hidden" : ""}
          />
          <div class="rp-ms-dropdown" role="listbox" hidden></div>
        </div>
        ${this._errorHTML()}
        ${this._hintHTML()}
      </div>
    `;
  }

  get _max() {
    const v = parseInt(this.getAttribute("max") || "0", 10);
    return isNaN(v) || v <= 0 ? null : v;
  }

  _isAtMax() {
    return this._max !== null && (this._selectedValues || []).length >= this._max;
  }

  _unselected() {
    return (this._initialOptions || []).filter(
      (o) => !(this._selectedValues || []).find((s) => s.value === o.value),
    );
  }

  _setLoadingState(on) {
    const input = this.querySelector(".rp-ms-input");
    if (!input) return;
    input.disabled = on;
    input.placeholder = on ? "Loading…" : this._isAtMax() ? "" : this._placeholder;
  }

  _bindMultiSelectEvents() {
    const ms = this.querySelector(".rp-multiselect");
    const input = this.querySelector(".rp-ms-input");
    const dropdown = this.querySelector(".rp-ms-dropdown");
    if (!ms || !input || !dropdown) return;

    ms.addEventListener("mousedown", (e) => {
      if (e.target !== input) e.preventDefault();
    });

    ms.addEventListener("click", (e) => {
      if (!e.target.closest("[data-ms-remove]") && !e.target.closest(".rp-ms-option")) {
        input.focus();
      }
    });

    ms.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-ms-remove]");
      if (!btn) return;
      this._removeChip(parseInt(btn.getAttribute("data-ms-remove"), 10));
    });

    input.addEventListener("input", () => this._updateDropdown());
    input.addEventListener("focus", () => this._updateDropdown());
    input.addEventListener("keydown", (e) => this._onKeydown(e));
    input.addEventListener("blur", () => {
      setTimeout(() => {
        this._closeDropdown();
        this._touched = true;
        this._updateError();
      }, 160);
    });

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

    if (!items.length) {
      dropdown.innerHTML = `<div class="rp-ms-empty">No options found</div>`;
    } else {
      dropdown.innerHTML = items.join("");
    }
    dropdown.hidden = false;
    this._highlightedIdx = -1;
    input.setAttribute("aria-expanded", "true");
  }

  _closeDropdown() {
    const dropdown = this.querySelector(".rp-ms-dropdown");
    if (dropdown) dropdown.hidden = true;
    const input = this.querySelector(".rp-ms-input");
    if (input) input.setAttribute("aria-expanded", "false");
    this._highlightedIdx = -1;
  }

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

  _parseValueCodes(val) {
    if (!val) return [];
    try {
      const parsed = JSON.parse(val);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return val
        .split(",")
        .map((v) => v.trim())
        .filter(Boolean);
    }
  }
}

customElements.define("wins-week-field", WinsWeekField);
