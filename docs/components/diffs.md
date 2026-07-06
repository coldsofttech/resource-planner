# Diff Components

Custom elements defined in `apps/web/static/js/components/diffs/`.

## `<diff-compare>`

Git-like diff/compare table, backing the Snapshot Compare feature (#197). Renders a set of typed rows (`add`/`del`) across configurable columns, reusing the green/red add/del color language of a unified text diff, generalized to tabular data instead of text lines.

There is no "changed" row state — a modified value is represented as an adjacent `del` row (old value) followed by an `add` row (new value).

| Attribute | Type   | Description       |
| --------- | ------ | ----------------- |
| `title`   | string | Card heading text |

**Public API — set via JS property, not an attribute:**

```js
diffEl.columns = [
  { key: "sprintName", label: "Sprint" },
  { key: "memberName", label: "Member" },
  { key: "teamName", label: "Team" },
  { key: "projectName", label: "Project" },
  { key: "phaseName", label: "Phase" },
  { key: "assignmentType", label: "Type" },
  { key: "days", label: "Days" },
];

diffEl.data = {
  rows: [
    {
      type: "del",
      cells: { sprintName: "Sprint 9", memberName: "john.doe@example.com", days: "2.75" },
    },
    {
      type: "add",
      cells: { sprintName: "Sprint 9", memberName: "john.doe@example.com", days: "1.25" },
    },
  ],
};
```

- `columns` — ordered column definitions; each renders as a `<td>`-equivalent cell keyed by `cells[key]`.
- `data.rows` — `undefined` renders nothing (initial/unset state); an empty array (`[]`) renders a muted "No differences found." message; a populated array renders the diff grid.
- Each row gets a leading gutter column with a single `+`/`-` glyph, colored per `type` (green add / red del).

```html
<diff-compare id="rp-snapshot-diff"></diff-compare>
```

```js
const diffEl = document.getElementById("rp-snapshot-diff");
diffEl.setAttribute("title", `${result.snapshot_a.label} → ${result.snapshot_b.label}`);
diffEl.columns = [
  /* ... */
];
diffEl.data = { rows: result.rows };
```

Avoid:

- Passing raw HTML in `cells` values — they are escaped via `esc()` on render, so only plain text is supported.
- Introducing a "changed" row type/color — a value change is always represented as a del+add pair, matching the git diff convention this component follows.

---

## Canonical implementation

`apps/web/static/js/modules/resource-plans/snapshots.js` — builds `columns`/`data` from `SnapshotService.compare()`'s API response and wires the Compare drawer's form → diff swap.
