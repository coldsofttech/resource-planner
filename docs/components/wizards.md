# Wizard Components

Custom elements defined in `apps/web/static/js/components/wizards/`.

---

## `<step-wizard>`

Multi-step form wizard with a sidebar step navigator and panel layout. The declarative child structure is parsed once on connect, then replaced with rendered HTML. Body child nodes are captured and re-inserted into panel slots so their component state is preserved across navigation. Current step is synced to the URL via a query param.

**Attributes on `<step-wizard>`:**

| Attribute          | Type                   | Default      | Description                                                                                                                 |
| ------------------ | ---------------------- | ------------ | --------------------------------------------------------------------------------------------------------------------------- |
| `name`             | string                 | —            | Logical wizard name (used externally to identify the wizard)                                                                |
| `navigation`       | `sequential` \| `free` | `sequential` | `sequential`: steps can only be accessed in order; `free`: any step can be jumped to                                        |
| `route-prefix`     | string                 | `step`       | Query param name used for URL step sync (e.g. `?step=2`)                                                                    |
| `validate-on-next` | boolean                | —            | When present, fires `rp:validate` on the current panel before advancing and blocks navigation if any field reports an error |

**Public API:**

| Member / Method       | Description                                                       |
| --------------------- | ----------------------------------------------------------------- |
| `wizard.next()`       | Advance to the next step (validates if `validate-on-next` is set) |
| `wizard.back()`       | Go to the previous step                                           |
| `wizard.goTo(index)`  | Jump to a step by 0-based index (sequential rules apply)          |
| `wizard.currentIndex` | Current active step index (read/write)                            |

**Events fired:**

| Event       | Description                                                        |
| ----------- | ------------------------------------------------------------------ |
| `rp:finish` | Fired (bubbles) when the Finish button is clicked on the last step |

---

## Declarative child structure

```html
<step-wizard name="setup" validate-on-next>
  <wizard-steps
    title="Setup Steps"
    estimated-time="~10 min"
    show-progress
    back-label="Back"
    next-label="Next"
    finish-label="Finish"
  >
    <wizard-step nav-title="Admin Account" nav-subtitle="Create admin user">
      <wizard-step-header
        icon="bi-person"
        title="Admin Account"
        subtitle="Create the admin user"
      ></wizard-step-header>
      <wizard-step-body>
        <first-name-field id="first_name" required></first-name-field>
        <email-field id="email" required prefix-icon></email-field>
        <password-field id="password" required eye-icon strength></password-field>
      </wizard-step-body>
    </wizard-step>

    <wizard-step nav-title="Application">
      <wizard-step-header icon="bi-gear" title="Application Settings"></wizard-step-header>
      <wizard-step-body>
        <text-field id="app_name" label="App Name" required></text-field>
      </wizard-step-body>
    </wizard-step>
  </wizard-steps>
</step-wizard>
```

---

## `<wizard-steps>`

Configuration container for the sidebar and button labels. Place as a direct child of `<step-wizard>`.

| Attribute        | Type    | Default         | Description                               |
| ---------------- | ------- | --------------- | ----------------------------------------- |
| `title`          | string  | `"Setup Steps"` | Sidebar heading                           |
| `estimated-time` | string  | —               | Time estimate shown in the sidebar footer |
| `show-progress`  | boolean | —               | Shows a progress bar in the sidebar       |
| `back-label`     | string  | `"Back"`        | Back button label                         |
| `next-label`     | string  | `"Next"`        | Next button label                         |
| `finish-label`   | string  | `"Finish"`      | Finish button label on the last step      |

---

## `<wizard-step>`

One step in the wizard. Contains a `<wizard-step-header>` and a `<wizard-step-body>`.

| Attribute      | Type   | Description                                   |
| -------------- | ------ | --------------------------------------------- |
| `nav-title`    | string | Step label shown in the sidebar navigator     |
| `nav-subtitle` | string | Secondary line shown in the sidebar navigator |

---

## `<wizard-step-header>`

Renders the step's icon, title, and subtitle at the top of the step panel.

| Attribute  | Type   | Description                             |
| ---------- | ------ | --------------------------------------- |
| `icon`     | string | Bootstrap Icon class (e.g. `bi-person`) |
| `title`    | string | Step heading                            |
| `subtitle` | string | Step description below the heading      |

---

## `<wizard-step-body>`

Slot container for the step's form fields and content. Direct child nodes are captured and inserted into the panel body slot.

---

## `<wizard-step-footer>`

Footer slot. Back / Next / Finish navigation buttons are rendered automatically by `<step-wizard>` — the footer does not need to declare them.

---

## Validation integration

When `validate-on-next` is present on `<step-wizard>`, clicking Next fires a `rp:validate` custom event on the current step panel. All `BaseField` subclasses listen for this event and report validation errors. Navigation is blocked if any field is invalid.

```js
// Custom validator example
const field = document.getElementById("my-field");
field._customValidators.push({
  fn: (value) => value.startsWith("RP-"),
  msg: "Must start with RP-.",
});
```
