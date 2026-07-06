import { DropdownField } from "../../dropdowns/dropdown-field.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* SprintField  <sprint-field>
 *
 * Dropdown field pre-wired to the sprints API.
 * Active sprints are fetched from GET /api/v1/sprints/options/ on connect, and
 * retried on reconnect until the fetch succeeds at least once.
 * Options display the sprint name (e.g. "Sprint 1").
 * Inherits all attributes and public API from DropdownField / BaseField.
 *
 * Defaults applied when the attribute is absent:
 *   label       → "Sprint"
 *   placeholder → "Select sprint…"
 *
 * Attributes:
 *   fy-code    – filters options to the given financial year code; re-fetches on change.
 *   allow-all  – prepends an "All Sprints" option (value="") selected by default;
 *                used in filter contexts.
 *   unassign   – prepends an "Unassign from current sprint" option (value="");
 *                used in edit contexts when the field already has a value and the user
 *                should be able to explicitly clear the sprint assignment.
 *   show-label – when present, renders "Sprint" as the visible field label.
 *
 * Usage:
 *   <sprint-field id="plan-sprint" required col="col-md-6"></sprint-field>
 *   <sprint-field id="plan-sprint" fy-code="FY-1"></sprint-field>
 *   <sprint-field id="filter-sprint" name="sprint" allow-all show-label></sprint-field>
 */
class SprintField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label", "allow-all", "unassign", "fy-code"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) {
      return this.getAttribute("label") || "Sprint";
    }
    return super._label;
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (name === "allow-all" || name === "unassign") {
      if (this._connected && this._sprintOptions !== undefined) {
        const saved = this._savedValue();
        this._initialOptions = this._collectSprintOptions();
        this._doRender();
        if (saved !== null) this._restoreValue(saved);
      }
      // If not yet connected or options not loaded, _fetchOptions / connectedCallback
      // will call _collectSprintOptions() and pick up the current attribute state.
      return;
    } else if (name === "fy-code" && this._connected && oldVal !== newVal) {
      this._sprintOptions = undefined;
      this._initialOptions = [];
      this._loaded = false;
      this._loadId = Symbol();
      const select = this.querySelector(".rp-input");
      if (select) select.disabled = true;
      this._fetchOptions(this._loadId);
    } else {
      super.attributeChangedCallback(name, oldVal, newVal);
    }
  }

  connectedCallback() {
    if (!this.hasAttribute("placeholder")) {
      this.setAttribute("placeholder", "Select sprint…");
    }

    if (this._initialOptions === undefined) this._initialOptions = [];

    super.connectedCallback();

    // Fetch whenever options haven't successfully loaded yet — not just on the very first
    // connect. Containers like <tab-panel> capture and re-insert child nodes on their own
    // initial render, which disconnects/reconnects this element before its first fetch
    // resolves; gating on "first connect" alone would then discard that in-flight result
    // and never retry, leaving the dropdown stuck on its placeholder.
    if (!this._loaded) {
      const select = this.querySelector(".rp-input");
      if (select) select.disabled = true;
      this._loadId = Symbol();
      this._fetchOptions(this._loadId);
    }
  }

  disconnectedCallback() {
    this._loadId = Symbol();
  }

  refresh() {
    this._loaded = false;
    this._loadId = Symbol();
    this._fetchOptions(this._loadId);
  }

  async _fetchOptions(id) {
    try {
      const fyCode = this.getAttribute("fy-code") || null;
      const { href, method } = API_URLS.sprints.options();
      const url = fyCode ? `${href}?fy_code=${encodeURIComponent(fyCode)}` : href;
      const res = await apiFetch(url, { method });
      if (this._loadId !== id) return;

      const sprints = res?.data ?? [];
      this._sprintOptions = sprints.map((s) => ({
        id: s.code,
        label: s.name,
        value: s.code,
        selected: false,
        disabled: false,
      }));

      this._initialOptions = this._collectSprintOptions();
      this._loaded = true;
      this._doRender();
    } catch {
      if (this._loadId !== id) return;
      this._setFetchError();
    }
  }

  // Builds the option-objects array for _initialOptions.
  // Named distinctly to avoid shadowing DropdownField._buildOptions() (the HTML string builder).
  _collectSprintOptions() {
    const hasAllOpt = this.hasAttribute("allow-all");
    const hasUnassign = this.hasAttribute("unassign");
    return [
      ...(hasAllOpt
        ? [{ id: "", label: "All Sprints", value: "", selected: true, disabled: false }]
        : []),
      ...(hasUnassign
        ? [
            {
              id: "",
              label: "Unassign from current sprint",
              value: "",
              selected: false,
              disabled: false,
            },
          ]
        : []),
      ...(this._sprintOptions || []),
    ];
  }

  _setFetchError() {
    const select = this.querySelector(".rp-input");
    const errEl = this.querySelector("[data-rp-error]");
    if (select) {
      select.disabled = true;
      select.innerHTML = '<option value="" disabled selected>Could not load sprints</option>';
    }
    if (errEl) {
      errEl.textContent = "Could not load sprints. Refresh the page to retry.";
      errEl.hidden = false;
    }
  }
}

customElements.define("sprint-field", SprintField);
