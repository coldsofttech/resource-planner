import { DropdownField } from "../../dropdowns/dropdown-field.js";

/* AuthTypeField  <auth-type-field>
 *
 * Static dropdown for filtering by authentication type.
 * Options: All Auth Types (value=""), Classic, OAuth, SAML.
 *
 * Attributes (all optional):
 *   id, name, label, col
 *   value      – "classic" | "oauth" | "saml" | "" (default: "" = All Auth Types)
 *   show-label – when present, renders "Auth Type" as the visible field label
 *
 * Extends DropdownField — inherits all validation, error, and hint behaviour.
 *
 * Usage:
 *   <!-- Filter context: shows "All Auth Types" as the default selection -->
 *   <auth-type-field id="rp-users-filter-auth-type" name="auth_type" show-label></auth-type-field>
 */
class AuthTypeField extends DropdownField {
  static get observedAttributes() {
    return [...super.observedAttributes, "show-label"];
  }

  get _col() {
    return this.getAttribute("col") || "";
  }

  get _label() {
    if (this.hasAttribute("show-label")) return this.getAttribute("label") || "Auth Type";
    return super._label;
  }

  connectedCallback() {
    if (this._initialOptions === undefined) {
      this._initialOptions = [
        { id: "", value: "", label: "All Auth Types", selected: true, disabled: false },
        { id: "classic", value: "classic", label: "Classic", selected: false, disabled: false },
        { id: "oauth", value: "oauth", label: "OAuth", selected: false, disabled: false },
        { id: "saml", value: "saml", label: "SAML", selected: false, disabled: false },
      ];
    }
    super.connectedCallback();
  }
}

customElements.define("auth-type-field", AuthTypeField);
