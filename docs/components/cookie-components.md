# Cookie Components

Custom elements defined in `apps/web/static/js/components/cookie-components.js`.
Styles live in `apps/web/static/css/styles/components/cookies.css`.

---

## `<rp-cookie>`

A fixed-position cookie consent banner that renders at the bottom of the viewport. On mobile it spans the full width; on screens ≥ 900 px it pins to the bottom-right corner at 520 px wide.

**Observed attributes:**

| Attribute         | Type    | Default      | Description                                                                                         |
| ----------------- | ------- | ------------ | --------------------------------------------------------------------------------------------------- |
| `open`            | boolean | —            | Add to show the banner; remove (or omit) to hide it                                                 |
| `icon`            | string  | `bi-cookie`  | Bootstrap Icons class for the leading icon                                                          |
| `title`           | string  | `Cookies`    | Bold heading text (HTML-escaped)                                                                    |
| `body`            | string  | —            | Body text rendered as **raw HTML** — hyperlinks and inline markup are supported                     |
| `accept-label`    | string  | `Accept all` | Label for the primary accept button                                                                 |
| `reject-label`    | string  | `Reject`     | Label for the muted reject button                                                                   |
| `more-info-label` | string  | —            | Label for an optional muted "more info" button; omit to hide it                                     |
| `more-info-href`  | string  | —            | URL opened in a new tab when the more-info button is clicked (used together with `more-info-label`) |

**Events emitted:**

| Event          | Fires when                       |
| -------------- | -------------------------------- |
| `rp:accept`    | User clicks the accept button    |
| `rp:reject`    | User clicks the reject button    |
| `rp:more-info` | User clicks the more-info button |

Both the accept and reject buttons remove the `open` attribute after firing their event, which hides the banner. The more-info button does **not** close the banner.

---

**Example — minimal (default labels):**

```html
<rp-cookie open body="We use essential cookies to keep you signed in."></rp-cookie>
```

---

**Example — custom labels with a privacy-policy link:**

```html
<rp-cookie
  id="cookie-banner"
  open
  title="Cookie notice"
  body='We use essential cookies for sign-in and optional analytics. See our <a href="/privacy/">privacy policy</a>.'
  accept-label="Got it"
  reject-label="No thanks"
  more-info-label="Learn more"
  more-info-href="/privacy/"
></rp-cookie>
```

---

**Example — custom icon:**

```html
<rp-cookie
  open
  icon="bi-shield-check"
  title="Privacy"
  body="Essential cookies only. No third-party tracking."
  accept-label="OK"
  reject-label="Decline"
></rp-cookie>
```

---

**Example — listening for consent events:**

```js
const banner = document.getElementById("cookie-banner");

banner.addEventListener("rp:accept", () => {
  localStorage.setItem("cookie-consent", "accepted");
  enableAnalytics();
});

banner.addEventListener("rp:reject", () => {
  localStorage.setItem("cookie-consent", "rejected");
});
```

---

**Example — show only when consent has not yet been recorded:**

```js
if (!localStorage.getItem("cookie-consent")) {
  document.getElementById("cookie-banner").setAttribute("open", "");
}
```

---

## Notes

- The `body` attribute is injected as `innerHTML`, so HTML tags and hyperlinks work as expected. Do **not** put untrusted user-supplied content in `body`.
- The `title`, `icon`, `accept-label`, `reject-label`, and `more-info-label` attributes are HTML-escaped before rendering.
- Clicking accept or reject fires the corresponding event **before** hiding the banner, so event listeners can run synchronously.
- The more-info button opens `more-info-href` in a new tab with `noopener` and does not close the banner, allowing users to read the policy without dismissing the notice.
