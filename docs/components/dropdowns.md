# Dropdown Components

Custom elements defined in `apps/web/static/js/components/dropdowns/`.

Dropdown components extend `BaseField` — see `fields.md` for inherited attributes (`col`, `label`, `required`, `id`, `name`, `hint`, `hint-type`, `value`, `autocomplete`).

---

## `<dropdown-field>`

Select/dropdown field. Options are declared as children and parsed once on connect.

**Declarative children:**

```html
<values-list>
  <value id="…" value="…" selected>Label</value>
  <value id="…" value="…" disabled>Disabled option</value>
</values-list>
```

| `<value>` attribute | Type    | Description                                                                |
| ------------------- | ------- | -------------------------------------------------------------------------- |
| `id`                | string  | Optional id on the rendered `<option>`                                     |
| `value`             | string  | Submitted value; falls back to text content                                |
| `selected`          | boolean | Pre-selects this option (fallback when `value` attr is absent on the host) |
| `disabled`          | boolean | Renders this option as disabled                                            |

**Additional attributes:**

| Attribute     | Type   | Default | Description                                               |
| ------------- | ------ | ------- | --------------------------------------------------------- |
| `placeholder` | string | —       | First disabled/hidden option prompting the user to choose |

**Validation:** required → an option with a non-empty value must be selected.

**Selection precedence:** the `value` attribute on the host element takes priority over the `selected` attribute on individual `<value>` children.

```html
<dropdown-field id="role" name="role" label="Role" required>
  <values-list>
    <value value="admin">Admin</value>
    <value value="member" selected>Member</value>
    <value value="viewer">Viewer</value>
  </values-list>
</dropdown-field>
```

---

## Module Dropdowns

Pre-configured convenience fields from `apps/web/static/js/components/modules/dropdowns/`:

### `<is-active-field>`

Business-specific status filter dropdown. Options: **All Statuses** (empty value, selected by default), **Active** (`true`), **Inactive** (`false`). Extends `<dropdown-field>` with hard-coded options — no `<values-list>` child needed.

| Attribute | Type   | Description                                  |
| --------- | ------ | -------------------------------------------- |
| `value`   | string | `"true"` \| `"false"` \| `""` (default `""`) |

```html
<is-active-field name="is_active" label="Status" col="col-md-3"></is-active-field>
```
