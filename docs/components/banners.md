# Banner Components

Custom elements defined in `apps/web/static/js/components/banners/`.

---

## `<flash-banner>`

An inline alert banner with a coloured icon, title, optional subtitle, optional action link, and a dismiss button. Stacks naturally with adjacent banners. Any extra classes added to the element (e.g. `mb-3`) are preserved across re-renders.

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

**Events emitted:**

| Event        | Fires when                       |
| ------------ | -------------------------------- |
| `rp:dismiss` | User clicks the × dismiss button |

**Example:**

```html
<flash-banner
  id="login-error"
  open
  type="error"
  title="Incorrect email or password"
  subtitle="2 attempts remaining before your account is locked."
  link-label="Reset password"
  link-href="/forgot-password/"
></flash-banner>
```

```js
const banner = document.getElementById("login-error");
banner.setAttribute("open", "");
banner.addEventListener("rp:dismiss", () => {
  /* ... */
});
```

**Notes:**

- `subtitle` is injected as `innerHTML` — do not put untrusted content there.
- The dismiss button is always rendered. To suppress dismissal, listen for `rp:dismiss` and re-open.
- Sets `role="alert"` automatically so screen readers announce the banner.

---

## `<fy-flash-banner>`

A system-wide top-strip banner for application-level announcements (e.g. Financial Year expiry). Unlike `<flash-banner>`, its message is rich HTML placed inside a `<banner-message>` child rather than an attribute. Pre-mounted in `templates/base.html` — do not add another instance.

**Observed attributes:**

| Attribute     | Type                                         | Default     | Description                             |
| ------------- | -------------------------------------------- | ----------- | --------------------------------------- |
| `open`        | boolean                                      | —           | Show the banner; remove to hide         |
| `type`        | `warning` \| `info` \| `danger` \| `success` | `warning`   | Sets background colour and default icon |
| `icon`        | string                                       | (from type) | Bootstrap Icons class override          |
| `link-label`  | string                                       | —           | CTA anchor text; omit to hide           |
| `link-href`   | string                                       | `#`         | CTA anchor URL                          |
| `dismissable` | boolean                                      | —           | Show the × dismiss button               |

**Declarative child:**

```html
<banner-message>Rich HTML content here</banner-message>
```

Content is captured once on first connect. Updating the child after connect has no effect.

**Events emitted:**

| Event        | Fires when                       |
| ------------ | -------------------------------- |
| `rp:dismiss` | User clicks the × dismiss button |

**Example:**

```html
<fy-flash-banner
  id="fy-banner"
  type="warning"
  link-label="Open Financial Years"
  link-href="/financial-years/"
  dismissable
  open
>
  <banner-message>
    Financial Year <strong>FY25–26</strong> expires in <strong>14 days</strong>.
  </banner-message>
</fy-flash-banner>
```

**Notes:**

- Use `<fy-flash-banner>` for system-wide top-strip notifications. Use `<flash-banner>` for inline page-level alerts.
- When `dismissable` is absent, no dismiss button is rendered.

---

## `<cookie-banner>`

A cookie consent banner rendered at the bottom of the viewport. Manages cookie preference state via the `setCookieConsent()` / `getCookieConsent()` utilities.

**Observed attributes:**

| Attribute      | Type   | Default                  | Description           |
| -------------- | ------ | ------------------------ | --------------------- |
| `title`        | string | `"We use cookies"`       | Banner heading text   |
| `body`         | string | (default policy text)    | Body paragraph text   |
| `accept-label` | string | `"Accept all"`           | Accept button label   |
| `reject-label` | string | `"Reject non-essential"` | Reject button label   |
| `more-label`   | string | `"Learn more"`           | Learn-more link label |
| `more-href`    | string | `"#"`                    | Learn-more link URL   |
| `policy-label` | string | `"Privacy Policy"`       | Policy link label     |
| `policy-href`  | string | `"#"`                    | Policy link URL       |

**Events emitted:**

| Event          | Fires when                      |
| -------------- | ------------------------------- |
| `rp:accept`    | User clicks the accept button   |
| `rp:reject`    | User clicks the reject button   |
| `rp:more-info` | User clicks the learn-more link |
