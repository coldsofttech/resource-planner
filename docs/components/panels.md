# Panel Components

Custom elements defined in `apps/web/static/js/components/panels/`.

---

## `<section-panel>`

Sunken card container with an optional titled header and a body slot. Body child nodes are captured once on connect and re-inserted into a slot div after render, preserving component state when the panel is moved by the wizard.

**Declarative children (captured before first render):**

```html
<section-panel id="details" title="Details" icon="bi-person" col="col-12">
  <panel-title>Team <strong>Details</strong></panel-title>
  <panel-body>
    <text-field id="name" label="Name" required></text-field>
    <text-field id="desc" label="Description" cols="3"></text-field>
  </panel-body>
</section-panel>
```

| Attribute | Type   | Default    | Description                                                         |
| --------- | ------ | ---------- | ------------------------------------------------------------------- |
| `col`     | string | `col-12`   | Bootstrap column class applied to the host element                  |
| `title`   | string | —          | Plain-text card heading (used when `<panel-title>` child is absent) |
| `icon`    | string | —          | Bootstrap Icon class shown before the title (e.g. `bi-person`)      |
| `id`      | string | —          | Element id; also used as `name` fallback                            |
| `name`    | string | `id` value | Logical name for the panel                                          |

**Re-connection safety:** when the wizard moves this element the `.rp-card` shell is kept intact — a full re-render is skipped to avoid detaching body nodes and losing component state.

---

## `<panel-title>`

Rich HTML heading container for `<section-panel>`. When present as a direct child, its `innerHTML` is used as the card heading instead of the `title` attribute. Content is captured once on first connect.

```html
<panel-title>Team <strong>Details</strong></panel-title>
```

---

## `<panel-body>`

Slot container for both `<section-panel>` and `<card-panel>`. Child nodes are captured once by the parent and inserted into the rendered `.rp-card-body`. Any valid HTML or custom elements can be placed inside.

```html
<panel-body>
  <text-field id="name" label="Name" required></text-field>
  <email-field id="email" label="Email" required></email-field>
</panel-body>
```

---

## `<card-panel>`

Flexible slot-driven card container. Maps three optional declarative children to the three CSS regions of `.rp-card`. Unlike `<section-panel>`, headers and content are completely free-form — no imposed styling or heading conventions.

Re-connection is wizard-safe: the render is skipped if the card shell already exists in the DOM.

### Attributes

| Attribute | Type   | Default   | Description                                                               |
| --------- | ------ | --------- | ------------------------------------------------------------------------- |
| `col`     | string | `col-12`  | Bootstrap column class applied to the host element                        |
| `variant` | string | `default` | `default` (surface bg, border, shadow) \| `sunken` (sunken bg, no shadow) |

### Slot children

Omit any slot to suppress that CSS region. If no slot children are declared, an empty `.rp-card-body` is rendered.

| Child            | Maps to         | Description                                                          |
| ---------------- | --------------- | -------------------------------------------------------------------- |
| `<panel-header>` | `.rp-card-head` | Card header; separated from body by a bottom border                  |
| `<panel-body>`   | `.rp-card-body` | Main card body with standard padding (shared with `<section-panel>`) |
| `<panel-footer>` | `.rp-card-foot` | Card footer; separated from body by a top border                     |

### Variants

| Value     | CSS applied              | Appearance                         |
| --------- | ------------------------ | ---------------------------------- |
| `default` | `rp-card`                | Surface background, border, shadow |
| `sunken`  | `rp-card rp-card-sunken` | Sunken background, no shadow       |

### Examples

```html
<!-- Sunken info card (content only) -->
<card-panel variant="sunken" col="col-md-6">
  <panel-body>
    <strong>File specification</strong>
    <ul class="mt-2" style="font-size:13px;color:var(--rp-text-muted);line-height:1.7">
      <li><span class="rp-mono">project_code</span> — required, ≤ 24 chars</li>
    </ul>
    <link-field href="#" icon="bi-download" style="font-size:13px">Download sample CSV</link-field>
  </panel-body>
</card-panel>

<!-- Card with header and content -->
<card-panel>
  <panel-header>
    <span class="rp-card-title">Team members</span>
    <primary-button label="Add member" size="sm"></primary-button>
  </panel-header>
  <panel-body>
    <data-table id="members-table">...</data-table>
  </panel-body>
</card-panel>

<!-- Card with all three slots -->
<card-panel>
  <panel-header>
    <span class="rp-card-title">Budget</span>
  </panel-header>
  <panel-body>
    <p>Allocated: £120,000</p>
  </panel-body>
  <panel-footer>
    <span style="color:var(--rp-text-muted);font-size:13px">Updated 2 hours ago</span>
    <link-field href="/budget/" variant="muted">View breakdown</link-field>
  </panel-footer>
</card-panel>
```

---

## `<panel-header>`

Slot container for the header region of `<card-panel>`. Child nodes are captured once and inserted into `.rp-card-head`. The header region uses `display: flex; justify-content: space-between` — place a title on the left and action controls on the right.

```html
<panel-header>
  <span class="rp-card-title">Section title</span>
  <primary-button label="Add" size="sm"></primary-button>
</panel-header>
```

---

## `<panel-footer>`

Slot container for the footer region of `<card-panel>`. Child nodes are captured once and inserted into `.rp-card-foot`. The footer region uses `display: flex; justify-content: space-between` — place metadata on the left and actions on the right.

```html
<panel-footer>
  <span style="color:var(--rp-text-muted);font-size:13px">3 items</span>
  <link-field href="#export" variant="muted">Export</link-field>
</panel-footer>
```
