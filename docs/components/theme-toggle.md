# Theme Toggle Component

Custom element defined in `apps/web/static/js/components/theme-toggle.js`.

---

## `<rp-theme-toggle>`

An icon button that toggles between light and dark themes. Persists the selection in `localStorage` under the key `rp-theme` and applies `data-theme="light|dark"` to `<html>`.

On mount it reads the stored theme preference, falling back to the OS `prefers-color-scheme` media query.

**Attributes:** none — the element has no configurable attributes.

**Events emitted:**

| Event              | Fires when                                | Detail                         |
| ------------------ | ----------------------------------------- | ------------------------------ |
| `rp-theme-changed` | Theme is toggled (dispatched on `window`) | `{ theme: "light" \| "dark" }` |

**Events listened:**

| Event              | Source   | Effect                                                     |
| ------------------ | -------- | ---------------------------------------------------------- |
| `rp-theme-changed` | `window` | Syncs icon if another toggle on the page changed the theme |

**Example:**

```html
<!-- Place in a navbar or header -->
<rp-theme-toggle></rp-theme-toggle>
```

```js
// React to theme changes elsewhere in the page
window.addEventListener("rp-theme-changed", (e) => {
  console.log("Active theme:", e.detail.theme); // "light" or "dark"
});
```

---

## Notes

- The rendered button uses the `rp-iconbtn` class and swaps between `bi-moon` (light mode) and `bi-sun` (dark mode) icons.
- Multiple `<rp-theme-toggle>` instances on the same page stay in sync via the `rp-theme-changed` window event.
- The `disconnectedCallback` removes the window listener to prevent memory leaks.
