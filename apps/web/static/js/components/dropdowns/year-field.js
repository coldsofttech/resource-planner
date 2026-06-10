import { DropdownField } from "./dropdown-field.js";

/* YearField  <year-field>
 *
 * Dropdown that renders a list of calendar years between `min` and `max` (both inclusive).
 * Years are listed in descending order (most recent first).
 * Extends DropdownField — inherits all validation, error, and hint behaviour.
 *
 * Attributes:
 *   min        – minimum year as a 4-digit string, e.g. "2023"
 *   max        – maximum year as a 4-digit string, e.g. "2026"
 *   allow-all  – when present, prepends an "All Years" option (value="") selected by default;
 *                intended for filter contexts.
 *   show-label – when present, renders "Year" as the visible field label.
 *
 * When `min` or `max` is absent or non-numeric the year list renders empty
 * (only the "All Years" option remains when allow-all is set).
 *
 * Usage:
 *   <!-- filter context -->
 *   <year-field id="filter-year" name="year" min="2023" max="2026" allow-all show-label col="col-auto"></year-field>
 *
 *   <!-- form field (required, label visible) -->
 *   <year-field id="plan-year" name="year" min="2020" max="2030" required label="Year" col="col-md-4"></year-field>
 */
export class YearField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "min", "max", "allow-all", "show-label"];
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Year";
    return super._label;
  }

  connectedCallback() {
    // Always derive options from current attribute state; do not guard with
    // _initialOptions === undefined because min/max can differ on reconnect.
    this._initialOptions = this._buildYearOptions();
    super.connectedCallback();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (["min", "max", "allow-all"].includes(name) && this._connected && oldVal !== newVal) {
      this._initialOptions = this._buildYearOptions();
      this._doRender();
      return;
    }
    super.attributeChangedCallback(name, oldVal, newVal);
  }

  _buildYearOptions() {
    const min = parseInt(this.getAttribute("min"), 10);
    const max = parseInt(this.getAttribute("max"), 10);
    const hasAllOpt = this.hasAttribute("allow-all");
    const opts = [];

    if (hasAllOpt) {
      opts.push({ id: "", value: "", label: "All Years", selected: true, disabled: false });
    }

    if (!isNaN(min) && !isNaN(max) && min <= max) {
      for (let y = max; y >= min; y--) {
        opts.push({
          id: String(y),
          value: String(y),
          label: String(y),
          selected: !hasAllOpt && y === max,
          disabled: false,
        });
      }
    }

    return opts;
  }
}

customElements.define("year-field", YearField);
