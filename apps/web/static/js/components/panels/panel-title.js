/* PanelTitle  <panel-title>
 * Declarative container for rich HTML heading content inside a <section-panel>.
 * Its innerHTML is captured once and used as the card heading, overriding the `title` attribute.
 * Do not use standalone — must be a direct child of <section-panel>. */
class PanelTitle extends HTMLElement {}

customElements.define("panel-title", PanelTitle);
