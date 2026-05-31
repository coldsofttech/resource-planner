# Wizard Component

Custom elements defined in `apps/web/static/js/components/wizard.js`.

`<rp-wizard>` is a multi-step form wizard with a sidebar navigation, optional progress bar, URL-based routing, and built-in field validation on Next.

---

## `<rp-wizard>`

The root wizard element. Wraps the full step structure and replaces its declarative children with a rendered two-column layout (sidebar + main panel area).

**Attributes:**

| Attribute          | Type                   | Default      | Description                                                                                                      |
| ------------------ | ---------------------- | ------------ | ---------------------------------------------------------------------------------------------------------------- |
| `name`             | string                 | —            | Logical name for the wizard instance                                                                             |
| `navigation`       | `sequential` \| `free` | `sequential` | `sequential` prevents jumping ahead past unvisited steps; `free` allows clicking any nav button                  |
| `route-prefix`     | string                 | `step`       | URL search-param key used for deep-linking (e.g. `?step=2`)                                                      |
| `validate-on-next` | boolean                | —            | When present, Next/Finish fires `rp:validate` on the current panel and blocks navigation if any field is invalid |

**Programmatic API:**

| Method / Property | Description                                                |
| ----------------- | ---------------------------------------------------------- |
| `next()`          | Advance to the next step (validates if `validate-on-next`) |
| `back()`          | Return to the previous step                                |
| `goTo(index)`     | Jump to a specific step by 0-based index                   |
| `currentIndex`    | Read the current 0-based step index                        |

**Events emitted:**

| Event       | Fires when                               |
| ----------- | ---------------------------------------- |
| `rp:finish` | User clicks Next/Finish on the last step |

**Example:**

```html
<rp-wizard id="setup-wizard" validate-on-next>
  <wizard-steps
    title="Setup Steps"
    show-progress
    estimated-time="5 min"
    back-label="Back"
    next-label="Next"
    finish-label="Finish"
  >
  </wizard-steps>

  <wizard-step nav-title="Account" nav-subtitle="Admin user">
    <wizard-step-header
      icon="bi-person"
      title="Create Admin Account"
      subtitle="This account will have full access."
    >
    </wizard-step-header>
    <wizard-step-body>
      <rp-field-first-name id="first-name" autocomplete="given-name"></rp-field-first-name>
      <rp-field-last-name id="last-name" autocomplete="family-name"></rp-field-last-name>
      <rp-field-email id="email" required autocomplete="email" col="col-md-8"></rp-field-email>
      <rp-field-password
        id="pw"
        required
        eye-icon
        strength
        autocomplete="new-password"
      ></rp-field-password>
    </wizard-step-body>
  </wizard-step>

  <wizard-step nav-title="App" nav-subtitle="Basic settings">
    <wizard-step-header icon="bi-gear" title="Application Settings"> </wizard-step-header>
    <wizard-step-body>
      <rp-field-text id="app-name" label="App Name" required col="col-md-8"></rp-field-text>
    </wizard-step-body>
  </wizard-step>
</rp-wizard>

<script>
  document.getElementById("setup-wizard").addEventListener("rp:finish", () => {
    // collect values and submit
  });
</script>
```

---

## `<wizard-steps>`

Configuration element for the sidebar. Place once as a direct child of `<rp-wizard>`.

**Attributes:**

| Attribute        | Type    | Default       | Description                                                |
| ---------------- | ------- | ------------- | ---------------------------------------------------------- |
| `title`          | string  | `Setup Steps` | Sidebar section heading                                    |
| `back-label`     | string  | `Back`        | Label for the Back button                                  |
| `next-label`     | string  | `Next`        | Label for the Next button                                  |
| `finish-label`   | string  | `Finish`      | Label for the Next button on the last step                 |
| `show-progress`  | boolean | —             | Show a progress bar and step counter in the sidebar footer |
| `estimated-time` | string  | —             | Optional time estimate shown beneath the progress bar      |

---

## `<wizard-step>`

Represents one step. Each `<wizard-step>` becomes one sidebar nav button and one panel.

**Attributes:**

| Attribute      | Type   | Default  | Description                               |
| -------------- | ------ | -------- | ----------------------------------------- |
| `nav-title`    | string | `Step N` | Label shown in the sidebar nav button     |
| `nav-subtitle` | string | —        | Smaller subtitle line under the nav title |

---

## `<wizard-step-header>`

Declares the panel header for a step. Place as a direct child of `<wizard-step>`.

**Attributes:**

| Attribute  | Type   | Default | Description                                                      |
| ---------- | ------ | ------- | ---------------------------------------------------------------- |
| `icon`     | string | —       | Bootstrap Icons class for the large step icon (e.g. `bi-person`) |
| `title`    | string | —       | Panel heading text                                               |
| `subtitle` | string | —       | Smaller description below the heading                            |

---

## `<wizard-step-body>`

Wraps the field content for a step. Direct children are placed inside the panel's `row g-3` grid. Place as a direct child of `<wizard-step>`.

---

## `<wizard-step-footer>`

Reserved footer slot for a step (no built-in rendering — available for custom use).

---

## Navigation behaviour

- **Sequential mode** (default): users can only advance by clicking Next or nav buttons for completed/current steps. Clicking a future step that hasn't been reached yet is blocked.
- **Free mode**: any nav button is clickable regardless of progress.
- The current step index is synced to the URL (`?step=N`) via `history.replaceState` so the browser Back button works.
- On mobile (> 5 steps) the sidebar shows only the current step ± 1, first, and last, with `…` ellipsis in between.

## Validation

When `validate-on-next` is set:

1. The wizard fires `rp:validate` on the active panel element.
2. All field components inside the panel respond by marking themselves touched and showing error messages.
3. `reportValidity()` is called on every native `input`, `select`, and `textarea` inside the panel.
4. Navigation is blocked if any field is invalid.
