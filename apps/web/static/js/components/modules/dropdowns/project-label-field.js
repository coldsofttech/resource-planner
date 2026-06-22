import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* ProjectLabelField  <project-label-field>
 *
 * Searchable dropdown field pre-wired to the global project labels options API.
 * Options are fetched from GET /api/v1/projects/labels/options/ on first connect.
 * Value is the ProjectLabel code (e.g. "PRJLBL-1").
 * Options display as "<label> (<project_name>)".
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Label"
 *   placeholder → "Search label…"
 *
 * Attributes:
 *   show-label – when present, renders "Label" as the visible field label.
 *   allow-all  – prepends an "All Labels" option (value="") selected by default.
 */
class ProjectLabelField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label", "allow-all"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Label";
    return super._label;
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "Search label…");
    // Enable combobox/searchable mode so users can type to filter
    if (!this.hasAttribute("searchable")) this.setAttribute("searchable", "");

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
      const { href, method } = API_URLS.projects.labelsOptions();
      const res = await apiFetch(href, { method });
      if (this._loadId !== id) return;

      const labels = res?.data ?? [];
      const hasAllOpt = this.hasAttribute("allow-all");
      this._initialOptions = [
        ...(hasAllOpt
          ? [{ id: "", label: "All Labels", value: "", selected: true, disabled: false }]
          : []),
        ...labels.map((l) => ({
          id: l.code,
          label: `${l.label} (${l.project_name})`,
          value: l.code,
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
      select.innerHTML = '<option value="" disabled selected>Could not load labels</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load labels. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("project-label-field", ProjectLabelField);
