"use strict";

import { apiFetch } from "../../../modules/utils/utils.js";
import { toast } from "../../../modules/utils/toast.js";
import { API_URLS, UI_URLS } from "../../../modules/main/urls.js";

/* ToDoPanel  <todo-panel>
 *
 * Top-bar trigger + dropdown panel showing the current user's open to-dos.
 * Polls GET /api/v1/to-do/open-count/ in the background to keep the badge
 * current (30s, matching <notifications-panel>), and separately polls
 * GET /api/v1/to-do/due-reminders/ to surface due reminders as toasts.
 *
 * Pre-mounted in templates/base.html. Do not add additional instances.
 */

const POLL_INTERVAL_MS = 30_000;
const RECENT_PAGE_SIZE = 8;

const PRIORITY_ICON = {
  low: "bi-arrow-down-circle-fill",
  medium: "bi-dash-circle-fill",
  high: "bi-arrow-up-circle-fill",
  urgent: "bi-exclamation-circle-fill",
};

class ToDoPanel extends HTMLElement {
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
    window.addEventListener("rp:todo-created", this._refreshCount);
    this._refreshCount();
    this._pollReminders();
    this._pollTimer = setInterval(() => {
      this._refreshCount();
      this._pollReminders();
    }, POLL_INTERVAL_MS);
  }

  disconnectedCallback() {
    document.removeEventListener("keydown", this._onKeydown);
    document.removeEventListener("click", this._onDocClick);
    window.removeEventListener("rp:todo-created", this._refreshCount);
    if (this._pollTimer) clearInterval(this._pollTimer);
  }

  _render() {
    this.innerHTML = `
      <div class="rp-iconbtn-wrap">
        <button class="rp-iconbtn" title="To-Do" data-trigger>
          <icon-field icon="bi-list-check" label="To-Do"></icon-field>
          <span class="rp-count-pill" data-badge hidden></span>
        </button>
      </div>
      <div class="rp-dd-panel dd-right rp-notif-panel" data-panel>
        <div class="rp-notif-head">
          <strong>To-Do</strong>
          <button type="button" class="rp-dd-link" data-add>
            Add
          </button>
        </div>
        <div class="rp-notif-list" data-list></div>
        <div class="rp-notif-foot">
          <a href="${UI_URLS.toDo.list()}">View all to-dos</a>
        </div>
      </div>
    `;

    this._refreshCount = this._refreshCount.bind(this);

    this.querySelector("[data-trigger]").addEventListener("click", (e) => {
      e.stopPropagation();
      this._togglePanel();
    });

    this.querySelector("[data-add]").addEventListener("click", (e) => {
      e.stopPropagation();
      this._closePanel();
      window.location.href = UI_URLS.toDo.list();
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
      const { href, method } = API_URLS.toDo.openCount();
      const resp = await apiFetch(href, { method });
      const count = resp?.data?.open_count ?? 0;
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

  async _pollReminders() {
    try {
      const { href, method } = API_URLS.toDo.dueReminders();
      const resp = await apiFetch(href, { method });
      const due = resp?.data ?? [];
      due.forEach((row) => {
        toast({
          type: "warning",
          title: "To-do reminder",
          message: row.title,
          persistent: true,
          actions: [
            {
              label: "View",
              onClick: () => {
                window.location.href = UI_URLS.toDo.list();
              },
            },
          ],
        });
      });
      if (due.length) this._loaded && this._loadRecent();
    } catch {
      // Non-critical — the next poll tick will retry.
    }
  }

  async _loadRecent() {
    const list = this.querySelector("[data-list]");
    if (!list) return;
    list.innerHTML = `<div class="rp-notif-empty">Loading…</div>`;

    try {
      const { href, method } = API_URLS.toDo.list();
      const resp = await apiFetch(`${href}?page_size=${RECENT_PAGE_SIZE}&status=`, { method });
      const results = resp?.data?.results ?? [];
      this._loaded = true;
      this._renderList(results);
    } catch {
      list.innerHTML = `<div class="rp-notif-empty">Couldn't load to-dos.</div>`;
    }
  }

  _renderList(rows) {
    const list = this.querySelector("[data-list]");
    if (!list) return;

    if (!rows.length) {
      list.replaceChildren();
      const empty = document.createElement("div");
      empty.className = "rp-notif-empty";
      empty.textContent = "Nothing on your list.";
      list.appendChild(empty);
      return;
    }

    const frag = document.createDocumentFragment();
    rows.forEach((row) => frag.appendChild(this._buildRow(row)));
    list.replaceChildren(frag);
  }

  _buildRow(row) {
    const item = document.createElement("div");
    item.className = "rp-notif-item";
    item.dataset.code = row.code;

    const icon = document.createElement("i");
    icon.className = `bi ${PRIORITY_ICON[row.priority] ?? "bi-dash-circle-fill"} rp-notif-icon`;
    item.appendChild(icon);

    const body = document.createElement("div");
    body.className = "rp-notif-item-body";

    const title = document.createElement("div");
    title.className = "rp-notif-item-title";
    title.textContent = row.title;
    body.appendChild(title);

    if (row.due_date) {
      const meta = document.createElement("div");
      meta.className = "rp-notif-item-meta";
      meta.textContent = row.is_overdue ? `Overdue — ${row.due_date}` : `Due ${row.due_date}`;
      body.appendChild(meta);
    }

    item.appendChild(body);

    const completeBtn = document.createElement("button");
    completeBtn.type = "button";
    completeBtn.className = "rp-notif-dismiss";
    completeBtn.title = "Mark complete";
    completeBtn.innerHTML = '<i class="bi bi-check2"></i>';
    completeBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      this._completeRow(row.code, item);
    });
    item.appendChild(completeBtn);

    item.addEventListener("click", () => {
      window.location.href = UI_URLS.toDo.list();
    });

    return item;
  }

  async _completeRow(code, el) {
    try {
      const { href, method } = API_URLS.toDo.complete(code);
      await apiFetch(href, { method });
      el.remove();
      this._refreshCount();
      const list = this.querySelector("[data-list]");
      if (list && !list.children.length) this._renderList([]);
      toast({ type: "success", title: "To-do completed", message: "Nice work." });
    } catch {
      // Non-critical — row stays visible until the next panel open.
    }
  }
}

customElements.define("todo-panel", ToDoPanel);
