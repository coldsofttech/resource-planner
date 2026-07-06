# Email Components

Custom elements defined in `apps/web/static/js/components/emails/`.

---

## `<email-view>`

Read-only email preview component. Renders To, Cc, and Subject metadata rows followed by the full HTML body of the email.

All declarative children are captured once on connect and replaced by the rendered output.

**Declarative children:**

| Element            | Description                                                                                                       |
| ------------------ | ----------------------------------------------------------------------------------------------------------------- |
| `<email-to-items>` | Container for To recipients. Required.                                                                            |
| `<email-to-item>`  | A single To recipient — place inside `<email-to-items>`, use `value` attribute.                                   |
| `<email-cc-items>` | Container for Cc recipients. Omit to hide the Cc row entirely.                                                    |
| `<email-cc-item>`  | A single Cc recipient — place inside `<email-cc-items>`, use `value` attribute.                                   |
| `<email-subject>`  | Subject line. Text content becomes the displayed subject.                                                         |
| `<email-body>`     | Email body. `innerHTML` is rendered as-is; accepts arbitrary HTML. Content must be trusted/application-generated. |

**Container attributes** (`<email-to-items>`, `<email-cc-items>`, `<email-subject>`):

| Attribute | Type   | Default            | Description                                 |
| --------- | ------ | ------------------ | ------------------------------------------- |
| `icon`    | string | see defaults below | Bootstrap Icon class shown in the row label |

Default icons: `To` → `bi-person-fill` · `Cc` → `bi-people-fill` · `Subject` → `bi-tag`

**Item attributes** (`<email-to-item>`, `<email-cc-item>`):

| Attribute | Type   | Description           |
| --------- | ------ | --------------------- |
| `value`   | string | Email address or name |

**Usage:**

```html
<email-view>
  <email-to-items icon="bi-person-fill">
    <email-to-item value="team@example.com"></email-to-item>
    <email-to-item value="lead@example.com"></email-to-item>
  </email-to-items>
  <email-cc-items icon="bi-people-fill">
    <email-cc-item value="manager@example.com"></email-cc-item>
  </email-cc-items>
  <email-subject icon="bi-tag">Recharge Approval Request — Sprint 183 (FY26-27)</email-subject>
  <email-body>
    <p>Dear Team,</p>
    <p>We are writing to request your approval…</p>
  </email-body>
</email-view>
```

**Without Cc** (Cc row is hidden when `<email-cc-items>` is absent):

```html
<email-view>
  <email-to-items>
    <email-to-item value="team@example.com"></email-to-item>
  </email-to-items>
  <email-subject>Sprint 183 — Forecast</email-subject>
  <email-body>
    <p>Email content here.</p>
  </email-body>
</email-view>
```
