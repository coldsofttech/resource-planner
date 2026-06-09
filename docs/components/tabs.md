# Tab Components

Custom elements defined in `apps/web/static/js/components/tabs/`.

---

## `<tab-panel>`

Declarative tab component. Declarative children are parsed once on connect, then replaced with rendered HTML. Panel content nodes are captured and re-inserted into slots so nested component state is preserved.

**Declarative children (captured before first render):**

```html
<tab-panel>
  <tab-items>
    <tab-item id="overview" active>
      <tab-header title="Overview" icon="bi-house"></tab-header>
      <tab-content>
        <p>Overview content here.</p>
      </tab-content>
    </tab-item>

    <tab-item id="team">
      <tab-header title="Team" count="12"></tab-header>
      <tab-content>
        <data-table>…</data-table>
      </tab-content>
    </tab-item>

    <tab-item id="finance">
      <tab-header title="Finance" icon="bi-cash"></tab-header>
      <tab-content>
        <p>Finance content here.</p>
      </tab-content>
    </tab-item>
  </tab-items>
</tab-panel>
```

**Public API:**

| Method / Property          | Description                                                  |
| -------------------------- | ------------------------------------------------------------ |
| `panel.setTab(id)`         | Switch to the tab with the given id                          |
| `panel.updateCount(id, n)` | Update a tab's count badge; pass `""` or `null` to remove it |
| `panel.activeTab`          | Getter — returns the currently active tab id                 |

**Events fired (all bubble):**

| Event           | Fires when                          |
| --------------- | ----------------------------------- |
| `rp:tab-change` | Tab switched; `detail: { tab: id }` |

**Keyboard interaction:** `ArrowLeft` / `ArrowRight` navigate between tabs when focus is on a tab button.

---

## `<tab-items>`

Declarative container for `<tab-item>` elements. Place as a direct child of `<tab-panel>` — do not use standalone.

---

## `<tab-item>`

Declarative container for one tab's config and content. Place inside `<tab-items>`.

| Attribute | Type    | Default         | Description                                               |
| --------- | ------- | --------------- | --------------------------------------------------------- |
| `id`      | string  | `"tab-{index}"` | Stable id for `setTab()` calls; auto-generated if omitted |
| `active`  | boolean | —               | Marks this tab as the initially active one                |

---

## `<tab-header>`

Declares the visual config for one tab button. Place as a direct child of `<tab-item>`.

| Attribute | Type   | Description                                                    |
| --------- | ------ | -------------------------------------------------------------- |
| `title`   | string | Tab button label                                               |
| `icon`    | string | Bootstrap Icon class shown before the label (e.g. `bi-person`) |
| `count`   | string | Optional numeric badge shown after the label                   |

---

## `<tab-content>`

Holds the panel body for one tab. Child nodes are captured once and re-inserted into the rendered panel slot, preserving component state. Place as a direct child of `<tab-item>`.

---

## Programmatic usage

```js
const panel = document.getElementById("project-tabs");

// Switch to a tab
panel.setTab("team");

// Update a count badge after data loads
async function loadTeamData() {
  const members = await fetchTeamMembers();
  panel.updateCount("team", members.length);
}

// React to tab changes
panel.addEventListener("rp:tab-change", (e) => {
  console.log("Active tab:", e.detail.tab);
});
```
