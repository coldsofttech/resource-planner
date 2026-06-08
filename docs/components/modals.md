# Modal Components

Custom elements defined in `apps/web/static/js/components/modals/`.

All modal components share a common `Modal` base class. Use `show()` / `hide()` to control visibility programmatically.

---

## Common Base Attributes

Every modal inherits these attributes from `Modal`:

| Attribute   | Type    | Default | Description                                                              |
| ----------- | ------- | ------- | ------------------------------------------------------------------------ |
| `open`      | boolean | —       | Modal is visible when present; managed via `show()` / `hide()`           |
| `closeable` | string  | —       | Set to `"false"` to remove the × button and disable backdrop-click-close |

**Public API (all variants):**

| Method         | Description      |
| -------------- | ---------------- |
| `modal.show()` | Opens the modal  |
| `modal.hide()` | Closes the modal |

**Interactions:** backdrop click closes (unless `closeable="false"`); × close button closes (unless `closeable="false"`).

---

## `<status-modal>`

A centred icon + title + body modal for status displays (progress, confirmation, result). Configure entirely via attributes; re-renders on any attribute change.

For programmatic control from JS, use the `statusModal` singleton utility — see `utilities.md`.

| Attribute          | Type                                        | Default | Description                                                           |
| ------------------ | ------------------------------------------- | ------- | --------------------------------------------------------------------- |
| `icon-type`        | `info` \| `success` \| `warning` \| `error` | `info`  | Icon style and colour                                                 |
| `icon`             | string                                      | —       | Bootstrap Icon class override; defaults to the `icon-type` icon       |
| `icon-bg-color`    | string                                      | —       | CSS colour value for the icon circle background                       |
| `title`            | string                                      | —       | Heading text                                                          |
| `body`             | string                                      | —       | Paragraph text below the title                                        |
| `dismiss-label`    | string                                      | —       | Label for the muted dismiss button; omit to hide                      |
| `secondary-label`  | string                                      | —       | Label for the secondary button; omit to hide                          |
| `secondary-icon`   | string                                      | —       | Bootstrap Icon class for the secondary button prefix                  |
| `primary-label`    | string                                      | —       | Label for the primary button; omit to hide                            |
| `primary-icon`     | string                                      | —       | Bootstrap Icon class for the primary button prefix                    |
| `primary-href`     | string                                      | —       | When set, primary click navigates to this URL instead of firing event |
| `primary-disabled` | boolean                                     | —       | Disables the primary button when present                              |

**Additional public API:**

| Method                          | Description                                                               |
| ------------------------------- | ------------------------------------------------------------------------- |
| `modal.setAdditionalBody(html)` | Injects extra HTML into the additional-body slot without a full re-render |

**Events fired (all bubble):**

| Event          | Description                                                 |
| -------------- | ----------------------------------------------------------- |
| `rp:dismiss`   | Dismiss button clicked (modal also hides)                   |
| `rp:secondary` | Secondary button clicked                                    |
| `rp:primary`   | Primary button clicked (navigates if `primary-href` is set) |

```html
<status-modal
  id="my-status"
  icon-type="success"
  title="Done!"
  body="Your changes have been saved."
  primary-label="Continue"
  primary-href="/dashboard/"
></status-modal>
```

---

## `<delete-modal>`

Extends the panel modal with a destructive delete action. Optionally gates the action behind a text-confirmation input.

Inherits `open` and `closeable` from `Modal`, plus `title` from `PanelModal`.

| Attribute             | Type   | Default  | Description                                                                  |
| --------------------- | ------ | -------- | ---------------------------------------------------------------------------- |
| `body`                | string | —        | Explanatory text shown in the modal body                                     |
| `confirm-value`       | string | —        | String the user must type to enable the Delete button; omit to skip the gate |
| `confirm-placeholder` | string | —        | Placeholder for the confirmation input; defaults to `Type "…" to confirm`    |
| `action-label`        | string | `Delete` | Label for the Delete button                                                  |

**Events fired (all bubble):**

| Event       | Description                                       |
| ----------- | ------------------------------------------------- |
| `rp:delete` | Delete button clicked (confirmation guard passed) |
| `rp:cancel` | Cancel button clicked (modal also hides)          |

```html
<delete-modal
  id="confirm-delete"
  title="Delete Team"
  body="This action cannot be undone."
  confirm-value="Engineering"
  action-label="Delete Team"
></delete-modal>
```

---

## `<activate-modal>`

Confirmation modal for activation actions. Extends `ConfirmModal`.

| Attribute      | Type   | Default    | Description                  |
| -------------- | ------ | ---------- | ---------------------------- |
| `title`        | string | —          | Modal heading                |
| `body`         | string | —          | Explanatory text             |
| `action-label` | string | `Activate` | Label for the confirm button |

**Events fired:** `rp:confirm` (bubbles), `rp:cancel` (bubbles, modal also hides).

```html
<activate-modal id="confirm-activate" title="Activate Team" body="Are you sure?"></activate-modal>
```

---

## `<deactivate-modal>`

Confirmation modal for deactivation actions. Extends `ConfirmModal`.

| Attribute      | Type   | Default      | Description                  |
| -------------- | ------ | ------------ | ---------------------------- |
| `title`        | string | —            | Modal heading                |
| `body`         | string | —            | Explanatory text             |
| `action-label` | string | `Deactivate` | Label for the confirm button |

**Events fired:** `rp:confirm` (bubbles), `rp:cancel` (bubbles, modal also hides).

```html
<deactivate-modal
  id="confirm-deactivate"
  title="Deactivate Team"
  body="Are you sure?"
></deactivate-modal>
```

---

**Inheritance chain:**

```
Modal (base)
  └── PanelModal
        ├── ConfirmModal (base)
        │     ├── ActivateModal   <activate-modal>
        │     └── DeactivateModal <deactivate-modal>
        └── DeleteModal           <delete-modal>
  └── StatusModal                 <status-modal>
```
