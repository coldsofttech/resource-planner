/* DrawerTabs  <drawer-tabs>
 * Declarative container for <drawer-tab> elements; parsed once by <drawer-modal> on connect.
 * Place as a direct child of <drawer-modal> — do not use standalone.
 * When present, the drawer renders a tab bar and shows/hides panels by name.
 */
class DrawerTabs extends HTMLElement {}
customElements.define("drawer-tabs", DrawerTabs);
