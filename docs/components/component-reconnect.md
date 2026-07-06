# Component Reconnect Guide

When a component is embedded inside `<tab-panel>` or moved by `<step-wizard>`, the browser fires
`disconnectedCallback` followed by `connectedCallback` on it — even though the component never
left the page from the user's perspective. Components that fetch data asynchronously or capture
child nodes on first connect must guard against re-running that work on every reconnect.

---

## Why reconnects happen

### `tab-panel`

`tab-panel._render()` captures declarative child nodes from `<tab-content>` elements and then
replaces its own `innerHTML` with rendered tab bar and panel slot HTML. The captured nodes are
subsequently re-inserted via `slot.appendChild(node)`.

This means every component inside a `<tab-content>` receives:

1. `disconnectedCallback` — when `innerHTML = …` detaches the original tree
2. `connectedCallback` — when `slot.appendChild(node)` re-attaches it

This happens **once on the initial render**, not on every tab switch — because `<tab-panel>` moves
nodes into slots only once and keeps them in the DOM across tab switches (hiding inactive panels
with `hidden` rather than removing nodes).

### `section-panel` inside `<step-wizard>`

The wizard re-parents `<section-panel>` elements as the user navigates between steps.
`disconnectedCallback` + `connectedCallback` fire each time the panel moves.

---

## The `=== undefined` sentinel pattern

Use a private field initialised to `undefined` as a first-connect guard. The check is
`field === undefined` — any other value (`null`, `[]`, `0`, a symbol) means "already ran".

### Pattern 1 — Child node capture (used in `section-panel`)

```js
class SectionPanel extends HTMLElement {
  connectedCallback() {
    if (this._bodyNodes === undefined) {
      // Runs once, on the very first connect.
      // Capture declarative child nodes before _render() replaces innerHTML.
      const body = this.querySelector("panel-body");
      this._bodyNodes = body ? Array.from(body.children) : [];
    }

    // Skip the full re-render when the shell already exists (wizard-safe).
    if (!this.querySelector(":scope > .rp-card")) this._render();
  }
}
```

`this._bodyNodes` transitions: `undefined` → `[]` or `[node, …]`.
On reconnect it is no longer `undefined`, so capture is skipped and the existing nodes are not
duplicated or lost.

---

### Pattern 2 — Async fetch with in-flight cancellation (used in `financial-year-field`)

Fetching data introduces a second concern: the element can be disconnected while the fetch is
still in-flight. If it reconnects before the response arrives, a second fetch must be started and
the first one discarded.

```js
class FinancialYearField extends HTMLElement {
  connectedCallback() {
    const firstConnect = this._initialOptions === undefined;

    if (firstConnect) {
      // True once. Set _initialOptions to a non-undefined value immediately so
      // reconnects during the in-flight request do not re-enter this branch.
      this._initialOptions = [];
      this._loadId = Symbol(); // unique token for this fetch attempt
    }

    // … base class rendering …

    if (firstConnect) {
      this._fetchOptions(this._loadId);
    } else if (this._data === undefined) {
      // Reconnected before the initial fetch completed (element was moved while
      // the request was in-flight). Start a fresh fetch with a new token.
      const id = Symbol();
      this._loadId = id;
      this._fetchOptions(id);
    }
    // If this._data !== undefined, the fetch already completed — skip entirely.
  }

  disconnectedCallback() {
    // Invalidate any in-flight fetch by rotating the token.
    // The pending _fetchOptions call will see the mismatch and bail out.
    this._loadId = Symbol();
  }

  async _fetchOptions(id) {
    try {
      const data = await apiFetch(/* … */);
      if (this._loadId !== id) return; // stale — a newer fetch is running

      this._data = data ?? [];
      this._render();
    } catch {
      if (this._loadId !== id) return;
      this._showFetchError();
    }
  }
}
```

The three states of `this._data`:

| Value              | Meaning                                                             |
| ------------------ | ------------------------------------------------------------------- |
| `undefined`        | Never fetched — first connect or reconnect during in-flight request |
| `null`             | Fetch returned a null/empty body                                    |
| An array or object | Fetch completed — skip on reconnect                                 |

---

## Sentinel pattern vs. `attributeChangedCallback`

| Scenario                                                  | Use                                                               |
| --------------------------------------------------------- | ----------------------------------------------------------------- |
| First-connect initialisation (capture nodes, start fetch) | `=== undefined` guard in `connectedCallback`                      |
| Re-render when a declared attribute changes after connect | `attributeChangedCallback`                                        |
| Prevent re-render before first connect                    | Guard `attributeChangedCallback` with `this._field !== undefined` |

Example of the combined pattern (from `financial-year-field`):

```js
class FinancialYearField extends HTMLElement {
  attributeChangedCallback(name, oldVal, newVal) {
    // Do nothing until the first connectedCallback has run.
    if (this._fyData !== undefined && this._connected) {
      this._updateOptions();
      this._doRender();
    } else {
      super.attributeChangedCallback(name, oldVal, newVal);
    }
  }
}
```

---

## Skeleton — safe async-loading component for use inside `tab-panel`

```js
class MyAsyncField extends HTMLElement {
  connectedCallback() {
    const firstConnect = this._data === undefined;

    if (firstConnect) {
      this._data = null; // mark as "fetch in progress"
      this._loadId = Symbol();
      this._render(); // render skeleton / loading state
      this._fetch(this._loadId);
    }
    // On reconnect with this._data !== undefined the existing rendered
    // content is still in the DOM — nothing to do.
  }

  disconnectedCallback() {
    this._loadId = Symbol(); // invalidate any in-flight fetch
  }

  async _fetch(id) {
    try {
      const result = await apiFetch(/* … */);
      if (this._loadId !== id) return;
      this._data = result;
      this._render();
    } catch {
      if (this._loadId !== id) return;
      this._renderError();
    }
  }

  _render() {
    /* build DOM from this._data */
  }
  _renderError() {
    /* show error state */
  }
}

customElements.define("my-async-field", MyAsyncField);
```

---

## Checklist for component authors

Before shipping a component that fetches data or captures child nodes, verify:

- [ ] `connectedCallback` checks `=== undefined` before running first-connect logic
- [ ] A `_loadId = Symbol()` token is created on first connect and rotated in `disconnectedCallback`
- [ ] `_fetchOptions` / `_fetch` bails out immediately when `this._loadId !== id`
- [ ] `attributeChangedCallback` guards re-renders with `this._field !== undefined` to avoid firing before first connect
- [ ] The component renders correctly after a disconnect → reconnect cycle (test by embedding it in a `<tab-panel>`)
