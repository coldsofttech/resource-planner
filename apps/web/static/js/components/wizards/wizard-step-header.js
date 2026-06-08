/* WizardStepHeader  <wizard-step-header>
 * Declarative container for a wizard step's header metadata; parsed once by <step-wizard>.
 * Must be a direct child of <wizard-step> — do not use standalone.
 *
 * Attributes:
 *   icon      – Bootstrap Icon class shown in the step header icon circle (e.g. "bi-person")
 *   title     – main heading for the step panel
 *   subtitle  – secondary descriptive text displayed below the title
 */
class WizardStepHeader extends HTMLElement {}

customElements.define("wizard-step-header", WizardStepHeader);
