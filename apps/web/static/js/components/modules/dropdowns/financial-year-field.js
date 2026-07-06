import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* FinancialYearField  <financial-year-field>
 *
 * Dropdown field pre-wired to the financial years API.
 * Active financial years are fetched from GET /api/v1/fy/options/ on first connect.
 * Inherits all attributes and public API from DropdownField / BaseField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Financial Year"
 *   placeholder → "Select financial year…"
 *
 * Attributes:
 *   allow-all  – prepends an "All Financial Years" option (value="") selected by default;
 *                used in filter contexts.
 *   show-label – when present, renders "Financial Year" as the visible field label.
 *   show-long  – display option labels using data.long_fy (e.g. "FY2024-2025").
 *   show-short – display option labels using data.short_fy. Takes priority over show-long.
 *                When neither is set, defaults to long_fy.
 *
 * Usage:
 *   <financial-year-field id="plan-fy" required col="col-md-6"></financial-year-field>
 *   <financial-year-field id="plan-fy" value="FY-1" show-short></financial-year-field>
 *   <financial-year-field id="filter-fy" name="fy" allow-all show-label show-long></financial-year-field>
 */
class FinancialYearField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label", "allow-all", "show-long", "show-short"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) {
      return this.getAttribute("label") || "Financial Year";
    }
    return super._label;
  }

  get _displayKey() {
    if (this.hasAttribute("show-short")) return "short_fy";
    return "long_fy";
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (
      (name === "allow-all" || name === "show-long" || name === "show-short") &&
      this._connected &&
      this._fyData !== undefined
    ) {
      this._updateFyOptions();
      this._initialOptions = this._buildOptionsList();
      this._doRender();
    } else {
      super.attributeChangedCallback(name, oldVal, newVal);
    }
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder")) {
      this.setAttribute("placeholder", "Select financial year…");
    }

    const firstConnect = this._initialOptions === undefined;
    if (firstConnect) {
      this._initialOptions = [];
      this._loadId = Symbol();
    }

    super.connectedCallback();

    if (firstConnect) {
      const select = this.querySelector(".rp-input");
      if (select) select.disabled = true;
      this._fetchOptions(this._loadId);
    } else if (this._fyData === undefined) {
      // Reconnected before the initial fetch completed (e.g. tab-panel re-renders its innerHTML
      // before this element was defined, causing disconnect then reconnect before fetch resolved).
      const id = Symbol();
      this._loadId = id;
      const select = this.querySelector(".rp-input");
      if (select) select.disabled = true;
      this._fetchOptions(id);
    }
  }

  disconnectedCallback() {
    this._loadId = Symbol();
  }

  async _fetchOptions(id) {
    try {
      const { href, method } = API_URLS.fy.options();
      const res = await apiFetch(href, { method });
      if (this._loadId !== id) return;

      this._fyData = res?.data ?? [];
      this._updateFyOptions();
      this._initialOptions = this._buildOptionsList();
      this._doRender();
    } catch {
      if (this._loadId !== id) return;
      this._setFetchError();
    }
  }

  _updateFyOptions() {
    const key = this._displayKey;
    this._fyOptions = (this._fyData || []).map((fy) => ({
      id: fy.code,
      label: fy[key] || fy.long_fy,
      value: fy.code,
      selected: false,
      disabled: false,
    }));
  }

  _buildOptionsList() {
    const hasAllOpt = this.hasAttribute("allow-all");
    return [
      ...(hasAllOpt
        ? [
            {
              id: "",
              label: "All Financial Years",
              value: "",
              selected: true,
              disabled: false,
            },
          ]
        : []),
      ...(this._fyOptions || []),
    ];
  }

  _setFetchError() {
    const select = this.querySelector(".rp-input");
    const errEl = this.querySelector("[data-rp-error]");
    if (select) {
      select.disabled = true;
      select.innerHTML =
        '<option value="" disabled selected>Could not load financial years</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load financial years. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("financial-year-field", FinancialYearField);
