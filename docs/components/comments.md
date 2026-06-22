# Comments Components

Custom elements defined in `apps/web/static/js/components/modules/comments/`.

| Component           | Purpose                                                                 |
| ------------------- | ----------------------------------------------------------------------- |
| `comments-panel`    | Top-level orchestrator — the only element you place in a template       |
| `comments-composer` | Rich-text input with formatting toolbar and @-mention autocomplete      |
| `comment-items`     | Semantic container for the comment list; manages the empty state        |
| `comment-item`      | Single comment card with inline edit, pin, and delete actions           |
| `comments-pager`    | Pagination control; hidden automatically when all comments fit one page |

All sub-components (`comments-composer`, `comment-items`, `comment-item`, `comments-pager`) are created and managed internally by `<comments-panel>`. You do not need to add them to your HTML.

---

## `<comments-panel>`

Top-level orchestrator for the comments UI. Drop this element into any detail template, then set `comments-url` once the resource code is known. The panel handles fetching, rendering, paginating, pinning, editing, and deleting comments.

| Attribute      | Type   | Description                                                                                                                                                  |
| -------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `comments-url` | string | Base API URL for this resource's comments (e.g. `/api/v1/projects/PROJ-1/comments/`). Setting or changing this attribute triggers a full reload from page 1. |

**Behaviour:**

- Fetches the current user from `GET /api/v1/users/me/` on connect and passes the avatar and display name to the composer.
- Loads 25 comments per page. Pinned comments are always shown first on page 1, separated from general comments by a divider. Pages 2+ show only general comments.
- Timestamps are relative: `just now`, `Xm ago`, `Xh ago`, then a short date for older entries.
- Reconnecting the element (e.g. after a `<section-panel>` moves it) aborts any in-flight listeners and re-initialises cleanly.

**Usage:**

```html
<!-- Place in template -->
<comments-panel id="rp-project-comments-panel"></comments-panel>
```

```js
// Wire after project data is available
const panel = document.getElementById("rp-project-comments-panel");
const { href } = API_URLS.projectComments.list(projectCode);
panel.setAttribute("comments-url", href);
```

---

## `<comments-composer>`

Rich-text comment input. Auto-created by `<comments-panel>` — do not add manually.

**Toolbar buttons:**

| Button           | Action                                                 |
| ---------------- | ------------------------------------------------------ |
| **B**            | Bold                                                   |
| _I_              | Italic                                                 |
| <u>U</u>         | Underline                                              |
| 🔗               | Insert / wrap selection in link (floating URL overlay) |
| List (unordered) | Bullet list                                            |
| List (ordered)   | Numbered list                                          |
| Eraser           | Clear all formatting                                   |
| @                | Trigger @-mention autocomplete                         |

**@-mention autocomplete:**

Type `@` anywhere in the editor to open a user-search dropdown. The search is debounced (200 ms) and hits `GET /api/v1/users/search/?q=<query>`. Navigate with ↑/↓, select with Enter, dismiss with Escape.

**Keyboard shortcut:** `⌘↵` / `Ctrl+↵` submits the comment without clicking the button.

**Public API (called by `<comments-panel>` internally):**

| Method                   | Description                                                                  |
| ------------------------ | ---------------------------------------------------------------------------- |
| `composer.clear()`       | Clears the editor content                                                    |
| `composer.setBusy(busy)` | Disables the submit button and shows a posting spinner when `busy` is `true` |

**Events dispatched (bubble to `<comments-panel>`):**

| Event               | Detail                  | Description                                                                                                                                                                 |
| ------------------- | ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `rp:comment:submit` | `{ comment, mentions }` | User clicked Comment or pressed ⌘↵. `comment` is the raw HTML string from the editor; `mentions` is an array of user codes extracted from `<span data-mention-code>` chips. |

---

## `<comment-item>`

Single comment card. Auto-created by `<comments-panel>` for each fetched comment — do not add manually.

**Attributes (set by the panel):**

| Attribute    | Type    | Description                                                                        |
| ------------ | ------- | ---------------------------------------------------------------------------------- |
| `code`       | string  | Comment code (e.g. `PROJCMT-42`)                                                   |
| `pinned`     | boolean | Present when the comment is pinned; adds the `.is-pinned` visual style             |
| `edited`     | boolean | Present when the comment has been edited; shows an "edited" badge                  |
| `is-own`     | boolean | Present when the logged-in user authored this comment; shows Edit / Delete buttons |
| `author`     | string  | Display name of the author                                                         |
| `avatar-url` | string  | Author's avatar URL; falls back to initials if absent                              |
| `time`       | string  | Human-readable relative timestamp string set by the panel                          |

**Actions visible per comment:**

| Action | Visible to   | Behaviour                                                         |
| ------ | ------------ | ----------------------------------------------------------------- |
| Pin    | All users    | Pins the comment; it moves to the top of page 1                   |
| Unpin  | All users    | Unpins the comment; restores chronological order                  |
| Edit   | Own comments | Opens an inline rich-text editor pre-filled with the current body |
| Delete | Own comments | Opens the panel's `<delete-modal>` for confirmation               |

Inline editing uses the same formatting toolbar and @-mention autocomplete as the composer. Cancel or Save closes the editor without reloading the page (Save triggers an API call first).

**Events dispatched (bubble to `<comments-panel>`):**

| Event               | Detail                        | Description                          |
| ------------------- | ----------------------------- | ------------------------------------ |
| `rp:comment:pin`    | `{ code }`                    | User clicked the pin button          |
| `rp:comment:unpin`  | `{ code }`                    | User clicked the unpin button        |
| `rp:comment:delete` | `{ code }`                    | User clicked Delete (before confirm) |
| `rp:comment:save`   | `{ code, comment, mentions }` | User clicked Save in inline edit     |

---

## `<comment-items>`

Semantic container for `<comment-item>` elements. Auto-created and managed by `<comments-panel>`.

**Public API (used internally by the panel):**

| Method             | Description                                |
| ------------------ | ------------------------------------------ |
| `list.clear()`     | Removes all child elements                 |
| `list.showEmpty()` | Renders "No comments yet" placeholder text |

---

## `<comments-pager>`

Pagination control for the comment list. Auto-created by `<comments-panel>`. Hidden automatically when `total-pages` is 1 or less.

| Attribute      | Type    | Description           |
| -------------- | ------- | --------------------- |
| `current-page` | integer | Active page number    |
| `total-pages`  | integer | Total number of pages |

Renders a window of up to 5 pages centred on the current page, with first/last always visible and ellipsis (`…`) for gaps.

**Events dispatched (bubble to `<comments-panel>`):**

| Event             | Detail     | Description                |
| ----------------- | ---------- | -------------------------- |
| `rp:pager:change` | `{ page }` | User clicked a page button |
