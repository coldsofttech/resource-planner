import { DropdownField } from "../../dropdowns/dropdown-field.js";

/* IsActiveField: <is-active-field>
 *
 * Business-specific dropdown for the is_active field.
 * Options: All Statuses (no filter), Active (true), Inactive (false).
 *
 * Attributes (all optional):
 *   id, name, label, col, required, hint, hint-type
 *   value      – "true" | "false" | "" (default: "" = All Statuses)
 *   show-label – when present, renders "Status" as the visible field label
 *
 * Extends DropdownField — inherits all validation, error, and hint behaviour.
 */
class IsActiveField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label"];
  }

  get _col() {
    return this.getAttribute("col") || "";
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Status";
    return super._label;
  }

  connectedCallback() {
    if (this._initialOptions === undefined) {
      this._initialOptions = [
        { id: "", value: "all", label: "All Statuses", selected: true, disabled: false },
        { id: "active", value: "true", label: "Active", selected: false, disabled: false },
        { id: "inactive", value: "false", label: "Inactive", selected: false, disabled: false },
      ];
    }
    super.connectedCallback();
  }
}

customElements.define("is-active-field", IsActiveField);
