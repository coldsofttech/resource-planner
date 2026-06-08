# Breadcrumb Components

Custom element defined in `apps/web/static/js/components/breadcrumbs/breadcrumbs.js`.

The component is pre-mounted in `templates/base.html` as `<page-breadcrumbs id="app-breadcrumbs">`. Page modules call `setCrumbs()` to set the correct trail for the active entity.

---

## `<page-breadcrumbs>`

Renders breadcrumb navigation in the top bar. Auto-generates a trail from `window.location.pathname` by default; override with the `crumbs` attribute or `setCrumbs()` when the page knows the entity name.

**Observed attributes:**

| Attribute | Type   | Default | Description                                                                                          |
| --------- | ------ | ------- | ---------------------------------------------------------------------------------------------------- |
| `crumbs`  | string | —       | JSON array of crumb objects: `[{label, href?}, ..., {label, current: true}]`. Omit to auto-generate. |

**Auto-generation rules:**

| URL path            | Generated trail                                                      |
| ------------------- | -------------------------------------------------------------------- |
| `/` or `/dashboard` | `Home` (current)                                                     |
| `/projects`         | `Home` → `Projects` (current)                                        |
| `/projects/123`     | `Home` → `Projects` → `…` (current — numeric segments render as `…`) |
| `/resource-plans`   | `Home` → `Resource Plans` (current — kebab-case is title-cased)      |

Numeric segments render as `…` — always call `setCrumbs()` from the page module to replace `…` with the real entity name.

**Public API:**

| Method                        | Description                                              |
| ----------------------------- | -------------------------------------------------------- |
| `setCrumbs(crumbs: object[])` | Sets the `crumbs` attribute with the provided JSON array |

Each crumb object:

| Key       | Type    | Description                                         |
| --------- | ------- | --------------------------------------------------- |
| `label`   | string  | Display text                                        |
| `href`    | string  | Link URL; omit on the current/last crumb            |
| `current` | boolean | Marks this crumb as the active page (bold, no link) |

---

**Example — entity detail page:**

```js
// URL: /projects/42
// Auto-generation produces: Home → Projects → …
// Override with the real project name:
document.getElementById("app-breadcrumbs").setCrumbs([
  { label: "Home", href: "/dashboard" },
  { label: "Projects", href: "/projects" },
  { label: "Alpha Project", current: true },
]);
```

---

**Notes:**

- The element is hidden on narrow viewports (≤ 900 px).
- Calling `setCrumbs([])` falls back to auto-generation from the URL.
- `label` and `href` values are HTML-escaped before rendering.
