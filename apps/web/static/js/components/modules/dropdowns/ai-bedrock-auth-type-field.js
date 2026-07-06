import { DropdownField } from "../../dropdowns/dropdown-field.js";

/* AiBedrockAuthTypeField  <ai-bedrock-auth-type-field>
 *
 * Static dropdown for selecting the AWS Bedrock authentication mode.
 * Options: IAM Role (instance profile) | IAM User (access key).
 *
 * Attributes (all optional):
 *   id, name, label, col
 *   value      – "role" | "user"
 *   show-label – when present, renders the field label
 *
 * Extends DropdownField — inherits all validation, error, and hint behaviour.
 *
 * Usage:
 *   <ai-bedrock-auth-type-field id="rp-ai-bedrock-auth-mode" name="ai_bedrock_auth_mode" show-label></ai-bedrock-auth-type-field>
 */
class AiBedrockAuthTypeField extends DropdownField {
  connectedCallback() {
    if (this._initialOptions === undefined) {
      this._initialOptions = [
        { id: "", value: "", label: "Select auth mode…", selected: true, disabled: false },
        {
          id: "role",
          value: "role",
          label: "IAM Role (instance profile)",
          selected: false,
          disabled: false,
        },
        {
          id: "user",
          value: "user",
          label: "IAM User (access key)",
          selected: false,
          disabled: false,
        },
      ];
    }
    super.connectedCallback();
  }
}

customElements.define("ai-bedrock-auth-type-field", AiBedrockAuthTypeField);
