# Field Components

Custom elements defined in `apps/web/static/js/components/field-components.js`. All field elements share a common base and integrate with the wizard's `rp:validate` event.

---

## Common Base Attributes

Every field component inherits these attributes from `BaseField`:

| Attribute      | Type                                         | Default       | Description                                                                                                                         |
| -------------- | -------------------------------------------- | ------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `col`          | string                                       | `col-md-6`    | Bootstrap column class applied to the host element                                                                                  |
| `label`        | string                                       | —             | Label text shown above the input                                                                                                    |
| `required`     | boolean                                      | —             | Marks the field as required; shows `*` and validates on blur                                                                        |
| `id`           | string                                       | —             | Sets element `id`; also used as `for` on the label and to derive `name`                                                             |
| `name`         | string                                       | `id` value    | Input `name` attribute; falls back to `id`                                                                                          |
| `hint`         | string                                       | —             | Plain-text hint shown below the input                                                                                               |
| `hint-type`    | `info` \| `warning` \| `success` \| `danger` | `info`        | Controls hint icon and colour                                                                                                       |
| `value`        | string                                       | —             | Initial value                                                                                                                       |
| `autocomplete` | string                                       | per-component | HTML `autocomplete` value forwarded to the native input/select; each component defines a sensible default (see individual sections) |

A `<field-hint>` child element can provide rich HTML hint content and takes precedence over the `hint` attribute.

---

## `<rp-field-text>`

Plain text input.

**Extra attributes:**

| Attribute      | Type    | Default | Description                                                                                                                                                 |
| -------------- | ------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `placeholder`  | string  | —       | Input placeholder                                                                                                                                           |
| `maxlength`    | number  | —       | Max character count                                                                                                                                         |
| `show-counter` | boolean | —       | Show a live character counter next to the label (`N/max` format). Requires `maxlength` to display the max cap; without it, only the current count is shown. |
| `autocomplete` | string  | `off`   | Overrides the built-in default                                                                                                                              |

**Counter notes:**

- When `show-counter` is present the label row becomes a flex row with the counter pushed to the trailing edge.
- Counter initialises to the length of the initial `value` and updates on every keystroke.
- The current count uses `var(--rp-text-subtle)`; the `/max` cap uses `var(--rp-border-strong)` and `font-variant-numeric: tabular-nums` for stable width.

**Custom validator hook:**

`_customValidators` is a public array on every text field instance. Push `{ fn, msg }` objects to add extra validation without subclassing:

```js
const el = document.getElementById("my-field");
el._customValidators.push({
  fn: (value) => /^[A-Z0-9]{20}$/.test(value),
  msg: "Must be 20 uppercase alphanumeric characters.",
});
```

The validators run after the built-in required check. The first failing validator wins.

**HTML in field values:**

Allowed HTML tags (`<b>`, `<strong>`, `<i>`, `<em>`, `<u>`, `<sup>`, `<sub>`) may be stored in a text field's value when it will later be rendered as `innerHTML`. Use `isValidAppNameHtml()` from `validators.js` to validate that only these tags are used and every opening tag has a matching close.

**Example:**

```html
<rp-field-text
  id="app-name"
  label="Application Name"
  placeholder="My App"
  required
  maxlength="50"
  show-counter
  autocomplete="organization"
  col="col-md-8"
></rp-field-text>
```

---

## `<rp-field-first-name>`

Specialised text field with defaults: label `First name`, `required`, `maxlength="100"`, placeholder `John`, autocomplete `given-name`.

All `rp-field-text` attributes are supported and can override the defaults.

**Example:**

```html
<rp-field-first-name id="first-name"></rp-field-first-name>
```

---

## `<rp-field-last-name>`

Specialised text field with defaults: label `Last name`, `required`, `maxlength="100"`, placeholder `Doe`, autocomplete `family-name`.

**Example:**

```html
<rp-field-last-name id="last-name"></rp-field-last-name>
```

---

## `<rp-field-email>`

Email input with format validation.

**Extra attributes:**

| Attribute      | Type    | Default                | Description                         |
| -------------- | ------- | ---------------------- | ----------------------------------- |
| `placeholder`  | string  | `john.doe@example.com` | Input placeholder                   |
| `maxlength`    | number  | `255`                  | Max character count                 |
| `prefix-icon`  | boolean | —                      | Show envelope icon inside the input |
| `autocomplete` | string  | `email`                | Overrides the built-in default      |

**Example:**

```html
<rp-field-email id="admin-email" label="Admin Email" required prefix-icon></rp-field-email>
```

---

## `<rp-field-website>`

URL input with a scheme selector dropdown. Validates that the hostname contains at least one dot (bare words like `notaurl` without a TLD are rejected).

**Extra attributes:**

| Attribute               | Type    | Default                          | Description                                                                                                                    |
| ----------------------- | ------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| `placeholder`           | string  | `example.com`                    | Input placeholder                                                                                                              |
| `maxlength`             | number  | —                                | Max character count                                                                                                            |
| `scheme`                | string  | first `<scheme>` with `selected` | Active scheme prefix                                                                                                           |
| `prefix-icon`           | boolean | —                                | Show globe icon                                                                                                                |
| `open-button`           | boolean | —                                | Show an external-link button that opens the URL                                                                                |
| `accept-trailing-slash` | boolean | —                                | When absent (default), trailing slashes are stripped from the raw path on blur. When present, trailing slashes are kept as-is. |
| `autocomplete`          | string  | `url`                            | Overrides the built-in default                                                                                                 |

Scheme options are declared as `<scheme-list><scheme>` children before the element renders. Mark one `selected`; mark one `disabled` to grey it out.

**Trailing slash behaviour:**

By default (`accept-trailing-slash` absent) the field strips trailing slashes on `blur` so values like `example.com/path/` become `example.com/path`. Set `accept-trailing-slash` on fields where a trailing slash is meaningful (e.g. ACS callback URLs).

**Programmatic API:**

| Member     | Description                   |
| ---------- | ----------------------------- |
| `value`    | Full URL (scheme + path)      |
| `rawValue` | Path portion only (no scheme) |
| `scheme`   | Active scheme string          |

**Example — no trailing slash (default):**

```html
<rp-field-website id="app-url" label="App URL" required open-button prefix-icon>
  <scheme-list>
    <scheme value="https://" selected>https://</scheme>
    <scheme value="http://">http://</scheme>
  </scheme-list>
</rp-field-website>
```

**Example — accept trailing slash (ACS/callback URL):**

```html
<rp-field-website id="acs-url" label="ACS URL" required prefix-icon accept-trailing-slash>
  <scheme-list>
    <scheme value="https://" selected>https://</scheme>
    <scheme value="http://">http://</scheme>
  </scheme-list>
</rp-field-website>
```

---

## `<rp-field-password>`

Password input with optional strength meter and show/hide toggle.

**Extra attributes:**

| Attribute      | Type    | Default          | Description                                                          |
| -------------- | ------- | ---------------- | -------------------------------------------------------------------- |
| `placeholder`  | string  | `Enter password` | Input placeholder                                                    |
| `prefix-icon`  | boolean | —                | Show key icon                                                        |
| `eye-icon`     | boolean | —                | Show show/hide toggle button                                         |
| `strength`     | boolean | —                | Show a 4-segment strength bar **and enforce strong password policy** |
| `autocomplete` | string  | `new-password`   | Use `current-password` for login flows                               |

**Strong password policy (when `strength` is present):**

Validation blocks advancement until all four criteria are met: 12+ characters, at least one uppercase letter, at least one lowercase letter, at least one digit, at least one symbol. Each unmet criterion produces a specific error message. The same rules are enforced server-side in `AdminInputSerializer.validate_password()`.

**Programmatic API:**

| Member     | Description                                |
| ---------- | ------------------------------------------ |
| `strength` | Integer 0–4 representing password strength |

**Example:**

```html
<rp-field-password
  id="admin-password"
  label="Password"
  required
  prefix-icon
  eye-icon
  strength
></rp-field-password>
```

---

## `<rp-field-confirm-password>`

Confirms that its value matches a sibling `<rp-field-password>`. Shows a green **Matches.** indicator on success; shows a validation error on mismatch that blocks wizard step advancement.

**Extra attributes:**

| Attribute           | Type    | Default        | Description                                          |
| ------------------- | ------- | -------------- | ---------------------------------------------------- |
| `password-field-id` | string  | —              | `id` of the `<rp-field-password>` to compare against |
| `prefix-icon`       | boolean | —              | Show key icon                                        |
| `eye-icon`          | boolean | —              | Show show/hide toggle                                |
| `autocomplete`      | string  | `new-password` | Overrides the built-in default                       |

**Validation behaviour:**

- Empty field → "Please confirm your password."
- Non-empty but does not match → "Passwords do not match." (shown once in the error slot; the match indicator is hidden).
- Matches → green "Matches." shown in the match indicator slot; no error.

**Example:**

```html
<rp-field-password id="pw" label="Password" required eye-icon></rp-field-password>
<rp-field-confirm-password
  id="pw-confirm"
  label="Confirm password"
  password-field-id="pw"
  eye-icon
></rp-field-confirm-password>
```

---

## `<rp-field-secret>`

Password-style input that renders an **Encrypted** badge on the label. Intended for storing secrets that will be Fernet-encrypted on the server.

**Extra attributes:**

| Attribute     | Type    | Default              | Description           |
| ------------- | ------- | -------------------- | --------------------- |
| `placeholder` | string  | `Enter secret value` | Input placeholder     |
| `prefix-icon` | boolean | —                    | Show shield-lock icon |
| `eye-icon`    | boolean | —                    | Show show/hide toggle |

**Example:**

```html
<rp-field-secret
  id="smtp-password"
  label="SMTP Password"
  required
  eye-icon
  prefix-icon
></rp-field-secret>
```

---

## `<rp-field-dropdown>`

Select element with declarative `<values-list><value>` options.

**Extra attributes:**

| Attribute      | Type   | Default | Description                                                 |
| -------------- | ------ | ------- | ----------------------------------------------------------- |
| `placeholder`  | string | —       | Disabled placeholder option shown when no value is selected |
| `autocomplete` | string | `off`   | Overrides the built-in default                              |

Options are declared as `<values-list><value>` children. Each `<value>` supports:

- `value` attribute (falls back to text content)
- `selected` boolean attribute
- `disabled` boolean attribute
- `id` attribute (passed through to the `<option>`)

**Example:**

```html
<rp-field-dropdown id="auth-mode" label="Auth Mode" required placeholder="Select…">
  <values-list>
    <value value="classic" selected>Classic</value>
    <value value="oauth">OAuth</value>
    <value value="saml">SAML</value>
  </values-list>
</rp-field-dropdown>
```

---

## `<rp-field-number>`

Number input with optional min/max/step constraints.

**Extra attributes:**

| Attribute      | Type   | Default | Description                    |
| -------------- | ------ | ------- | ------------------------------ |
| `placeholder`  | string | —       | Input placeholder              |
| `min`          | number | —       | Minimum allowed value          |
| `max`          | number | —       | Maximum allowed value          |
| `step`         | number | `1`     | Increment step                 |
| `autocomplete` | string | `off`   | Overrides the built-in default |

**Example:**

```html
<rp-field-number
  id="smtp-port"
  label="SMTP Port"
  required
  min="1"
  max="65535"
  value="587"
></rp-field-number>
```

---

## `<rp-field-decimal>`

Identical to `<rp-field-number>` but defaults `step` to `0.1`. Inherits autocomplete default `off` from `<rp-field-number>`.

**Example:**

```html
<rp-field-decimal id="rate" label="Tax Rate (%)" min="0" max="100" value="10"></rp-field-decimal>
```

---

## `<rp-field-checkbox>`

Single checkbox input.

**Extra attributes:**

| Attribute  | Type    | Default | Description                  |
| ---------- | ------- | ------- | ---------------------------- |
| `value`    | string  | `on`    | Value submitted when checked |
| `checked`  | boolean | —       | Initial checked state        |
| `disabled` | boolean | —       | Disables the input           |

**Programmatic API:**

| Member    | Description                   |
| --------- | ----------------------------- |
| `checked` | Get/set current checked state |

**Example:**

```html
<rp-field-checkbox id="allow-reg" label="Allow user registration" checked></rp-field-checkbox>
```

---

## `<rp-field-checkbox-group>`

Group of checkboxes sharing a name, defined via `<rp-option>` children.

**Programmatic API:**

| Member  | Description                              |
| ------- | ---------------------------------------- |
| `value` | Comma-separated string of checked values |

**Example:**

```html
<rp-field-checkbox-group id="features" label="Features" required>
  <rp-option value="logs" label="Logging" checked></rp-option>
  <rp-option value="metrics" label="Metrics"></rp-option>
  <rp-option value="alerts" label="Alerts" disabled></rp-option>
</rp-field-checkbox-group>
```

---

## `<rp-field-radio>`

Single radio button (rarely used standalone; prefer `<rp-field-radio-group>`).

Attributes: same as `<rp-field-checkbox>`.

---

## `<rp-field-radio-group>`

Mutually exclusive radio buttons defined via `<rp-option>` children.

**Programmatic API:**

| Member  | Description                            |
| ------- | -------------------------------------- |
| `value` | Value of the currently selected option |

**Example:**

```html
<rp-field-radio-group id="deployment-type" label="Deployment Type" required>
  <rp-option value="local" label="Local" checked></rp-option>
  <rp-option value="aws" label="AWS"></rp-option>
</rp-field-radio-group>
```

---

## `<rp-field-toggle>`

Single toggle switch. Visually styled differently from a checkbox but otherwise identical in behaviour.

Attributes: same as `<rp-field-checkbox>`.

**Example:**

```html
<rp-field-toggle id="smtp-auth" label="Enable SMTP authentication"></rp-field-toggle>
```

---

## `<rp-field-toggle-group>`

Group of toggle switches. Identical to `<rp-field-checkbox-group>` with a toggle visual style.

**Example:**

```html
<rp-field-toggle-group id="notifs" label="Notifications">
  <rp-option value="email" label="Email" checked></rp-option>
  <rp-option value="sms" label="SMS"></rp-option>
</rp-field-toggle-group>
```

---

## `<rp-field-hint>`

Standalone banner-style hint block, not attached to any input.

**Attributes:**

| Attribute | Type                                         | Default  | Description                     |
| --------- | -------------------------------------------- | -------- | ------------------------------- |
| `type`    | `info` \| `warning` \| `success` \| `danger` | `info`   | Colour and icon                 |
| `col`     | string                                       | `col-12` | Bootstrap column class          |
| `title`   | string                                       | —        | Bold title line inside the hint |

Inner HTML is rendered as the hint body (HTML allowed).

**Example:**

```html
<rp-field-hint type="warning" col="col-12" title="Important">
  Changes here require a server restart to take effect.
</rp-field-hint>
```

---

## `<rp-option>`

Data container used inside `<rp-field-checkbox-group>`, `<rp-field-radio-group>`, and `<rp-field-toggle-group>`.

**Attributes:**

| Attribute  | Type    | Default      | Description           |
| ---------- | ------- | ------------ | --------------------- |
| `value`    | string  | `""`         | Submitted value       |
| `label`    | string  | text content | Display label         |
| `checked`  | boolean | —            | Initial checked state |
| `disabled` | boolean | —            | Disables this option  |

---

## Events

All field components listen to `rp:validate` — the wizard fires this event on a panel to trigger validation of every field inside it. Fields respond by marking themselves touched, showing inline error messages, and calling `input.setCustomValidity(err)` on the underlying native input so the wizard's `reportValidity()` loop correctly blocks step advancement for any custom error (including password mismatch, Fernet key format, AWS key format, etc.).

## Validators utility (`validators.js`)

`apps/web/static/js/modules/utils/validators.js` exports the following functions used both in field components and wizard-specific wiring:

| Function                  | Description                                                             |
| ------------------------- | ----------------------------------------------------------------------- |
| `isRequired(v)`           | Non-empty string check                                                  |
| `isEmail(v)`              | Basic email format                                                      |
| `isUrl(v)`                | Valid URL via `URL` constructor                                         |
| `isMinLength(v, n)`       | Length ≥ n                                                              |
| `isMaxLength(v, n)`       | Length ≤ n                                                              |
| `isStrongPassword(v)`     | 12+ chars, upper, lower, digit, symbol                                  |
| `isValidAppNameHtml(v)`   | Only `<b> <strong> <i> <em> <u> <sup> <sub>` allowed; all tags balanced |
| `isAwsAccessKeyId(v)`     | 20 uppercase alphanumeric chars                                         |
| `isAwsSecretAccessKey(v)` | 40 base64 chars                                                         |
| `isAwsRegion(v)`          | Pattern `xx-xxxx-d` (e.g. `eu-west-1`)                                  |
| `isFernetKey(v)`          | 44-char URL-safe base64                                                 |
| `isX509Cert(v)`           | Base64 body without PEM headers                                         |
| `isS3Arn(v)`              | `arn:aws:s3:::<bucket>` format                                          |

---

## `<rp-field-otp>`

A numeric one-time-password (OTP) input that renders N individual digit boxes with keyboard, paste, and backspace navigation built in.

**Extra attributes:**

| Attribute | Type   | Default | Description                     |
| --------- | ------ | ------- | ------------------------------- |
| `digits`  | number | `6`     | Number of digit boxes to render |

**Programmatic API:**

| Member  | Type   | Description                                                             |
| ------- | ------ | ----------------------------------------------------------------------- |
| `value` | string | Get: concatenated digit values. Set: distribute chars into digit boxes. |

**Behaviour:**

- **Sequential focus** — typing a digit moves focus to the next box automatically.
- **Backspace** — on an empty box, focus returns to the previous box.
- **Paste** — pasting a digit string fills boxes left-to-right from the focused position; non-digits are stripped.
- **Hidden input** — the assembled value is synced into a `type="hidden"` input for standard form serialisation.
- Validation blocks form advancement when `required` and the code is shorter than `digits`.

**Example:**

```html
<rp-field-otp id="rp-fp-otp" name="code" digits="6" col="col-12" required></rp-field-otp>
```

---

## `<rp-field-icon-picker>`

A button-triggered icon picker that loads all 2,050 Bootstrap Icons from a lazy-fetched JSON file (`/static/js/data/bootstrap-icons.json`). The selected icon name (without the `bi-` prefix) is stored in a hidden `<input>` for form submission and exposed via `.value`.

**Extra attributes:**

| Attribute     | Type    | Default          | Description                                 |
| ------------- | ------- | ---------------- | ------------------------------------------- |
| `placeholder` | string  | `Select an icon` | Text shown on the trigger button when empty |
| `disabled`    | boolean | —                | Disables the trigger button                 |

**Programmatic API:**

| Member    | Type             | Description                                                                      |
| --------- | ---------------- | -------------------------------------------------------------------------------- |
| `value`   | string (get/set) | Bootstrap Icon name without prefix, e.g. `"rocket-takeoff"`. Empty string = none |
| `open()`  | method           | Open the picker panel                                                            |
| `close()` | method           | Close the picker panel                                                           |

**Emits:** `change` (bubbles) — fired when the user selects or clears an icon.

**Panel behaviour:**

- **Singleton** — one panel is shared across all instances on the page; it repositions itself to the triggering button on each open.
- **Lazy-loaded** — icon data is fetched from `/static/js/data/bootstrap-icons.json` only on the first open; subsequent opens reuse the cached data.
- **Search** — full substring search across all 2,050 icon names, filtered live as the user types.
- **Categories** — 20 category tabs (Arrows, Media, Communication, …) generated from JSON; an "All" tab is always present.
- **IntersectionObserver batching** — the grid renders icons in 300-item batches to keep the main thread unblocked even in the All category.
- **Keyboard navigation** — `Escape` closes; arrow keys move focus through the grid; `Enter` selects the focused icon.
- **Mobile** — CSS positions the panel as a bottom sheet on viewports ≤ 640 px.
- **Single-click selection** — clicking an icon immediately confirms and closes the panel.

**Icon data generation:**

The JSON is generated from the Bootstrap Icons CDN CSS by running:

```bash
python scripts/build/generate_icons_json.py
```

This script is also integrated into `scripts/dev/dev.py` and runs automatically when you start the dev server if the JSON is absent or the script has changed.

**Example:**

```html
<rp-field-icon-picker
  id="project-icon"
  name="icon"
  label="Project icon"
  value="rocket-takeoff"
  hint="Used on cards, breadcrumbs, and the project list."
  required
  col="col-md-6"
></rp-field-icon-picker>
```

**Programmatic example:**

```js
const picker = document.getElementById("project-icon");

// Read value
console.log(picker.value); // "rocket-takeoff"

// Set value
picker.value = "star-fill";

// Open/close
picker.open();
picker.close();

// React to change
picker.addEventListener("change", (e) => {
  console.log("Selected:", e.target.value);
});
```
