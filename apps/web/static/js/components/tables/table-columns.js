/* TableColumns  <table-columns>
 * Declarative root container for column definitions; parsed once by <data-table> on connect.
 * Place as a direct child of <data-table> — do not use standalone.
 * Direct children must be <table-column> elements.
 */
class TableColumns extends HTMLElement {}
customElements.define("table-columns", TableColumns);
