/* TableActions  <table-actions>
 * Declarative root container for row action definitions; parsed once by <data-table> on connect.
 * Place as a direct child of <data-table> — do not use standalone.
 * Direct children must be <table-action> elements.
 * When the total action count exceeds `max-inline-actions` (default 2), overflow actions are
 * collapsed into a "…" dropdown menu.
 */
class TableActions extends HTMLElement {}
customElements.define("table-actions", TableActions);
