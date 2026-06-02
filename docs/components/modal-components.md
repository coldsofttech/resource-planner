# Modal Components

Custom elements defined in `apps/web/static/js/components/modal-components.js`.

---

## `<rp-modal-status>`

A full-screen overlay modal with an icon hero, title, body text, an optional rich HTML slot, and up to three action buttons (dismiss / secondary / primary).

**Observed attributes:**

| Attribute          | Type                                        | Default                    | Description                                                                               |
| ------------------ | ------------------------------------------- | -------------------------- | ----------------------------------------------------------------------------------------- |
| `open`             | boolean                                     | —                          | Add to show the modal; remove to hide it                                                  |
| `closeable`        | `"false"` \| any                            | `true`                     | Set `closeable="false"` to prevent the × button and backdrop-click from closing the modal |
| `icon-type`        | `info` \| `success` \| `warning` \| `error` | `info`                     | Selects the background colour class and default icon                                      |
| `icon`             | string                                      | (derived from `icon-type`) | Bootstrap Icons class that overrides the default icon (e.g. `bi-rocket`)                  |
| `icon-bg-color`    | string                                      | —                          | Inline CSS colour for the icon background (e.g. `#6f42c1`)                                |
| `title`            | string                                      | —                          | Heading text                                                                              |
| `body`             | string                                      | —                          | Paragraph text below the heading                                                          |
| `dismiss-label`    | string                                      | —                          | Label for the muted dismiss button; omit to hide it                                       |
| `secondary-label`  | string                                      | —                          | Label for the secondary button; omit to hide it                                           |
| `secondary-icon`   | string                                      | —                          | Bootstrap Icons class prefixed to the secondary button label                              |
| `primary-label`    | string                                      | —                          | Label for the primary button; omit to hide it                                             |
| `primary-icon`     | string                                      | —                          | Bootstrap Icons class prefixed to the primary button label                                |
| `primary-href`     | string                                      | —                          | When set, clicking primary navigates to this URL (after emitting `rp:primary`)            |
| `primary-disabled` | boolean                                     | —                          | Disables the primary button                                                               |

**Programmatic API:**

| Method                    | Description                                                                   |
| ------------------------- | ----------------------------------------------------------------------------- |
| `setAdditionalBody(html)` | Injects arbitrary HTML into the additional-body slot below the main body text |

**Events emitted:**

| Event          | Fires when                       |
| -------------- | -------------------------------- |
| `rp:dismiss`   | User clicks the dismiss button   |
| `rp:secondary` | User clicks the secondary button |
| `rp:primary`   | User clicks the primary button   |

**Example — success confirmation:**

```html
<rp-modal-status
  id="save-modal"
  icon-type="success"
  title="Setup complete"
  body="Your configuration has been saved."
  primary-label="Go to Dashboard"
  primary-icon="bi-house"
  primary-href="/dashboard/"
  closeable="false"
></rp-modal-status>
```

```js
// Open it programmatically
document.getElementById("save-modal").setAttribute("open", "");

// Listen for primary click
document.getElementById("save-modal").addEventListener("rp:primary", () => {
  console.log("User clicked primary");
});
```

**Example — error with dynamic detail:**

```html
<rp-modal-status
  id="error-modal"
  icon-type="error"
  title="Something went wrong"
  dismiss-label="Close"
></rp-modal-status>
```

```js
const modal = document.getElementById("error-modal");
modal.setAttribute("body", "Failed to connect to the database.");
modal.setAdditionalBody(`<pre class="rp-code">ECONNREFUSED 127.0.0.1:5432</pre>`);
modal.setAttribute("open", "");
```

---

## Notes

- The modal backdrop is the element itself (full-screen grid). Clicking outside the inner `.rp-modal` box closes it when `closeable` is not `"false"`.
- The additional-body slot persists across attribute-change re-renders only when set via `setAdditionalBody()` before the next render; storing it in `_additionalBody` ensures it is re-injected.
- All button labels are HTML-escaped; use `setAdditionalBody()` for rich content.
