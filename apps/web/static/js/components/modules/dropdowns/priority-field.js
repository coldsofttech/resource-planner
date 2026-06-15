import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* PriorityField  <priority-field>
 *
 * Dropdown field pre-wired to the project priority options API.
 * Options are fetched from GET /api/v1/projects/options/?fields=priority on
 * first connect. Inherits all attributes and public API from DropdownField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Priority"
 *   placeholder → "Select priority..."
 *
 * Attributes:
 *   allow-all  – prepends an "All Priority Levels" option (value="")
 *                selected by default; used in filter contexts.
 *   show-label – when present, renders "Priority" as the visible field label.
 *
 * Usage:
 *   <priority-field id="proj-priority" required col="col-md-6"></priority-field>
 *
 *   <!-- Filter context -->
 *   <priority-field id="filter-priority" name="priority" allow-all></priority-field>
 */
class PriorityField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Priority";
    return super._label;
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "Select priority...");

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
      const { href, method } = API_URLS.projects.priorityOptions();
      const res = await apiFetch(href, { method });
      if (this._loadId !== id) return;

      const items = res?.data ?? [];
      const hasAllOpt = this.hasAttribute("allow-all");
      const hasNotSet = this.hasAttribute("not-set");
      this._initialOptions = [
        ...(hasAllOpt
          ? [{ id: "", label: "All Priority Levels", value: "", selected: true, disabled: false }]
          : []),
        ...(hasNotSet
          ? [{ id: "", label: "Not Set", value: "", selected: true, disabled: false }]
          : []),
        ...items.map((t) => ({
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
      select.innerHTML =
        '<option value="" disabled selected>Could not load priority options</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load priority options. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("priority-field", PriorityField);
