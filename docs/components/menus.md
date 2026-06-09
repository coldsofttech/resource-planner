# Menu Bar Components

Custom elements defined in `apps/web/static/js/components/menus/`.

The `<menu-bar id="app-menu-bar">` element is pre-mounted in `templates/base.html`. Do not add it to individual page templates. Configure it by populating `<menu-items>` before the element connects.

---

## `<menu-bar>`

Renders the application navigation bar from a declarative child structure. Children are parsed once on connect, then replaced with rendered nav HTML.

**Declarative child structure:**

```html
<menu-bar id="app-menu-bar">
  <menu-items>
    <menu-item id="nav-dashboard" name="Dashboard" href="/dashboard/" icon="bi-house"></menu-item>

    <menu-group id="nav-planning" name="Planning" icon="bi-calendar3" cols="2">
      <menu-section label="Projects">
        <menu-item name="Projects" href="/projects/" icon="bi-folder"></menu-item>
        <menu-item name="Resource Plans" href="/resource-plans/"></menu-item>
      </menu-section>
      <menu-section label="Sprints">
        <menu-item name="Sprints" href="/sprints/" icon="bi-lightning"></menu-item>
      </menu-section>
    </menu-group>
  </menu-items>
</menu-bar>
```

**Active state:** items whose `href` exactly matches or is a prefix of the current pathname automatically receive the `is-active` class. A `<menu-group>` trigger is also marked active when any child item is active.

**Mobile:** a hamburger toggle button is rendered and shown only on narrow viewports. Clicking it toggles the `rp-mobile-open` class on the host element. Pressing Escape or clicking outside closes open dropdowns and the mobile menu.

---

## `<menu-items>`

Root container parsed by `<menu-bar>`. Must be a direct child. Not a registered custom element — used as a declarative data container only.

---

## `<menu-item>`

A navigation link rendered inside the nav bar or inside a `<menu-group>` dropdown column.

| Attribute | Type   | Description                                                   |
| --------- | ------ | ------------------------------------------------------------- |
| `id`      | string | Element id carried through to the rendered `<a>`              |
| `name`    | string | Display label                                                 |
| `href`    | string | Navigation URL                                                |
| `icon`    | string | Bootstrap Icon class shown before the label (e.g. `bi-house`) |

---

## `<menu-group>`

A dropdown group trigger that opens a panel of `<menu-section>` / `<menu-item>` children.

| Attribute | Type   | Default | Description                                                      |
| --------- | ------ | ------- | ---------------------------------------------------------------- |
| `id`      | string | —       | Element id carried through to the rendered trigger               |
| `name`    | string | —       | Display label for the trigger                                    |
| `icon`    | string | —       | Bootstrap Icon class shown before the label                      |
| `cols`    | number | `1`     | Number of mega-menu columns; values > 1 activate the mega layout |

---

## `<menu-section>`

A column heading inside a `<menu-group>` dropdown. Contains `<menu-item>` children.

| Attribute | Type   | Description         |
| --------- | ------ | ------------------- |
| `label`   | string | Column heading text |

---

**Keyboard interactions:**

- Enter / Space on a focused group trigger opens the dropdown.
- Escape closes all open dropdowns and the mobile menu.
- Clicking outside the menu bar closes all open panels.
