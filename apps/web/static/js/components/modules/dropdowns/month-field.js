import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* MonthField  <month-field>
 *
 * Dropdown field pre-wired to the sprint months API, scoped to a financial year.
 * Options are fetched from GET /api/v1/sprints/months/?fy_code=... whenever the
 * `fy-code` attribute is set/changed. Options display a formatted month label
 * (e.g. "Apr 2025"); the option value is the raw "YYYY-MM" string.
 * Inherits all attributes and public API from DropdownField / BaseField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Month"
 *   placeholder → "Select month…"
 *
 * Attributes:
 *   fy-code    – financial year code to scope the month options to; re-fetches on change.
 *                Clears all options when absent/empty.
 *   show-label – when present, renders "Month" as the visible field label.
 *
 * Usage:
 *   <month-field id="kpi-month" fy-code="FY-1" show-label required></month-field>
 */
class MonthField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label", "fy-code"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) {
      return this.getAttribute("label") || "Month";
    }
    return super._label;
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (name === "fy-code" && this._connected && oldVal !== newVal) {
      this._monthOptions = undefined;
      this._initialOptions = [];
      this._loaded = false;
      this._loadId = Symbol();
      const select = this.querySelector(".rp-input");
      if (select) select.disabled = true;
      if (newVal) {
        this._fetchOptions(this._loadId);
      } else {
        this._doRender();
      }
      return;
    }
    super.attributeChangedCallback(name, oldVal, newVal);
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder")) {
      this.setAttribute("placeholder", "Select month…");
    }

    if (this._initialOptions === undefined) this._initialOptions = [];

    super.connectedCallback();

    if (!this._loaded && this.getAttribute("fy-code")) {
      const select = this.querySelector(".rp-input");
      if (select) select.disabled = true;
      this._loadId = Symbol();
      this._fetchOptions(this._loadId);
    }
  }

  disconnectedCallback() {
    this._loadId = Symbol();
  }

  refresh() {
    if (!this.getAttribute("fy-code")) return;
    this._loaded = false;
    this._loadId = Symbol();
    this._fetchOptions(this._loadId);
  }

  async _fetchOptions(id) {
    const fyCode = this.getAttribute("fy-code");
    if (!fyCode) return;
    try {
      const { href, method } = API_URLS.sprints.months();
      const url = `${href}?fy_code=${encodeURIComponent(fyCode)}`;
      const res = await apiFetch(url, { method });
      if (this._loadId !== id) return;

      const months = res?.data ?? [];
      this._monthOptions = months.map((m) => ({
        id: m.value,
        label: m.label,
        value: m.value,
        selected: false,
        disabled: false,
      }));

      this._initialOptions = this._monthOptions;
      this._loaded = true;
      this._doRender();
    } catch {
      if (this._loadId !== id) return;
      this._setFetchError();
    }
  }

  _setFetchError() {
    const select = this.querySelector(".rp-input");
    const errEl = this.querySelector("[data-rp-error]");
    if (select) {
      select.disabled = true;
      select.innerHTML = '<option value="" disabled selected>Could not load months</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load months. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("month-field", MonthField);
