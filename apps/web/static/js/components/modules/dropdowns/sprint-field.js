import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* SprintField  <sprint-field>
 *
 * Dropdown field pre-wired to the sprints API.
 * Active sprints are fetched from GET /api/v1/sprints/options/ on first connect.
 * Options display the sprint name (e.g. "Sprint 1").
 * Inherits all attributes and public API from DropdownField / BaseField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Sprint"
 *   placeholder → "Select sprint…"
 *
 * Attributes:
 *   fy-code    – filters options to the given financial year code; re-fetches on change.
 *   allow-all  – prepends an "All Sprints" option (value="") selected by default;
 *                used in filter contexts.
 *   show-label – when present, renders "Sprint" as the visible field label.
 *
 * Usage:
 *   <sprint-field id="plan-sprint" required col="col-md-6"></sprint-field>
 *   <sprint-field id="plan-sprint" fy-code="FY-1"></sprint-field>
 *   <sprint-field id="filter-sprint" name="sprint" allow-all show-label></sprint-field>
 */
class SprintField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label", "allow-all", "fy-code"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) {
      return this.getAttribute("label") || "Sprint";
    }
    return super._label;
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (name === "allow-all" && this._connected && this._sprintOptions !== undefined) {
      this._initialOptions = this._buildOptions();
      this._doRender();
    } else if (name === "fy-code" && this._connected && oldVal !== newVal) {
      this._sprintOptions = undefined;
      this._initialOptions = [];
      this._loadId = Symbol();
      const select = this.querySelector(".rp-input");
      if (select) select.disabled = true;
      this._fetchOptions(this._loadId);
    } else {
      super.attributeChangedCallback(name, oldVal, newVal);
    }
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder")) {
      this.setAttribute("placeholder", "Select sprint…");
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
    }
  }

  disconnectedCallback() {
    this._loadId = Symbol();
  }

  async _fetchOptions(id) {
    try {
      const fyCode = this.getAttribute("fy-code") || null;
      const { href, method } = API_URLS.sprints.options();
      const url = fyCode ? `${href}?fy_code=${encodeURIComponent(fyCode)}` : href;
      const res = await apiFetch(url, { method });
      if (this._loadId !== id) return;

      const sprints = res?.data ?? [];
      this._sprintOptions = sprints.map((s) => ({
        id: s.code,
        label: s.name,
        value: s.code,
        selected: false,
        disabled: false,
      }));

      this._initialOptions = this._buildOptions();
      this._doRender();
    } catch {
      if (this._loadId !== id) return;
      this._setFetchError();
    }
  }

  _buildOptions() {
    const hasAllOpt = this.hasAttribute("allow-all");
    return [
      ...(hasAllOpt
        ? [{ id: "", label: "All Sprints", value: "", selected: true, disabled: false }]
        : []),
      ...(this._sprintOptions || []),
    ];
  }

  _setFetchError() {
    const select = this.querySelector(".rp-input");
    const errEl = this.querySelector("[data-rp-error]");
    if (select) {
      select.disabled = true;
      select.innerHTML = '<option value="" disabled selected>Could not load sprints</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load sprints. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("sprint-field", SprintField);
