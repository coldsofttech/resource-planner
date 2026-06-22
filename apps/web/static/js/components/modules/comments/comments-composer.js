"use strict";

import { esc } from "../../utils.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* CommentsComposer  <comments-composer>
 *
 * Rich-text comment editor with formatting toolbar and @-mention autocomplete.
 * Applies rp-comment-composer directly to itself.
 *
 * Attributes:
 *   avatar-url    — current user's avatar URL
 *   display-name  — current user's display name
 *   seed          — email used for initials (matches nav-bar user-profile approach)
 *
 * Events dispatched:
 *   rp:comment:submit  — { comment, mentions } — bubbles to <comments-panel>
 */

// Same split logic as user-profile.js — produces "CC" from "cold.c@mail.com" etc.
function _initials(seed) {
  const parts = String(seed || "")
    .trim()
    .split(/[\s@._-]+/)
    .filter(Boolean);
  if (!parts.length) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

class CommentsComposer extends HTMLElement {
  static get observedAttributes() {
    return ["avatar-url", "display-name", "seed"];
  }

  connectedCallback() {
    this._mentionInfo = null;
    this._mentionDebounce = null;
    this._savedRange = null;
    this.className = "rp-comment-composer";
    this._render();
  }

  disconnectedCallback() {
    clearTimeout(this._mentionDebounce);
  }

  attributeChangedCallback(attr, oldVal, newVal) {
    if (!this._rendered || oldVal === newVal) return;
    this._updateAvatar();
  }

  _updateAvatar() {
    const av = this._avatarEl;
    if (!av) return;
    const url = this.getAttribute("avatar-url") || "";
    const seed = this.getAttribute("seed") || "";
    const name = this.getAttribute("display-name") || "";
    const fallbackText = seed ? _initials(seed) : name ? _initials(name) : "?";

    av.innerHTML = "";
    if (url) {
      const img = document.createElement("img");
      img.src = url;
      img.alt = name;
      img.style.cssText =
        "width:100%;height:100%;object-fit:cover;display:block;border-radius:inherit;";
      img.addEventListener("error", () => {
        av.innerHTML = "";
        av.textContent = fallbackText;
      });
      av.appendChild(img);
    } else {
      av.textContent = fallbackText;
    }
  }

  _render() {
    // Avatar — raw div, same approach as user-profile.js in the nav bar
    const avatar = document.createElement("div");
    avatar.className = "rp-avatar d-none d-lg-inline";
    this._avatarEl = avatar;
    this._updateAvatar();

    // Body wrapper
    const body = document.createElement("div");
    body.className = "rp-comment-composer-body";

    // Editor wrapper: position:relative so mention dropdown can float below it
    const editorWrap = document.createElement("div");
    editorWrap.style.cssText = "position:relative";

    // Editor
    const editor = document.createElement("div");
    editor.className = "rp-input rp-comment-editor";
    editor.contentEditable = "true";
    editor.setAttribute("role", "textbox");
    editor.setAttribute("aria-multiline", "true");
    editor.setAttribute("aria-label", "Add a comment");
    editor.setAttribute("data-placeholder", "Add a comment… use @ to mention someone");
    editor.style.cssText = "min-height:120px;padding:8px 10px;line-height:1.5;overflow:auto";

    // Mention dropdown (absolutely positioned below the editor)
    const dropdown = document.createElement("div");
    dropdown.className = "rp-comment-mention-dropdown";
    dropdown.setAttribute("role", "listbox");
    dropdown.hidden = true;

    editorWrap.appendChild(editor);
    editorWrap.appendChild(dropdown);

    // Toolbar + send
    const actions = document.createElement("div");
    actions.className = "rp-comment-composer-actions";
    actions.innerHTML = `
      <div class="rp-comment-composer-tools">
        <button class="rp-btn rp-btn-muted rp-btn-sm rp-btn-icon" data-cmd="bold"      title="Bold"             type="button"><i class="bi bi-type-bold"></i></button>
        <button class="rp-btn rp-btn-muted rp-btn-sm rp-btn-icon" data-cmd="italic"    title="Italic"           type="button"><i class="bi bi-type-italic"></i></button>
        <button class="rp-btn rp-btn-muted rp-btn-sm rp-btn-icon" data-cmd="underline" title="Underline"        type="button"><i class="bi bi-type-underline"></i></button>
        <button class="rp-btn rp-btn-muted rp-btn-sm rp-btn-icon" data-cmd="link"      title="Insert Link"      type="button"><i class="bi bi-link-45deg"></i></button>
        <button class="rp-btn rp-btn-muted rp-btn-sm rp-btn-icon" data-cmd="bullets"   title="Bullet List"      type="button"><i class="bi bi-list-ul"></i></button>
        <button class="rp-btn rp-btn-muted rp-btn-sm rp-btn-icon" data-cmd="numbers"   title="Numbered List"    type="button"><i class="bi bi-list-ol"></i></button>
        <button class="rp-btn rp-btn-muted rp-btn-sm rp-btn-icon" data-cmd="unformat"  title="Clear Formatting" type="button"><i class="bi bi-eraser"></i></button>
        <button class="rp-btn rp-btn-muted rp-btn-sm rp-btn-icon" data-cmd="mention"   title="Mention"          type="button"><i class="bi bi-at"></i></button>
      </div>
      <div class="d-flex gap-2 align-items-center">
        <span class="rp-subtle d-none d-lg-inline" style="font-size:11px"><span class="rp-mono">⌘↵</span> to send</span>
        <button class="rp-btn rp-btn-primary rp-btn-sm" type="button" data-submit>
          <i class="bi bi-send"></i> <span class="d-none d-lg-inline">Comment</span>
        </button>
      </div>
    `;

    body.appendChild(editorWrap);
    body.appendChild(actions);

    this.innerHTML = "";
    this.appendChild(avatar);
    this.appendChild(body);

    this._editor = editor;
    this._dropdown = dropdown;
    this._rendered = true;

    this._bindEditor();
    this._bindToolbar();
  }

  _bindEditor() {
    const ed = this._editor;

    ed.addEventListener("keydown", (e) => {
      // ⌘↵ or Ctrl+↵ submits
      if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        this._submit();
        return;
      }
      const dd = this._dropdown;
      if (dd && !dd.hidden) {
        if (e.key === "Escape") {
          e.preventDefault();
          dd.hidden = true;
          return;
        }
        if (e.key === "ArrowDown") {
          e.preventDefault();
          this._moveFocus(1);
          return;
        }
        if (e.key === "ArrowUp") {
          e.preventDefault();
          this._moveFocus(-1);
          return;
        }
        if (e.key === "Enter") {
          e.preventDefault();
          dd.querySelector("[aria-selected='true']")?.click();
          return;
        }
      }
    });

    ed.addEventListener("input", () => {
      const info = this._getCursorMention();
      if (info) {
        this._mentionInfo = info;
        clearTimeout(this._mentionDebounce);
        this._mentionDebounce = setTimeout(() => this._fetchMentions(info.query), 200);
      } else {
        this._mentionInfo = null;
        this._dropdown.hidden = true;
      }
    });
  }

  _bindToolbar() {
    this.querySelectorAll("[data-cmd]").forEach((btn) => {
      btn.addEventListener("mousedown", (e) => {
        e.preventDefault(); // keep editor focus
        this._execCmd(btn.dataset.cmd);
      });
    });

    this.querySelector("[data-submit]")?.addEventListener("click", () => this._submit());
  }

  _execCmd(cmd) {
    this._editor.focus();
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
        if (document.queryCommandState("insertUnorderedList"))
          document.execCommand("insertUnorderedList");
        if (document.queryCommandState("insertOrderedList"))
          document.execCommand("insertOrderedList");
        break;
      case "mention":
        document.execCommand("insertText", false, "@");
        {
          const info = this._getCursorMention();
          if (info) {
            this._mentionInfo = info;
            this._fetchMentions(info.query);
          }
        }
        break;
      case "link": {
        const saved = this._saveRange();
        this._showLinkOverlay(this._editor, saved);
        break;
      }
    }
  }

  _saveRange() {
    const sel = window.getSelection();
    return sel && sel.rangeCount ? sel.getRangeAt(0).cloneRange() : null;
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
      const ref = savedRange || null;
      if (ref) {
        const rect = ref.getBoundingClientRect();
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

    // Invisible full-screen backdrop behind the overlay — catches outside clicks
    // without any timing race. Overlay is z:9999, backdrop is z:9998, page is below.
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

    // Outside click: any pointer landing on the backdrop (not the overlay) closes it
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

  _getCursorMention() {
    const sel = window.getSelection();
    if (!sel || !sel.rangeCount) return null;
    const range = sel.getRangeAt(0);
    if (!range.collapsed) return null;
    const node = range.startContainer;
    if (node.nodeType !== Node.TEXT_NODE || !this._editor.contains(node)) return null;
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

  async _fetchMentions(query) {
    const { href } = API_URLS.users.search(query);
    try {
      const envelope = await apiFetch(href);
      this._showDropdown(envelope?.data?.results || []);
    } catch {
      this._dropdown.hidden = true;
    }
  }

  _showDropdown(users) {
    const dd = this._dropdown;
    if (!users.length) {
      dd.hidden = true;
      return;
    }
    dd.innerHTML = users
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
    dd.hidden = false;

    dd.querySelectorAll("[data-user-code]").forEach((btn) => {
      btn.addEventListener("click", () => {
        this._insertMention(btn.dataset.userCode, btn.dataset.userName);
      });
    });
  }

  _moveFocus(dir) {
    const items = [...this._dropdown.querySelectorAll("[role='option']")];
    const cur = items.findIndex((el) => el.getAttribute("aria-selected") === "true");
    const next = Math.max(0, Math.min(items.length - 1, cur + dir));
    items.forEach((el, i) => el.setAttribute("aria-selected", String(i === next)));
  }

  _insertMention(code, name) {
    this._dropdown.hidden = true;
    const info = this._mentionInfo;
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
    this._mentionInfo = null;
  }

  _submit() {
    const comment = this._editor.innerHTML.trim();
    const mentions = [...this._editor.querySelectorAll("[data-mention-code]")].map(
      (s) => s.dataset.mentionCode,
    );
    this.dispatchEvent(
      new CustomEvent("rp:comment:submit", { bubbles: true, detail: { comment, mentions } }),
    );
  }

  clear() {
    if (this._editor) this._editor.innerHTML = "";
  }

  setBusy(busy) {
    const btn = this.querySelector("[data-submit]");
    if (!btn) return;
    btn.disabled = busy;
    btn.innerHTML = busy
      ? `<i class="bi bi-hourglass-split"></i> Posting…`
      : `<i class="bi bi-send"></i> Comment`;
  }
}

if (!customElements.get("comments-composer")) {
  customElements.define("comments-composer", CommentsComposer);
}
