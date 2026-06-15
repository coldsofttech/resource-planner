import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* ProjectStatusField  <project-status-field>
 *
 * Dropdown field pre-wired to the project statuses API. Active project statuses
 * are fetched from GET /api/v1/projects/statuses/options/ on first connect.
 * Inherits all attributes and public API from DropdownField and BaseField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Project Status"
 *   placeholder → "Select project status..."
 *
 * Attributes:
 *   allow-all  – when present, prepends an "All Project Statuses" option (value="")
 *                selected by default; used in filter contexts.
 *   show-label – when present, renders "Project Status" as the visible field label
 *
 * Usage:
 *   <project-status-field id="project-status" required col="col-md-6"></project-status-field>
 *
 *   <!-- With pre-selected value (project status code) -->
 *   <project-status-field id="project-status" value="PROJSTAT-1"></project-status-field>
 *
 *   <!-- Filter context: shows "All Project Statuses" as the default selection -->
 *   <project-status-field id="filter-status" name="project_status" allow-all></project-status-field>
 */
class ProjectStatusField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Project Status";
    return super._label;
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder"))
      this.setAttribute("placeholder", "Select project status...");

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

  refresh() {
    this._loadId = Symbol();
    this._fetchOptions(this._loadId);
  }

  async _fetchOptions(id) {
    try {
      const { href, method } = API_URLS.projectStatuses.options();
      const res = await apiFetch(href, { method });
      if (this._loadId !== id) return;

      const statuses = res?.data ?? [];
      const hasAllOpt = this.hasAttribute("allow-all");
      this._initialOptions = [
        ...(hasAllOpt
          ? [{ id: "", label: "All Project Statuses", value: "", selected: true, disabled: false }]
          : []),
        ...statuses.map((s) => ({
          id: s.code,
          label: s.name,
          value: s.code,
          selected: false,
          disabled: false,
        })),
      ];

      this._doRender();

      // If no value is currently selected (value attr didn't match any option),
      // auto-select the first real option so the create drawer never shows null.
      if (!hasAllOpt) {
        const select = this.querySelector(".rp-input");
        if (select && !select.value) {
          const first = this._initialOptions.find((o) => o.value);
          if (first) this.value = first.value;
        }
      }
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
        '<option value="" disabled selected>Could not load project statuses</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load project statuses. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("project-status-field", ProjectStatusField);
