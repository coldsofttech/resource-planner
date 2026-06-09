/* ListView  <list-view>
 *
 * Coordinator that connects a <filter-panel> child to a <data-table> child.
 * When the filter emits rp:filter:change, this element builds the new URL
 * (base URL + filter params) and sets it on the table, triggering a reload.
 *
 * Attributes:
 *   layout             – "horizontal" (default) | "vertical"
 *                        horizontal: filter bar above table (column stack)
 *                        vertical:   filterpane beside table (side-by-side row)
 *   show-active-filters – boolean; when present, auto-injects an
 *                        <active-filter> before <filter-panel> that shows
 *                        a dismissable tag for every active filter.
 *
 * Usage (horizontal, with active filter row):
 *   <list-view show-active-filters>
 *     <filter-panel>
 *       <search-field name="search" ...></search-field>
 *       <is-active-field name="is_active" label="Status"></is-active-field>
 *     </filter-panel>
 *     <data-table url="/api/v1/teams/" paginated ...>
 *       <table-columns>...</table-columns>
 *       <table-actions>...</table-actions>
 *     </data-table>
 *   </list-view>
 *
 *   <list-view layout="vertical" show-active-filters>
 *     <filter-panel layout="vertical">
 *       <filter-group name="status" label="Status" open>
 *         <filter-option value="true" count="12">Active</filter-option>
 *         <filter-option value="false" count="3">Inactive</filter-option>
 *       </filter-group>
 *     </filter-panel>
 *     <data-table url="/api/v1/teams/" ...>...</data-table>
 *   </list-view>
 */
class ListView extends HTMLElement {
  connectedCallback() {
    const table = this.querySelector("data-table");
    const filter = this.querySelector("filter-panel");

    if (table) this._baseUrl = table.getAttribute("url") || "";

    if (this.hasAttribute("show-active-filters") && filter) {
      this._injectActiveFilter(filter);
    }

    if (filter && table) {
      filter.addEventListener("rp:filter:change", (e) => {
        const params = e.detail?.params;
        if (!params) return;

        const qs = params.toString();
        const url = qs
          ? `${this._baseUrl}${this._baseUrl.includes("?") ? "&" : "?"}${qs}`
          : this._baseUrl;

        table.setAttribute("url", url);
      });
    }
  }

  _injectActiveFilter(filter) {
    let af = this.querySelector("active-filter");
    if (!af) {
      af = document.createElement("active-filter");
      this.insertBefore(af, filter);
    }
    // Explicitly wire the filter reference — avoids timing dependence on
    // connectedCallback auto-discovery.
    af.setFilter?.(filter);
  }
}

customElements.define("list-view", ListView);
