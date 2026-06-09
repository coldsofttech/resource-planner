/* PanelBody  <panel-body>
 * Declarative container for the body content of a <section-panel>. Its direct child nodes
 * are captured once and inserted into the rendered card body slot. Do not use standalone —
 * must be a direct child of <section-panel>. */
class PanelBody extends HTMLElement {}

customElements.define("panel-body", PanelBody);
