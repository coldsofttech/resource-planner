# Button Components

Custom elements defined in `apps/web/static/js/components/buttons/`.

All button variants share the same attribute surface via `PrimaryButton`. They render a single `<button>` internally and re-render whenever an observed attribute changes.

---

## Common Attributes

| Attribute     | Type                            | Default  | Description                                                       |
| ------------- | ------------------------------- | -------- | ----------------------------------------------------------------- |
| `label`       | string                          | —        | Button text                                                       |
| `prefix-icon` | string                          | —        | Bootstrap Icons class for a leading icon (e.g. `bi-arrow-left`)   |
| `suffix-icon` | string                          | —        | Bootstrap Icons class for a trailing icon (e.g. `bi-arrow-right`) |
| `disabled`    | boolean                         | —        | Disables the button                                               |
| `type`        | `button` \| `submit` \| `reset` | `button` | Native button type                                                |

---

## `<primary-button>`

Primary action button styled with `rp-btn-primary`.

```html
<primary-button label="Save" suffix-icon="bi-check2" type="submit"></primary-button>
```

---

## `<secondary-button>`

Secondary action button styled with `rp-btn-secondary`. Used for secondary actions that need visual weight without being the primary call-to-action.

```html
<secondary-button label="Export" prefix-icon="bi-download"></secondary-button>
```

---

## `<muted-button>`

Muted / tertiary button styled with `rp-btn-muted`. Used for non-destructive secondary actions such as Back or Cancel.

```html
<muted-button label="Back" prefix-icon="bi-arrow-left"></muted-button>
```

---

## `<engine-button>`

Engine-styled button (`rp-btn-engine`). Used for prominent utility / processing actions.

```html
<engine-button label="Run Engine" prefix-icon="bi-play-fill"></engine-button>
```

---

## `<delete-button>`

Destructive delete button styled with `rp-btn-delete` (red). Used for irreversible delete actions.

```html
<delete-button label="Delete" prefix-icon="bi-trash3"></delete-button>
```

---

## `<activate-button>`

Activate button styled with `rp-btn-activate`. Used for activation confirmation actions.

```html
<activate-button label="Activate" prefix-icon="bi-toggle-on"></activate-button>
```

---

## `<deactivate-button>`

Deactivate button styled with `rp-btn-deactivate`. Used for deactivation confirmation actions.

```html
<deactivate-button label="Deactivate" prefix-icon="bi-toggle-off"></deactivate-button>
```

---

## `<dropdown-button>`

Split button that combines a primary action on the left with a dropdown panel of additional options on the right. Shares the same variant and size system as the single-action buttons above.

### Attributes

| Attribute     | Type                                                                                                   | Default   | Description                                         |
| ------------- | ------------------------------------------------------------------------------------------------------ | --------- | --------------------------------------------------- |
| `label`       | string                                                                                                 | —         | Text shown on the main (left) button                |
| `prefix-icon` | string                                                                                                 | —         | Bootstrap Icons class for the main button icon      |
| `variant`     | `primary` \| `secondary` \| `muted` \| `engine` \| `delete` \| `activate` \| `deactivate` \| `neutral` | `primary` | Visual style applied to both halves of the button   |
| `size`        | `sm` \| `lg`                                                                                           | —         | Size modifier — maps to `.rp-btn-sm` / `.rp-btn-lg` |
| `disabled`    | boolean                                                                                                | —         | Disables both the main button and the chevron       |

### Child elements (`<values-list>` / `<value>`)

Dropdown options are declared as `<value>` children inside a `<values-list>`. They are captured once on first connect and are not re-read on subsequent reconnections.

| Attribute  | Type    | Description                                                                             |
| ---------- | ------- | --------------------------------------------------------------------------------------- |
| `value`    | string  | Identifier included in the `rp:select` event detail (used for non-href items)           |
| `icon`     | string  | Bootstrap Icons class shown before the label (e.g. `bi-kanban`)                         |
| `href`     | string  | When set, the item renders as `<a href="…">` for page navigation instead of a JS action |
| `disabled` | boolean | Greys out the item and prevents interaction                                             |

### Event

`rp:select` — bubbles from the host element when a non-href item is clicked.

```js
el.addEventListener("rp:select", (e) => {
  const { value, label } = e.detail;
});
```

Items that have `href` trigger native navigation and do not fire `rp:select`.

### Examples

```html
<!-- Primary split button with mixed link and JS-action items -->
<dropdown-button label="New project" prefix-icon="bi-plus-lg">
  <values-list>
    <value icon="bi-kanban" href="/projects/new/">From scratch</value>
    <value icon="bi-clipboard-data" value="estimate">From estimate</value>
    <value icon="bi-upload" value="import" disabled>Import (coming soon)</value>
  </values-list>
</dropdown-button>

<!-- Secondary, small -->
<dropdown-button label="Add" variant="secondary" size="sm">
  <values-list>
    <value icon="bi-person-plus" value="member">Add member</value>
    <value icon="bi-building" value="team">Add team</value>
  </values-list>
</dropdown-button>

<!-- Muted -->
<dropdown-button label="Export" variant="muted" prefix-icon="bi-download">
  <values-list>
    <value icon="bi-filetype-csv" value="csv">CSV</value>
    <value icon="bi-filetype-xlsx" value="xlsx">Excel</value>
  </values-list>
</dropdown-button>
```

### JS interaction

```js
document.querySelector("dropdown-button").addEventListener("rp:select", (e) => {
  const { value, label } = e.detail; // e.g. "estimate", "From estimate"
  // handle action
});
```

### Notes

- The chevron half and the main button inherit the same variant and size — no extra classes needed.
- The dropdown panel aligns to the right edge of the button (`right: 0`) via the existing `.rp-splitbtn-wrap > .rp-dd-panel` CSS rule.
- Outside-click and Escape key handling are self-contained — no additional wiring is needed.
- `disabled` on the host disables both halves. `disabled` on a `<value>` item disables only that row.

---

## Button State Utilities

Use the shared utilities from `utils/index.js` for async button state management:

```js
import { snapshotButton, setBusyButton, restoreButton } from "/static/js/modules/utils/index.js";

async function handleSubmit(btn) {
  const snap = snapshotButton(btn);
  setBusyButton(btn, "Saving…");
  try {
    await apiFetch(/* ... */);
    restoreButton(btn, snap, { label: "Saved", suffixIcon: "bi-check-circle-fill" });
  } catch {
    restoreButton(btn, snap);
  }
}
```

---

## Notes

- All variants are used by `<step-wizard>` internally for Back/Next/Finish navigation.
- The `disabled` attribute is reflected onto the inner `<button>` so CSS `:disabled` selectors work.
- Icon-only buttons (no `label`) are valid — set only `prefix-icon` or `suffix-icon`.
