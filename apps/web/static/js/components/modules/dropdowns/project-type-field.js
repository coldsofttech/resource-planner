import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* ProjectTypeField  <project-type-field>
 *
 * Dropdown field pre-wired to the project types API. Active project types are
 * fetched from GET /api/v1/projects/types/options/ on first connect. Inherits
 * all attributes and public API from DropdownField and BaseField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Project Type"
 *   placeholder → "Select project type..."
 *
 * Attributes:
 *   allow-all  – when present, prepends an "All Project Types" option (value="")
 *                selected by default; used in filter contexts.
 *   show-label – when present, renders "Project Type" as the visible field label
 *
 * Usage:
 *   <project-type-field id="project-type" required col="col-md-6"></project-type-field>
 *
 *   <!-- With pre-selected value (project type code) -->
 *   <project-type-field id="project-type" value="PROJTYPE-1"></project-type-field>
 *
 *   <!-- Filter context: shows "All Project Types" as the default selection -->
 *   <project-type-field id="filter-type" name="project_type" allow-all></project-type-field>
 */
class ProjectTypeField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Project Type";
    return super._label;
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder"))
      this.setAttribute("placeholder", "Select project type...");

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

  async _fetchOptions(id) {
    try {
      const { href, method } = API_URLS.projectTypes.options();
      const res = await apiFetch(href, { method });
      if (this._loadId !== id) return;

      const types = res?.data ?? [];
      const hasAllOpt = this.hasAttribute("allow-all");
      this._initialOptions = [
        ...(hasAllOpt
          ? [{ id: "", label: "All Project Types", value: "", selected: true, disabled: false }]
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
      select.innerHTML = '<option value="" disabled selected>Could not load project types</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load project types. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("project-type-field", ProjectTypeField);
