/* MenuGroup  <menu-group>
 * Declarative data container for a dropdown navigation group (mega menu); parsed once by
 * <menu-bar> on connect. Must be placed inside <menu-items> — do not use standalone.
 * Child elements should be <menu-section> elements.
 *
 * Attributes:
 *   id    – optional element id
 *   name  – display label for the group trigger button (required)
 *   icon  – Bootstrap Icon class shown before the label (e.g. "bi-grid")
 *   cols  – number of columns in the mega-menu dropdown (default 1)
 */
class MenuGroup extends HTMLElement {}
customElements.define("menu-group", MenuGroup);
