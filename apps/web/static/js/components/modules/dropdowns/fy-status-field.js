import { DropdownField } from "../../dropdowns/dropdown-field.js";

/* FyStatusField: <fy-status-field>
 *
 * Business-specific dropdown for the financial year status field.
 * Options: Future, In Progress, Completed, Expired.
 *
 * Attributes (all optional):
 *   id, name, label, col, required, hint, hint-type
 *   value      – "future" | "in_progress" | "completed" | "expired" | "" (default: "" = All Statuses)
 *   allow-all  – prepends an "All Statuses" option (value="") selected by default; used in filter contexts
 *   show-label – when present, renders "Status" as the visible field label
 *
 * Extends DropdownField — inherits all validation, error, and hint behaviour.
 */

const STATUS_OPTIONS = [
  { id: "future", value: "future", label: "Future", selected: false, disabled: false },
  {
    id: "in_progress",
    value: "in_progress",
    label: "In Progress",
    selected: false,
    disabled: false,
  },
  { id: "completed", value: "completed", label: "Completed", selected: false, disabled: false },
  { id: "expired", value: "expired", label: "Expired", selected: false, disabled: false },
];

class FyStatusField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label", "allow-all"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Status";
    return super._label;
  }

  connectedCallback() {
    if (this._initialOptions === undefined) {
      this._initialOptions = this._statusOptions();
    }
    super.connectedCallback();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (name === "allow-all" && this._connected) {
      this._initialOptions = this._statusOptions();
      this._doRender();
    } else {
      super.attributeChangedCallback(name, oldVal, newVal);
    }
  }

  _statusOptions() {
    if (this.hasAttribute("allow-all")) {
      return [
        { id: "", value: "", label: "All Statuses", selected: true, disabled: false },
        ...STATUS_OPTIONS,
      ];
    }
    return [{ ...STATUS_OPTIONS[0], selected: true }, ...STATUS_OPTIONS.slice(1)];
  }
}

customElements.define("fy-status-field", FyStatusField);
