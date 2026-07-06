# JS Utility Functions

Shared utility functions from `apps/web/static/js/modules/utils/`. Import from the barrel:

```js
import { toast, statusModal } from "/static/js/modules/utils/index.js";
```

---

## `toast(options)`

**Source:** `apps/web/static/js/modules/utils/toast.js`

Shows a transient notification toast in a corner of the screen. Returns a `{ dismiss }` handle for programmatic dismissal.

```js
import { toast } from "/static/js/modules/utils/index.js";

toast({ type: "success", title: "Saved", message: "Your changes have been saved." });
toast({ type: "error", title: "Failed", message: err.data?.error?.message });
toast({ type: "warning", title: "Warning", message: "Check your input." });
toast({ type: "info", title: "Info", message: "Operation in progress." });
```

**Options:**

| Option       | Type    | Default       | Description                                           |
| ------------ | ------- | ------------- | ----------------------------------------------------- |
| `type`       | string  | `"info"`      | `"info"` \| `"success"` \| `"warning"` \| `"error"`   |
| `title`      | string  | `""`          | Bold heading text                                     |
| `message`    | string  | `""`          | Sub-text below the title                              |
| `actions`    | array   | `[]`          | `[{ label: string, onClick: fn }]` action buttons     |
| `duration`   | number  | `5000`        | Auto-dismiss delay in milliseconds                    |
| `persistent` | boolean | `false`       | When `true`, never auto-dismisses                     |
| `position`   | string  | `"top-right"` | Toast host position (CSS class on the host container) |
| `mini`       | boolean | `false`       | Compact single-line variant                           |

**Return value:**

```js
const { dismiss } = toast({ type: "info", title: "Processing…", persistent: true });
// later:
dismiss();
```

**Never:**

- Use `alert()` or console-only feedback for user messages.
- Build custom notification elements; always use `toast()`.

---

## `statusModal`

**Source:** `apps/web/static/js/modules/utils/modal.js`

A singleton JS object that controls a blocking overlay modal for status displays (progress, confirmation, result). Unlike `<status-modal>` (the custom element), this utility does not require a DOM element to be present — it mounts one on demand.

```js
import { statusModal } from "/static/js/modules/utils/index.js";

// Open
statusModal.open({
  iconType: "info",
  title: "Setting up…",
  body: "This may take a moment.",
  closeable: false,
  primaryBtn: { label: "Cancel", onClick: () => statusModal.close() },
});

// Update in-place (e.g. progress steps)
statusModal.update({ title: "Almost done…", iconType: "success" });

// Close
statusModal.close();
```

**`open(config)` / `update(patch)` config shape:**

| Key              | Type    | Default  | Description                                                                                                    |
| ---------------- | ------- | -------- | -------------------------------------------------------------------------------------------------------------- |
| `iconType`       | string  | `"info"` | `"info"` \| `"success"` \| `"warning"` \| `"error"`                                                            |
| `icon`           | string  | —        | Bootstrap Icon class override                                                                                  |
| `iconBgColor`    | string  | —        | CSS colour for the icon circle background                                                                      |
| `title`          | string  | `""`     | Modal heading                                                                                                  |
| `body`           | string  | `""`     | Paragraph text below title                                                                                     |
| `additionalBody` | string  | `""`     | Extra HTML appended below body                                                                                 |
| `closeable`      | boolean | `true`   | When `false`, removes × button and backdrop-click-close                                                        |
| `dismissBtn`     | object  | —        | `{ label, icon?, disabled?, onClick? }` — muted button                                                         |
| `secondaryBtn`   | object  | —        | `{ label, icon?, disabled?, onClick? }` — secondary button                                                     |
| `primaryBtn`     | object  | —        | `{ label, icon?, disabled?, onClick?, href? }` — primary button; `href` navigates instead of calling `onClick` |

**Methods:**

| Method                      | Description                                                |
| --------------------------- | ---------------------------------------------------------- |
| `statusModal.open(config)`  | Mounts (if needed) and opens the modal                     |
| `statusModal.update(patch)` | Merges `patch` into current config and re-renders in-place |
| `statusModal.close()`       | Hides the overlay                                          |

**Never:**

- Create custom overlay/backdrop elements; always use `statusModal`.
- Duplicate modal lifecycle logic per feature.

---

## `barChart(container, config)`

**Source:** `apps/web/static/js/modules/utils/bar-chart.js`

Imperative counterpart to the declarative `<bar-chart>` custom element (see [charts.md](charts.md)). Creates a `<bar-chart>`, mounts it into `container`, and sets its data — for pages that build chart placement dynamically rather than declaring `<bar-chart>` markup directly in a template.

```js
import { barChart } from "/static/js/modules/utils/index.js";

const chart = barChart(document.getElementById("chart-slot"), {
  title: "Team Utilisation — Net Capacity vs Allocated",
  data: { labels, bars, line },
});

// Later — re-render in place:
chart.data = newData;
```

Returns the mounted `<bar-chart>` element.

---

## `heatmapChart(container, config)`

**Source:** `apps/web/static/js/modules/utils/heatmap-chart.js`

Imperative counterpart to the declarative `<heatmap-chart>` custom element (see [charts.md](charts.md)). Same mount/return pattern as `barChart()`.

```js
import { heatmapChart } from "/static/js/modules/utils/index.js";

const heatmap = heatmapChart(document.getElementById("heatmap-slot"), {
  title: "Member Utilisation Heatmap",
  data: { sprints, rows },
});
```

Returns the mounted `<heatmap-chart>` element.

---

## Other utilities

For other shared utilities (`apiFetch`, `getCsrfToken`, `snapshotButton`, `setBusyButton`, `restoreButton`, `setLink`, validators, cookie utilities, `API_URLS`, `UI_URLS`), see the JS Standards rule file at `.claude/rules/js-standards.md`.
