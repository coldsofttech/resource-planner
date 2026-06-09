/* TabHeader  <tab-header>
 * Declares the visual config for one tab button; parsed once by <tab-panel> on connect.
 * Place as a direct child of <tab-item> — do not use standalone.
 *
 * Attributes:
 *   title  – tab button label
 *   icon   – Bootstrap Icon class (e.g. "bi-person") shown before the label
 *   count  – optional badge number shown after the label
 */
class TabHeader extends HTMLElement {}
customElements.define("tab-header", TabHeader);
