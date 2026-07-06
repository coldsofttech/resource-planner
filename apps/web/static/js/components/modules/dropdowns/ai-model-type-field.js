import { DropdownField } from "../../dropdowns/dropdown-field.js";

/* AiModelTypeField  <ai-model-type-field>
 *
 * Static dropdown for selecting an AI provider.
 * Options: Anthropic | AWS Bedrock.
 *
 * Attributes (all optional):
 *   id, name, label, col
 *   value      – "anthropic" | "bedrock"
 *   show-label – when present, renders the field label
 *   required   – when present, marks the field as required
 *
 * Extends DropdownField — inherits all validation, error, and hint behaviour.
 *
 * Usage:
 *   <ai-model-type-field id="rp-ai-provider" name="ai_provider" label="AI Provider" show-label required></ai-model-type-field>
 */
class AiModelTypeField extends DropdownField {
  connectedCallback() {
    if (this._initialOptions === undefined) {
      this._initialOptions = [
        { id: "", value: "", label: "Select provider…", selected: true, disabled: false },
        {
          id: "anthropic",
          value: "anthropic",
          label: "Anthropic",
          selected: false,
          disabled: false,
        },
        { id: "bedrock", value: "bedrock", label: "AWS Bedrock", selected: false, disabled: false },
      ];
    }
    super.connectedCallback();
  }
}

customElements.define("ai-model-type-field", AiModelTypeField);
