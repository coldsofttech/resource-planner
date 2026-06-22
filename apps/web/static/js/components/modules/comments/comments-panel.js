"use strict";

import { esc } from "../../utils.js";
import { apiFetch } from "../../../modules/utils/utils.js";
import { toast } from "../../../modules/utils/toast.js";

/* CommentsPanel  <comments-panel>
 *
 * Top-level orchestrator for the comments UI.
 * Manages fetching, rendering, pinning, editing, and deleting comments.
 *
 * Attributes:
 *   comments-url  — base API URL for this resource's comments
 *                   e.g. /api/v1/projects/PROJ-001/comments/
 *
 * Composed of:
 *   <comments-composer>  — rich-text input (created on connectedCallback)
 *   <comments-list>      — wraps <comment> elements
 *   <comments-pager>     — page navigation
 *   <delete-modal>       — confirmation for delete
 */
class CommentsPanel extends HTMLElement {
  static get observedAttributes() {
    return ["comments-url"];
  }

  connectedCallback() {
    // Abort stale listeners from a previous connection (section-panel moves children).
    this._ctrl?.abort();
    this._ctrl = new AbortController();

    // Epoch guards against multiple concurrent _init() chains (section-panel
    // reconnects this element several times; each fires an async _init that
    // would otherwise all reach _bindEvents() and register duplicate listeners).
    this._epoch = (this._epoch || 0) + 1;
    const epoch = this._epoch;

    this._currentPage = 1;
    this._currentUser = null;
    this._pinnedComments = [];
    this._pendingDeleteCode = null;
    this._build();
    this._init(epoch);
  }

  disconnectedCallback() {
    this._ctrl?.abort();
  }

  attributeChangedCallback(attr, oldVal, newVal) {
    // newVal (not oldVal) because oldVal is null on the first setAttribute call.
    if (attr === "comments-url" && newVal && oldVal !== newVal) {
      this._currentPage = 1;
      this._pinnedComments = [];
      this._load(1);
    }
  }

  _build() {
    this.className = "rp-comments-panel";

    const composer = document.createElement("comments-composer");
    composer.id = "rp-comments-composer";

    const list = document.createElement("comment-items");
    list.id = "rp-comments-list";

    const pager = document.createElement("comments-pager");
    pager.id = "rp-comments-pager";
    pager.hidden = true;

    const deleteModal = document.createElement("delete-modal");
    deleteModal.id = "rp-comments-delete-modal";
    deleteModal.setAttribute("title", "Delete comment?");
    deleteModal.setAttribute("body", "This will permanently remove the comment.");
    deleteModal.setAttribute("confirm-label", "Delete");

    this.innerHTML = "";
    this.appendChild(composer);
    this.appendChild(list);
    this.appendChild(pager);
    this.appendChild(deleteModal);

    this._composer = composer;
    this._list = list;
    this._pager = pager;
    this._deleteModal = deleteModal;
  }

  async _init(epoch) {
    await this._fetchCurrentUser();
    // Bail if a later connectedCallback has superseded this init chain.
    if (this._epoch !== epoch) return;
    this._bindEvents();
    this._load(1);
  }

  async _fetchCurrentUser() {
    try {
      const envelope = await apiFetch("/api/v1/users/me/");
      // BaseViewSet wraps every response: { success, message, data: { ... } }
      const data = envelope?.data || envelope;
      this._currentUser = data;
      if (this._composer) {
        this._composer.setAttribute("avatar-url", data.avatar_url || "");
        this._composer.setAttribute("display-name", data.display_name || data.email || "");
        // Use email as seed so initials match the nav bar (splits on @._-)
        if (data.email) this._composer.setAttribute("seed", data.email);
      }
    } catch {
      // non-fatal — composer renders without avatar
    }
  }

  _bindEvents() {
    const s = { signal: this._ctrl.signal };

    // New comment submitted from composer
    this.addEventListener(
      "rp:comment:submit",
      (e) => {
        e.stopPropagation();
        this._handleSubmit(e.detail);
      },
      s,
    );

    // Pin / Unpin
    this.addEventListener(
      "rp:comment:pin",
      (e) => {
        e.stopPropagation();
        this._handlePin(e.detail.code, true);
      },
      s,
    );
    this.addEventListener(
      "rp:comment:unpin",
      (e) => {
        e.stopPropagation();
        this._handlePin(e.detail.code, false);
      },
      s,
    );

    // Inline edit save
    this.addEventListener(
      "rp:comment:save",
      (e) => {
        e.stopPropagation();
        this._handleSave(e.detail);
      },
      s,
    );

    // Delete — open confirmation modal
    this.addEventListener(
      "rp:comment:delete",
      (e) => {
        e.stopPropagation();
        this._pendingDeleteCode = e.detail.code;
        this._deleteModal.show?.();
      },
      s,
    );

    // Delete modal confirmed
    this._deleteModal.addEventListener(
      "rp:delete",
      () => {
        if (this._pendingDeleteCode) {
          this._handleDelete(this._pendingDeleteCode);
          this._pendingDeleteCode = null;
        }
      },
      s,
    );

    // Pagination
    this.addEventListener(
      "rp:pager:change",
      (e) => {
        e.stopPropagation();
        this._load(e.detail.page);
      },
      s,
    );
  }

  _commentsUrl() {
    return this.getAttribute("comments-url") || "";
  }

  _commentUrl(code) {
    const base = this._commentsUrl().replace(/\/$/, "");
    return `${base}/${code}/`;
  }

  _pinUrl(code, pinned) {
    const base = this._commentUrl(code).replace(/\/$/, "");
    return `${base}/${pinned ? "pin" : "unpin"}/`;
  }

  async _load(page) {
    const base = this._commentsUrl();
    if (!base) return;
    const url = `${base}?page=${page}&page_size=25`;
    try {
      const envelope = await apiFetch(url);
      this._currentPage = page;

      // Response shape: { success, message, data: { results: [...], pagination: {...} } }
      const results = envelope?.data?.results || [];
      const pagination = envelope?.data?.pagination || {};

      if (page === 1) {
        this._pinnedComments = results.filter((c) => c.is_pinned);
      }

      const general = results.filter((c) => !c.is_pinned);

      this._renderList(page === 1 ? this._pinnedComments : [], general);

      const totalPages = pagination.total_pages || 1;
      this._pager.setAttribute("current-page", String(pagination.current_page || page));
      this._pager.setAttribute("total-pages", String(totalPages));
      this._pager.hidden = totalPages <= 1;
    } catch {
      toast({ type: "error", title: "Error", message: "Failed to load comments." });
    }
  }

  _renderList(pinned, general) {
    this._list.clear();

    if (!pinned.length && !general.length) {
      this._list.showEmpty();
      return;
    }

    const myCode = this._currentUser?.profile_code || "";

    pinned.forEach((c) => {
      const el = this._makeCommentEl(c, myCode);
      this._list.appendChild(el);
    });

    if (pinned.length && general.length) {
      const hr = document.createElement("hr");
      hr.className = "rp-divider my-2";
      this._list.appendChild(hr);
    }

    general.forEach((c) => {
      const el = this._makeCommentEl(c, myCode);
      this._list.appendChild(el);
      const hr = document.createElement("hr");
      hr.className = "rp-comment-divider";
      this._list.appendChild(hr);
    });
  }

  _makeCommentEl(c, myCode) {
    const el = document.createElement("comment-item");
    el.setAttribute("code", c.code || "");
    if (c.is_pinned) el.setAttribute("pinned", "");
    if (c.is_edited) el.setAttribute("edited", "");

    const author = c.created_by?.display_name || c.created_by?.email || "Unknown";
    el.setAttribute("author", author);

    const avatarUrl = c.created_by?.avatar_url || "";
    if (avatarUrl) el.setAttribute("avatar-url", avatarUrl);

    const timeStr = c.is_pinned
      ? `pinned ${this._formatTime(c.updated_at || c.created_at)}`
      : this._formatTime(c.created_at);
    el.setAttribute("time", timeStr);

    const isOwn = myCode && c.created_by?.profile_code === myCode;
    if (isOwn) el.setAttribute("is-own", "");

    // Set body before appending to DOM so connectedCallback can capture it
    el.innerHTML = c.comment || "";

    return el;
  }

  _formatTime(iso) {
    if (!iso) return "";
    try {
      const d = new Date(iso);
      const now = new Date();
      const diff = now - d;
      if (diff < 60_000) return "just now";
      if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
      if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
      return d.toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
        year: d.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
      });
    } catch {
      return "";
    }
  }

  async _handleSubmit({ comment, mentions }) {
    const apiUrl = this._commentsUrl();
    if (!apiUrl) return;
    const body = comment?.trim();
    if (!body) return;
    this._composer.setBusy(true);
    try {
      await apiFetch(apiUrl, {
        method: "POST",
        body: JSON.stringify({ comment: body, mentions }),
      });
      this._composer.clear();
      await this._load(1);
    } catch (err) {
      const msg = err?.data?.error?.message ?? "Failed to post comment.";
      toast({ type: "error", title: "Error", message: msg });
    } finally {
      this._composer.setBusy(false);
    }
  }

  async _handlePin(code, pin) {
    try {
      await apiFetch(this._pinUrl(code, pin), { method: "POST" });
      await this._load(1);
    } catch (err) {
      const msg = err?.data?.error?.message ?? `Failed to ${pin ? "pin" : "unpin"} comment.`;
      toast({ type: "error", title: "Error", message: msg });
    }
  }

  async _handleSave({ code, comment, mentions }) {
    const body = comment?.trim();
    if (!body) return;
    try {
      await apiFetch(this._commentUrl(code), {
        method: "PATCH",
        body: JSON.stringify({ comment: body, mentions }),
      });
      await this._load(this._currentPage);
    } catch (err) {
      const msg = err?.data?.error?.message ?? "Failed to update comment.";
      toast({ type: "error", title: "Error", message: msg });
    }
  }

  async _handleDelete(code) {
    try {
      await apiFetch(this._commentUrl(code), { method: "DELETE" });
      this._deleteModal.hide?.();
      toast({
        type: "success",
        title: "Comment deleted",
        message: "The comment has been removed.",
      });
      await this._load(this._currentPage);
    } catch (err) {
      const msg = err?.data?.error?.message ?? "Failed to delete comment.";
      toast({ type: "error", title: "Error", message: msg });
    }
  }
}

if (!customElements.get("comments-panel")) {
  customElements.define("comments-panel", CommentsPanel);
}
