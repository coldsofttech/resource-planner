# Choice Components

Custom elements defined in `apps/web/static/js/components/choices/`.

Choice components extend `BaseField` — see `fields.md` for inherited attributes (`col`, `label`, `required`, `id`, `name`, `hint`, `hint-type`, `value`, `autocomplete`).

---

## `<checkbox-field>`

Single checkbox input. Extends `ChoiceField` with `type="checkbox"`.

**Additional attributes:**

| Attribute  | Type    | Default | Description                       |
| ---------- | ------- | ------- | --------------------------------- |
| `checked`  | boolean | —       | Initial checked state             |
| `disabled` | boolean | —       | Disables the input                |
| `value`    | string  | `"on"`  | Submitted form value when checked |

**Public API:**

| Member            | Description                             |
| ----------------- | --------------------------------------- |
| `field.checked`   | Getter: current checked state (boolean) |
| `field.checked =` | Setter: sets checked state on the input |

**Validation:** required → input must be checked.

```html
<checkbox-field id="agree" name="agree" label="I agree to the terms" required></checkbox-field>
```

---

## `<radio-field>`

Single radio input. Extends `ChoiceField` with `type="radio"`.

Same attributes as `<checkbox-field>`. Typically used inside a `<form>` alongside sibling radio fields sharing the same `name`.

```html
<radio-field id="opt-a" name="choice" value="a" label="Option A" checked></radio-field>
<radio-field id="opt-b" name="choice" value="b" label="Option B"></radio-field>
```

---

## `<checkbox-group-field>`

Group of checkbox inputs rendered from declarative `<option-field>` children. Multiple options can be selected simultaneously.

`field.value` returns a comma-separated string of all checked values.

**Declarative children:**

```html
<option-field value="red" label="Red" checked></option-field>
<option-field value="green" label="Green" disabled></option-field>
<option-field value="blue" label="Blue"></option-field>
```

**Validation:** required → at least one option must be checked.

```html
<checkbox-group-field id="colours" name="colours" label="Colours" required>
  <option-field value="red" label="Red"></option-field>
  <option-field value="green" label="Green"></option-field>
  <option-field value="blue" label="Blue"></option-field>
</checkbox-group-field>
```

---

## `<radio-group-field>`

Group of radio inputs rendered from declarative `<option-field>` children. Only one option can be selected at a time.

`field.value` returns the single selected value string, or `""` when nothing is selected.

**Validation:** required → an option must be selected.

```html
<radio-group-field id="plan" name="plan" label="Plan" required>
  <option-field value="basic" label="Basic" checked></option-field>
  <option-field value="pro" label="Pro"></option-field>
</radio-group-field>
```

---

## `<option-field>`

Declarative data container for a single option within a `<checkbox-group-field>` or `<radio-group-field>`. Parsed once on connect — do not use standalone.

| Attribute  | Type    | Description                                           |
| ---------- | ------- | ----------------------------------------------------- |
| `label`    | string  | Display text (falls back to text content when absent) |
| `value`    | string  | Submitted value for this option                       |
| `checked`  | boolean | Pre-selects this option                               |
| `disabled` | boolean | Disables this option                                  |

---

## Notes

- All choice components use the `rp:validate` event from the nearest wizard panel to trigger validation.
- The `value` attribute on a group pre-selects matching options at render time (comma-separated for checkboxes, single value for radios).
- Use `<toggle-field>` / `<toggle-group-field>` for the pill-switch visual variant — see `toggles.md`.
