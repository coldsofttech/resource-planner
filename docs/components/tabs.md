# Tab Components

Custom elements defined in `apps/web/static/js/components/tabs/`.

---

## `<tab-panel>`

Declarative tab component. Declarative children are parsed once on connect, then replaced with rendered HTML. Panel content nodes are **captured (moved, not cloned)** into rendered slot divs — component state inside `<tab-content>` (e.g. a `<data-table>` that has already fetched data) is preserved when switching tabs.

Tab state is synced to the `?tab=<id>` URL query parameter via `history.replaceState`. On load, if `?tab=<id>` is present in the URL, that tab is made active — overriding the `active` attribute declared on `<tab-item>`.

**Declarative structure:**

```html
<tab-panel id="project-tabs">
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

Semantic wrapper for `<tab-item>` elements. Place as a direct child of `<tab-panel>`. No JS behaviour is attached to this element — it exists by convention in all templates to group tab declarations and improve readability.

---

## `<tab-item>`

Declarative container for one tab's config and content. Place inside `<tab-items>`.

| Attribute | Type    | Default         | Description                                                                       |
| --------- | ------- | --------------- | --------------------------------------------------------------------------------- |
| `id`      | string  | `"tab-{index}"` | Stable id for `setTab()` calls; auto-generated if omitted                         |
| `active`  | boolean | —               | Marks this tab as the initially active one (overridden by `?tab=<id>` in the URL) |

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

Holds the panel body for one tab. Child nodes are **captured (moved, not cloned)** once on connect and re-inserted into the rendered panel slot. This means nested component state — such as a `<data-table>` that has already loaded its rows — is preserved when the user switches between tabs and returns.

Place as a direct child of `<tab-item>`.

---

## URL state

Tab state is persisted in the page URL via `?tab=<id>` using `history.replaceState`. This means:

- Refreshing the page restores the previously active tab.
- Sharing the URL opens the page at the correct tab.
- The `active` attribute on `<tab-item>` is only used as a fallback when `?tab` is absent from the URL.

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

// React to tab changes (e.g. to lazy-load a table on first switch)
panel.addEventListener("rp:tab-change", (e) => {
  console.log("Active tab:", e.detail.tab);
});
```

---

## Minimal working example — two tabs each containing a `<data-table>`

```html
<tab-panel id="rp-example-tabs">
  <tab-items>
    <tab-item id="forecast" active>
      <tab-header title="Forecast" icon="bi-graph-up-arrow"></tab-header>
      <tab-content>
        <data-table
          id="rp-forecast-table"
          src="/api/v1/example/forecast/"
          row-renderer="renderForecastRow"
        >
          <table-columns>
            <table-column field="name" label="Name"></table-column>
            <table-column field="value" label="Value"></table-column>
          </table-columns>
        </data-table>
      </tab-content>
    </tab-item>

    <tab-item id="actuals">
      <tab-header title="Actuals" icon="bi-receipt"></tab-header>
      <tab-content>
        <data-table
          id="rp-actuals-table"
          src="/api/v1/example/actuals/"
          row-renderer="renderActualsRow"
        >
          <table-columns>
            <table-column field="name" label="Name"></table-column>
            <table-column field="amount" label="Amount"></table-column>
          </table-columns>
        </data-table>
      </tab-content>
    </tab-item>
  </tab-items>
</tab-panel>
```

Both `<data-table>` elements load their data independently. Because `<tab-content>` nodes are moved (not cloned) into panel slots, switching tabs and returning does not re-fetch or reset table state.
