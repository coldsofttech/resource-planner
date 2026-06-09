/* MenuItem  <menu-item>
 * Declarative data container for a single navigation link; parsed once by <menu-bar> on connect.
 * Must be placed inside <menu-items> — do not use standalone.
 *
 * Attributes:
 *   id    – optional element id
 *   name  – display label for the nav item (required)
 *   href  – navigation URL (default "#")
 *   icon  – Bootstrap Icon class shown before the label (e.g. "bi-house")
 *
 * Active state: automatically applied when `href` exactly matches or is a prefix of the
 * current pathname.
 */
class MenuItem extends HTMLElement {}
customElements.define("menu-item", MenuItem);
