# Button Components

Custom elements defined in `apps/web/static/js/components/button-components.js`.

All button variants share the same attribute surface via `ButtonPrimary`. They render a single `<button>` internally and re-render whenever an observed attribute changes.

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

## `<rp-button-primary>`

Primary action button styled with `rp-btn-primary`.

**Example:**

```html
<rp-button-primary label="Save" suffix-icon="bi-check2" type="submit"></rp-button-primary>
```

---

## `<rp-button-muted>`

Secondary / muted button styled with `rp-btn-muted`. Used for non-destructive secondary actions such as Back.

**Example:**

```html
<rp-button-muted label="Back" prefix-icon="bi-arrow-left"></rp-button-muted>
```

---

## `<rp-button-engine>`

Engine-styled button (`rp-btn-engine`). Used for prominent utility actions.

**Example:**

```html
<rp-button-engine label="Run" prefix-icon="bi-play-fill"></rp-button-engine>
```

---

## Notes

- All three variants are used by `<rp-wizard>` internally for its Back/Next/Finish navigation.
- The `disabled` attribute is reflected directly onto the inner `<button>`, so standard CSS `:disabled` and `button.disabled` selectors both work.
- Icons-only buttons (no `label`) are valid — set only `prefix-icon` or `suffix-icon`.
