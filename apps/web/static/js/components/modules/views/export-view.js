import { esc } from "../../utils.js";
import { apiFetch } from "../../../modules/utils/utils.js";

/* ExportView  <export-view>
 *
 * Self-contained export workflow rendered inside a large <drawer-modal>.
 * On open: wires the read-only active-filter and fetches specs-url to populate
 * the column list.  Export button dispatches rp:export — actual download not
 * wired yet.
 *
 * Attributes:
 *   title            – drawer title (default: "Export")
 *   eyebrow          – drawer eyebrow text (optional)
 *   active-filter-id – ID of the <active-filter> (or <filter-panel>) whose
 *                      active filters are mirrored read-only inside the drawer.
 *                      When omitted the filter row is hidden.
 *   specs-url        – GET endpoint returning { data: { columns: [{ key, label, default }] } }
 *                      Columns with default: false are unchecked; all others are checked.
 *   export-url       – GET endpoint for the actual export download (reserved for later)
 *
 * Public API:
 *   view.show()  – opens the drawer
 *   view.hide()  – closes the drawer
 *
 * Events:
 *   rp:export (bubbles) – fired when Export is clicked; detail: { format, columns }
 *
 * Usage:
 *   <export-view id="teams-export"
 *     title="Export Teams"
 *     eyebrow="Teams"
 *     active-filter-id="rp-teams-active-filter"
 *     specs-url="/api/v1/teams/export/specs/"
 *     export-url="/api/v1/teams/export/"
 *     table-id="rp-teams-table">
 *   </export-view>
 *
 *   document.getElementById("rp-teams-export-btn").addEventListener("click", () => {
 *     document.getElementById("teams-export").show();
 *   });
 */
class ExportView extends HTMLElement {
  connectedCallback() {
    if (this._connected) return;
    this._connected = true;
    this._selectedFormat = "csv";
    this._render();
    this._bindEvents();
  }

  show() {
    this.querySelector("drawer-modal")?.show();
  }

  hide() {
    this.querySelector("drawer-modal")?.hide();
  }

  // --- Render ---

  _render() {
    const title = esc(this.getAttribute("title") || "Export");
    const eyebrow = this.getAttribute("eyebrow");
    const eyebrowAttr = eyebrow ? ` eyebrow="${esc(eyebrow)}"` : "";
    const hasFilter = !!this.getAttribute("active-filter-id");

    const filtersRow = hasFilter
      ? `<div class="mb-3" data-export-filters><active-filter read-only></active-filter></div>`
      : "";

    const formats = [
      { value: "csv", icon: "bi-filetype-csv", label: "CSV" },
      { value: "xlsx", icon: "bi-filetype-xlsx", label: "XLSX" },
      { value: "pdf", icon: "bi-filetype-pdf", label: "PDF" },
      { value: "json", icon: "bi-filetype-json", label: "JSON" },
    ];

    const formatsHTML = formats
      .map((f) => {
        const isActive = f.value === this._selectedFormat;
        const activeStyle = isActive
          ? ` style="background:var(--rp-accent-soft);color:var(--rp-accent-soft-text);border-color:transparent"`
          : "";
        const segmentClass = isActive ? " rp-segment-btn" : "";
        return `<button class="rp-btn rp-btn-secondary rp-btn-sm${segmentClass}" data-format="${f.value}"${activeStyle}>
          <i class="bi ${f.icon}" aria-hidden="true"></i>${esc(f.label)}
        </button>`;
      })
      .join("");

    this.innerHTML = `
      <drawer-modal width="900">
        <drawer-header${eyebrowAttr} title="${title}" no-sizes></drawer-header>
        <drawer-panel name="main">
          ${filtersRow}

          <div class="d-flex gap-2 mb-3" data-export-formats>
            ${formatsHTML}
          </div>

          <div class="rp-card">
            <div class="rp-card-body">
              <div class="d-flex align-items-center justify-content-between mb-2">
                <strong style="font-size:13px">Columns</strong>
                <div class="d-flex gap-2">
                  <a href="#" class="rp-link" style="font-size:12px" data-select-all>Select all</a>
                  <a href="#" class="rp-link" style="font-size:12px" data-clear-all>Clear all</a>
                </div>
              </div>
              <div data-export-columns style="max-height:260px;overflow-y:auto" class="rp-stack-8">
                <span style="font-size:13px;color:var(--rp-text-muted)">Loading columns…</span>
              </div>
            </div>
          </div>
        </drawer-panel>
        <drawer-footer close="Cancel" primary="Export" primary-icon="bi-download"></drawer-footer>
      </drawer-modal>
    `;
  }

  // --- Event binding ---

  _bindEvents() {
    const drawer = this.querySelector("drawer-modal");

    drawer?.addEventListener("rp:open", () => {
      this._wireFilter();
      this._loadSpecs();
    });

    this.querySelector("[data-export-formats]")?.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-format]");
      if (!btn) return;
      this._selectedFormat = btn.dataset.format;
      this.querySelectorAll("[data-format]").forEach((b) => {
        const active = b === btn;
        b.style.background = active ? "var(--rp-accent-soft)" : "";
        b.style.color = active ? "var(--rp-accent-soft-text)" : "";
        b.style.borderColor = active ? "transparent" : "";
        b.classList.toggle("rp-segment-btn", active);
      });
    });

    this.addEventListener("click", (e) => {
      if (e.target.closest("[data-select-all]")) {
        e.preventDefault();
        this.querySelectorAll("[data-export-columns] .rp-check").forEach((cb) => {
          cb.checked = true;
        });
        this._syncExportBtn();
        return;
      }
      if (e.target.closest("[data-clear-all]")) {
        e.preventDefault();
        this.querySelectorAll("[data-export-columns] .rp-check").forEach((cb) => {
          cb.checked = false;
        });
        this._syncExportBtn();
      }
    });

    this.addEventListener("change", (e) => {
      if (e.target.classList.contains("rp-check")) this._syncExportBtn();
    });

    drawer?.addEventListener("rp:footer-primary", () => this._onExport());
  }

  // --- Filter wiring ---

  _wireFilter() {
    const filterId = this.getAttribute("active-filter-id");
    if (!filterId) return;

    const el = document.getElementById(filterId);
    if (!el) return;

    // Accept either a <filter-panel> directly or an <active-filter> (read its ._filter)
    const filterPanel = el.tagName === "FILTER-PANEL" ? el : el._filter;
    if (!filterPanel) return;

    this.querySelector("[data-export-filters] active-filter")?.setFilter(filterPanel);
  }

  // --- Specs ---

  async _loadSpecs() {
    const specsUrl = this.getAttribute("specs-url");
    const columnsEl = this.querySelector("[data-export-columns]");

    if (!specsUrl) {
      if (columnsEl)
        columnsEl.innerHTML = `<span style="font-size:13px;color:var(--rp-text-muted)">No columns configured.</span>`;
      return;
    }

    try {
      const res = await apiFetch(specsUrl);
      const specs = res?.data ?? res;
      this._renderColumns(specs?.columns ?? []);
    } catch {
      if (columnsEl)
        columnsEl.innerHTML = `<span style="font-size:13px;color:var(--rp-text-muted)">Unable to load columns.</span>`;
    }
  }

  _renderColumns(columns) {
    const columnsEl = this.querySelector("[data-export-columns]");
    if (!columnsEl) return;

    if (!columns.length) {
      columnsEl.innerHTML = `<span style="font-size:13px;color:var(--rp-text-muted)">No columns available.</span>`;
      return;
    }

    columnsEl.innerHTML = columns
      .map((col) => {
        const checked = col.default !== false;
        return `<label class="rp-field-row">
          <input type="checkbox" class="rp-check" data-column-key="${esc(col.key)}"${checked ? " checked" : ""} />
          <span>${esc(col.label)}</span>
        </label>`;
      })
      .join("");

    this._syncExportBtn();
  }

  // --- Export button state ---

  _syncExportBtn() {
    const anyChecked = !!this.querySelector("[data-export-columns] .rp-check:checked");
    this.querySelector("[data-footer-primary]")?.toggleAttribute("disabled", !anyChecked);
  }

  // --- Export ---

  _onExport() {
    const columns = [...this.querySelectorAll("[data-export-columns] .rp-check")]
      .filter((cb) => cb.checked)
      .map((cb) => cb.dataset.columnKey);

    const exportUrl = this.getAttribute("export-url");
    if (exportUrl) {
      const url = new URL(exportUrl, window.location.origin);
      url.searchParams.set("type", this._selectedFormat);
      if (columns.length) url.searchParams.set("fields", columns.join(","));

      const filterId = this.getAttribute("active-filter-id");
      if (filterId) {
        const el = document.getElementById(filterId);
        const filterPanel = el?.tagName === "FILTER-PANEL" ? el : el?._filter;
        filterPanel?.getParams?.().forEach((value, key) => url.searchParams.set(key, value));
      }

      window.location.href = url.toString();
    }

    this.dispatchEvent(
      new CustomEvent("rp:export", {
        bubbles: true,
        detail: { format: this._selectedFormat, columns },
      }),
    );
  }
}

customElements.define("export-view", ExportView);
