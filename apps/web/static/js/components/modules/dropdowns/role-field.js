import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* RoleField  <role-field>
 *
 * Dropdown field pre-wired to the roles API. Active roles are fetched from
 * GET /api/v1/roles/options/ on first connect. The role marked is_default is
 * pre-selected when no `value` attribute is provided. Inherits all attributes
 * and public API from DropdownField and BaseField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Role"
 *   placeholder → "Select role..."
 *
 * Attributes:
 *   allow-all  – when present, prepends an "All Roles" option (value="")
 *                selected by default; used in filter contexts.
 *   show-label – when present, renders "Role" as the visible field label
 *
 * Usage:
 *   <role-field id="member-role" required col="col-md-6"></role-field>
 *
 *   <!-- With pre-selected value (role code) -->
 *   <role-field id="member-role" value="ROLE-1"></role-field>
 *
 *   <!-- Filter context: shows "All Roles" as the default selection -->
 *   <role-field id="filter-role" name="role" allow-all></role-field>
 */
class RoleField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Role";
    return super._label;
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "Select role...");

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
      const { href, method } = API_URLS.roles.options();
      const res = await apiFetch(href, { method });
      if (this._loadId !== id) return;

      const roles = res?.data ?? [];
      const hasAllOpt = this.hasAttribute("allow-all");
      this._initialOptions = [
        ...(hasAllOpt
          ? [{ id: "", label: "All Roles", value: "", selected: true, disabled: false }]
          : []),
        ...roles.map((r) => ({
          id: r.code,
          label: r.role,
          value: r.code,
          selected: !hasAllOpt && Boolean(r.is_default),
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
      select.innerHTML = '<option value="" disabled selected>Could not load roles</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load roles. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("role-field", RoleField);
