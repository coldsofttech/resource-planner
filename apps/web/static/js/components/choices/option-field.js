/* OptionField  <option-field>
 * Declarative data container for a single option within a <checkbox-group-field> or
 * <radio-group-field>. Parsed once by the group on connect — do not use standalone.
 *
 * Attributes:
 *   label     – display text for the option (falls back to text content when absent)
 *   value     – submitted value for this option
 *   checked   – boolean; pre-selects this option
 *   disabled  – boolean; disables this option
 */
class OptionField extends HTMLElement {}

customElements.define("option-field", OptionField);
