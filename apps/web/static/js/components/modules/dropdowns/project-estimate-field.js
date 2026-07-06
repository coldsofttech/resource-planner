import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* ProjectEstimateField  <project-estimate-field>
 *
 * Dropdown field pre-wired to a single project's estimate versions.
 * Options are (re)fetched from GET /api/v1/projects/<code>/estimates/
 * whenever the `project-code` attribute is set/changed. Inherits all
 * attributes and public API from DropdownField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Estimate"
 *   placeholder → "Select estimate..."
 *
 * Attributes:
 *   project-code – code of the project whose estimate versions should be
 *                  listed. Clears and re-fetches options whenever changed.
 *   show-label   – when present, renders "Estimate" as the visible field label.
 *
 * Usage:
 *   <project-estimate-field id="basis-estimate" project-code="PROJ-1"></project-estimate-field>
 */
class ProjectEstimateField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label", "project-code"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Estimate";
    return super._label;
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (name === "project-code" && this.isConnected && oldVal !== newVal) {
      this._loadId = Symbol();
      this._fetchOptions(newVal || "", this._loadId);
      return;
    }
    super.attributeChangedCallback(name, oldVal, newVal);
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "Select estimate...");

    const firstConnect = this._initialOptions === undefined;
    if (firstConnect) {
      this._initialOptions = [];
      this._loadId = Symbol();
    }

    super.connectedCallback();

    if (firstConnect) {
      const select = this.querySelector(".rp-input");
      if (select) select.disabled = true;
      this._fetchOptions(this.getAttribute("project-code") || "", this._loadId);
    }
  }

  disconnectedCallback() {
    this._loadId = Symbol();
  }

  async _fetchOptions(projectCode, id) {
    this._estimatesByCode = {};
    if (!projectCode) {
      this._initialOptions = [];
      this._doRender();
      return;
    }
    try {
      const { href, method } = API_URLS.projectEstimates.list(projectCode);
      const res = await apiFetch(href, { method });
      if (this._loadId !== id) return;

      const items = res?.data?.results ?? [];
      items.forEach((e) => {
        this._estimatesByCode[e.code] = e;
      });
      this._initialOptions = items.map((e) => ({
        id: e.code,
        label: `${e.version_display} — ${e.status}`,
        value: e.code,
        selected: false,
        disabled: false,
      }));

      const select = this.querySelector(".rp-input");
      if (select) select.disabled = false;
      this._doRender();
    } catch {
      if (this._loadId !== id) return;
      this._setFetchError();
    }
  }

  // Returns the total_cost for a given estimate code, or null if unknown.
  getEstimateTotalCost(code) {
    return this._estimatesByCode?.[code]?.total_cost ?? null;
  }

  _setFetchError() {
    const select = this.querySelector(".rp-input");
    const errEl = this.querySelector("[data-rp-error]");
    if (select) {
      select.disabled = true;
      select.innerHTML = '<option value="" disabled selected>Could not load estimates</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load estimates. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("project-estimate-field", ProjectEstimateField);
