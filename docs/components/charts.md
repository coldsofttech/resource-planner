# Chart Components

Custom elements defined in `apps/web/static/js/components/charts/`.

Two chart types back the Utilisation Graph (#196): `<bar-chart>` (Chart.js-backed grouped bars + line combo, dual y-axis) and `<heatmap-chart>` (dependency-free CSS Grid heatmap with discrete threshold buckets).

Both also have an imperative JS utility counterpart — see [utilities.md](utilities.md).

---

## `<bar-chart>`

Grouped-bar + multi-line combo chart backed by Chart.js. Supports a single left axis (e.g. the Programmes tab's all-£ Forecast/Budget/Cumulative view) or a dual axis (e.g. the Teams/Members tabs' Days-vs-Util% view).

| Attribute  | Type   | Description                        |
| ---------- | ------ | ---------------------------------- |
| `title`    | string | Card heading text                  |
| `subtitle` | string | Small muted text next to the title |

**Public API — set via JS property, not an attribute (Chart.js needs live objects):**

```js
// Dual-axis: bars in Days (left), a % line on its own right axis
chart.data = {
  labels: ["Sprint 1", "Sprint 2", "Sprint 3"],
  axisLeftLabel: "Days",
  axisRightLabel: "Util%",
  bars: [
    { label: "Net Capacity", data: [10, 10, 8], color: "#6366f1" },
    { label: "Allocated", data: [4, 6, 8], color: "#f59e0b" },
  ],
  lines: [{ label: "Util%", data: [40, 60, 100], color: "#10b981", axis: "y1", max: 140 }],
};

// Single-axis: bars + 2 lines (one dashed) all sharing the £ scale
chart.data = {
  labels,
  axisLeftLabel: "£",
  bars: [{ label: "Forecast Cost (£)", data: forecastData, color: "#6366f1" }],
  lines: [
    { label: "Budget Baseline (£)", data: baselineData, color: "#ef4444", dashed: true },
    { label: "Cumulative (£)", data: cumulativeData, color: "#10b981" },
  ],
  meta: "Budget: £100,050    Forecast: £85,675",
};
```

- `bars` — rendered as grouped bars on the left axis (`axisLeftLabel`, default `"Value"`).
- `lines` — array of line series. Each defaults to the **left** axis (same scale as bars); set `axis: "y1"` only when a line needs a genuinely different scale (e.g. a % line alongside absolute-value bars) — `axisRightLabel` and `max` apply to that right axis.
- `dashed: true` on a line renders a dashed stroke with no point markers — use for a constant baseline/target line.
- `meta` — optional right-aligned header text next to the title (e.g. a running totals summary).
- Re-assigning `.data` destroys and recreates the underlying `Chart` instance.

```html
<bar-chart id="team-util-chart" title="Team Utilisation — Net Capacity vs Allocated"></bar-chart>
```

```js
const chart = document.getElementById("team-util-chart");
chart.data = { labels, axisLeftLabel: "Days", axisRightLabel: "Util%", bars, lines };
```

Avoid:

- Setting chart data via HTML attributes — Chart.js requires live JS arrays/objects.
- Reading `.data` back and mutating it in place — always assign a new object to trigger `_renderChart()`.

---

## `<heatmap-chart>`

Pure CSS Grid heatmap — no charting library. Member/sprint utilisation grid with discrete threshold-bucket coloring and an inline legend.

| Attribute | Type   | Description       |
| --------- | ------ | ----------------- |
| `title`   | string | Card heading text |

**Public API:**

```js
chart.data = {
  sprints: [{ sprint_code: "SPRINT-1", sprint_number: 1 } /* ... */],
  rows: [
    {
      label: "Doe, John",
      sublabel: "Backend",
      cells: [
        { display: "70%", bucket: "healthy", is_over: false },
        { display: "—", bucket: "none", is_over: false },
        { display: "10d", bucket: null, is_over: false },
      ],
    },
  ],
};
```

- `bucket` — one of `"none"` \| `"ramp"` \| `"healthy"` \| `"excellent"` \| `"over"`, or `null` for the absolute-day fallback (no capacity but some allocation exists — shown as `"Xd"` instead of a percentage).
- `is_over` — when `true`, adds a red underline treatment to the cell.

**Bucket thresholds (rendered in the legend):**

| Bucket      | Threshold     | Color                      |
| ----------- | ------------- | -------------------------- |
| `none`      | 0% / no alloc | Muted / sunken             |
| `ramp`      | < 50%         | Warning (amber)            |
| `healthy`   | 50–89%        | Success soft (light green) |
| `excellent` | 90–100%       | Success (solid green)      |
| `over`      | > 100%        | Danger (red)               |

```html
<heatmap-chart id="member-util-heatmap" title="Member Utilisation Heatmap"></heatmap-chart>
```

```js
const heatmap = document.getElementById("member-util-heatmap");
heatmap.data = { sprints, rows };
```

Avoid:

- Using a canvas/matrix charting plugin for this — the reference design uses discrete named buckets with in-cell text, which is a table-layout problem, not a plotting problem. CSS Grid gives real DOM text, native hover, and automatic dark/light theming for free.

---

## Canonical implementation

`apps/web/static/js/modules/resource-plans/utilisation.js` — builds chart/heatmap data from `UtilisationService.teams()` / `.members()` API responses and wires the Bar/Heatmap toggle on the Members tab.
