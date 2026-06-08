/* WizardSteps  <wizard-steps>
 * Declarative root container for a <step-wizard>; parsed once on connect.
 * Holds all <wizard-step> children and configures the wizard's sidebar and navigation labels.
 * Must be a direct child of <step-wizard> — do not use standalone.
 *
 * Attributes:
 *   title           – sidebar section heading (default "Setup Steps")
 *   estimated-time  – estimated completion time displayed in the sidebar footer
 *   show-progress   – boolean; shows a progress bar in the sidebar footer
 *   back-label      – label for the Back button (default "Back")
 *   next-label      – label for the Next button (default "Next")
 *   finish-label    – label for the Finish button on the last step (default "Finish")
 */
class WizardSteps extends HTMLElement {}

customElements.define("wizard-steps", WizardSteps);
