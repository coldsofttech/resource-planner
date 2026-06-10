import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* MemberField  <member-field>
 *
 * Dropdown field pre-wired to the members API. Active members are fetched
 * from GET /api/v1/members/?page_size=200 on first connect.
 * Inherits all attributes and public API from DropdownField and BaseField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Member"
 *   placeholder → "Select member..."
 *
 * Options render as "Display Name (code)".
 *
 * Attributes:
 *   allow-all  – when present, prepends an "All Members" option (value="")
 *                selected by default; used in filter contexts.
 *   show-label – when present, renders "Member" as the visible field label.
 *
 * Usage:
 *   <member-field id="leave-member" required col="col-12"></member-field>
 *
 *   <!-- With pre-selected value (member code) -->
 *   <member-field id="leave-member" value="MBR-0001"></member-field>
 *
 *   <!-- Filter context: shows "All Members" as the default selection -->
 *   <member-field id="filter-member" name="member" allow-all></member-field>
 */
class MemberField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Member";
    return super._label;
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "Select member…");

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
      const { href, method } = API_URLS.members.list();
      const res = await apiFetch(`${href}?page_size=200`, { method });
      if (this._loadId !== id) return;

      const members = res?.data?.results ?? [];
      const hasAllOpt = this.hasAttribute("allow-all");
      this._initialOptions = [
        ...(hasAllOpt
          ? [{ id: "", label: "All Members", value: "", selected: true, disabled: false }]
          : []),
        ...members.map((m) => {
          const name = m.display_name || m.email || m.code;
          return {
            id: m.code,
            label: `${name}`,
            value: m.code,
            selected: false,
            disabled: false,
          };
        }),
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
      select.innerHTML = '<option value="" disabled selected>Could not load members</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load members. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("member-field", MemberField);
