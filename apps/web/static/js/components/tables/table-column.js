/* TableColumn  <table-column>
 * Declarative data container defining a single table column; parsed once by <data-table>.
 * Must be placed inside <table-columns> — do not use standalone.
 *
 * Attributes:
 *   label    – column heading text (required)
 *   key      – row object key whose value is displayed in this column (required)
 *   sortable – boolean; when present, the column heading becomes a sort toggle
 *   numeric  – boolean; right-aligns the cell content
 *   mono     – boolean; renders the cell value in a monospace font
 *   width    – CSS width value applied to the column (e.g. "120px", "10%")
 */
class TableColumn extends HTMLElement {}
customElements.define("table-column", TableColumn);
