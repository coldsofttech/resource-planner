import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* ResourcePlanVersionField  <resource-plan-version-field>
 *
 * Dropdown field pre-wired to the resource plan detail API. Versions are read
 * from the `versions` list on GET /api/v1/resource-plans/<code>/ for the plan
 * given by the `plan-code` attribute, and re-fetched whenever it changes.
 * Inherits all attributes and public API from DropdownField / BaseField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Version"
 *   placeholder → "Select version…"
 *
 * Attributes:
 *   plan-code  – the resource plan code to load versions for; clears and
 *                disables the field when absent.
 *   show-label – when present, renders "Version" as the visible field label.
 *
 * Usage:
 *   <resource-plan-version-field id="dvc-version" plan-code="RES-1" required show-label></resource-plan-version-field>
 */
class ResourcePlanVersionField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label", "plan-code"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) {
      return this.getAttribute("label") || "Version";
    }
    return super._label;
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (name === "plan-code" && this._connected && oldVal !== newVal) {
      this._loaded = false;
      this._initialOptions = [];
      this._loadId = Symbol();
      const select = this.querySelector(".rp-input");
      if (!newVal) {
        this._setEmptyState();
        return;
      }
      if (select) select.disabled = true;
      this._fetchOptions(this._loadId);
      return;
    }
    super.attributeChangedCallback(name, oldVal, newVal);
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder")) {
      this.setAttribute("placeholder", "Select version…");
    }

    if (this._initialOptions === undefined) this._initialOptions = [];

    super.connectedCallback();

    if (!this._loaded && this.getAttribute("plan-code")) {
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
    this._loaded = false;
    this._loadId = Symbol();
    if (this.getAttribute("plan-code")) this._fetchOptions(this._loadId);
  }

  _setEmptyState() {
    this._initialOptions = [];
    this._doRender();
    const select = this.querySelector(".rp-input");
    if (select) select.disabled = true;
  }

  async _fetchOptions(id) {
    try {
      const planCode = this.getAttribute("plan-code");
      const { href, method } = API_URLS.resourcePlans.detail(planCode);
      const res = await apiFetch(href, { method });
      if (this._loadId !== id) return;

      const versions = res?.data?.versions ?? [];
      this._initialOptions = versions.map((v) => ({
        id: String(v.version),
        label: `Version ${v.version} (${v.status_display})`,
        value: String(v.version),
        selected: false,
        disabled: false,
      }));

      this._loaded = true;
      this._doRender();
      const select = this.querySelector(".rp-input");
      if (select) select.disabled = false;
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
      select.innerHTML = '<option value="" disabled selected>Could not load versions</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load versions. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("resource-plan-version-field", ResourcePlanVersionField);
