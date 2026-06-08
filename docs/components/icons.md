# Icon Components

Custom elements defined in `apps/web/static/js/components/icons/`.

| Component           | Purpose                                                         |
| ------------------- | --------------------------------------------------------------- |
| `icon-field`        | Inline icon display; replaces raw `<i class="bi bi-*">` tags    |
| `icon-picker-field` | Form field; searchable Bootstrap Icon picker with category tabs |

---

## `<icon-field>`

Inline icon display component backed by Bootstrap Icons. Replaces raw `<i class="bi bi-*">` tags with a semantic, accessible element whose appearance is fully driven by HTML attributes.

### Attributes

| Attribute | Type   | Default | Description                                                                                                                                                           |
| --------- | ------ | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `icon`    | string | —       | Bootstrap Icons class, with or without the `bi-` prefix (e.g. `"bi-arrow-right"` or `"arrow-right"`). Required.                                                       |
| `size`    | string | `"md"`  | Named size (`xs` \| `sm` \| `md` \| `lg` \| `xl` \| `2x`) or any valid CSS `font-size` value (e.g. `"1.5rem"`, `"20px"`).                                             |
| `color`   | string | —       | Named colour token (`info` \| `success` \| `warning` \| `danger` \| `muted` \| `primary`) or any CSS color value (e.g. `"var(--rp-info)"`, `"#ff0000"`).              |
| `label`   | string | —       | Accessible label text. When set, the `<i>` receives `aria-hidden="true"` and a `visually-hidden` `<span>` carries the text. When absent, `role="img"` + `aria-label`. |
| `title`   | string | —       | Native tooltip text shown on hover.                                                                                                                                   |

### Named sizes

| Value | `font-size` |
| ----- | ----------- |
| `xs`  | `0.75rem`   |
| `sm`  | `0.875rem`  |
| `md`  | `1rem`      |
| `lg`  | `1.25rem`   |
| `xl`  | `1.5rem`    |
| `2x`  | `2rem`      |

### Named colour tokens

| Value     | CSS variable                  |
| --------- | ----------------------------- |
| `info`    | `var(--rp-info)`              |
| `success` | `var(--rp-success-soft-text)` |
| `warning` | `var(--rp-warning-soft-text)` |
| `danger`  | `var(--rp-danger-soft-text)`  |
| `muted`   | `var(--rp-text-muted)`        |
| `primary` | `var(--rp-primary)`           |

### Examples

```html
<!-- Named colour + named size -->
<icon-field icon="bi-check-circle" color="success" size="lg" label="Completed"></icon-field>

<!-- Warning indicator with tooltip -->
<icon-field icon="bi-exclamation-triangle" color="warning" title="Needs attention"></icon-field>

<!-- Arbitrary CSS size, prefix-free shorthand -->
<icon-field icon="arrow-right" size="1.5rem"></icon-field>

<!-- Muted small icon — purely decorative (no label) -->
<icon-field icon="bi-person" color="muted" size="sm"></icon-field>

<!-- Danger badge icon -->
<icon-field icon="bi-x-circle-fill" color="danger" size="xl" label="Error"></icon-field>
```

### Accessibility

- When `label` is set: the `<i>` receives `aria-hidden="true"` and a `visually-hidden` `<span>` carries the label text for screen readers.
- When `label` is absent: the `<i>` receives `role="img"` and `aria-label` auto-derived from the icon name (hyphens replaced with spaces, `bi-` prefix stripped).
- Use `label` whenever the icon conveys a meaningful action, status, or state not described by surrounding text.
- Purely decorative icons can omit `label` — the auto-derived `aria-label` keeps them minimally accessible.

### Rules

- Always use `<icon-field>` instead of raw `<i class="bi bi-*">` tags in templates and JS-rendered HTML.
- Pass `label` whenever the icon is the sole conveyor of meaning (e.g. a standalone status indicator).
- Prefer named colour tokens over raw CSS values to ensure dark-mode theme compatibility.
- Prefer named size tokens over raw values unless a non-standard size is required.

Avoid:

- raw `<i class="bi ...">` tags in templates or JS-rendered content
- custom inline `style` attributes for colour or size when a named token exists
- omitting `label` on icons that are the only indicator of an important state

---

## `<icon-picker-field>`

Form field that opens a searchable Bootstrap Icons picker panel. Extends `BaseField` — inherits all standard field attributes (`col`, `label`, `required`, `id`, `name`, `hint`, `hint-type`, `value`).

Icon data is loaded lazily from `/static/js/data/bootstrap-icons.json` on first open. Regenerate that file with `scripts/build/generate_icons_json.py`.

### Additional Attributes

| Attribute     | Type    | Default            | Description                     |
| ------------- | ------- | ------------------ | ------------------------------- |
| `placeholder` | string  | `"Select an icon"` | Trigger button placeholder text |
| `disabled`    | boolean | —                  | Disables the picker trigger     |

### Public API

| Member              | Description                                                      |
| ------------------- | ---------------------------------------------------------------- |
| `field.value`       | Current icon name without `bi-` prefix (e.g. `"rocket-takeoff"`) |
| `field.value = "…"` | Set icon programmatically                                        |
| `field.open()`      | Open the picker panel                                            |
| `field.close()`     | Close the picker panel                                           |

**Events:** `change` (bubbles) — fired when the user selects a new icon.

### Picker panel behaviour

- **Singleton** — one panel and one backdrop are created on the page and reused across all instances.
- **Lazy loading** — icon JSON is fetched once on first open; shows a loading state while fetching.
- **Category tabs** — populated from the JSON `categories` array; `All` tab always present.
- **Search** — real-time filter within the active category.
- **Virtual scrolling** — first 300 icons rendered immediately; more appended via `IntersectionObserver` as the user scrolls.
- **Responsive** — bottom-sheet on viewports < 768 px; dropdown-positioned on desktop.
- **Keyboard** — Arrow keys navigate the grid; Enter selects; Escape closes; Tab traps focus inside the panel.

### Example

```html
<icon-picker-field id="icon" name="icon" label="Icon" required></icon-picker-field>
```

```js
const picker = document.getElementById("icon");
picker.value = "rocket-takeoff"; // set programmatically
picker.open(); // open panel from JS
picker.addEventListener("change", () => console.log(picker.value));
```
