/* MenuSection  <menu-section>
 * Declarative data container for a labelled section within a <menu-group> dropdown;
 * parsed once by <menu-bar> on connect. Must be placed inside <menu-group> — do not use
 * standalone. Child elements should be <menu-item> elements.
 *
 * Attributes:
 *   label  – section heading displayed above the items in the dropdown column
 */
class MenuSection extends HTMLElement {}
customElements.define("menu-section", MenuSection);
