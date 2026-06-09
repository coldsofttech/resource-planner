/* DrawerTab  <drawer-tab>
 * Declarative data container for a single tab; parsed once by <drawer-modal> on connect.
 * Must be placed inside <drawer-tabs> — do not use standalone.
 * Text content becomes the tab label.
 *
 * Attributes:
 *   panel   – name of the <drawer-panel> this tab activates (required)
 *   count   – optional numeric badge shown next to the tab label
 *   active  – boolean; marks this tab as the initially active tab
 */
class DrawerTab extends HTMLElement {}
customElements.define("drawer-tab", DrawerTab);
