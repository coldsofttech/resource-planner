/* PanelHeader  <panel-header>
 * Declarative slot for the header region of a <card-panel>.
 * Its child nodes are captured once and inserted into .rp-card-head.
 * Do not use standalone — must be a direct child of <card-panel>. */
class PanelHeader extends HTMLElement {}

customElements.define("panel-header", PanelHeader);
