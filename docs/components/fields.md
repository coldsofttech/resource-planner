# Field Components

Custom elements defined in `apps/web/static/js/components/fields/`. All field elements share a common base and integrate with the wizard's `rp:validate` event.

---

## Common Base Attributes

Every field component inherits these attributes from `BaseField`:

| Attribute      | Type                                         | Default    | Description                                                                              |
| -------------- | -------------------------------------------- | ---------- | ---------------------------------------------------------------------------------------- |
| `col`          | string                                       | `col-md-6` | Bootstrap column class applied to the host element                                       |
| `label`        | string                                       | —          | Label text shown above the input                                                         |
| `required`     | boolean                                      | —          | Marks the field as required; validates on blur                                           |
| `id`           | string                                       | —          | Sets element `id`; also used as `for` on the label and to derive `name`                  |
| `name`         | string                                       | `id` value | Input `name` attribute; falls back to `id`                                               |
| `hint`         | string                                       | —          | Plain-text hint shown below the input                                                    |
| `hint-type`    | `info` \| `warning` \| `success` \| `danger` | `info`     | Controls hint icon and colour                                                            |
| `value`        | string                                       | —          | Initial value                                                                            |
| `autocomplete` | string                                       | per-field  | HTML `autocomplete` forwarded to the native input; each field defines a sensible default |

A `<field-hint>` child element can provide rich HTML hint content and takes precedence over the `hint` attribute.

**Custom validators:**

```js
const el = document.getElementById("my-field");
el._customValidators.push({
  fn: (value) => /^[A-Z]{3}$/.test(value),
  msg: "Must be 3 uppercase letters.",
});
```

---

## `<text-field>`

Plain text input or multi-line textarea.

| Attribute      | Type    | Default | Description                                          |
| -------------- | ------- | ------- | ---------------------------------------------------- |
| `placeholder`  | string  | —       | Input placeholder text                               |
| `maxlength`    | number  | —       | Maximum character count                              |
| `show-counter` | boolean | —       | Shows a live character counter next to the label     |
| `cols`         | integer | —       | ≥ 2: renders a `<textarea>` with this number of rows |

```html
<text-field id="desc" name="description" label="Description" cols="4" col="col-12"></text-field>
```

---

## `<email-field>`

Email address input with built-in format validation. Always required; defaults: label "Email address", maxlength 255, placeholder "john.doe@example.com".

| Attribute     | Type    | Default | Description                                 |
| ------------- | ------- | ------- | ------------------------------------------- |
| `prefix-icon` | boolean | —       | Shows an envelope icon (bi-envelope) prefix |

```html
<email-field id="email" name="email" prefix-icon></email-field>
```

---

## `<password-field>`

Password input with optional eye-icon and strength meter. Defaults: label "Password", required.

| Attribute     | Type    | Default | Description                                              |
| ------------- | ------- | ------- | -------------------------------------------------------- |
| `eye-icon`    | boolean | —       | Shows a show/hide password toggle button                 |
| `prefix-icon` | boolean | —       | Shows a key icon (bi-key) prefix                         |
| `strength`    | boolean | —       | Enables the 4-segment strength meter and enforces policy |

Password policy (when `strength` is present): 12+ characters, uppercase, lowercase, digit, symbol.

**Public API:** `field.strength` → current score 0–4.

```html
<password-field id="password" name="password" eye-icon strength></password-field>
```

---

## `<confirm-password-field>`

Password confirmation input that cross-validates against a sibling `<password-field>`. Defaults: label "Confirm password", required.

| Attribute           | Type    | Description                                               |
| ------------------- | ------- | --------------------------------------------------------- |
| `password-field-id` | string  | `id` of the sibling `<password-field>` to compare against |
| `eye-icon`          | boolean | Shows a show/hide toggle                                  |
| `prefix-icon`       | boolean | Shows a key icon prefix                                   |

Shows "Matches." success indicator when values agree.

```html
<confirm-password-field
  id="confirm"
  name="confirm_password"
  password-field-id="password"
  eye-icon
></confirm-password-field>
```

---

## `<secret-field>`

Password-style input for sensitive values (API keys, tokens). Shows an "Encrypted" badge on the label.

| Attribute     | Type    | Description                               |
| ------------- | ------- | ----------------------------------------- |
| `eye-icon`    | boolean | Shows a show/hide toggle                  |
| `prefix-icon` | boolean | Shows a shield-lock icon (bi-shield-lock) |
| `required`    | boolean | Marks the field as required (not default) |

```html
<secret-field
  id="api-key"
  name="api_key"
  label="API Key"
  required
  eye-icon
  prefix-icon
></secret-field>
```

---

## `<number-field>`

Integer numeric input. Exported for extension by `<decimal-field>`.

| Attribute     | Type   | Default | Description           |
| ------------- | ------ | ------- | --------------------- |
| `placeholder` | string | —       | Input placeholder     |
| `min`         | number | —       | Minimum allowed value |
| `max`         | number | —       | Maximum allowed value |
| `step`        | number | `1`     | Increment step        |

```html
<number-field id="port" name="port" label="Port" min="1" max="65535" value="5432"></number-field>
```

---

## `<decimal-field>`

Decimal/floating-point numeric input. Extends `<number-field>` with `step` defaulting to `"0.1"`.

```html
<decimal-field id="rate" name="rate" label="Rate (%)" min="0" max="100"></decimal-field>
```

---

## `<website-field>`

URL input with a configurable scheme selector. Defaults: label "Website", placeholder "example.com".

**Declarative children:**

```html
<scheme-list>
  <scheme value="https://" selected>HTTPS</scheme>
  <scheme value="http://">HTTP</scheme>
</scheme-list>
```

| Attribute               | Type    | Description                                        |
| ----------------------- | ------- | -------------------------------------------------- |
| `accept-trailing-slash` | boolean | When absent, trailing slashes are stripped on blur |
| `prefix-icon`           | boolean | Shows a globe icon (bi-globe2) prefix              |
| `open-button`           | boolean | Shows an external-link button                      |

**Public API:**

| Member           | Description                                            |
| ---------------- | ------------------------------------------------------ |
| `field.value`    | Full URL including scheme (e.g. `https://example.com`) |
| `field.rawValue` | Path only, without scheme (e.g. `example.com`)         |
| `field.scheme`   | Currently selected scheme (e.g. `https://`)            |

Smart paste: pasting a full URL automatically splits the scheme from the path.

---

## `<otp-field>`

N-digit one-time-password input. Renders N single-character inputs with sequential focus, backspace navigation, and paste handling.

| Attribute | Type   | Default | Description                      |
| --------- | ------ | ------- | -------------------------------- |
| `digits`  | number | `6`     | Number of digit inputs to render |

**Public API:** `field.value` / `field.value = "123456"` — reads/distributes the digit string.

```html
<otp-field id="otp" name="otp" label="Verification code" digits="6" required></otp-field>
```

---

## `<hint-field>`

Standalone inline hint/callout block (not a `BaseField` subclass). Content is captured from `innerHTML` on connect.

| Attribute | Type                                         | Default  | Description                              |
| --------- | -------------------------------------------- | -------- | ---------------------------------------- |
| `type`    | `info` \| `warning` \| `success` \| `danger` | `info`   | Visual variant                           |
| `col`     | string                                       | `col-12` | Bootstrap column class                   |
| `title`   | string                                       | —        | Optional bold heading inside the callout |

```html
<hint-field type="warning" col="col-12" title="Important">
  This action <strong>cannot be undone</strong>. Read the <a href="/docs/">docs</a> first.
</hint-field>
```

---

## `<view-field>`

Read-only display field rendered as a `<dt>`/`<dd>` pair. Intended for use inside a `<dl>` element.

| Attribute | Type    | Description                                                                                                                     |
| --------- | ------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `label`   | string  | Field label rendered in the `<dt>` element                                                                                      |
| `meta`    | boolean | Adds `is-meta` class for compact/secondary styling                                                                              |
| `code`    | boolean | Wraps the value in `<code class="rp-mono">` for monospace display                                                               |
| `badge`   | string  | CSS class(es) for a badge wrapper span around the value — e.g. `badge="rp-badge rp-badge-success"` or `badge="rp-status-badge"` |
| `desc`    | boolean | Switches to single-column stacked layout — label on one line, value full-width below; for long text content                     |
| `tags`    | string  | CSS class(es) for each tag span; enables flex-wrap `<dd>` layout for multi-value display — e.g. `tags="rp-badge rp-badge-soft"` |

**Public API:**

| Member               | Description                                                                                   |
| -------------------- | --------------------------------------------------------------------------------------------- |
| `field.value`        | Getter: current `innerHTML` of the value element                                              |
| `field.value = html` | Setter: sets `innerHTML` when passed a string                                                 |
| `field.value = arr`  | Setter: renders each string in the array as a tag span using the `tags` class; `[]` shows `—` |

```html
<dl>
  <view-field id="team-name" label="Team name"></view-field>
  <view-field id="team-code" label="Code" code></view-field>
  <view-field id="team-status" label="Status"></view-field>
  <view-field id="team-notes" label="Notes" desc></view-field>
  <view-field id="team-skills" label="Skills" tags="rp-badge rp-badge-soft"></view-field>
</dl>
```

```js
document.getElementById("team-name").value = "Engineering";
document.getElementById("team-code").value = "ENG-001";
// badge class is state-dependent — set via setAttribute before value
const statusEl = document.getElementById("team-status");
statusEl.setAttribute("badge", "rp-badge rp-badge-soft rp-badge-success");
statusEl.value = "Active";
document.getElementById("team-notes").value =
  "A longer description rendered on its own full-width line.";
document.getElementById("team-skills").value = ["Python", "Django", "React"];
```

---

## `<search-field>`

Search input with a prefix icon and optional Ctrl+K / ⌘K keyboard shortcut.

| Attribute     | Type   | Default       | Description                                     |
| ------------- | ------ | ------------- | ----------------------------------------------- |
| `placeholder` | string | `"Search…"`   | Input placeholder text                          |
| `prefix-icon` | string | `"bi-search"` | Bootstrap Icon class for the prefix icon        |
| `suffix-icon` | string | —             | Bootstrap Icon class; omit to show ⌘K hint text |
| `width`       | string | `"240px"`     | CSS width of the control                        |

**Public API:** `field.value` / `field.value =` / `field.focus()`.

**Events:** `rp:search` (bubbles) — fired on Enter; `detail: { value }`.

```html
<search-field id="team-search" name="search" placeholder="Search teams…"></search-field>
```

---

## `<file-import-field>`

Drag-and-drop / click-to-browse file import field. Renders a drop zone, a hidden file input, and removable file tags for each selected file. Extends `BaseField` and participates in the wizard `rp:validate` lifecycle.

CSS for the drop zone lives in `static/css/styles/components/file-drops.css` (`.rp-drop`, `.rp-drop.is-over`). File tags use the existing `.rp-tag` class from `badges.css`.

### Attributes

| Attribute      | Type    | Default                     | Description                                                                            |
| -------------- | ------- | --------------------------- | -------------------------------------------------------------------------------------- |
| `accept`       | string  | `.csv,.xlsx`                | Comma-separated extensions or MIME types; files not matching are silently rejected     |
| `max-size`     | number  | `26214400` (25 MB)          | Maximum file size in bytes; oversized files are silently rejected                      |
| `multiple`     | boolean | —                           | Allows selecting more than one file                                                    |
| `icon`         | string  | `bi-cloud-upload`           | Bootstrap Icon class for the drop zone icon                                            |
| `drop-label`   | string  | `Drop files here`           | Primary heading inside the drop zone                                                   |
| `browse-label` | string  | `browse from your computer` | Text rendered inside the browse link                                                   |
| `sub-text`     | string  | —                           | Small caption line below the browse link (e.g. `Max 25 MB · UTF-8 · headers on row 1`) |

All base attributes (`id`, `name`, `col`, `label`, `required`, `hint`, `hint-type`) are inherited from `BaseField`.

### Public API

| Member          | Description                                         |
| --------------- | --------------------------------------------------- |
| `field.files`   | Getter — array of selected `File` objects           |
| `field.value`   | Getter — name of the first selected file, or `""`   |
| `field.clear()` | Removes all selected files and resets the drop zone |

### Events

| Event       | Bubbles | `detail`            | When fired                             |
| ----------- | ------- | ------------------- | -------------------------------------- |
| `rp:change` | yes     | `{ files: File[] }` | File selection added or a file removed |

### Validation

- `required` — at least one file must be selected before the field is valid.
- Files that fail the `accept` filter or exceed `max-size` are silently dropped; they never enter the selection.

### File icon mapping

| Extension       | Icon                          |
| --------------- | ----------------------------- |
| `.csv`          | `bi-filetype-csv`             |
| `.xlsx`, `.xls` | `bi-file-earmark-spreadsheet` |
| `.pdf`          | `bi-file-earmark-pdf`         |
| anything else   | `bi-file-earmark`             |

### Examples

```html
<!-- Single-file CSV/XLSX import (wizard step) -->
<file-import-field
  id="import-file"
  label="Import file"
  required
  col="col-12"
  accept=".csv,.xlsx"
  max-size="26214400"
  drop-label="Drop CSV or XLSX here"
  sub-text="Max 25 MB · UTF-8 · headers on row 1"
>
</file-import-field>

<!-- Multi-file with PDF support -->
<file-import-field
  id="attachments"
  label="Attachments"
  multiple
  accept=".pdf,.xlsx"
  drop-label="Drop files here"
>
</file-import-field>
```

```js
// React to file selection
document.getElementById("import-file").addEventListener("rp:change", (e) => {
  console.log(e.detail.files); // File[]
});

// Read files programmatically
const files = document.getElementById("import-file").files;

// Clear selection
document.getElementById("import-file").clear();
```

---

## Module Fields

Pre-configured convenience fields from `apps/web/static/js/components/modules/fields/`:

### `<first-name-field>`

Pre-configured `<text-field>`. Defaults: label "First name", required, maxlength 100, placeholder "John", autocomplete "given-name".

### `<last-name-field>`

Pre-configured `<text-field>`. Defaults: label "Last name", required, maxlength 100, placeholder "Doe", autocomplete "family-name".

---

## `<link-field>`

Anchor link component that wraps all `<a>` tag scenarios with consistent styling, accessibility, external-link safety, and optional icon support. Not a `BaseField` subclass — does not participate in form validation.

Link text can be supplied via the `label` attribute or as declarative text content between the tags. When both are present, `label` takes precedence. Text content is captured once on first connect before `innerHTML` is replaced; reconnects reuse the original captured value.

```html
<link-field href="/login/">Sign in</link-field>
<link-field href="/login/" label="Sign in"></link-field>
```

### Attributes

| Attribute       | Type    | Default   | Description                                                                                                   |
| --------------- | ------- | --------- | ------------------------------------------------------------------------------------------------------------- |
| `href`          | string  | `"#"`     | Link destination                                                                                              |
| `label`         | string  | —         | Link text; falls back to text content declared between tags                                                   |
| `icon`          | string  | —         | Bootstrap Icons class, with or without `bi-` prefix (e.g. `"bi-arrow-right"` or `"arrow-right"`)              |
| `icon-position` | string  | `"start"` | `"start"` \| `"end"` — icon placement relative to label text                                                  |
| `target`        | string  | —         | Forwarded to `<a>`; `"_blank"` auto-adds `rel="noopener noreferrer"`                                          |
| `rel`           | string  | —         | Explicit rel value; merged with auto-added safety rel for `_blank` links                                      |
| `disabled`      | boolean | —         | Renders non-interactive: `aria-disabled="true"`, `tabindex="-1"`, adds `is-disabled` class, intercepts clicks |
| `active`        | boolean | —         | Adds `is-active` class                                                                                        |
| `auto-active`   | boolean | —         | Compares `href` to `location.pathname`; adds `is-active` when matching (see Auto-active below)                |
| `variant`       | string  | `"link"`  | Visual style — see Variants table below                                                                       |
| `icon-size`     | string  | `"md"`    | Named size (`xs` \| `sm` \| `md` \| `lg` \| `xl` \| `2x`) or any CSS `font-size` value                        |
| `icon-color`    | string  | —         | Named colour token or any CSS color value (same token set as `<icon-field>`)                                  |
| `title`         | string  | —         | Tooltip text forwarded to the anchor; also used as `aria-label` fallback on icon-only links                   |

### Variants

| Value      | CSS class    | Use case                                       |
| ---------- | ------------ | ---------------------------------------------- |
| `link`     | `rp-link`    | Standard styled text link (default)            |
| `muted`    | `rp-muted`   | Secondary or footer link                       |
| `icon-btn` | `rp-iconbtn` | Icon-only action link (e.g. table row actions) |
| `plain`    | —            | No class; inherits parent styling              |

### Icon rendering

When text is visible alongside an icon, the icon is always `aria-hidden="true"` (decorative — the label text carries the accessible meaning). For icon-only links (`icon-btn` variant or no label text), the anchor carries `aria-label` from the `label` attribute, falling back to `title`. Always set `label` or `title` on icon-only links.

### External link safety

When `target="_blank"`, `rel="noopener noreferrer"` is always included (merged with any explicit `rel` value) to prevent reverse tabnapping.

### Auto-active detection

`auto-active` adds `is-active` if `location.pathname` exactly equals `href` or starts with `href` followed by `/`. The `#` href is never considered active. For finer control use the boolean `active` attribute.

### Examples

```html
<!-- Standard text link (declarative content) -->
<link-field href="/login/">Sign in</link-field>

<!-- Text link with icon prefix -->
<link-field href="/login/" icon="bi-arrow-left">Sign in</link-field>

<!-- Text link with icon suffix -->
<link-field
  href="/onboarding/"
  icon="arrow-right-circle-fill"
  icon-position="end"
  label="Get started"
></link-field>

<!-- External link (auto-adds rel="noopener noreferrer") -->
<link-field href="https://example.com" target="_blank" label="Documentation"></link-field>

<!-- Muted secondary link -->
<link-field href="/forgot-password/" variant="muted" label="Forgot password?"></link-field>

<!-- Icon-only action link (label is required for a11y) -->
<link-field
  href="/projects/1/"
  icon="bi-eye"
  label="View project"
  variant="icon-btn"
  title="View project"
></link-field>

<!-- Disabled link (click intercepted, aria-disabled set) -->
<link-field href="/restricted/" disabled label="Restricted"></link-field>

<!-- Auto-active navigation link -->
<link-field href="/projects/" auto-active label="Projects"></link-field>

<!-- Icon with colour and size -->
<link-field
  href="/alerts/"
  icon="bi-exclamation-triangle"
  icon-color="warning"
  icon-size="lg"
  label="Alerts"
></link-field>
```
