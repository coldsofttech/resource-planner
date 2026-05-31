# Banner Components

Custom elements defined in `apps/web/static/js/components/banner-components.js`.
Styles live in `apps/web/static/css/styles/components/banners.css`.

---

## `<rp-flash-banner>`

An inline alert banner with a coloured icon, title, optional subtitle, optional action link, and a dismiss button. Stacks naturally with adjacent banners (`margin-top: 8px` via `.rp-flash + .rp-flash`). Any extra classes added to the element (e.g. `mb-3`) are preserved across re-renders.

**Observed attributes:**

| Attribute    | Type                                        | Default               | Description                                                                             |
| ------------ | ------------------------------------------- | --------------------- | --------------------------------------------------------------------------------------- |
| `open`       | boolean                                     | —                     | Add to show the banner; remove (or omit) to hide it                                     |
| `type`       | `info` \| `success` \| `warning` \| `error` | `info`                | Sets the colour scheme and default icon                                                 |
| `icon`       | string                                      | (derived from `type`) | Bootstrap Icons class that overrides the default icon (e.g. `bi-lock-fill`)             |
| `title`      | string                                      | —                     | Bold heading text (HTML-escaped)                                                        |
| `subtitle`   | string                                      | —                     | Smaller body text rendered as **raw HTML** — inline markup and hyperlinks are supported |
| `link-label` | string                                      | —                     | Label for an optional action link; omit to hide it                                      |
| `link-href`  | string                                      | `#`                   | URL for the action link (used together with `link-label`)                               |

**Type → CSS class mapping:**

| `type`    | CSS class applied | Default icon                   |
| --------- | ----------------- | ------------------------------ |
| `info`    | `info`            | `bi-info-circle-fill`          |
| `success` | `success`         | `bi-check-circle-fill`         |
| `warning` | `warning`         | `bi-exclamation-triangle-fill` |
| `error`   | `danger`          | `bi-x-circle-fill`             |

**Events emitted:**

| Event        | Fires when                       |
| ------------ | -------------------------------- |
| `rp:dismiss` | User clicks the × dismiss button |

Clicking dismiss fires `rp:dismiss` and then removes the `open` attribute, hiding the banner.

---

**Example — authentication error with a reset link:**

```html
<rp-flash-banner
  id="login-error"
  open
  type="error"
  title="Incorrect email or password"
  subtitle="2 attempts remaining before your account is locked for 15 minutes."
  link-label="Reset password"
  link-href="/forgot-password/"
></rp-flash-banner>
```

---

**Example — success confirmation:**

```html
<rp-flash-banner
  open
  type="success"
  title="Settings saved"
  subtitle="Your changes have been applied."
></rp-flash-banner>
```

---

**Example — warning with inline HTML in the subtitle:**

```html
<rp-flash-banner
  open
  type="warning"
  title="Subscription expiring soon"
  subtitle='Your plan expires in <strong>3 days</strong>. <a href="/billing/">Renew now</a> to avoid interruption.'
></rp-flash-banner>
```

---

**Example — custom icon:**

```html
<rp-flash-banner
  open
  type="error"
  icon="bi-shield-x"
  title="Access denied"
  subtitle="You do not have permission to view this resource."
></rp-flash-banner>
```

---

**Example — showing and hiding programmatically:**

```js
const banner = document.getElementById("login-error");

// Show
banner.setAttribute("open", "");

// Update content before showing
banner.setAttribute("type", "error");
banner.setAttribute("title", "Incorrect email or password");
banner.setAttribute("subtitle", "2 attempts remaining.");
banner.setAttribute("open", "");

// Listen for dismiss
banner.addEventListener("rp:dismiss", () => {
  console.log("User dismissed the banner");
});
```

---

**Example — adding spacing without losing dynamic classes:**

```html
<!-- Extra classes like mb-3 are preserved across re-renders -->
<rp-flash-banner class="mb-3" open type="info" title="Maintenance window tonight"></rp-flash-banner>
```

---

## Notes

- The `subtitle` attribute is injected as `innerHTML`, so inline HTML and hyperlinks work as expected. Do **not** put untrusted user-supplied content in `subtitle`.
- `title`, `icon`, `link-label`, and `link-href` are HTML-escaped before rendering.
- The dismiss button is always present. If you need a non-dismissible banner, listen for `rp:dismiss` and call `event.target.setAttribute("open", "")` to reopen it, or simply suppress the handler.
- The component sets `role="alert"` on itself at connect time so screen readers announce the banner when it appears.
