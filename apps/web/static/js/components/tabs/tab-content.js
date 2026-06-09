/* TabContent  <tab-content>
 * Holds the panel body for one tab; child nodes are captured once by <tab-panel> on connect
 * and re-inserted into the rendered panel slot, preserving component state.
 * Place as a direct child of <tab-item> — do not use standalone.
 */
class TabContent extends HTMLElement {}
customElements.define("tab-content", TabContent);
