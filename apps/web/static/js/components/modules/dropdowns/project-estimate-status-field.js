import { DropdownField } from "../../dropdowns/dropdown-field.js";

/* ProjectEstimateStatusField  <project-estimate-status-field>
 *
 * Business-specific dropdown for project estimate status.
 * Options: Draft, Reviewed, Shared, Approved.
 * When `allow-superseded` is present, Superseded is appended as the last option.
 *
 * Attributes (all optional):
 *   id, name, label, col, required, hint, hint-type
 *   value             – "DRAFT" | "REVIEWED" | "SHARED" | "APPROVED" | "SUPERSEDED" | ""
 *   allow-all         – prepends an "All Statuses" option (value="") selected by default;
 *                       used in filter contexts
 *   allow-superseded  – appends "Superseded" as the last option
 *   show-label        – when present, renders "Status" as the visible field label
 *
 * Extends DropdownField — inherits all validation, error, and hint behaviour.
 */

const BASE_OPTIONS = [
  { id: "DRAFT", value: "DRAFT", label: "Draft", selected: false, disabled: false },
  { id: "REVIEWED", value: "REVIEWED", label: "Reviewed", selected: false, disabled: false },
  { id: "SHARED", value: "SHARED", label: "Shared", selected: false, disabled: false },
  { id: "APPROVED", value: "APPROVED", label: "Approved", selected: false, disabled: false },
];

const SUPERSEDED_OPTION = {
  id: "SUPERSEDED",
  value: "SUPERSEDED",
  label: "Superseded",
  selected: false,
  disabled: false,
};

class ProjectEstimateStatusField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label", "allow-all", "allow-superseded"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Status";
    return super._label;
  }

  connectedCallback() {
    if (this._initialOptions === undefined) {
      this._initialOptions = this._getOptions();
    }
    super.connectedCallback();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if ((name === "allow-all" || name === "allow-superseded") && this._connected) {
      this._initialOptions = this._getOptions();
      this._doRender();
    } else {
      super.attributeChangedCallback(name, oldVal, newVal);
    }
  }

  _getOptions() {
    const allOpt = this.hasAttribute("allow-all")
      ? [{ id: "", value: "", label: "All Statuses", selected: true, disabled: false }]
      : [];
    const superseded = this.hasAttribute("allow-superseded") ? [SUPERSEDED_OPTION] : [];
    const base = allOpt.length
      ? BASE_OPTIONS
      : [{ ...BASE_OPTIONS[0], selected: true }, ...BASE_OPTIONS.slice(1)];
    return [...allOpt, ...base, ...superseded];
  }
}

customElements.define("project-estimate-status-field", ProjectEstimateStatusField);
