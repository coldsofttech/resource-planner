import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* RechargeTypeField  <recharge-type-field>
 *
 * Dropdown field pre-wired to the recharge types options API.
 * Options are fetched from GET /api/v1/recharges/types/options/ on first connect.
 * Value is the RechargeType code (e.g. "RT-1").
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Mapping"
 *   placeholder → "Select mapping…"
 *
 * Attributes:
 *   show-label – when present, renders "Mapping" as the visible field label.
 *   allow-all  – prepends an "All Types" option (value="") selected by default.
 */
class RechargeTypeField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label", "allow-all"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Mapping";
    return super._label;
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "Select mapping…");

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
      const { href, method } = API_URLS.rechargeTypes.options();
      const res = await apiFetch(href, { method });
      if (this._loadId !== id) return;

      const types = res?.data ?? [];
      const hasAllOpt = this.hasAttribute("allow-all");
      this._initialOptions = [
        ...(hasAllOpt
          ? [{ id: "", label: "All Types", value: "", selected: true, disabled: false }]
          : []),
        ...types.map((t) => ({
          id: t.code,
          label: t.name,
          value: t.code,
          selected: false,
          disabled: false,
        })),
      ];
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
      select.innerHTML = '<option value="" disabled selected>Could not load mappings</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load mappings. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("recharge-type-field", RechargeTypeField);
