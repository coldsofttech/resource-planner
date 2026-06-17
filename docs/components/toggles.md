# Toggle Components

Custom elements defined in `apps/web/static/js/components/toggles/`.

---

## `<toggle-field>`

Single toggle switch input. A pill-switch visual variant of `<checkbox-field>`. Extends `ChoiceField` using the `rp-toggle` CSS class.

Inherits all attributes from `BaseField` and `ChoiceField`:

| Attribute   | Type    | Default    | Description                                    |
| ----------- | ------- | ---------- | ---------------------------------------------- |
| `col`       | string  | `col-md-6` | Bootstrap column class                         |
| `label`     | string  | —          | Label text                                     |
| `required`  | boolean | —          | Marks the field as required; must be checked   |
| `id`        | string  | —          | Element id; also used as input `name` fallback |
| `name`      | string  | `id`       | Input `name` attribute                         |
| `checked`   | boolean | —          | Initial checked state                          |
| `disabled`  | boolean | —          | Disables the input                             |
| `value`     | string  | `"on"`     | Submitted form value when checked              |
| `hint`      | string  | —          | Plain-text hint shown below the input          |
| `hint-type` | string  | `info`     | Controls hint icon and colour                  |

**Public API:** `field.checked` (getter) / `field.checked =` (setter).

**Validation:** required → input must be checked.

```html
<toggle-field
  id="notifications"
  name="notifications"
  label="Email notifications"
  checked
></toggle-field>
```

---

## `<toggle-group-field>`

Group of toggle switch inputs rendered from declarative `<option-field>` children. A pill-switch visual variant of `<checkbox-group-field>`.

`field.value` returns a comma-separated string of all checked values.

**Declarative children:**

```html
<option-field value="email" label="Email" checked></option-field>
<option-field value="slack" label="Slack"></option-field>
<option-field value="sms" label="SMS" disabled></option-field>
```

**Validation:** required → at least one option must be checked.

```html
<toggle-group-field id="channels" name="channels" label="Notification channels" required>
  <option-field value="email" label="Email" checked></option-field>
  <option-field value="slack" label="Slack"></option-field>
</toggle-group-field>
```

---

## `<theme-toggle>`

Three-way theme toggle (light → dark → system). No public attributes. Persists the user's preference via `setTheme()` in `localStorage` and applies `data-theme="light|dark"` to `<html>`. The **system** mode follows the OS `prefers-color-scheme` media query and responds to OS changes dynamically.

Multiple instances on the same page stay in sync via the `rp-theme-changed` window event.

Pre-mounted in `templates/base.html` as `<rp-theme-toggle>`. Do not add it to individual page templates.

```html
<!-- Already in base.html — do not re-add -->
<rp-theme-toggle></rp-theme-toggle>
```

**Events (dispatched on `window`):**

| Event              | Detail                         | Description                  |
| ------------------ | ------------------------------ | ---------------------------- |
| `rp-theme-changed` | `{ theme: "light" \| "dark" }` | Fired when the theme changes |

**Listen for theme changes:**

```js
window.addEventListener("rp-theme-changed", (e) => {
  const isDark = e.detail.theme === "dark";
  // respond to theme change
});
```
