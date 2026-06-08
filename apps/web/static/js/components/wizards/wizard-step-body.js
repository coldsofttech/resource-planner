/* WizardStepBody  <wizard-step-body>
 * Declarative container for a wizard step's form content; parsed once by <step-wizard>.
 * Direct children are captured and placed inside the step's `.row.g-3` body slot.
 * Must be a direct child of <wizard-step> — do not use standalone.
 */
class WizardStepBody extends HTMLElement {}

customElements.define("wizard-step-body", WizardStepBody);
