import { apiFetch } from "../../modules/utils/utils.js";
import { esc } from "../utils.js";

/* ─────────────────────────────────────────────────────────────────────────
 * DataTable  <data-table>
 *
 * Attributes
 *   title              – card head title (optional)
 *   subtitle           – card head subtitle (optional)
 *   url                – API endpoint; triggers dynamic mode
 *   paginated          – boolean; parse pagination block & render pager
 *   page-size          – rows per page (default 20)
 *   data               – JSON array string for static mode
 *   row-template       – global function name: fn(row, idx) → td cells HTML
 *   max-inline-actions – max icon buttons before "…" overflow (default 2)
 *   empty-message      – custom empty-state text
 *   fixable            – number of leading columns to pin (e.g. fixable="2")
 *   actions-fixable    – boolean; pins the trailing actions column to the right edge
 *   expandable         – boolean; adds a leading chevron toggle that expands a detail row
 *   detail-template    – global function name: fn(row, idx) → detail row HTML (colspan'd),
 *                         only used when expandable is set
 *
 * Declarative children (read before first render, then discarded)
 *   <table-columns>
 *     <table-column label key [sortable] [numeric] [mono] [width]>
 *   <table-actions>
 *     <table-action  icon label [event] [href] [danger]>
 *       icon   – Bootstrap icon class, e.g. "bi-pencil"
 *       event  – CustomEvent name dispatched with { row, index } detail
 *       href   – navigation URL; supports {key} tokens resolved from the row
 *       danger – style the item red
 *
 * Public API
 *   table.rows = [...]          – set rows programmatically (clears pagination)
 *   table.setRows(rows, pg?)    – set rows + optional pagination object
 *   table.refresh()             – re-fetch from url at the current page
 *
 * Events dispatched (bubble)
 *   <whatever event= names are on table-action elements>
 *   detail: { row: Object, index: Number }
 * ───────────────────────────────────────────────────────────────────────── */
class DataTable extends HTMLElement {
  static get observedAttributes() {
    return [
      "title",
      "subtitle",
      "url",
      "paginated",
      "page-size",
      "data",
      "row-template",
      "max-inline-actions",
      "empty-message",
    ];
  }

  connectedCallback() {
    if (!this._configured) {
      this._readConfig();
      this._configured = true;
    }
    this._currentPage = 1;
    this._sortKey = "";
    this._sortDir = "ASC";
    this._rows = [];
    this._pagination = null;
    this._render();
    this._bindEvents();
    this._applyFixedColumns();

    if (this.getAttribute("url")) {
      this._loadData(1);
    } else if (this._staticRows) {
      this._applyRows(this._staticRows, null);
    }
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (!this._configured || oldVal === newVal) return;
    if (name === "data") {
      this._staticRows = this._parseData(newVal);
      if (!this.getAttribute("url")) this._applyRows(this._staticRows, null);
    } else if (name === "url") {
      if (newVal) {
        this._currentPage = 1;
        this._loadData(1);
      }
    } else if (name === "title" || name === "subtitle") {
      this._syncCardHead();
    }
  }

  disconnectedCallback() {
    if (this._onDocClick) document.removeEventListener("click", this._onDocClick);
  }

  get _title() {
    return this.getAttribute("title") || "";
  }
  get _subtitle() {
    return this.getAttribute("subtitle") || "";
  }
  get _apiUrl() {
    return this.getAttribute("url") || "";
  }
  get _isPaginated() {
    return this.hasAttribute("paginated");
  }
  get _pageSize() {
    return parseInt(this.getAttribute("page-size") || "20", 10);
  }
  get _rowTmplFn() {
    return this.getAttribute("row-template") || "";
  }
  get _maxInline() {
    return parseInt(this.getAttribute("max-inline-actions") || "2", 10);
  }
  get _emptyMsg() {
    return this.getAttribute("empty-message") || "No records found.";
  }
  get _isExpandable() {
    return this.hasAttribute("expandable");
  }
  get _detailTmplFn() {
    return this.getAttribute("detail-template") || "";
  }

  _readConfig() {
    this._columns = Array.from(this.querySelectorAll("table-column")).map((el) => ({
      label: el.getAttribute("label") || "",
      key: el.getAttribute("key") || "",
      sortable: el.hasAttribute("sortable"),
      numeric: el.hasAttribute("numeric"),
      mono: el.hasAttribute("mono"),
      width: el.getAttribute("width") || "",
      hideMobile: el.hasAttribute("hide-mobile"),
    }));

    this._actions = Array.from(this.querySelectorAll("table-action")).map((el) => ({
      icon: el.getAttribute("icon") || "",
      label: el.getAttribute("label") || "",
      event: el.getAttribute("event") || "",
      href: el.getAttribute("href") || "",
      danger: el.hasAttribute("danger"),
      dangerKey: el.getAttribute("danger-key") || "",
      colorKey: el.getAttribute("color-key") || "",
      hiddenKey: el.getAttribute("hidden-key") || "",
    }));

    this._staticRows = this._parseData(this.getAttribute("data"));
    this._fixableCount = parseInt(this.getAttribute("fixable") || "0", 10);
    this._actionsFixable = this.hasAttribute("actions-fixable");
  }

  _parseData(raw) {
    if (!raw) return null;
    try {
      return JSON.parse(raw);
    } catch {
      return null;
    }
  }

  _render() {
    const headHTML = this._buildCardHead();
    const theadCells = this._buildTheadCells();
    const tableClasses = [
      this._fixableCount > 0 ? "rp-table--fixable" : "",
      this._actionsFixable ? "rp-table--actions-fixable" : "",
    ]
      .filter(Boolean)
      .join(" ");
    const tableClass = tableClasses ? ` ${tableClasses}` : "";

    this.innerHTML = `
      <div class="rp-table-wrap">
        ${headHTML}
        <div class="rp-table-scroll">
          <table class="rp-table${tableClass}">
            <thead><tr>${theadCells}</tr></thead>
            <tbody data-rp-tbody></tbody>
          </table>
        </div>
        <div class="rp-table-state" data-rp-state="loading" hidden>
          <i class="bi bi-hourglass-split"></i> Loading…
        </div>
        <div class="rp-table-state" data-rp-state="empty" hidden>
          <i class="bi bi-inbox"></i> ${esc(this._emptyMsg)}
        </div>
        <div class="rp-table-state rp-table-state--error" data-rp-state="error" hidden>
          <i class="bi bi-exclamation-circle"></i>
          <span data-rp-errmsg></span>
        </div>
        <div data-rp-pagination hidden></div>
      </div>
    `;
  }

  _buildCardHead() {
    if (!this._title && !this._subtitle) return "";
    return `
      <div class="rp-card-head" data-rp-card-head>
        <div>
          ${this._title ? `<h2 class="rp-card-title">${esc(this._title)}</h2>` : ""}
          ${this._subtitle ? `<p class="rp-table-subtitle">${esc(this._subtitle)}</p>` : ""}
        </div>
      </div>
    `;
  }

  _buildTheadCells() {
    const fixCount = this._fixableCount;
    const cells = this._isExpandable ? [`<th style="width:40px"></th>`] : [];
    cells.push(
      ...this._columns.map((col, idx) => {
        const width = col.width ? ` style="width:${esc(col.width)}"` : "";
        const align = col.numeric ? ` class="text-end"` : "";
        const mobile = col.hideMobile ? ` data-rp-hide-mobile` : "";
        const fixed = idx < fixCount ? ` data-rp-fixed` : "";
        const fixedLast = idx === fixCount - 1 ? ` data-rp-fixed-last` : "";
        let inner;
        if (col.sortable) {
          inner = `<span class="rp-sort" data-rp-sort="${esc(col.key)}">
          ${esc(col.label)}
          <i class="bi bi-arrow-down-up rp-sort-icon" data-rp-sort-icon="${esc(col.key)}"></i>
        </span>`;
        } else {
          inner = esc(col.label);
        }
        return `<th${width}${align}${mobile}${fixed}${fixedLast}>${inner}</th>`;
      }),
    );

    if (this._actions.length > 0) {
      const afx = this._actionsFixable ? ` data-rp-actions-fixed` : "";
      cells.push(`<th style="width:${this._actionColWidth()}px"${afx}></th>`);
    }
    return cells.join("");
  }

  _actionColWidth() {
    const inline = Math.min(this._actions.length, this._maxInline);
    const hasMore = this._actions.length > this._maxInline;
    return (inline + (hasMore ? 1 : 0)) * 34 + 12;
  }

  _syncCardHead() {
    const wrap = this.querySelector(".rp-table-wrap");
    if (!wrap) return;
    const existing = wrap.querySelector("[data-rp-card-head]");
    const hasHead = this._title || this._subtitle;

    if (!hasHead) {
      existing?.remove();
      return;
    }

    const html = `
      <div>
        ${this._title ? `<h2 class="rp-card-title">${esc(this._title)}</h2>` : ""}
        ${this._subtitle ? `<p class="rp-table-subtitle">${esc(this._subtitle)}</p>` : ""}
      </div>
    `;

    if (existing) {
      existing.innerHTML = html;
    } else {
      const div = document.createElement("div");
      div.className = "rp-card-head";
      div.setAttribute("data-rp-card-head", "");
      div.innerHTML = html;
      wrap.prepend(div);
    }
  }

  async _loadData(page = 1) {
    this._currentPage = page;
    this._showState("loading");

    // Merge pagination + sort into the base URL, preserving any existing params
    // (e.g. a search= param injected by the host page via the url attribute).
    let fetchUrl;
    try {
      const base = new URL(this._apiUrl, window.location.origin);
      base.searchParams.set("page", page);
      base.searchParams.set("page_size", this._pageSize);
      if (this._sortKey) {
        base.searchParams.set("sort", this._sortKey);
        base.searchParams.set("order_by", this._sortDir);
      }
      fetchUrl = base.pathname + base.search;
    } catch {
      fetchUrl = `${this._apiUrl}?page=${page}&page_size=${this._pageSize}`;
    }

    try {
      const json = await apiFetch(fetchUrl);
      // Support both { data: { results, pagination } } and { results, pagination }
      const payload = json?.data ?? json;

      let rows, pagination;
      if (this._isPaginated) {
        rows = payload?.results ?? [];
        pagination = payload?.pagination ?? null;
      } else {
        rows = Array.isArray(payload) ? payload : (payload?.results ?? []);
        pagination = null;
      }

      this._applyRows(rows, pagination);
    } catch (err) {
      const msg = err?.data?.error?.message ?? err?.data?.message ?? "Failed to load data.";
      this._showState("error", msg);
    }
  }

  _applyRows(rows, pagination) {
    this._rows = rows ?? [];
    this._pagination = pagination ?? null;

    if (this._rows.length === 0) {
      this._showState("empty");
      this.dispatchEvent(
        new CustomEvent("rp:data:loaded", {
          bubbles: true,
          detail: { rows: this._rows, pagination: this._pagination },
        }),
      );
      return;
    }

    this._showState(null);
    this._renderRows();

    if (this._isPaginated && this._pagination) {
      this._renderPagination(this._pagination);
    }

    this.dispatchEvent(
      new CustomEvent("rp:data:loaded", {
        bubbles: true,
        detail: { rows: this._rows, pagination: this._pagination },
      }),
    );
  }

  _renderRows() {
    const tbody = this.querySelector("[data-rp-tbody]");
    if (!tbody) return;

    const tmplFn = this._rowTmplFn ? window[this._rowTmplFn] : null;
    const detailFn = this._isExpandable && this._detailTmplFn ? window[this._detailTmplFn] : null;
    const totalCols =
      this._columns.length + (this._actions.length > 0 ? 1 : 0) + (this._isExpandable ? 1 : 0);

    tbody.innerHTML = this._rows
      .map((row, idx) => {
        const cells = typeof tmplFn === "function" ? tmplFn(row, idx) : this._buildAutoCells(row);
        const actionCell = this._actions.length > 0 ? this._buildActionCell(row, idx) : "";
        const expandCell = this._isExpandable ? this._buildExpandCell(idx) : "";
        const mainRow = `<tr data-rp-row="${idx}">${expandCell}${cells}${actionCell}</tr>`;
        if (!this._isExpandable) return mainRow;

        const detailHTML = typeof detailFn === "function" ? detailFn(row, idx) : "";
        const detailRow = `<tr class="rp-table-detail-row" data-rp-detail-row="${idx}" hidden><td colspan="${totalCols}">${detailHTML}</td></tr>`;
        return mainRow + detailRow;
      })
      .join("");

    this._applyMobileHide(tbody);
    this._applyFixedColumns();
  }

  _buildExpandCell(idx) {
    return `<td class="rp-table-expand-cell">
      <button type="button" class="rp-iconbtn" data-rp-expand-toggle="${idx}" aria-label="Toggle details" aria-expanded="false">
        <i class="bi bi-chevron-right"></i>
      </button>
    </td>`;
  }

  _buildAutoCells(row) {
    return this._columns
      .map((col) => {
        const raw = row[col.key] ?? "";
        const val = esc(String(raw));
        if (col.mono) return `<td><code class="rp-mono">${val}</code></td>`;
        if (col.numeric) return `<td class="rp-td-num">${val}</td>`;
        return `<td>${val}</td>`;
      })
      .join("");
  }

  _applyFixedColumns() {
    if (!this._fixableCount) return;
    const table = this.querySelector(".rp-table");
    if (!table) return;

    // Measure header cells and assign left offsets
    const ths = Array.from(table.querySelectorAll("thead tr th[data-rp-fixed]"));
    const offsets = [];
    let left = 0;

    ths.forEach((th) => {
      offsets.push(left);
      th.style.left = `${left}px`;
      left += th.getBoundingClientRect().width || 0;
    });

    // Apply the same offsets to matching body cells
    const tdOffset = this._isExpandable ? 1 : 0;
    table.querySelectorAll("tbody tr[data-rp-row]").forEach((tr) => {
      const tds = tr.querySelectorAll("td");
      offsets.forEach((off, i) => {
        const td = tds[i + tdOffset];
        if (!td) return;
        td.setAttribute("data-rp-fixed", "");
        if (i === offsets.length - 1) td.setAttribute("data-rp-fixed-last", "");
        td.style.left = `${off}px`;
      });
    });
  }

  _applyMobileHide(tbody) {
    const hiddenIndices = this._columns
      .map((col, i) => (col.hideMobile ? i : -1))
      .filter((i) => i >= 0);

    if (hiddenIndices.length === 0) return;

    const offset = this._isExpandable ? 1 : 0;
    tbody.querySelectorAll("tr[data-rp-row]").forEach((tr) => {
      const tds = tr.querySelectorAll("td");
      hiddenIndices.forEach((i) => {
        if (tds[i + offset]) tds[i + offset].setAttribute("data-rp-hide-mobile", "");
      });
    });
  }

  _buildActionCell(row, idx) {
    const inline = this._actions.slice(0, this._maxInline);
    const overflow = this._actions.slice(this._maxInline);

    const inlineBtns = inline
      .map((a) => {
        if (a.hiddenKey && row[a.hiddenKey]) return "";
        const iconColor = this._resolveIconColor(a, row);
        const colorStyle = iconColor ? ` style="color:${iconColor}"` : "";
        if (a.href) {
          return `<a href="${this._resolveHref(a.href, row)}"
            class="rp-iconbtn"
            title="${esc(a.label)}"
            aria-label="${esc(a.label)}"${colorStyle}
          ><i class="bi ${esc(a.icon)}"></i></a>`;
        }
        return `<button
          class="rp-iconbtn"
          data-rp-action="${esc(a.event)}"
          data-rp-row="${idx}"
          title="${esc(a.label)}"
          aria-label="${esc(a.label)}"${colorStyle}
        ><i class="bi ${esc(a.icon)}"></i></button>`;
      })
      .join("");

    let moreHTML = "";
    if (overflow.length > 0) {
      const items = overflow
        .map((a) => {
          if (a.hiddenKey && row[a.hiddenKey]) return "";
          // Apply color directly to the icon — CSS `.rp-dd-panel .bi { color: var(--rp-text-muted) }`
          // has higher specificity than inherited button color, so we must target the icon element.
          const iconColor = this._resolveIconColor(a, row);
          const iconStyle = iconColor ? ` style="color:${iconColor}"` : "";
          const textStyle = iconColor ? ` style="color:${iconColor}"` : "";
          if (a.href) {
            return `<a href="${this._resolveHref(a.href, row)}"${textStyle}>
              <i class="bi ${esc(a.icon)}"${iconStyle}></i>${esc(a.label)}
            </a>`;
          }
          return `<button
            class="rp-dd-link"
            data-rp-action="${esc(a.event)}"
            data-rp-row="${idx}"${textStyle}
          ><i class="bi ${esc(a.icon)}"${iconStyle}></i>${esc(a.label)}</button>`;
        })
        .join("");

      if (items.trim()) {
        moreHTML = `
          <span class="rp-table-more-wrap">
            <button
              class="rp-iconbtn rp-table-more-btn"
              title="More actions"
              aria-label="More actions"
              aria-haspopup="true"
            ><i class="bi bi-three-dots"></i></button>
            <div class="rp-dd-panel dd-right rp-table-more-menu">${items}</div>
          </span>
        `;
      }
    }

    const afx = this._actionsFixable ? ` data-rp-actions-fixed` : "";
    return `<td class="rp-td-actions"${afx}><span class="rp-icon-row">${inlineBtns}${moreHTML}</span></td>`;
  }

  _resolveIconColor(a, row) {
    if (a.danger || (a.dangerKey && row[a.dangerKey])) return "var(--rp-danger)";
    if (a.colorKey) return row[a.colorKey] ? "var(--rp-danger)" : "var(--rp-success)";
    return "";
  }

  _resolveHref(href, row) {
    return href.replace(/\{(\w+)\}/g, (_, key) => esc(String(row[key] ?? "")));
  }

  _renderPagination(p) {
    const container = this.querySelector("[data-rp-pagination]");
    if (!container) return;

    const { total_count, total_pages, current_page, page_size } = p;

    if (!total_pages || total_pages <= 1) {
      container.hidden = true;
      return;
    }

    const from = (current_page - 1) * page_size + 1;
    const to = Math.min(current_page * page_size, total_count);

    container.innerHTML = `
      <div class="rp-pagination">
        <div>Showing <strong>${from}–${to}</strong> of <strong>${total_count}</strong></div>
        <div class="rp-pager">
          <button data-rp-page="1" title="First page"${current_page === 1 ? " disabled" : ""}>
            <i class="bi bi-chevron-double-left"></i>
          </button>
          <button data-rp-page="${current_page - 1}" title="Previous page"${current_page === 1 ? " disabled" : ""}>
            <i class="bi bi-chevron-left"></i>
          </button>
          ${this._pageNumbers(current_page, total_pages)}
          <button data-rp-page="${current_page + 1}" title="Next page"${current_page === total_pages ? " disabled" : ""}>
            <i class="bi bi-chevron-right"></i>
          </button>
          <button data-rp-page="${total_pages}" title="Last page"${current_page === total_pages ? " disabled" : ""}>
            <i class="bi bi-chevron-double-right"></i>
          </button>
        </div>
      </div>
    `;
    container.hidden = false;
  }

  _pageNumbers(current, total) {
    const delta = 2;
    const start = Math.max(1, current - delta);
    const end = Math.min(total, current + delta);
    const out = [];

    if (start > 1) {
      out.push(`<button data-rp-page="1">1</button>`);
      if (start > 2) out.push(`<button disabled aria-hidden="true">…</button>`);
    }
    for (let p = start; p <= end; p++) {
      const cls = p === current ? ' class="is-active"' : "";
      const cur = p === current ? ' aria-current="page"' : "";
      out.push(`<button data-rp-page="${p}"${cls}${cur}>${p}</button>`);
    }
    if (end < total) {
      if (end < total - 1) out.push(`<button disabled aria-hidden="true">…</button>`);
      out.push(`<button data-rp-page="${total}">${total}</button>`);
    }
    return out.join("");
  }

  _showState(state, errMsg) {
    ["loading", "empty", "error"].forEach((s) => {
      const el = this.querySelector(`[data-rp-state="${s}"]`);
      if (el) el.hidden = s !== state;
    });

    if (state === "error" && errMsg) {
      const msgEl = this.querySelector("[data-rp-errmsg]");
      if (msgEl) msgEl.textContent = errMsg;
    }

    if (state !== null) {
      const tbody = this.querySelector("[data-rp-tbody]");
      if (tbody) tbody.innerHTML = "";
      const pager = this.querySelector("[data-rp-pagination]");
      if (pager) pager.hidden = true;
    }
  }

  _updateSortIcons() {
    this.querySelectorAll("[data-rp-sort-icon]").forEach((icon) => {
      const key = icon.getAttribute("data-rp-sort-icon");
      if (key === this._sortKey) {
        icon.className = `bi ${this._sortDir === "ASC" ? "bi-arrow-up" : "bi-arrow-down"} rp-sort-icon rp-sort-icon--active`;
      } else {
        icon.className = "bi bi-arrow-down-up rp-sort-icon";
      }
    });
  }

  _bindEvents() {
    const wrap = this.querySelector(".rp-table-wrap");
    if (!wrap) return;

    this._onDocClick = () => this._closeMenus();
    document.addEventListener("click", this._onDocClick);

    wrap.addEventListener("click", (e) => {
      // Sort header
      const sortEl = e.target.closest("[data-rp-sort]");
      if (sortEl) {
        const key = sortEl.getAttribute("data-rp-sort");
        this._sortDir = this._sortKey === key && this._sortDir === "ASC" ? "DESC" : "ASC";
        this._sortKey = key;
        this._updateSortIcons();
        if (this._apiUrl) this._loadData(1);
        return;
      }

      // Expand/collapse toggle
      const expandBtn = e.target.closest("[data-rp-expand-toggle]");
      if (expandBtn) {
        const idx = expandBtn.getAttribute("data-rp-expand-toggle");
        const detailRow = wrap.querySelector(`tr[data-rp-detail-row="${idx}"]`);
        if (detailRow) {
          const isOpen = !detailRow.hidden;
          detailRow.hidden = isOpen;
          expandBtn.setAttribute("aria-expanded", String(!isOpen));
          const icon = expandBtn.querySelector("i");
          if (icon) {
            icon.classList.toggle("bi-chevron-right", isOpen);
            icon.classList.toggle("bi-chevron-down", !isOpen);
          }
        }
        return;
      }

      // Pagination button
      const pageEl = e.target.closest("[data-rp-page]");
      if (pageEl && !pageEl.disabled) {
        const page = parseInt(pageEl.getAttribute("data-rp-page"), 10);
        if (!isNaN(page) && page !== this._currentPage) this._loadData(page);
        return;
      }

      // Action dispatch (inline & overflow)
      const actionEl = e.target.closest("[data-rp-action]");
      if (actionEl) {
        const evtName = actionEl.getAttribute("data-rp-action");
        const rowIdx = parseInt(actionEl.getAttribute("data-rp-row"), 10);
        if (evtName) {
          this.dispatchEvent(
            new CustomEvent(evtName, {
              bubbles: true,
              detail: { row: this._rows[rowIdx] ?? null, index: rowIdx },
            }),
          );
        }
        this._closeMenus();
        e.stopPropagation();
        return;
      }

      // "…" overflow toggle
      const moreBtn = e.target.closest(".rp-table-more-btn");
      if (moreBtn) {
        e.stopPropagation();
        const menu = moreBtn.closest(".rp-table-more-wrap")?.querySelector(".rp-table-more-menu");
        if (!menu) return;
        const wasOpen = menu.classList.contains("rp-dd-open");
        this._closeMenus();
        if (!wasOpen) {
          // Use position:fixed so the dropdown escapes overflow:hidden on the table wrapper
          const rect = moreBtn.getBoundingClientRect();
          menu.style.position = "fixed";
          menu.style.top = `${rect.bottom + 4}px`;
          menu.style.right = `${window.innerWidth - rect.right}px`;
          menu.style.left = "auto";
          menu.classList.add("rp-dd-open");
        }
        return;
      }
    });
  }

  _closeMenus() {
    this.querySelectorAll(".rp-table-more-menu.rp-dd-open").forEach((m) => {
      m.classList.remove("rp-dd-open");
      m.style.position = "";
      m.style.top = "";
      m.style.right = "";
      m.style.left = "";
    });
  }

  set rows(data) {
    this._applyRows(Array.isArray(data) ? data : [], null);
  }

  get rows() {
    return this._rows ?? [];
  }

  setRows(rows, pagination = null) {
    this._applyRows(rows, pagination);
  }

  refresh() {
    if (this._apiUrl) this._loadData(this._currentPage);
  }
}

customElements.define("data-table", DataTable);
