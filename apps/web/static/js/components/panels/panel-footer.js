/* PanelFooter  <panel-footer>
 * Declarative slot for the footer region of a <card-panel>.
 * Its child nodes are captured once and inserted into .rp-card-foot.
 * Do not use standalone — must be a direct child of <card-panel>. */
class PanelFooter extends HTMLElement {}

customElements.define("panel-footer", PanelFooter);
