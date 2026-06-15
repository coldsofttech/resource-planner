import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* ProjectField  <project-field>
 *
 * Dropdown field pre-wired to the projects API. Active projects are fetched
 * from GET /api/v1/projects/options/ on first connect. Inherits all attributes
 * and public API from DropdownField and BaseField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Project"
 *   placeholder → "Select project..."
 *
 * Attributes:
 *   programme-id – id of a <programme-field> (or any dropdown) whose value
 *                  provides the programme code to filter project options.
 *                  When provided and a programme is selected, only projects
 *                  belonging to that programme are shown. When no programme
 *                  is selected, all active projects are shown.
 *   allow-all    – when present, prepends an "All Projects" option (value="")
 *                  selected by default; used in filter contexts.
 *   show-label   – when present, renders "Project" as the visible field label.
 *
 * Usage:
 *   <!-- Standalone: loads all active projects -->
 *   <project-field id="task-project" required col="col-md-6"></project-field>
 *
 *   <!-- Filtered by programme: reacts to the programme field's value -->
 *   <programme-field id="prog-field" required></programme-field>
 *   <project-field id="proj-field" programme-id="prog-field" required></project-field>
 *
 *   <!-- Filter context: shows "All Projects" as the default selection -->
 *   <project-field id="filter-project" name="project" allow-all></project-field>
 *
 *   <!-- Filter context scoped by programme -->
 *   <project-field id="filter-project" name="project" allow-all programme-id="filter-programme"></project-field>
 */
class ProjectField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label", "programme-id"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Project";
    return super._label;
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder")) this.setAttribute("placeholder", "Select project...");

    const firstConnect = this._initialOptions === undefined;
    if (firstConnect) {
      this._initialOptions = [];
      this._loadId = Symbol();
      this._programmeChangeHandler = null;
      this._watchedProgrammeEl = null;
    }

    super.connectedCallback();

    if (firstConnect) {
      this._attachProgrammeWatcher();
    }
  }

  disconnectedCallback() {
    this._loadId = Symbol();
    this._detachProgrammeWatcher();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    super.attributeChangedCallback(name, oldVal, newVal);
    if (name === "programme-id" && oldVal !== newVal && this.isConnected) {
      this._detachProgrammeWatcher();
      this._attachProgrammeWatcher();
    }
  }

  _attachProgrammeWatcher() {
    const programmeId = this.getAttribute("programme-id");

    if (!programmeId) {
      // Standalone mode — load all projects.
      this._fetchOptions(null, this._loadId);
      return;
    }

    const programmeEl = document.getElementById(programmeId);
    if (!programmeEl) {
      // Element not yet in DOM — load all projects as fallback.
      this._fetchOptions(null, this._loadId);
      return;
    }

    this._watchedProgrammeEl = programmeEl;
    this._programmeChangeHandler = () => {
      const code = this._getProgrammeValue(programmeEl);
      this._loadId = Symbol();
      this._fetchOptions(code || null, this._loadId);
    };

    programmeEl.addEventListener("change", this._programmeChangeHandler);

    // Load with the current programme value (may be empty on first render).
    const currentCode = this._getProgrammeValue(programmeEl);
    this._fetchOptions(currentCode || null, this._loadId);
  }

  _detachProgrammeWatcher() {
    if (this._watchedProgrammeEl && this._programmeChangeHandler) {
      this._watchedProgrammeEl.removeEventListener("change", this._programmeChangeHandler);
    }
    this._watchedProgrammeEl = null;
    this._programmeChangeHandler = null;
  }

  _getProgrammeValue(el) {
    const select = el.querySelector?.(".rp-input") ?? el.querySelector?.("select");
    if (select) return select.value || "";
    if (el.value !== undefined) return el.value || "";
    return "";
  }

  async _fetchOptions(programmeCode, id) {
    const select = this.querySelector(".rp-input");
    if (select) select.disabled = true;

    try {
      const { href, method } = API_URLS.projects.options();
      const url = programmeCode ? `${href}?programme=${encodeURIComponent(programmeCode)}` : href;

      const res = await apiFetch(url, { method });
      if (this._loadId !== id) return;

      const projects = res?.data ?? [];
      const hasAllOpt = this.hasAttribute("allow-all");
      this._initialOptions = [
        ...(hasAllOpt
          ? [{ id: "", label: "All Projects", value: "", selected: true, disabled: false }]
          : []),
        ...projects.map((p) => ({
          id: p.code,
          label: p.display_name || p.name,
          value: p.code,
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
      select.innerHTML = '<option value="" disabled selected>Could not load projects</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load projects. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("project-field", ProjectField);
