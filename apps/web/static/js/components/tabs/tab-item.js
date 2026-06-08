/* TabItem  <tab-item>
 * Declarative container for one tab's header config and content; parsed once by <tab-panel>.
 * Place inside <tab-items> — do not use standalone.
 *
 * Attributes:
 *   id      – stable id for programmatic setTab() calls; defaults to "tab-{index}"
 *   active  – boolean; marks this tab as the initially active one
 */
class TabItem extends HTMLElement {}
customElements.define("tab-item", TabItem);
