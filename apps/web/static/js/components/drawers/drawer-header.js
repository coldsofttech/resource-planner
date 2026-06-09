/* DrawerHeader  <drawer-header>
 * Declarative data container parsed once by <drawer-modal> on connect.
 * Place as a direct child of <drawer-modal> — do not use standalone.
 *
 * Attributes (all optional):
 *   eyebrow        – small eyebrow text rendered above the title
 *   title          – main heading text inside the drawer header
 *   badge          – badge label displayed next to the title
 *   badge-variant  – badge colour variant (default "neutral"); matches rp-badge variants
 *   no-sizes       – boolean; when present, hides the width snap buttons (440/640/900/full)
 *
 * Children (optional):
 *   <identicon-field> – when present as a direct child, the drawer places it in the header
 *                       avatar slot (before the title block). Set `name` and `variant` from JS.
 *   <user-avatar>     – alternative to <identicon-field>; placed in the same header avatar slot.
 *                       Set `avatar-url` and `name` from JS.
 */
class DrawerHeader extends HTMLElement {}
customElements.define("drawer-header", DrawerHeader);
