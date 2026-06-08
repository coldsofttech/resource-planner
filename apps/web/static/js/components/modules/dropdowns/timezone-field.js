import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* TimezoneField  <timezone-field>
 *
 * Dropdown field pre-wired to the users timezone options API.
 * Timezones are fetched from GET /api/v1/users/options/ on first connect
 * and cached for the lifetime of the element.
 * Inherits all attributes and public API from DropdownField and BaseField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Timezone"
 *   placeholder → "Select timezone…"
 *
 * Attributes:
 *   show-label – when present, renders "Timezone" as the visible field label.
 *
 * Usage:
 *   <timezone-field id="user-timezone" required col="col-md-6"></timezone-field>
 *
 *   <!-- With pre-selected value -->
 *   <timezone-field id="user-timezone" value="UTC"></timezone-field>
 */
class TimezoneField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Timezone";
    return super._label;
  }

  connectedCallback() {
    // if (!this.hasAttribute("label")) this.setAttribute("label", "Timezone");
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "Select timezone…");

    const firstConnect = this._initialOptions === undefined;
    if (firstConnect) {
      this._initialOptions = [];
      this._loadId = Symbol();
    }

    super.connectedCallback();

    // Re-fetch if this is the first connect OR if options never loaded (e.g. the
    // element was disconnected mid-fetch by section-panel._render() which uses innerHTML).
    const shouldFetch = firstConnect || this._initialOptions.length === 0;
    if (shouldFetch) {
      this._loadId = Symbol();
      const select = this.querySelector(".rp-input");
      if (select) select.disabled = true;
      this._fetchOptions(this._loadId);
    }
  }

  disconnectedCallback() {
    this._loadId = Symbol();
  }

  // ── Private ──────────────────────────────────────────────────────────────

  async _fetchOptions(id) {
    try {
      const { href, method } = API_URLS.users.options();
      const res = await apiFetch(href, { method });
      if (this._loadId !== id) return;

      const tzs = res?.data?.timezones ?? [];
      const currentVal = this.getAttribute("value") || "";

      this._initialOptions = tzs.map((tz) => ({
        id: tz.value,
        label: tz.label,
        value: tz.value,
        selected: tz.value === currentVal,
        disabled: false,
      }));

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
      select.innerHTML = '<option value="" disabled selected>Could not load timezones</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load timezones. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("timezone-field", TimezoneField);
