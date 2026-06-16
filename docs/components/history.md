# History Components

Custom elements defined in `apps/web/static/js/components/history/`.

| Component       | Purpose                                                  |
| --------------- | -------------------------------------------------------- |
| `history-panel` | Card container that wraps a history timeline             |
| `history-items` | Timeline body — manages loading/empty/error states       |
| `history-item`  | A single timeline entry with icon, label, note, and meta |

---

## `<history-panel>`

Card shell for a version-history timeline. Captures its direct child elements before rendering and re-inserts them into the panel body slot, preserving any nested component state.

| Attribute | Type   | Default              | Description                         |
| --------- | ------ | -------------------- | ----------------------------------- |
| `title`   | string | `"Version History"`  | Panel header text                   |
| `icon`    | string | `"bi-clock-history"` | Bootstrap Icon class for the header |
| `col`     | string | `"col-12"`           | Bootstrap column class              |

```html
<history-panel title="Change Log" col="col-md-8">
  <history-items id="my-history">
    <history-item label="Created" meta="2 hours ago"></history-item>
  </history-items>
</history-panel>
```

---

## `<history-items>`

Timeline body component. Renders a placeholder message when empty, and exposes methods for loading / setting items programmatically.

| Attribute     | Type   | Default                   | Description                          |
| ------------- | ------ | ------------------------- | ------------------------------------ |
| `placeholder` | string | `"No history available."` | Text shown when no items are present |

**Public API:**

| Method                       | Description                                                          |
| ---------------------------- | -------------------------------------------------------------------- |
| `items.loading(msg?)`        | Shows a spinner with optional message (default `"Loading history…"`) |
| `items.empty(msg?)`          | Shows the placeholder (or custom `msg`)                              |
| `items.error(msg?)`          | Shows an error message (default `"Failed to load history."`)         |
| `items.setItems(elements[])` | Replaces the body with the provided `<history-item>` elements        |

```js
const history = document.getElementById("my-history");

history.loading();
try {
  const items = await fetchHistory(entityCode);
  history.setItems(
    items.map((h) => {
      const el = document.createElement("history-item");
      el.setAttribute("label", h.action);
      el.setAttribute("meta", h.timestamp);
      el.setAttribute("note", h.note || "");
      return el;
    }),
  );
} catch {
  history.error();
}
```

---

## `<history-item>`

A single entry in the history timeline. All user-supplied values are rendered via `textContent` — never `innerHTML` — so no escaping is required.

| Attribute    | Type    | Default | Description                                                                             |
| ------------ | ------- | ------- | --------------------------------------------------------------------------------------- |
| `label`      | string  | —       | Primary line (action name or event type)                                                |
| `icon`       | string  | —       | Bootstrap Icon class for the timeline dot (e.g. `bi-pencil`)                            |
| `icon-color` | string  | —       | Named colour token: `accent` \| `success` \| `muted` \| `danger` \| `warning` \| `info` |
| `status`     | string  | —       | Secondary label rendered next to `label` (e.g. a status badge value)                    |
| `note`       | string  | —       | Indented note text below the label                                                      |
| `meta`       | string  | —       | Timestamp or other secondary text shown on the right                                    |
| `connector`  | boolean | —       | When present, draws a vertical line below the icon to connect to the next item          |

```html
<history-items>
  <history-item
    label="Status changed to Active"
    icon="bi-check-circle"
    icon-color="success"
    meta="3 hours ago"
    connector
  ></history-item>
  <history-item
    label="Created"
    icon="bi-plus-circle"
    icon-color="accent"
    note="Initial project setup"
    meta="2025-01-15 09:30"
  ></history-item>
</history-items>
```
