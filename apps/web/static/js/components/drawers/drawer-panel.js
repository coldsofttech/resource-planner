/* DrawerPanel  <drawer-panel>
 * Declarative content container for a drawer tab pane; parsed once by <drawer-modal> on connect.
 * Child nodes are captured then re-inserted into the rendered body slot matching the panel name.
 * Place as a direct child of <drawer-modal> — do not use standalone.
 *
 * Attributes:
 *   name  – matches the `panel` attribute on the corresponding <drawer-tab> (required)
 */
class DrawerPanel extends HTMLElement {}
customElements.define("drawer-panel", DrawerPanel);
