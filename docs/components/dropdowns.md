# Dropdown Components

Custom elements defined in `apps/web/static/js/components/dropdowns/`.

Dropdown components extend `BaseField` — see `fields.md` for inherited attributes (`col`, `label`, `required`, `id`, `name`, `hint`, `hint-type`, `value`, `autocomplete`).

---

## `<dropdown-field>`

Select/dropdown field. Options are declared as children and parsed once on connect.

**Declarative children:**

```html
<values-list>
  <value id="…" value="…" selected>Label</value>
  <value id="…" value="…" disabled>Disabled option</value>
</values-list>
```

| `<value>` attribute | Type    | Description                                                                |
| ------------------- | ------- | -------------------------------------------------------------------------- |
| `id`                | string  | Optional id on the rendered `<option>`                                     |
| `value`             | string  | Submitted value; falls back to text content                                |
| `selected`          | boolean | Pre-selects this option (fallback when `value` attr is absent on the host) |
| `disabled`          | boolean | Renders this option as disabled                                            |

**Additional attributes:**

| Attribute     | Type   | Default | Description                                               |
| ------------- | ------ | ------- | --------------------------------------------------------- |
| `placeholder` | string | —       | First disabled/hidden option prompting the user to choose |

**Validation:** required → an option with a non-empty value must be selected.

**Selection precedence:** the `value` attribute on the host element takes priority over the `selected` attribute on individual `<value>` children.

```html
<dropdown-field id="role" name="role" label="Role" required>
  <values-list>
    <value value="admin">Admin</value>
    <value value="member" selected>Member</value>
    <value value="viewer">Viewer</value>
  </values-list>
</dropdown-field>
```

---

## Module Dropdowns

Pre-configured convenience fields from `apps/web/static/js/components/modules/dropdowns/`:

### `<is-active-field>`

Business-specific status filter dropdown. Options: **All Statuses** (empty value, selected by default), **Active** (`true`), **Inactive** (`false`). Extends `<dropdown-field>` with hard-coded options — no `<values-list>` child needed.

| Attribute | Type   | Description                                  |
| --------- | ------ | -------------------------------------------- |
| `value`   | string | `"true"` \| `"false"` \| `""` (default `""`) |

```html
<is-active-field name="is_active" label="Status" col="col-md-3"></is-active-field>
```

---

### Static Dropdown Fields

These fields extend `DropdownField` with hardcoded options — no API fetch and no `<values-list>` child needed.

#### `<auth-type-field>`

Authentication type filter. Options: All Auth Types / Classic / OAuth / SAML.

| Attribute    | Type    | Description                                            |
| ------------ | ------- | ------------------------------------------------------ |
| `value`      | string  | `"classic"` \| `"oauth"` \| `"saml"` \| `""` (default) |
| `show-label` | boolean | Renders "Auth Type" as the visible field label         |

```html
<auth-type-field name="auth_type" show-label></auth-type-field>
```

---

#### `<fy-status-field>`

Financial year status filter. Options: Future / In Progress / Completed / Expired.

| Attribute    | Type    | Description                                                              |
| ------------ | ------- | ------------------------------------------------------------------------ |
| `value`      | string  | `"future"` \| `"in_progress"` \| `"completed"` \| `"expired"` \| `""`    |
| `allow-all`  | boolean | Prepends an "All Statuses" option (default when used in filter contexts) |
| `show-label` | boolean | Renders "Status" as the visible field label                              |

```html
<fy-status-field name="fy_status" allow-all show-label></fy-status-field>
```

---

#### `<project-estimate-status-field>`

Project estimate status filter. Options: Draft / Reviewed / Shared / Approved (+ optional Superseded).

| Attribute          | Type    | Description                                                                       |
| ------------------ | ------- | --------------------------------------------------------------------------------- |
| `value`            | string  | `"DRAFT"` \| `"REVIEWED"` \| `"SHARED"` \| `"APPROVED"` \| `"SUPERSEDED"` \| `""` |
| `allow-all`        | boolean | Prepends an "All Statuses" option                                                 |
| `allow-superseded` | boolean | Appends "Superseded" as the last option                                           |
| `show-label`       | boolean | Renders "Status" as the visible field label                                       |

---

#### `<sprint-status-field>`

Sprint status filter. Options: Future / In Progress / Completed / Expired.

| Attribute    | Type    | Description                                                           |
| ------------ | ------- | --------------------------------------------------------------------- |
| `value`      | string  | `"future"` \| `"in_progress"` \| `"completed"` \| `"expired"` \| `""` |
| `allow-all`  | boolean | Prepends an "All Statuses" option                                     |
| `show-label` | boolean | Renders "Status" as the visible field label                           |

---

### API-Fetching Dropdown Fields

These fields fetch their options from the API on first connect and cache them for the element's lifetime. All inherit the full `DropdownField` / `BaseField` API.

**Common attributes (all fields below unless noted):**

| Attribute    | Type    | Description                                                                                              |
| ------------ | ------- | -------------------------------------------------------------------------------------------------------- |
| `value`      | string  | Pre-selected option code; takes priority over `is_default` from the API                                  |
| `allow-all`  | boolean | Prepends an "All …" option with `value=""`, selected by default; use in filter contexts                  |
| `show-label` | boolean | Renders the field label as visible text; without this attribute the label is hidden (label-less variant) |

| Element                     | Default label      | API endpoint                                      | Notes                                                           |
| --------------------------- | ------------------ | ------------------------------------------------- | --------------------------------------------------------------- |
| `<role-field>`              | Role               | `GET /api/v1/roles/options/`                      | Pre-selects `is_default` role when `value` is absent            |
| `<timezone-field>`          | Timezone           | `GET /api/v1/users/options/`                      | No `allow-all`                                                  |
| `<employment-type-field>`   | Employment Type    | `GET /api/v1/emp-types/options/`                  | Pre-selects `is_default` employment type when `value` is absent |
| `<location-field>`          | Location           | `GET /api/v1/locations/options/`                  | Options render as "City, Country"; pre-selects `is_default`     |
| `<confidence-field>`        | Confidence         | `GET /api/v1/projects/options/?fields=confidence` |                                                                 |
| `<priority-field>`          | Priority           | `GET /api/v1/projects/options/?fields=priority`   |                                                                 |
| `<programme-field>`         | Programme          | `GET /api/v1/programmes/options/`                 |                                                                 |
| `<project-field>`           | Project            | `GET /api/v1/projects/options/`                   | See `programme-id` below                                        |
| `<project-status-field>`    | Project Status     | `GET /api/v1/projects/statuses/options/`          |                                                                 |
| `<project-substatus-field>` | Project Sub-Status | `GET /api/v1/projects/sub-statuses/options/`      | See `status-id` below                                           |
| `<project-type-field>`      | Project Type       | `GET /api/v1/projects/types/options/`             |                                                                 |
| `<sprint-field>`            | Sprint             | `GET /api/v1/sprints/options/`                    | See `fy-code`, `allow-all`, `unassign` below                    |

**Additional attributes for specific fields:**

`<financial-year-field>` → `GET /api/v1/fy/options/`:

| Attribute    | Type    | Description                                                   |
| ------------ | ------- | ------------------------------------------------------------- |
| `show-long`  | boolean | Labels show `FY2024-2025` format                              |
| `show-short` | boolean | Labels show short FY format (takes priority over `show-long`) |

```html
<financial-year-field id="plan-fy" required col="col-md-6" show-label></financial-year-field>
<financial-year-field
  id="filter-fy"
  name="fy"
  allow-all
  show-label
  show-short
></financial-year-field>
```

`<project-field>`:

| Attribute      | Type   | Description                                                                                                         |
| -------------- | ------ | ------------------------------------------------------------------------------------------------------------------- |
| `programme-id` | string | `id` of a `<programme-field>` whose value scopes the project list; shows all projects when no programme is selected |

```html
<programme-field id="prog-field" required col="col-md-6" show-label></programme-field>
<project-field
  id="proj-field"
  programme-id="prog-field"
  required
  col="col-md-6"
  show-label
></project-field>
```

`<project-substatus-field>`:

| Attribute   | Type   | Description                                                                                                         |
| ----------- | ------ | ------------------------------------------------------------------------------------------------------------------- |
| `status-id` | string | `id` of a `<project-status-field>` whose value scopes the sub-status list; disabled when no main status is selected |

`<sprint-field>`:

Options are fetched from `GET /api/v1/sprints/options/` on first connect. The select is disabled while loading and re-fetches automatically when `fy-code` changes.

| Attribute    | Type    | Description                                                                                                                                                                             |
| ------------ | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `fy-code`    | string  | Financial year code; filters options to sprints in that FY. Changing the attribute immediately re-fetches and disables the select until the new options arrive.                         |
| `allow-all`  | boolean | Prepends **All Sprints** (`value=""`) as the first option, selected by default. Use in filter contexts.                                                                                 |
| `unassign`   | boolean | Prepends **Unassign from current sprint** (`value=""`) as the first option. Use in edit contexts when the field already has a value and the user should be able to explicitly clear it. |
| `show-label` | boolean | Renders "Sprint" as the visible field label (hidden by default, matching the label-less variant used in most inline field groups).                                                      |

**Public API:**

| Method            | Description                                                                                                                                                            |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `field.refresh()` | Re-fetches sprint options from the API. Disables the select during loading and restores it when done. Useful after a new sprint is created without a full page reload. |

**Error state:** If the API request fails, the select is disabled and shows "Could not load sprints". The field error element shows "Could not load sprints. Refresh the page to retry."

```html
<!-- Form / create context: required, scoped to a FY, with visible label -->
<sprint-field id="plan-sprint" required col="col-md-6" fy-code="FY-1" show-label></sprint-field>

<!-- Filter context: show all sprints in the selected FY, with an "All Sprints" option -->
<sprint-field id="filter-sprint" name="sprint" fy-code="FY-1" allow-all show-label></sprint-field>

<!-- Edit context: allow the user to clear the current sprint assignment -->
<sprint-field id="edit-sprint" col="col-md-6" unassign show-label></sprint-field>
```

```js
// Scope options to whichever FY the user selects
fyField.addEventListener("rp:change", (e) => {
  sprintField.setAttribute("fy-code", e.detail.value);
});

// Refresh options after a new sprint is created
document.getElementById("plan-sprint").refresh();
```

---

### Hybrid Single / Multi-Select Dropdown Fields

These fields extend `DropdownField` and support a `multi-select` attribute that switches them to chip-based multi-value selection (same visual as `<multi-select-field>`).

| Attribute      | Type    | Description                                                                                                              |
| -------------- | ------- | ------------------------------------------------------------------------------------------------------------------------ |
| `multi-select` | boolean | Renders as a chip-based multi-select; `value` returns JSON array string; setter accepts JSON array, CSV string, or Array |

| Element                 | Default label | API endpoint                         | Extra attributes                                             |
| ----------------------- | ------------- | ------------------------------------ | ------------------------------------------------------------ |
| `<team-field>`          | Team          | `GET /api/v1/teams/options/`         | `unassign` — prepends "Unassign" option (single-select only) |
| `<business-unit-field>` | Business Unit | `GET /api/v1/bu/options/`            |                                                              |
| `<member-field>`        | Member        | `GET /api/v1/members/?page_size=200` | See full details below                                       |

```html
<!-- Single-select with allow-all for filters -->
<team-field name="team" allow-all show-label></team-field>

<!-- Multi-select mode -->
<team-field id="project-teams" multi-select required col="col-12" show-label></team-field>
```

```js
// Read multi-select value
JSON.parse(document.getElementById("project-teams").value); // → ["TEAM-1", "TEAM-2"]
document.getElementById("project-teams").values; // → [{ id, label, value }, …]
```

---

#### `<member-field>`

Options are fetched from `GET /api/v1/members/?page_size=200` on first connect. Each option renders as the member's **display name**, falling back to **email**, then **member code**.

| Attribute      | Type    | Description                                                                                                                                                                                                                 |
| -------------- | ------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `multi-select` | boolean | Switches to chip-based multi-select mode. `value` returns a JSON array string; the setter accepts a JSON array, CSV string, or `Array`.                                                                                     |
| `allow-all`    | boolean | **Single-select only** — prepends **All Members** (`value=""`) as the first option, selected by default. Ignored when `multi-select` is present.                                                                            |
| `show-label`   | boolean | Renders "Member" as the visible field label (hidden by default).                                                                                                                                                            |
| `max`          | number  | **Multi-select only** — maximum number of chips that can be selected. The search input hides once this limit is reached.                                                                                                    |
| `value`        | string  | Pre-selected member code (single-select), or a JSON array / CSV string of codes (multi-select). In multi-select mode chips appear immediately as code placeholders and are resolved to real names once options have loaded. |

**Reading the value:**

```js
// Single-select
field.value; // → "MBR-0001"

// Multi-select
JSON.parse(field.value); // → ["MBR-0001", "MBR-0002"]
field.values; // → [{ id, label, value }, …]
```

**Multi-select keyboard navigation:**

| Key       | Behaviour                                            |
| --------- | ---------------------------------------------------- |
| Type      | Filters the dropdown to matching member names        |
| ↓ / ↑     | Moves highlight through dropdown options             |
| Enter     | Adds the highlighted option as a chip                |
| Backspace | Removes the last chip when the search input is empty |
| Escape    | Closes the dropdown                                  |

**Loading state:** In single-select mode the `<select>` is disabled while options load. In multi-select mode the search input shows "Loading…" as a placeholder. Any pre-selected codes appear as chips immediately with the code as a temporary label; labels are upgraded to display names once options arrive.

**Error state:** If the API request fails, the field is disabled and shows "Could not load members. Refresh the page to retry." In multi-select mode the `.rp-multiselect` wrapper also receives the `is-invalid` class.

```html
<!-- Single-select (form / create context) -->
<member-field id="leave-member" required col="col-12" show-label></member-field>

<!-- Single-select with pre-selected value -->
<member-field id="leave-member" value="MBR-0001" show-label col="col-md-6"></member-field>

<!-- Single-select filter (all members option) -->
<member-field id="filter-member" name="member" allow-all show-label></member-field>

<!-- Multi-select (no cap on selections) -->
<member-field id="sprint-members" multi-select required col="col-12" show-label></member-field>

<!-- Multi-select with pre-selected values and a cap of 5 -->
<member-field
  id="sprint-members"
  multi-select
  required
  max="5"
  value='["MBR-0001","MBR-0002"]'
  col="col-12"
  show-label
></member-field>
```

```js
// Set value programmatically (multi-select)
document.getElementById("sprint-members").value = JSON.stringify(["MBR-0001", "MBR-0002"]);

// Read selected chips
const chips = document.getElementById("sprint-members").values;
// → [{ id: "MBR-0001", label: "Alice Smith", value: "MBR-0001" }, …]
```

---

### API-Fetching Multi-Select Fields

These fields extend `MultiSelectField` directly — they do not have a single-select mode. See `fields.md` for the full `MultiSelectField` attribute and API reference.

| Element                | Default label | API endpoint                  | Notes                                               |
| ---------------------- | ------------- | ----------------------------- | --------------------------------------------------- |
| `<skills-field>`       | Skills        | `GET /api/v1/skills/options/` |                                                     |
| `<project-tags-field>` | Tags          | `GET /api/v1/tags/`           | Value is JSON array of tag codes e.g. `["TAG-001"]` |

| Attribute    | Type    | Description                                                          |
| ------------ | ------- | -------------------------------------------------------------------- |
| `show-label` | boolean | Renders the field label as visible text                              |
| `max`        | number  | Maximum number of chips selectable (inherited from MultiSelectField) |

```html
<skills-field id="member-skills" required col="col-md-12" show-label></skills-field>
<project-tags-field id="project-tags" col="col-12" show-label></project-tags-field>
```

```js
JSON.parse(document.getElementById("member-skills").value); // → ["SKILL-001", "SKILL-002"]
```
