"use strict";

import { apiFetch } from "../../../modules/utils/utils.js";
import { API_URLS, UI_URLS } from "../../../modules/main/urls.js";

/* NotificationsPanel  <notifications-panel>
 *
 * Top-bar bell trigger + dropdown panel showing the current user's most recent
 * notifications. Polls GET /api/v1/notifications/unread-count/ in the background
 * to keep the badge current, and lazily loads the recent list on first open.
 *
 * Poll interval: 30s. Unlike the short-lived job-status polls elsewhere in the
 * app (2-5s, used while a specific async job is running), this poll runs for the
 * lifetime of the page, so a longer interval avoids needlessly hammering the
 * server for a value that rarely needs sub-minute freshness.
 *
 * Pre-mounted in templates/base.html. Do not add additional instances.
 */

const POLL_INTERVAL_MS = 30_000;
const RECENT_PAGE_SIZE = 8;

const TYPE_ICON = {
  info: "bi-info-circle-fill",
  success: "bi-check-circle-fill",
  warning: "bi-exclamation-triangle-fill",
  error: "bi-x-circle-fill",
  comment: "bi-chat-left-text-fill",
  reminder: "bi-alarm-fill",
};

class NotificationsPanel extends HTMLElement {
  constructor() {
    super();
    this._open = false;
    this._loaded = false;
    this._pollTimer = null;

    this._onDocClick = (e) => {
      if (this._open && !this.contains(e.target)) this._closePanel();
    };
    this._onKeydown = (e) => {
      if (e.key === "Escape" && this._open) this._closePanel();
    };
  }

  connectedCallback() {
    this.style.position = "relative";
    this._render();
    document.addEventListener("keydown", this._onKeydown);
    window.addEventListener("rp:notification-created", this._refreshCount);
    this._refreshCount();
    this._pollTimer = setInterval(() => this._refreshCount(), POLL_INTERVAL_MS);
  }

  disconnectedCallback() {
    document.removeEventListener("keydown", this._onKeydown);
    document.removeEventListener("click", this._onDocClick);
    window.removeEventListener("rp:notification-created", this._refreshCount);
    if (this._pollTimer) clearInterval(this._pollTimer);
  }

  _render() {
    this.innerHTML = `
      <div class="rp-iconbtn-wrap">
        <button class="rp-iconbtn" title="Notifications" data-trigger>
          <icon-field icon="bi-bell" label="Notifications"></icon-field>
          <span class="rp-count-pill" data-badge hidden></span>
        </button>
      </div>
      <div class="rp-dd-panel dd-right rp-notif-panel" data-panel>
        <div class="rp-notif-head">
          <strong>Notifications</strong>
          <button type="button" class="rp-dd-link rp-notif-mark-all" data-mark-all>
            Mark all read
          </button>
        </div>
        <div class="rp-notif-list" data-list></div>
        <div class="rp-notif-foot">
          <a href="${UI_URLS.notifications.list()}">View all notifications</a>
        </div>
      </div>
    `;

    this._refreshCount = this._refreshCount.bind(this);

    this.querySelector("[data-trigger]").addEventListener("click", (e) => {
      e.stopPropagation();
      this._togglePanel();
    });

    this.querySelector("[data-mark-all]").addEventListener("click", async () => {
      const { href, method } = API_URLS.notifications.markAllRead();
      try {
        await apiFetch(href, { method });
        this._loaded = false;
        await this._loadRecent();
        this._refreshCount();
      } catch {
        // Non-critical — badge/list simply stay as-is until next poll.
      }
    });
  }

  _togglePanel() {
    this._open ? this._closePanel() : this._openPanel();
  }

  _openPanel() {
    this._open = true;
    this.querySelector("[data-panel]").classList.add("rp-dd-open");
    document.addEventListener("click", this._onDocClick);
    if (!this._loaded) this._loadRecent();
  }

  _closePanel() {
    this._open = false;
    this.querySelector("[data-panel]")?.classList.remove("rp-dd-open");
    document.removeEventListener("click", this._onDocClick);
  }

  async _refreshCount() {
    try {
      const { href, method } = API_URLS.notifications.unreadCount();
      const resp = await apiFetch(href, { method });
      const count = resp?.data?.unread_count ?? 0;
      const badge = this.querySelector("[data-badge]");
      if (!badge) return;
      if (count > 0) {
        badge.textContent = count > 99 ? "99+" : String(count);
        badge.hidden = false;
      } else {
        badge.hidden = true;
      }
    } catch {
      // Silent — badge simply keeps its last known value until the next poll.
    }
  }

  async _loadRecent() {
    const list = this.querySelector("[data-list]");
    if (!list) return;
    list.innerHTML = `<div class="rp-notif-empty">Loading…</div>`;

    try {
      const { href, method } = API_URLS.notifications.list();
      const resp = await apiFetch(`${href}?page_size=${RECENT_PAGE_SIZE}&is_dismissed=false`, {
        method,
      });
      const results = resp?.data?.results ?? [];
      this._loaded = true;
      this._renderList(results);
    } catch {
      list.innerHTML = `<div class="rp-notif-empty">Couldn't load notifications.</div>`;
    }
  }

  _renderList(rows) {
    const list = this.querySelector("[data-list]");
    if (!list) return;

    if (!rows.length) {
      list.replaceChildren();
      const empty = document.createElement("div");
      empty.className = "rp-notif-empty";
      empty.textContent = "You're all caught up.";
      list.appendChild(empty);
      return;
    }

    const frag = document.createDocumentFragment();
    rows.forEach((row) => frag.appendChild(this._buildRow(row)));
    list.replaceChildren(frag);
  }

  _buildRow(row) {
    const item = document.createElement("div");
    item.className = "rp-notif-item" + (row.is_read ? "" : " is-unread");
    item.dataset.code = row.code;

    const icon = document.createElement("i");
    icon.className = `bi ${TYPE_ICON[row.notification_type] ?? "bi-info-circle-fill"} rp-notif-icon`;
    item.appendChild(icon);

    const body = document.createElement("div");
    body.className = "rp-notif-item-body";

    const title = document.createElement("div");
    title.className = "rp-notif-item-title";
    title.textContent = row.title;
    body.appendChild(title);

    if (row.body) {
      const text = document.createElement("div");
      text.className = "rp-notif-item-text";
      text.textContent = row.body;
      body.appendChild(text);
    }

    const meta = document.createElement("div");
    meta.className = "rp-notif-item-meta";
    meta.textContent = this._formatTime(row.created_at);
    body.appendChild(meta);

    item.appendChild(body);

    const dismissBtn = document.createElement("button");
    dismissBtn.type = "button";
    dismissBtn.className = "rp-notif-dismiss";
    dismissBtn.title = "Dismiss";
    dismissBtn.innerHTML = '<i class="bi bi-x"></i>';
    dismissBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      this._dismissRow(row.code, item);
    });
    item.appendChild(dismissBtn);

    item.addEventListener("click", () => this._openRow(row));

    return item;
  }

  async _openRow(row) {
    if (!row.is_read) {
      try {
        const { href, method } = API_URLS.notifications.markRead(row.code);
        await apiFetch(href, { method });
        this._refreshCount();
      } catch {
        // Non-critical — link navigation proceeds regardless.
      }
    }
    if (row.link) {
      window.location.href = row.link;
    } else {
      this._closePanel();
    }
  }

  async _dismissRow(code, el) {
    try {
      const { href, method } = API_URLS.notifications.dismiss(code);
      await apiFetch(href, { method });
      el.remove();
      this._refreshCount();
      const list = this.querySelector("[data-list]");
      if (list && !list.children.length) this._renderList([]);
    } catch {
      // Non-critical — row stays visible until the next panel open.
    }
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
}

customElements.define("notifications-panel", NotificationsPanel);
