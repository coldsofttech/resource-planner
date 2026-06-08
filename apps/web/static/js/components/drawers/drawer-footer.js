/* DrawerFooter  <drawer-footer>
 * Declarative data container parsed once by <drawer-modal> on connect.
 * Place as a direct child of <drawer-modal> — do not use standalone.
 *
 * Attributes (all optional):
 *   meta             – informational text rendered on the left side of the footer
 *   close            – label for the muted close/cancel button; omit to hide the button
 *   secondary        – label for the secondary action button; omit to hide
 *   secondary-icon   – Bootstrap Icon class for the secondary button prefix icon
 *   primary          – label for the primary action button; omit to hide
 *   primary-icon     – Bootstrap Icon class for the primary button prefix icon
 *
 * Events fired by <drawer-modal> when footer buttons are clicked:
 *   rp:footer-close      – close/cancel button clicked (drawer also hides)
 *   rp:footer-secondary  – secondary button clicked
 *   rp:footer-primary    – primary button clicked
 */
class DrawerFooter extends HTMLElement {}
customElements.define("drawer-footer", DrawerFooter);
