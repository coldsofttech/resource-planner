# Table Components

Custom elements defined in `apps/web/static/js/components/tables/`.

---

## `<data-table>`

Full-featured data table with dynamic (API-driven) and static modes, sorting, pagination, and row actions.

| Attribute            | Type    | Default | Description                                                                                              |
| -------------------- | ------- | ------- | -------------------------------------------------------------------------------------------------------- |
| `url`                | string  | —       | API endpoint URL; triggers dynamic mode (auto-fetches on connect)                                        |
| `paginated`          | boolean | —       | Parses the pagination block from API response and renders a pager                                        |
| `page-size`          | number  | `20`    | Rows per page                                                                                            |
| `data`               | string  | —       | JSON array string for static mode (no API call)                                                          |
| `title`              | string  | —       | Card head title                                                                                          |
| `subtitle`           | string  | —       | Card head subtitle                                                                                       |
| `row-template`       | string  | —       | Global function name: `fn(row, index) → td cells HTML`                                                   |
| `max-inline-actions` | number  | `2`     | Max icon buttons before collapsing into a `…` overflow menu                                              |
| `empty-message`      | string  | —       | Custom empty-state text                                                                                  |
| `fixable`            | number  | —       | Number of leading columns to pin (sticky) when scrolling horizontally. Only first columns are supported. |
| `actions-fixable`    | boolean | —       | Pins the trailing actions column to the right edge when scrolling horizontally.                          |
| `expandable`         | boolean | —       | Adds a leading chevron toggle per row that expands a colspan'd detail row                                |
| `detail-template`    | string  | —       | Global function name: `fn(row, index) → detail row HTML`. Only used when `expandable` is set             |

**Declarative children (read before first render, then discarded):**

```html
<data-table url="/api/v1/teams/" paginated>
  <table-columns>
    <table-column label="Name" key="name" sortable></table-column>
    <table-column label="Status" key="is_active"></table-column>
    <table-column label="Members" key="member_count" numeric></table-column>
  </table-columns>
  <table-actions>
    <table-action icon="bi-pencil" label="Edit" event="rp:edit"></table-action>
    <table-action icon="bi-trash3" label="Delete" event="rp:delete" danger></table-action>
  </table-actions>
</data-table>
```

**Fixed (pinned) columns:**

Use `fixable` to pin the first N columns so they stay visible during horizontal scroll:

```html
<data-table url="/api/v1/projects/" paginated fixable="2">
  <table-columns>
    <table-column label="Code" key="code" width="100px"></table-column>
    <table-column label="Name" key="name" width="200px"></table-column>
    <!-- remaining columns scroll freely -->
    <table-column label="Team" key="team_name"></table-column>
    <table-column label="Status" key="status"></table-column>
    <table-column label="Budget" key="budget" numeric></table-column>
  </table-columns>
</data-table>
```

Only leading columns can be pinned (`fixable` applies from index 0). Setting `width` on fixed columns ensures consistent layout.

**Fixed actions column:**

Use `actions-fixable` to keep the row-action buttons visible at the right edge during horizontal scroll:

```html
<data-table url="/api/v1/projects/" paginated actions-fixable>
  <table-columns>
    <table-column label="Name" key="name"></table-column>
    <!-- many columns … -->
  </table-columns>
  <table-actions>
    <table-action icon="bi-pencil" label="Edit" event="rp:edit"></table-action>
    <table-action icon="bi-trash3" label="Delete" event="rp:delete" danger></table-action>
  </table-actions>
</data-table>
```

Both attributes can be combined: `<data-table fixable="2" actions-fixable>`.

**Expandable rows:**

Use `expandable` with `detail-template` to let each row expand into a
colspan'd detail row (e.g. showing sub-steps or nested detail for that row):

```html
<data-table
  url="/api/v1/engine-jobs/"
  paginated
  expandable
  row-template="renderJobRow"
  detail-template="renderJobSteps"
>
  <table-columns>
    <table-column label="Mode" key="mode_display"></table-column>
    <table-column label="Status" key="status_display"></table-column>
  </table-columns>
</data-table>

<script>
  window.renderJobRow = (row) => `<td>${row.mode_display}</td><td>${row.status_display}</td>`;
  window.renderJobSteps = (row) => `
    <strong>Steps</strong>
    <ul>${row.steps.map((s) => `<li>${s.name_display} — ${s.duration_milliseconds}ms</li>`).join("")}</ul>
  `;
</script>
```

Clicking the chevron toggles the detail row open/closed. Expanded state is
not preserved across `refresh()`/re-render — a fresh render always starts
collapsed.

**Public API:**

| Member / Method            | Description                                   |
| -------------------------- | --------------------------------------------- |
| `table.rows = [...]`       | Set rows programmatically (clears pagination) |
| `table.setRows(rows, pg?)` | Set rows + optional pagination object         |
| `table.refresh()`          | Re-fetch from `url` at the current page       |

**Events dispatched (bubble):** custom event names defined by `event=` on `<table-action>` elements. Each event carries `detail: { row: Object, index: Number }`.

---

## `<table-columns>`

Root container for `<table-column>` definitions. Parsed once by `<data-table>` on connect.

---

## `<table-column>`

Defines one column in the table.

| Attribute  | Type    | Description                                                |
| ---------- | ------- | ---------------------------------------------------------- |
| `label`    | string  | Column header text                                         |
| `key`      | string  | Row object property name to render as cell content         |
| `sortable` | boolean | Adds a sort toggle to the header; clicking cycles ASC/DESC |
| `numeric`  | boolean | Right-aligns cell content                                  |
| `mono`     | boolean | Renders cell content in a monospace font                   |
| `width`    | string  | CSS width value for the column (e.g. `120px`, `10%`)       |

---

## `<table-actions>`

Root container for `<table-action>` definitions. Parsed once by `<data-table>` on connect.

Actions beyond `max-inline-actions` collapse into a `…` overflow dropdown.

---

## `<table-action>`

Defines one row action (icon button or overflow menu item).

| Attribute    | Type    | Description                                                                                                                                                   |
| ------------ | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `icon`       | string  | Bootstrap Icon class (e.g. `bi-pencil`)                                                                                                                       |
| `label`      | string  | Accessible label (tooltip on icon button; text in overflow menu)                                                                                              |
| `event`      | string  | CustomEvent name dispatched with `{ row, index }` detail when the action is clicked                                                                           |
| `href`       | string  | Navigation URL; supports `{key}` tokens resolved from the row (e.g. `/teams/{id}/`)                                                                           |
| `danger`     | boolean | Styles the overflow menu item red                                                                                                                             |
| `hidden-key` | string  | Row field name — action is hidden for rows where that field is truthy. For multi-condition cases, add a computed field to the row data and reference it here. |
