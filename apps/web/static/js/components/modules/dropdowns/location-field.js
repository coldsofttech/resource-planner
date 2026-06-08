import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* LocationField  <location-field>
 *
 * Dropdown field pre-wired to the locations API. Active locations are fetched
 * from GET /api/v1/locations/options/ on first connect. The location marked
 * is_default is pre-selected when no `value` attribute is provided.
 * Inherits all attributes and public API from DropdownField and BaseField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Location"
 *   placeholder → "Select location..."
 *
 * Options render as "City, Country".
 *
 * Attributes:
 *   allow-all  – when present, prepends an "All Locations" option (value="")
 *                selected by default; used in filter contexts.
 *   show-label – when present, renders "Location" as the visible field label.
 *
 * Usage:
 *   <location-field id="member-location" required col="col-md-6"></location-field>
 *
 *   <!-- With pre-selected value (location code) -->
 *   <location-field id="member-location" value="LOC-0001"></location-field>
 *
 *   <!-- Filter context: shows "All Locations" as the default selection -->
 *   <location-field id="filter-location" name="location" allow-all></location-field>
 */
class LocationField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Location";
    return super._label;
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "Select location…");

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
    // Invalidate any in-flight fetch so its result is discarded on reconnect.
    this._loadId = Symbol();
  }

  // ── Private ──────────────────────────────────────────────────────────────

  async _fetchOptions(id) {
    try {
      const { href, method } = API_URLS.locations.options();
      const res = await apiFetch(href, { method });
      if (this._loadId !== id) return;

      const locations = res?.data ?? [];
      const hasAllOpt = this.hasAttribute("allow-all");
      this._initialOptions = [
        ...(hasAllOpt
          ? [{ id: "", label: "All Locations", value: "", selected: true, disabled: false }]
          : []),
        ...locations.map((loc) => ({
          id: loc.code,
          label: `${loc.city}, ${loc.country}`,
          value: loc.code,
          selected: !hasAllOpt && Boolean(loc.is_default),
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
      select.innerHTML = '<option value="" disabled selected>Could not load locations</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load locations. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("location-field", LocationField);
