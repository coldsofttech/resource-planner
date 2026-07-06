import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* ResourcePlanField  <resource-plan-field>
 *
 * Dropdown field pre-wired to the resource plans API. Active resource plans
 * are fetched from GET /api/v1/resource-plans/options/ on connect, and
 * retried on reconnect until the fetch succeeds at least once. Inherits all
 * attributes and public API from DropdownField and BaseField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Resource Plan"
 *   placeholder → "Select resource plan…"
 *
 * Attributes:
 *   show-label – when present, renders "Resource Plan" as the visible field label.
 *
 * Usage:
 *   <resource-plan-field id="dvc-plan" required col="col-md-3" show-label></resource-plan-field>
 */
class ResourcePlanField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) {
      return this.getAttribute("label") || "Resource Plan";
    }
    return super._label;
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder")) {
      this.setAttribute("placeholder", "Select resource plan…");
    }

    if (this._initialOptions === undefined) this._initialOptions = [];

    super.connectedCallback();

    if (!this._loaded) {
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
    this._fetchOptions(this._loadId);
  }

  async _fetchOptions(id) {
    try {
      const { href, method } = API_URLS.resourcePlans.options();
      const res = await apiFetch(href, { method });
      if (this._loadId !== id) return;

      const plans = res?.data ?? [];
      this._initialOptions = plans.map((p) => ({
        id: p.code,
        label: p.name,
        value: p.code,
        selected: false,
        disabled: false,
      }));

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
      select.innerHTML =
        '<option value="" disabled selected>Could not load resource plans</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load resource plans. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("resource-plan-field", ResourcePlanField);
