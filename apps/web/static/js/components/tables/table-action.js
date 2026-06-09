/* TableAction  <table-action>
 * Declarative data container for a single row action; parsed once by <data-table> on connect.
 * Must be placed inside <table-actions> — do not use standalone.
 *
 * Attributes:
 *   icon   – Bootstrap Icon class shown in the action button (e.g. "bi-pencil") (required)
 *   label  – accessible label and tooltip text for the action (required)
 *   event  – CustomEvent name dispatched on click with `detail: { row, index }`
 *   href   – navigation URL on click; supports `{key}` tokens resolved from the row object
 *   danger – boolean; styles the action item in red (for destructive actions)
 */
class TableAction extends HTMLElement {}
customElements.define("table-action", TableAction);
