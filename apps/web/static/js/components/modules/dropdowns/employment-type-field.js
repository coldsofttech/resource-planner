import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* EmploymentTypeField  <employment-type-field>
 *
 * Dropdown field pre-wired to the employment types API. Active employment
 * types are fetched from GET /api/v1/emp-types/options/ on first connect.
 * The type marked is_default is pre-selected when no `value` attribute is
 * provided. Inherits all attributes and public API from DropdownField and
 * BaseField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Employment Type"
 *   placeholder → "Select employment type..."
 *
 * Attributes:
 *   allow-all  – when present, prepends an "All Types" option (value="")
 *                selected by default; used in filter contexts.
 *   show-label – when present, renders "Employment Type" as the visible field label.
 *
 * Usage:
 *   <employment-type-field id="member-emp-type" required col="col-md-6"></employment-type-field>
 *
 *   <!-- With pre-selected value (employment type code) -->
 *   <employment-type-field id="member-emp-type" value="EMPTYPE-1"></employment-type-field>
 *
 *   <!-- Filter context: shows "All Types" as the default selection -->
 *   <employment-type-field id="filter-emp-type" name="employment_type" allow-all></employment-type-field>
 */
class EmploymentTypeField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Employment Type";
    return super._label;
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder"))
      this.setAttribute("placeholder", "Select employment type…");

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
      const { href, method } = API_URLS.empTypes.options();
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
          selected: !hasAllOpt && Boolean(t.is_default),
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
      select.innerHTML =
        '<option value="" disabled selected>Could not load employment types</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load employment types. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("employment-type-field", EmploymentTypeField);
