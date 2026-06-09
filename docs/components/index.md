# UI & JS Components

All components are Web Components (Custom Elements v1) loaded from `apps/web/static/js/components/` via `components/index.js` and compiled into `dist/components.min.js`.

---

## Component Reference

| Doc                              | Components                                                                                                                                                                                                                                                                   |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [banners.md](banners.md)         | `flash-banner`, `fy-flash-banner`, `cookie-banner`                                                                                                                                                                                                                           |
| [breadcrumbs.md](breadcrumbs.md) | `page-breadcrumbs`                                                                                                                                                                                                                                                           |
| [buttons.md](buttons.md)         | `primary-button`, `secondary-button`, `muted-button`, `engine-button`, `delete-button`, `activate-button`, `deactivate-button`, `dropdown-button`                                                                                                                            |
| [choices.md](choices.md)         | `checkbox-field`, `radio-field`, `checkbox-group-field`, `radio-group-field`, `option-field`                                                                                                                                                                                 |
| [drawers.md](drawers.md)         | `drawer-modal`, `drawer-header`, `drawer-footer`, `drawer-tabs`, `drawer-tab`, `drawer-panel`                                                                                                                                                                                |
| [dropdowns.md](dropdowns.md)     | `dropdown-field`, `is-active-field`                                                                                                                                                                                                                                          |
| [fields.md](fields.md)           | `text-field`, `email-field`, `password-field`, `confirm-password-field`, `secret-field`, `number-field`, `decimal-field`, `website-field`, `otp-field`, `hint-field`, `view-field`, `search-field`, `file-import-field`, `link-field`, `first-name-field`, `last-name-field` |
| [filters.md](filters.md)         | `filter-panel`, `filter-group`, `filter-option`, `active-filter`                                                                                                                                                                                                             |
| [icons.md](icons.md)             | `icon-field`, `icon-picker-field`                                                                                                                                                                                                                                            |
| [menus.md](menus.md)             | `menu-bar`, `menu-items`, `menu-item`, `menu-group`, `menu-section`                                                                                                                                                                                                          |
| [modals.md](modals.md)           | `status-modal`, `delete-modal`, `activate-modal`, `deactivate-modal`                                                                                                                                                                                                         |
| [modules.md](modules.md)         | `list-view`, `sprint-pill`, `is-active-field`, `first-name-field`, `last-name-field`                                                                                                                                                                                         |
| [panels.md](panels.md)           | `section-panel`, `panel-title`, `panel-body`, `card-panel`, `panel-header`, `panel-footer`                                                                                                                                                                                   |
| [tables.md](tables.md)           | `data-table`, `table-columns`, `table-column`, `table-actions`, `table-action`                                                                                                                                                                                               |
| [tabs.md](tabs.md)               | `tab-panel`, `tab-items`, `tab-item`, `tab-header`, `tab-content`                                                                                                                                                                                                            |
| [toggles.md](toggles.md)         | `toggle-field`, `toggle-group-field`, `theme-toggle`                                                                                                                                                                                                                         |
| [utilities.md](utilities.md)     | `toast()`, `statusModal`                                                                                                                                                                                                                                                     |
| [wizards.md](wizards.md)         | `step-wizard`, `wizard-steps`, `wizard-step`, `wizard-step-header`, `wizard-step-body`, `wizard-step-footer`                                                                                                                                                                 |

---

## Pre-mounted elements (in `templates/base.html`)

The following components are mounted once in the base template. Do not add them to child templates:

| Element                                   | Description                                                   |
| ----------------------------------------- | ------------------------------------------------------------- |
| `<page-breadcrumbs id="app-breadcrumbs">` | Call `setCrumbs()` from page JS to set entity-specific trails |
| `<menu-bar id="app-menu-bar">`            | Populate `<menu-items>` in the template                       |
| `<sprint-pill id="active-sprint">`        | Set `name`, `end`, and `status` attributes from layout JS     |
| `<rp-theme-toggle>`                       | Dark/light mode toggle                                        |
| `<flash-banner id="page-flash">`          | Per-page inline flash banner                                  |
| `<fy-flash-banner id="fy-banner">`        | System-wide FY expiry top-strip banner                        |
