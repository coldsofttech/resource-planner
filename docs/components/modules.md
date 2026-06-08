# Module Components

Pre-configured components from `apps/web/static/js/components/modules/`. These build on shared primitives for domain-specific use cases.

---

## Views

### `<list-view>`

Coordinator that connects a `<filter-panel>` child to a `<data-table>` child. When the filter emits `rp:filter:change`, this element builds the new URL (base URL + filter params) and sets it on the table, triggering a reload.

| Attribute             | Type                       | Default      | Description                                                               |
| --------------------- | -------------------------- | ------------ | ------------------------------------------------------------------------- |
| `layout`              | `horizontal` \| `vertical` | `horizontal` | `horizontal`: filter bar above table; `vertical`: filterpane beside table |
| `show-active-filters` | boolean                    | —            | When present, auto-injects an `<active-filter>` before the filter panel   |

**Usage (horizontal):**

```html
<list-view show-active-filters>
  <filter-panel>
    <search-field name="search" placeholder="Search teams…"></search-field>
    <is-active-field name="is_active" label="Status" col="col-md-3"></is-active-field>
  </filter-panel>
  <data-table url="/api/v1/teams/" paginated>
    <table-columns>…</table-columns>
    <table-actions>…</table-actions>
  </data-table>
</list-view>
```

**Usage (vertical):**

```html
<list-view layout="vertical" show-active-filters>
  <filter-panel layout="vertical">
    <filter-group name="status" label="Status" open>
      <filter-option value="true" count="12">Active</filter-option>
      <filter-option value="false" count="3">Inactive</filter-option>
    </filter-group>
  </filter-panel>
  <data-table url="/api/v1/teams/" paginated>…</data-table>
</list-view>
```

---

### `<import-view>`

Self-contained import workflow inside a large `<drawer-modal>`. See source for full API — exposes `show()` / `hide()` and fires `rp:import:complete`.

---

### `<export-view>`

Self-contained export workflow inside a large `<drawer-modal>`. On open: mirrors active filters read-only and loads column specs. Fires `rp:export` when the Export button is clicked — actual download is not wired yet.

| Attribute          | Type   | Description                                                                                                                                                           |
| ------------------ | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`            | string | Drawer title. Default: `"Export"`                                                                                                                                     |
| `eyebrow`          | string | Optional eyebrow text above the title                                                                                                                                 |
| `active-filter-id` | string | `id` of an `<active-filter>` (or `<filter-panel>`) whose active filters are shown read-only inside the drawer. When omitted the filter row is not rendered.           |
| `specs-url`        | string | `GET` endpoint returning `{ data: { columns: [{ key, label }] } }` — populates the column checkboxes                                                                  |
| `export-url`       | string | `GET` endpoint for the actual export download (reserved — not wired yet)                                                                                              |
| `table-id`         | string | Optional `id` of a `<data-table>`; columns whose `key` matches a `<table-column key="…">` on that table are pre-checked. All columns checked by default when omitted. |

**Events:**

| Event       | Detail                | Description                                                                                                                  |
| ----------- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `rp:export` | `{ format, columns }` | Fired on Export click. `format` is `"csv"` \| `"xlsx"` \| `"pdf"` \| `"json"`. `columns` is an array of checked column keys. |

**Usage:**

```html
<export-view
  id="teams-export"
  title="Export Teams"
  eyebrow="Teams"
  active-filter-id="rp-teams-active-filter"
  specs-url="/api/v1/teams/export/specs/"
  export-url="/api/v1/teams/export/"
  table-id="rp-teams-table"
>
</export-view>
```

```js
document.getElementById("rp-teams-export-btn").addEventListener("click", () => {
  document.getElementById("teams-export").show();
});
```

**Public API:**

| Method        | Description       |
| ------------- | ----------------- |
| `view.show()` | Opens the drawer  |
| `view.hide()` | Closes the drawer |

---

## Pills

### `<sprint-pill>`

Displays the active sprint name and a live countdown to its end date. The element hides itself when `name` is omitted.

| Attribute | Type   | Default  | Description                                                             |
| --------- | ------ | -------- | ----------------------------------------------------------------------- |
| `name`    | string | —        | Sprint label (e.g. `S24.10`); element hides when absent                 |
| `end`     | string | —        | ISO-8601 datetime of the sprint end (e.g. `2026-05-30T17:00:00`)        |
| `status`  | string | `active` | `active` \| `warning` \| `inactive` — controls the indicator dot colour |

The countdown auto-updates every minute. Set attributes from JS after sprint data is available — the element is pre-mounted in `templates/base.html` as `<sprint-pill id="active-sprint">`.

```js
const pill = document.getElementById("active-sprint");
pill.setAttribute("name", "S24.10");
pill.setAttribute("end", "2026-05-30T17:00:00");
pill.setAttribute("status", "active");
```

---

## Dropdowns

### `<is-active-field>`

Business-specific status filter dropdown. Pre-configured options — no `<values-list>` child needed. See `dropdowns.md` for full documentation.

---

## Module Fields

Pre-configured text field wrappers from `apps/web/static/js/components/modules/fields/`.

### `<first-name-field>`

Pre-configured `<text-field>`. Defaults: label "First name", required, maxlength 100, placeholder "John", autocomplete "given-name".

### `<last-name-field>`

Pre-configured `<text-field>`. Defaults: label "Last name", required, maxlength 100, placeholder "Doe", autocomplete "family-name".
