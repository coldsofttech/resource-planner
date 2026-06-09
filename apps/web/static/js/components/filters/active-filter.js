import { esc } from "../utils.js";

/* ActiveFilter  <active-filter>
 *
 * Displays a row of removable tags for every currently-active filter,
 * plus a "Clear all" link that resets all filters at once.
 *
 * Attributes:
 *   for        – ID of the <filter-panel> element to observe (optional).
 *                When omitted the nearest <filter-panel> inside the same
 *                <list-view> ancestor is used automatically.
 *   read-only  – Boolean. When present, hides the per-tag remove (bi-x)
 *                buttons and the "Clear all" link so filters are display-only.
 *
 * The component hides itself (hidden attribute) when no filters are active
 * and re-renders whenever the linked <filter-panel> emits rp:filter:change.
 *
 * Usage (standalone):
 *   <active-filter for="my-filter"></active-filter>
 *   <filter-panel id="my-filter">...</filter-panel>
 *
 * Usage inside list-view with show-active-filters (auto-injected):
 *   <list-view show-active-filters>
 *     <filter-panel>...</filter-panel>
 *     <data-table>...</data-table>
 *   </list-view>
 */
export class ActiveFilter extends HTMLElement {
  connectedCallback() {
    // Defer discovery one microtask so that all siblings are connected and
    // upgraded before we query them.  list-view may also call setFilter()
    // explicitly — that call supersedes the auto-discovery below.
    Promise.resolve().then(() => {
      if (this._filter) return; // already wired (e.g. via setFilter)
      const found = this._findFilter();
      if (found) this.setFilter(found);
    });
  }

  disconnectedCallback() {
    if (this._filter && this._onChange) {
      this._filter.removeEventListener("rp:filter:change", this._onChange);
    }
  }

  /* ── Public wiring API (called by list-view or by connectedCallback) ── */

  setFilter(filter) {
    if (this._filter && this._onChange) {
      this._filter.removeEventListener("rp:filter:change", this._onChange);
    }
    this._filter = filter;
    this._onChange = () => this._render();
    this._filter.addEventListener("rp:filter:change", this._onChange);
    this._render();
  }

  /* ── Filter discovery ────────────────────────────────────────────────── */

  _findFilter() {
    const forId = this.getAttribute("for");
    if (forId) return document.getElementById(forId);

    const listView = this.closest("list-view");
    if (listView) return listView.querySelector("filter-panel");

    let sib = this.nextElementSibling;
    while (sib) {
      if (sib.tagName === "FILTER-PANEL") return sib;
      sib = sib.nextElementSibling;
    }
    return null;
  }

  /* ── Render ──────────────────────────────────────────────────────────── */

  _render() {
    const filter = this._filter;
    if (!filter?.getFilterLabels) {
      this.hidden = true;
      return;
    }

    const labels = filter.getFilterLabels();
    if (!labels || labels.length === 0) {
      this.hidden = true;
      this.innerHTML = "";
      return;
    }

    this.hidden = false;

    const readOnly = this.hasAttribute("read-only");

    const tagsHTML = labels
      .map((f) => {
        const displayValues = f.values.map((v) => esc(v.label)).join(", ");
        const removeBtn = readOnly
          ? ""
          : `<button type="button" aria-label="Remove ${esc(f.label)} filter" data-rp-remove="${esc(f.name)}">
            <i class="bi bi-x" aria-hidden="true"></i>
          </button>`;
        return `<span class="rp-tag" data-rp-active-name="${esc(f.name)}">
          <i class="bi bi-funnel" aria-hidden="true"></i>
          ${esc(f.label)}: ${displayValues}
          ${removeBtn}
        </span>`;
      })
      .join("");

    const clearAllHTML = readOnly
      ? ""
      : `<a class="rp-link rp-active-filter-clear" href="#" style="font-size:13px">Clear all</a>`;

    this.innerHTML = `
      <p class="rp-eyebrow rp-active-filter-eyebrow">Active filters</p>
      <div class="rp-active-filter-tags">
        ${tagsHTML}
        ${clearAllHTML}
      </div>
    `;

    this.querySelector(".rp-active-filter-clear")?.addEventListener("click", (e) => {
      e.preventDefault();
      filter.reset();
    });

    this.querySelectorAll("[data-rp-remove]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const name = btn.getAttribute("data-rp-remove");
        filter.clearFilter?.(name);
      });
    });
  }
}

customElements.define("active-filter", ActiveFilter);
