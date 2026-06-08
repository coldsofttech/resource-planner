/* MenuItems  <menu-items>
 * Declarative root container for navigation items; parsed once by <menu-bar> on connect.
 * Place as a direct child of <menu-bar> — do not use standalone.
 * Direct children must be <menu-item> or <menu-group> elements.
 */
class MenuItems extends HTMLElement {}
customElements.define("menu-items", MenuItems);
