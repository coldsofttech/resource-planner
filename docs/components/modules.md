# Module Components

Pre-configured components from `apps/web/static/js/components/modules/`. These build on shared primitives for domain-specific use cases.

---

## Views

### `<list-view>`

Coordinator that connects a `<filter-panel>` child to a `<data-table>` child. When the filter emits `rp:filter:change`, this element builds the new URL (base URL + filter params) and sets it on the table, triggering a reload.

| Attribute             | Type                       | Default      | Description                                                               |
| --------------------- | -------------------------- | ------------ | ------------------------------------------------------------------------- |
| `layout`              | `horizontal` \| `vertical` | `horizontal` | `horizontal`: filter bar above table; `vertical`: filterpane beside table |
| `show-active-filters` | boolean                    | —            | When present, auto-injects an `<active-filter>` before the filter panel   |

**Usage (horizontal):**

```html
<list-view show-active-filters>
  <filter-panel>
    <search-field name="search" placeholder="Search teams…"></search-field>
    <is-active-field name="is_active" label="Status" col="col-md-3"></is-active-field>
  </filter-panel>
  <data-table url="/api/v1/teams/" paginated>
    <table-columns>…</table-columns>
    <table-actions>…</table-actions>
  </data-table>
</list-view>
```

**Usage (vertical):**

```html
<list-view layout="vertical" show-active-filters>
  <filter-panel layout="vertical">
    <filter-group name="status" label="Status" open>
      <filter-option value="true" count="12">Active</filter-option>
      <filter-option value="false" count="3">Inactive</filter-option>
    </filter-group>
  </filter-panel>
  <data-table url="/api/v1/teams/" paginated>…</data-table>
</list-view>
```

---

### `<import-view>`

Self-contained import workflow inside a large `<drawer-modal>`. See source for full API — exposes `show()` / `hide()` and fires `rp:import:complete`.

---

### `<export-view>`

Self-contained export workflow inside a large `<drawer-modal>`. On open: mirrors active filters read-only and loads column specs. Fires `rp:export` when the Export button is clicked — actual download is not wired yet.

| Attribute          | Type   | Description                                                                                                                                                           |
| ------------------ | ------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `title`            | string | Drawer title. Default: `"Export"`                                                                                                                                     |
| `eyebrow`          | string | Optional eyebrow text above the title                                                                                                                                 |
| `active-filter-id` | string | `id` of an `<active-filter>` (or `<filter-panel>`) whose active filters are shown read-only inside the drawer. When omitted the filter row is not rendered.           |
| `specs-url`        | string | `GET` endpoint returning `{ data: { columns: [{ key, label }] } }` — populates the column checkboxes                                                                  |
| `export-url`       | string | `GET` endpoint for the actual export download (reserved — not wired yet)                                                                                              |
| `table-id`         | string | Optional `id` of a `<data-table>`; columns whose `key` matches a `<table-column key="…">` on that table are pre-checked. All columns checked by default when omitted. |

**Events:**

| Event       | Detail                | Description                                                                                                                  |
| ----------- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `rp:export` | `{ format, columns }` | Fired on Export click. `format` is `"csv"` \| `"xlsx"` \| `"pdf"` \| `"json"`. `columns` is an array of checked column keys. |

**Usage:**

```html
<export-view
  id="teams-export"
  title="Export Teams"
  eyebrow="Teams"
  active-filter-id="rp-teams-active-filter"
  specs-url="/api/v1/teams/export/specs/"
  export-url="/api/v1/teams/export/"
  table-id="rp-teams-table"
>
</export-view>
```

```js
document.getElementById("rp-teams-export-btn").addEventListener("click", () => {
  document.getElementById("teams-export").show();
});
```

**Public API:**

| Method        | Description       |
| ------------- | ----------------- |
| `view.show()` | Opens the drawer  |
| `view.hide()` | Closes the drawer |

---

## Pills

### `<sprint-pill>`

Displays the active sprint name and a live countdown to its end date. The element **auto-fetches** `GET /api/v1/sprints/active/` on connect — no external attributes are required. It hides itself when there is no active sprint or when the fetch fails.

The dot colour reflects sprint health:

| Colour | Condition                                             |
| ------ | ----------------------------------------------------- |
| Green  | In progress, more than 3 days remaining               |
| Amber  | In progress, 3 days or fewer remaining                |
| Muted  | Sprint not in progress (should not normally be shown) |

The countdown auto-updates every minute.

**Click navigation:** Clicking the pill (or pressing Enter / Space while it has focus) navigates to the sprint detail page at `/sprints/<code>/`. The element sets `role="link"` and `tabindex="0"` automatically so it is keyboard-accessible.

The element is pre-mounted in `templates/base.html` as `<sprint-pill id="active-sprint">` — do not add it to individual page templates.

```html
<!-- Already in base.html — do not repeat in child templates -->
<sprint-pill id="active-sprint"></sprint-pill>
```

---

## Dropdowns

### `<is-active-field>`

Business-specific status filter dropdown. Pre-configured options — no `<values-list>` child needed. See `dropdowns.md` for full documentation.

---

## Module Fields

Pre-configured text field wrappers from `apps/web/static/js/components/modules/fields/`.

### `<first-name-field>`

Pre-configured `<text-field>`. Defaults: label "First name", required, maxlength 100, placeholder "John", autocomplete "given-name".

### `<last-name-field>`

Pre-configured `<text-field>`. Defaults: label "Last name", required, maxlength 100, placeholder "Doe", autocomplete "family-name".

---

## Account Components

Components from `apps/web/static/js/components/modules/account/` and `apps/web/static/js/components/modules/users/` for user profile and avatar rendering.

### `<user-avatar>`

Circular avatar display for user and member rows, drawers, and any context that needs a user photo with an initials fallback. Applies the `rp-avatar` class (and a size modifier) directly to itself, so it can be dropped in anywhere an `rp-avatar` div would have been used.

| Attribute    | Type   | Default | Description                                                                                                                                                                                                                                                                                                                |
| ------------ | ------ | ------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `avatar-url` | string | —       | Photo URL. Absent or empty renders the initials fallback. If the image fails to load, the element silently falls back to initials.                                                                                                                                                                                         |
| `name`       | string | —       | Display name — used for the `<img alt>` attribute and to derive initials when `seed` is not set. Initials are taken from the first letter of the first and last space-separated word (e.g. `"Mira Aslan"` → `MA`; a single word uses its first two characters).                                                            |
| `seed`       | string | —       | Alternative seed for initials — splits on `@`, `.`, `_`, `-`, and whitespace rather than spaces only. Use this when the only available value is an email address (e.g. `"mira.aslan@co.com"` → `MA`). When both `name` and `seed` are set, `seed` takes precedence for initials only; `name` is still used for `alt` text. |
| `size`       | string | `"md"`  | `"sm"` \| `"md"` (32 px, default) \| `"lg"` \| `"xl"`                                                                                                                                                                                                                                                                      |

All four attributes are observed — updating any of them re-renders the element in place.

```html
<!-- Display name → initials fallback -->
<user-avatar name="Mira Aslan" size="sm"></user-avatar>

<!-- Photo with name for alt text -->
<user-avatar avatar-url="/media/avatars/1.jpg" name="Mira Aslan" size="lg"></user-avatar>

<!-- Email seed (e.g. when display_name is not available) -->
<user-avatar seed="mira.aslan@company.com" size="md"></user-avatar>

<!-- Both name (for alt) and seed (for initials) -->
<user-avatar name="Mira Aslan" seed="mira.aslan@company.com" size="md"></user-avatar>
```

```js
// Set from row data after an API response
const el = document.querySelector("user-avatar");
el.setAttribute("avatar-url", row.avatar_url || "");
el.setAttribute("name", row.display_name || row.email || "");
// Supply seed when the user may not have a display name
if (!row.display_name && row.email) {
  el.setAttribute("seed", row.email);
}
```

---

### `<user-avatar-profile>`

Avatar upload component for the account profile page. Renders the current avatar (or an initials fallback) with a camera button to pick and upload a new photo. SSO accounts disable the camera button.

| Attribute    | Type    | Default | Description                                                                                              |
| ------------ | ------- | ------- | -------------------------------------------------------------------------------------------------------- |
| `avatar-url` | string  | —       | Current photo URL; absent or empty renders the initials identicon                                        |
| `seed`       | string  | —       | Seed string used to derive initials for the fallback avatar (typically the user's display name or email) |
| `is-sso`     | boolean | —       | When present, disables the camera button with a tooltip explaining SSO accounts cannot change avatars    |
| `sso-name`   | string  | —       | Name of the SSO provider shown in the disabled tooltip (e.g. `"Google"`)                                 |

**Accepted file formats:** JPEG, PNG, GIF, WEBP. Maximum size: 5 MB.

**Public API:**

| Method                     | Description                                   |
| -------------------------- | --------------------------------------------- |
| `component.setAvatar(url)` | Updates the displayed avatar to the given URL |

**Events:**

| Event               | Detail                  | Description                            |
| ------------------- | ----------------------- | -------------------------------------- |
| `rp:avatar:changed` | `{ avatarUrl: string }` | Fired after the new avatar is uploaded |

```html
<user-avatar-profile avatar-url="/media/avatars/user-1.jpg" seed="Jane Smith"></user-avatar-profile>
```

```html
<!-- SSO user — camera disabled -->
<user-avatar-profile seed="jane.smith@company.com" is-sso sso-name="Google"></user-avatar-profile>
```

```js
const profile = document.querySelector("user-avatar-profile");
profile.addEventListener("rp:avatar:changed", (e) => {
  console.log("New avatar URL:", e.detail.avatarUrl);
});
```

---

### `<user-profile>`

Top-bar account dropdown. Renders an avatar trigger button and a dropdown panel populated from `GET /api/v1/auth/me/` on first open. Pre-mounted in `templates/base.html` — do not add additional instances.

**Responsibilities:**

- Displays user avatar (or initials fallback) in the trigger button and panel header
- Shows user name and email in the panel
- Syncs the server-stored theme preference to `localStorage` on first load
- Persists theme changes via `PATCH /api/v1/users/me/preferences/` when `<theme-toggle>` fires
- Handles `Ctrl+,` / `⌘+,` shortcut to navigate to `/profile/`
- Handles sign-out via `POST /api/v1/auth/logout/`

---

## Permissions

### `<permissions-panel>`

Self-contained component for displaying and editing permission category assignments. Handles both group and user subjects in edit or view modes.

| Attribute      | Type   | Description           |
| -------------- | ------ | --------------------- |
| `subject-type` | string | `"group"` \| `"user"` |

**Public API:**

| Method                            | Description                                                                          |
| --------------------------------- | ------------------------------------------------------------------------------------ |
| `panel.load(subjectCode)`         | Loads categories and current assignments for editing                                 |
| `panel.save()`                    | Diffs and persists changes; returns a `Promise`                                      |
| `panel.loadAssigned(subjectCode)` | Loads current assignments as a read-only list                                        |
| `panel.loadEffective(userCode)`   | Loads effective (group + direct) permissions as a read-only list (user subject only) |

**Events:**

| Event                  | Detail     | Description                       |
| ---------------------- | ---------- | --------------------------------- |
| `rp:permissions:saved` | `{ code }` | Fired after a successful `save()` |

```html
<permissions-panel subject-type="group"></permissions-panel>
```

```js
const panel = document.querySelector("permissions-panel");
await panel.load("GRP-0001");

// Later, on save button click:
await panel.save();
```
