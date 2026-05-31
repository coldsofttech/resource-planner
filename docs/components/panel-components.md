# Panel Components

Custom elements defined in `apps/web/static/js/components/panel-components.js`.

`<rp-panel>` renders a sunken card container. The title and body are declared via child slot elements so that content survives re-renders and wizard navigation.

---

## `<rp-panel>`

A titled card that wraps a group of fields or content.

**Attributes:**

| Attribute | Type   | Default    | Description                                                             |
| --------- | ------ | ---------- | ----------------------------------------------------------------------- |
| `col`     | string | `col-12`   | Bootstrap column class applied to the host element                      |
| `title`   | string | —          | Plain-text heading shown in the card header                             |
| `icon`    | string | —          | Bootstrap Icons class for an icon beside the title (e.g. `bi-envelope`) |
| `id`      | string | —          | Element ID                                                              |
| `name`    | string | `id` value | Logical name (mirrors `id` by default)                                  |

A `<panel-title>` child element can provide rich HTML title content and takes precedence over the `title` attribute.

**Example:**

```html
<rp-panel col="col-12" title="Email Settings" icon="bi-envelope">
  <panel-body>
    <rp-field-text id="email-host" label="SMTP Host" required col="col-md-6"></rp-field-text>
    <rp-field-number id="email-port" label="Port" value="587" col="col-md-3"></rp-field-number>
  </panel-body>
</rp-panel>
```

---

## `<panel-title>`

Slot element for rich HTML panel title. Place as a direct child of `<rp-panel>`. Its `innerHTML` is used verbatim in the card header and takes precedence over the `title` attribute.

**Example:**

```html
<rp-panel col="col-12">
  <panel-title>Database <span class="rp-badge rp-badge-soft">required</span></panel-title>
  <panel-body>
    <!-- fields -->
  </panel-body>
</rp-panel>
```

---

## `<panel-body>`

Slot element that wraps the panel's content children. Direct children of `<panel-body>` are moved into the `.rp-card-body` container during render. This preserves live DOM nodes (custom elements, event listeners) through attribute-change re-renders and wizard step navigation.

**Example:**

```html
<rp-panel title="Infrastructure">
  <panel-body>
    <rp-field-dropdown id="deployment-type" label="Deployment" required>
      <values-list>
        <value value="local" selected>Local</value>
        <value value="aws">AWS</value>
      </values-list>
    </rp-field-dropdown>
  </panel-body>
</rp-panel>
```

---

## Notes

- If neither `title` nor `<panel-title>` is provided and `icon` is also absent, the card header is omitted entirely.
- `<rp-panel>` is safe to use inside `<rp-wizard>` step bodies — the wizard re-uses the DOM node and the panel skips re-render if the `.rp-card` shell is already present.
