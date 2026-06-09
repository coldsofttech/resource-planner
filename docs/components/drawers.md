# Drawer Components

Custom elements defined in `apps/web/static/js/components/drawers/`.

---

## `<drawer-modal>`

A slide-in right-side panel (drawer) with a resizable handle, tab support, and a structured header/body/footer. Configured entirely through declarative child elements that are parsed once on connect.

**Attribute:**

| Attribute | Type             | Default | Description                                          |
| --------- | ---------------- | ------- | ---------------------------------------------------- |
| `width`   | number \| `full` | `640`   | Initial drawer width in pixels, or `"full"` for full |

**Declarative children (all optional):**

```html
<drawer-modal width="640">
  <drawer-header
    eyebrow="Team"
    title="Engineering"
    badge="Active"
    badge-variant="success"
  ></drawer-header>

  <drawer-tabs>
    <drawer-tab panel="details" active>Details</drawer-tab>
    <drawer-tab panel="members" count="12">Members</drawer-tab>
  </drawer-tabs>

  <drawer-panel name="details">
    <!-- details content here -->
  </drawer-panel>

  <drawer-panel name="members">
    <!-- members content here -->
  </drawer-panel>

  <drawer-footer
    meta="Updated 2 hours ago"
    close="Cancel"
    secondary="Export"
    secondary-icon="bi-download"
    primary="Save"
    primary-icon="bi-check2"
  ></drawer-footer>
</drawer-modal>
```

**Public API:**

| Method                | Description                         |
| --------------------- | ----------------------------------- |
| `drawer.show()`       | Opens the drawer                    |
| `drawer.hide()`       | Closes the drawer                   |
| `drawer.setTab(name)` | Switches to the named tab panel     |
| `drawer.setWidth(w)`  | Sets width: number (px) or `"full"` |

**Events fired (all bubble):**

| Event                 | Fires when                                              |
| --------------------- | ------------------------------------------------------- |
| `rp:open`             | Drawer opened                                           |
| `rp:close`            | Drawer closed (backdrop, × button, or footer close)     |
| `rp:tab-change`       | Tab switched; `detail: { panel: "panelName" }`          |
| `rp:resize`           | Width changed; `detail: { width: number \| "full" }`    |
| `rp:footer-close`     | Footer cancel/close button clicked (drawer also closes) |
| `rp:footer-secondary` | Footer secondary button clicked                         |
| `rp:footer-primary`   | Footer primary button clicked                           |

**Interactions:**

- Resize handle (left edge): drag to resize; double-click to reset to default width.
- Width snap buttons: 440 / 640 / 900 / full (hidden when `no-sizes` is set on `<drawer-header>`).
- Backdrop click closes the drawer.
- Mobile: swipe down on the grab bar (top strip) to close.

---

## `<drawer-header>`

Declarative data container for the drawer header. Place as a direct child of `<drawer-modal>`.

| Attribute       | Type    | Default     | Description                                        |
| --------------- | ------- | ----------- | -------------------------------------------------- |
| `eyebrow`       | string  | —           | Small text above the title                         |
| `title`         | string  | —           | Main heading text                                  |
| `badge`         | string  | —           | Badge label next to the title                      |
| `badge-variant` | string  | `"neutral"` | Badge colour variant (matches `rp-badge` variants) |
| `no-sizes`      | boolean | —           | When present, hides the width snap buttons         |

---

## `<drawer-footer>`

Declarative data container for the drawer footer. Place as a direct child of `<drawer-modal>`.

| Attribute        | Type   | Description                                       |
| ---------------- | ------ | ------------------------------------------------- |
| `meta`           | string | Informational text on the left side of the footer |
| `close`          | string | Label for the muted close button; omit to hide    |
| `secondary`      | string | Label for the secondary button; omit to hide      |
| `secondary-icon` | string | Bootstrap Icon class for the secondary button     |
| `primary`        | string | Label for the primary button; omit to hide        |
| `primary-icon`   | string | Bootstrap Icon class for the primary button       |

---

## `<drawer-tabs>` / `<drawer-tab>` / `<drawer-panel>`

Declarative tab system. `<drawer-tabs>` wraps one or more `<drawer-tab>` elements; each tab maps to a `<drawer-panel>` by name.

**`<drawer-tab>` attributes:**

| Attribute | Type    | Description                                     |
| --------- | ------- | ----------------------------------------------- |
| `panel`   | string  | Name of the `<drawer-panel>` this tab activates |
| `count`   | string  | Optional numeric badge next to the tab label    |
| `active`  | boolean | Marks this tab as the initially active tab      |

Tab label is the element's text content.

**`<drawer-panel>` attributes:**

| Attribute | Type   | Description                                     |
| --------- | ------ | ----------------------------------------------- |
| `name`    | string | Matches the `panel` attribute on `<drawer-tab>` |

---

**Example — programmatic usage:**

```js
const drawer = document.getElementById("team-drawer");

// Show drawer for a team row
function openTeam(team) {
  drawer.setAttribute("width", "640");
  drawer.show();
  drawer.setTab("details");
}

drawer.addEventListener("rp:footer-primary", async () => {
  // handle save
});

drawer.addEventListener("rp:close", () => {
  // handle close / cleanup
});
```
