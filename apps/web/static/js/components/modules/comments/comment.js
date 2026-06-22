"use strict";

import { esc } from "../../utils.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* Comment  <comment-item>
 *
 * Single comment card. Renders once from attributes + innerHTML body.
 * Is-editing state is managed internally (CSS-driven via .is-editing class).
 *
 * Attributes:
 *   code        — ProjectComment code
 *   pinned      — boolean; present when pinned
 *   author      — display name of the author
 *   avatar-url  — author avatar URL
 *   time        — human-readable relative time string
 *   edited      — boolean; present when the comment has been edited
 *   is-own      — boolean; present when current user owns this comment
 *
 * Children set before connection:
 *   innerHTML   — rich-text HTML body of the comment
 *
 * Events dispatched (all bubble):
 *   rp:comment:pin    — { code }
 *   rp:comment:unpin  — { code }
 *   rp:comment:delete — { code }
 *   rp:comment:save   — { code, comment, mentions }
 */
class Comment extends HTMLElement {
  connectedCallback() {
    // Save body HTML set by parent before insertion
    this._bodyHtml = this.innerHTML;
    this._editMentionInfo = null;
    this._editMentionDebounce = null;
    this._render();
  }

  disconnectedCallback() {
    clearTimeout(this._editMentionDebounce);
  }

  _render() {
    const code = this.getAttribute("code") || "";
    const isPinned = this.hasAttribute("pinned");
    const isOwn = this.hasAttribute("is-own");
    const author = this.getAttribute("author") || "Unknown";
    const avatarUrl = this.getAttribute("avatar-url") || "";
    const time = this.getAttribute("time") || "";
    const isEdited = this.hasAttribute("edited");
    // Use seed (email-splitting initials) when author looks like an email
    const isEmail = author.includes("@");

    this.className = `rp-comment${isPinned ? " is-pinned" : ""}`;

    const pinBtn = isPinned
      ? `<button class="rp-iconbtn" data-action="unpin" title="Unpin"><i class="bi bi-pin-angle-fill" style="color:var(--rp-warning-soft-text)"></i></button>`
      : `<button class="rp-iconbtn" data-action="pin" title="Pin"><i class="bi bi-pin-angle"></i></button>`;
    const editBtn = isOwn
      ? `<button class="rp-iconbtn" data-action="edit" title="Edit"><i class="bi bi-pencil"></i></button>`
      : "";
    const deleteBtn = isOwn
      ? `<button class="rp-iconbtn" data-action="delete" title="Delete" style="color:var(--rp-danger-soft-text)"><i class="bi bi-trash3"></i></button>`
      : "";
    const editedBadge = isEdited
      ? `<span class="rp-badge rp-badge-soft rp-badge-neutral ms-1"><i class="bi bi-pencil-fill"></i> edited</span>`
      : "";

    // Note: body is server-stored HTML from our contentEditable — rendered as-is.
    // All other values are user-attributed strings and go through esc().
    this.innerHTML = `
      <div class="rp-comment-head">
        <user-avatar
          ${avatarUrl ? `avatar-url="${esc(avatarUrl)}"` : ""}
          name="${esc(author)}"
          ${isEmail ? `seed="${esc(author)}"` : ""}
          size="sm"
          style="width:24px;height:24px;font-size:11px;flex-shrink:0"
          class="d-none d-lg-inline"
        ></user-avatar>
        <span class="rp-comment-author">${esc(author)}</span>
        <span class="rp-comment-time">· ${esc(time)}</span>
        ${editedBadge}
        <div class="rp-comment-actions">${pinBtn}${editBtn}${deleteBtn}</div>
      </div>
      <div class="rp-comment-body">${this._bodyHtml || ""}</div>
      <div class="rp-comment-edit">
        <div style="position:relative">
          <div
            class="rp-input rp-comment-editor"
            contenteditable="true"
            role="textbox"
            aria-multiline="true"
            style="min-height:100px;padding:8px 10px;line-height:1.5"
          >${this._bodyHtml || ""}</div>
          <div class="rp-comment-mention-dropdown" role="listbox" hidden></div>
        </div>
        <div class="rp-comment-composer-tools mt-1">
          <button class="rp-btn rp-btn-muted rp-btn-sm rp-btn-icon" data-edit-cmd="bold"      title="Bold"             type="button"><i class="bi bi-type-bold"></i></button>
          <button class="rp-btn rp-btn-muted rp-btn-sm rp-btn-icon" data-edit-cmd="italic"    title="Italic"           type="button"><i class="bi bi-type-italic"></i></button>
          <button class="rp-btn rp-btn-muted rp-btn-sm rp-btn-icon" data-edit-cmd="underline" title="Underline"        type="button"><i class="bi bi-type-underline"></i></button>
          <button class="rp-btn rp-btn-muted rp-btn-sm rp-btn-icon" data-edit-cmd="link"      title="Insert Link"      type="button"><i class="bi bi-link-45deg"></i></button>
          <button class="rp-btn rp-btn-muted rp-btn-sm rp-btn-icon" data-edit-cmd="mention"   title="Mention"          type="button"><i class="bi bi-at"></i></button>
          <button class="rp-btn rp-btn-muted rp-btn-sm rp-btn-icon" data-edit-cmd="bullets"   title="Bullet List"      type="button"><i class="bi bi-list-ul"></i></button>
          <button class="rp-btn rp-btn-muted rp-btn-sm rp-btn-icon" data-edit-cmd="numbers"   title="Numbered List"    type="button"><i class="bi bi-list-ol"></i></button>
          <button class="rp-btn rp-btn-muted rp-btn-sm rp-btn-icon" data-edit-cmd="unformat"  title="Clear Formatting" type="button"><i class="bi bi-eraser"></i></button>
        </div>
        <div class="d-flex justify-content-end gap-2 mt-2">
          <button class="rp-btn rp-btn-muted rp-btn-sm" type="button" data-action="cancel-edit">Cancel</button>
          <button class="rp-btn rp-btn-primary rp-btn-sm" type="button" data-action="save-edit">
            <i class="bi bi-check2"></i> Save
          </button>
        </div>
      </div>
    `;

    // All hyperlinks in the rendered body open in a new tab
    this.querySelectorAll(".rp-comment-body a[href]").forEach((a) => {
      a.target = "_blank";
      a.rel = "noopener noreferrer";
    });

    this._bindActions(code);
  }

  _bindActions(code) {
    const editor = this.querySelector(".rp-comment-edit .rp-comment-editor");
    const dropdown = this.querySelector(".rp-comment-edit .rp-comment-mention-dropdown");

    // Toolbar: mousedown + preventDefault keeps editor focus while formatting
    this.addEventListener("mousedown", (e) => {
      const tb = e.target.closest("[data-edit-cmd]");
      if (!tb) return;
      e.preventDefault();
      if (!editor) return;
      editor.focus();
      const cmd = tb.dataset.editCmd;
      switch (cmd) {
        case "bold":
          document.execCommand("bold");
          break;
        case "italic":
          document.execCommand("italic");
          break;
        case "underline":
          document.execCommand("underline");
          break;
        case "bullets":
          document.execCommand("insertUnorderedList");
          break;
        case "numbers":
          document.execCommand("insertOrderedList");
          break;
        case "unformat":
          document.execCommand("removeFormat");
          document.execCommand("unlink");
          // Also clear active list formatting
          if (document.queryCommandState("insertUnorderedList"))
            document.execCommand("insertUnorderedList");
          if (document.queryCommandState("insertOrderedList"))
            document.execCommand("insertOrderedList");
          break;
        case "mention":
          document.execCommand("insertText", false, "@");
          {
            const info = this._editGetCursorMention(editor);
            if (info) {
              this._editMentionInfo = info;
              this._editFetchMentions(info.query, editor, dropdown);
            }
          }
          break;
        case "link": {
          const sel = window.getSelection();
          const saved = sel?.rangeCount ? sel.getRangeAt(0).cloneRange() : null;
          this._showLinkOverlay(editor, saved);
          break;
        }
      }
    });

    // Input listener for @-mention autocomplete in edit mode
    if (editor && dropdown) {
      editor.addEventListener("input", () => {
        const info = this._editGetCursorMention(editor);
        if (info) {
          this._editMentionInfo = info;
          clearTimeout(this._editMentionDebounce);
          this._editMentionDebounce = setTimeout(
            () => this._editFetchMentions(info.query, editor, dropdown),
            200,
          );
        } else {
          this._editMentionInfo = null;
          dropdown.hidden = true;
        }
      });

      editor.addEventListener("keydown", (e) => {
        if (!dropdown || dropdown.hidden) return;
        if (e.key === "Escape") {
          e.preventDefault();
          dropdown.hidden = true;
          return;
        }
        if (e.key === "ArrowDown") {
          e.preventDefault();
          this._editMoveFocus(dropdown, 1);
          return;
        }
        if (e.key === "ArrowUp") {
          e.preventDefault();
          this._editMoveFocus(dropdown, -1);
          return;
        }
        if (e.key === "Enter") {
          e.preventDefault();
          dropdown.querySelector("[aria-selected='true']")?.click();
          return;
        }
      });
    }

    this.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-action]");
      if (!btn) return;
      switch (btn.dataset.action) {
        case "pin":
          this._dispatch("rp:comment:pin", { code });
          break;
        case "unpin":
          this._dispatch("rp:comment:unpin", { code });
          break;
        case "edit":
          this._openEdit();
          break;
        case "delete":
          this._dispatch("rp:comment:delete", { code });
          break;
        case "cancel-edit":
          this._closeEdit();
          break;
        case "save-edit":
          this._saveEdit(code);
          break;
      }
    });
  }

  _showLinkOverlay(editor, savedRange) {
    // Remove any stale overlay + backdrop from a previous open
    document.querySelector(".rp-link-overlay")?.remove();
    document.querySelector(".rp-link-backdrop")?.remove();

    const overlay = document.createElement("div");
    overlay.className = "rp-link-overlay";
    overlay.innerHTML = `
      <input class="rp-input" type="url" placeholder="https://" autocomplete="off">
      <button class="rp-btn rp-btn-primary rp-btn-icon rp-btn-sm" type="button" data-lp-ok title="Apply link"><i class="bi bi-check2"></i></button>
      <button class="rp-btn rp-btn-muted rp-btn-icon rp-btn-sm" type="button" data-lp-cancel title="Cancel"><i class="bi bi-x"></i></button>
    `;

    let left = 0,
      top = 0;
    try {
      if (savedRange) {
        const rect = savedRange.getBoundingClientRect();
        left = rect.left;
        top = rect.bottom + 6;
      } else {
        const rect = editor.getBoundingClientRect();
        left = rect.left;
        top = rect.bottom + 6;
      }
    } catch {
      /* ignore */
    }

    overlay.style.cssText = `position:fixed;left:${Math.max(8, left)}px;top:${top}px;z-index:9999`;

    // Invisible full-screen backdrop — catches outside clicks without timing races
    const backdrop = document.createElement("div");
    backdrop.className = "rp-link-backdrop";
    backdrop.style.cssText = "position:fixed;inset:0;z-index:9998";

    document.body.appendChild(backdrop);
    document.body.appendChild(overlay);

    const input = overlay.querySelector("input");
    input.focus();

    const closeOverlay = () => {
      overlay.remove();
      backdrop.remove();
    };

    backdrop.addEventListener("mousedown", () => {
      closeOverlay();
      editor.focus();
    });

    const apply = () => {
      const url = input.value.trim();
      if (url) {
        if (savedRange) {
          const sel = window.getSelection();
          sel.removeAllRanges();
          sel.addRange(savedRange);
        }
        editor.focus();
        document.execCommand("createLink", false, url);
      }
      closeOverlay();
      editor.focus();
    };

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        apply();
      }
      if (e.key === "Escape") {
        closeOverlay();
        editor.focus();
      }
    });
    overlay.querySelector("[data-lp-ok]").addEventListener("click", apply);
    overlay.querySelector("[data-lp-cancel]").addEventListener("click", () => {
      closeOverlay();
      editor.focus();
    });
  }

  _editGetCursorMention(editor) {
    const sel = window.getSelection();
    if (!sel || !sel.rangeCount) return null;
    const range = sel.getRangeAt(0);
    if (!range.collapsed) return null;
    const node = range.startContainer;
    if (node.nodeType !== Node.TEXT_NODE || !editor.contains(node)) return null;
    const text = node.textContent.slice(0, range.startOffset);
    const match = text.match(/@(\w*)$/);
    if (!match) return null;
    return {
      query: match[1],
      node,
      startOffset: range.startOffset - match[0].length,
      endOffset: range.startOffset,
    };
  }

  async _editFetchMentions(query, editor, dropdown) {
    const { href } = API_URLS.users.search(query);
    try {
      const envelope = await apiFetch(href);
      this._editShowDropdown(envelope?.data?.results || [], editor, dropdown);
    } catch {
      dropdown.hidden = true;
    }
  }

  _editShowDropdown(users, editor, dropdown) {
    if (!users.length) {
      dropdown.hidden = true;
      return;
    }
    dropdown.innerHTML = users
      .map((u, i) => {
        const name = esc(u.display_name || u.email || "");
        const email =
          u.display_name && u.email
            ? `<span class="rp-comment-mention-email text-muted rp-fs-12">${esc(u.email)}</span>`
            : "";
        return `<button
        class="rp-comment-mention-item"
        role="option"
        aria-selected="${i === 0}"
        data-user-code="${esc(u.code || "")}"
        data-user-name="${esc(u.display_name || u.email || "")}"
        type="button"
      ><span class="rp-comment-mention-name">${name}</span>${email}</button>`;
      })
      .join("");
    dropdown.hidden = false;

    dropdown.querySelectorAll("[data-user-code]").forEach((btn) => {
      btn.addEventListener("click", () => {
        this._editInsertMention(btn.dataset.userCode, btn.dataset.userName, dropdown);
      });
    });
  }

  _editMoveFocus(dropdown, dir) {
    const items = [...dropdown.querySelectorAll("[role='option']")];
    const cur = items.findIndex((el) => el.getAttribute("aria-selected") === "true");
    const next = Math.max(0, Math.min(items.length - 1, cur + dir));
    items.forEach((el, i) => el.setAttribute("aria-selected", String(i === next)));
  }

  _editInsertMention(code, name, dropdown) {
    dropdown.hidden = true;
    const info = this._editMentionInfo;
    if (!info) return;

    const range = document.createRange();
    range.setStart(info.node, info.startOffset);
    range.setEnd(info.node, info.endOffset);
    range.deleteContents();

    const span = document.createElement("span");
    span.className = "rp-mention";
    span.contentEditable = "false";
    span.dataset.mentionCode = code;
    span.textContent = `@${name}`;
    range.insertNode(span);

    const after = document.createRange();
    after.setStartAfter(span);
    after.collapse(true);
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(after);
    document.execCommand("insertText", false, " ");
    this._editMentionInfo = null;
  }

  _dispatch(type, detail) {
    this.dispatchEvent(new CustomEvent(type, { bubbles: true, detail }));
  }

  _openEdit() {
    this.classList.add("is-editing");
    this.querySelector(".rp-comment-edit .rp-comment-editor")?.focus();
  }

  _closeEdit() {
    this.classList.remove("is-editing");
  }

  _saveEdit(code) {
    const editor = this.querySelector(".rp-comment-edit .rp-comment-editor");
    const comment = editor ? editor.innerHTML.trim() : "";
    const mentions = editor
      ? [...editor.querySelectorAll("[data-mention-code]")].map((s) => s.dataset.mentionCode)
      : [];
    this._dispatch("rp:comment:save", { code, comment, mentions });
  }
}

if (!customElements.get("comment-item")) {
  customElements.define("comment-item", Comment);
}
