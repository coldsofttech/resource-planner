/* WizardStep  <wizard-step>
 * Declarative container for a single wizard step; parsed once by <step-wizard> on connect.
 * Must be placed inside <wizard-steps> — do not use standalone.
 * Each step has an optional <wizard-step-header> and a <wizard-step-body> for form content.
 *
 * Attributes:
 *   nav-title     – label shown for this step in the sidebar navigator (required)
 *   nav-subtitle  – secondary text shown beneath the nav-title in the sidebar (optional)
 */
class WizardStep extends HTMLElement {}

customElements.define("wizard-step", WizardStep);
