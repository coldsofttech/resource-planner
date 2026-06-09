# Filter Components

Custom elements defined in `apps/web/static/js/components/filters/`.

---

## `<filter-panel>`

The main filter container. Operates in two modes controlled by the `layout` attribute.

| Attribute | Type                       | Default      | Description        |
| --------- | -------------------------- | ------------ | ------------------ |
| `layout`  | `horizontal` \| `vertical` | `horizontal` | Filter layout mode |

---

### Horizontal mode

A CSS flex row. Direct children must expose `.value` and a `name` (or `param`) attribute — typically `<search-field>`, `<is-active-field>`, or `<dropdown-field>`.

```html
<filter-panel>
  <search-field name="search" placeholder="Search teams…"></search-field>
  <is-active-field name="is_active" label="Status" col="col-md-3"></is-active-field>
</filter-panel>
```

Emits `rp:filter:change` when:

- `rp:search` fires (Enter on a search field)
- A search input is cleared (input event, empty value) — debounced 400 ms
- A `<select>` changes

---

### Vertical mode

Renders a filter pane from declarative `<filter-group>` / `<filter-option>` children.

```html
<filter-panel layout="vertical">
  <filter-group name="status" label="Status" open>
    <filter-option value="active" count="14" checked>Active</filter-option>
    <filter-option value="inactive" count="3">Inactive</filter-option>
  </filter-group>
  <filter-group name="type" label="Type">
    <filter-option value="project">Project</filter-option>
    <filter-option value="programme">Programme</filter-option>
  </filter-group>
</filter-panel>
```

**`<filter-group>` attributes:**

| Attribute | Type    | Description                          |
| --------- | ------- | ------------------------------------ |
| `name`    | string  | Key used in `URLSearchParams` output |
| `label`   | string  | Accordion heading                    |
| `open`    | boolean | Expands this group by default        |

**`<filter-option>` attributes:**

| Attribute | Type    | Description                                    |
| --------- | ------- | ---------------------------------------------- |
| `value`   | string  | Submitted value; falls back to text content    |
| `count`   | string  | Optional numeric label shown beside the option |
| `checked` | boolean | Pre-selects this option                        |

Features: accordion groups, meta-search input ("Filter filters"), selected-count badges, Reset button.

Emits `rp:filter:change` when any checkbox changes or Reset is clicked.

---

### Public API

| Method                     | Description                                                              |
| -------------------------- | ------------------------------------------------------------------------ |
| `filter.getParams()`       | Returns `URLSearchParams` of current filter state                        |
| `filter.reset()`           | Clears all filter state and emits `rp:filter:change`                     |
| `filter.getFilterLabels()` | Returns `[{ name, label, values: [{value, label}] }]` for active filters |
| `filter.clearFilter(name)` | Clears a specific filter by its name/param key                           |

**Event:**

| Event              | Detail                        | Description                      |
| ------------------ | ----------------------------- | -------------------------------- |
| `rp:filter:change` | `{ params: URLSearchParams }` | Fires on any filter state change |

---

## `<active-filter>`

Displays a row of removable tags for every currently active filter, plus a "Clear all" link.

Hides itself (`hidden` attribute) when no filters are active. Re-renders whenever the linked `<filter-panel>` emits `rp:filter:change`.

| Attribute   | Type    | Description                                                                                                                                |
| ----------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------ |
| `for`       | string  | `id` of the `<filter-panel>` to observe. When omitted, auto-discovers the nearest `<filter-panel>` inside the same `<list-view>` ancestor. |
| `read-only` | boolean | When present, hides the per-tag remove (×) buttons and the "Clear all" link. Filters are shown as display-only tags.                       |

**Usage (standalone):**

```html
<active-filter for="my-filter"></active-filter> <filter-panel id="my-filter">…</filter-panel>
```

**Usage inside `<list-view>` (auto-injected):**

```html
<list-view show-active-filters>
  <filter-panel>…</filter-panel>
  <data-table>…</data-table>
</list-view>
```

When `show-active-filters` is on `<list-view>`, an `<active-filter>` is injected automatically before the `<filter-panel>`.

**Public API:**

| Method                  | Description                                          |
| ----------------------- | ---------------------------------------------------- |
| `af.setFilter(panelEl)` | Wire to a specific `<filter-panel>` programmatically |
