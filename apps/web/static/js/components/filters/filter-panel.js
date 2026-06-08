import { esc } from "../utils.js";

/* FilterPanel  <filter-panel>
 *
 * Attributes:
 *   layout  – "horizontal" (default) | "vertical"
 *
 * ── Horizontal mode ──────────────────────────────────────────────────────
 * CSS flex row.  Direct children must expose .value and a "name" attribute
 * (search-field, is-active-field, dropdown-field, etc.).
 * Emits rp:filter:change when:
 *   - rp:search fires (Enter on a search field)
 *   - a search input is cleared (input event, empty value)
 *   - a select changes (change event on a <select>)
 *
 * ── Vertical mode ────────────────────────────────────────────────────────
 * Renders a filterpane from declarative children:
 *   <filter-group name="status" label="Status" [open]>
 *     <filter-option value="active" [count="14"] [checked]>Active</filter-option>
 *   </filter-group>
 * Features: accordion groups, meta-search, Reset button, selected-count badges.
 * Emits rp:filter:change when any checkbox changes or Reset is clicked.
 *
 * Public API:
 *   filter.getParams()  → URLSearchParams of current filter state
 *   filter.reset()      → clear all filter state and emit rp:filter:change
 *
 * Emits:
 *   rp:filter:change (bubbles)  detail: { params: URLSearchParams }
 */
export class FilterPanel extends HTMLElement {
  get _layout() {
    return this.getAttribute("layout") || "horizontal";
  }

  connectedCallback() {
    this._connected = true;

    if (this._layout === "vertical") {
      if (this._groups === undefined) this._groups = this._readGroups();
      this._renderVertical();
      this._bindVerticalEvents();
    } else {
      this._bindHorizontalEvents();
    }
  }

  /* ── Declarative children (vertical mode) ────────────────────────────── */

  _readGroups() {
    return Array.from(this.querySelectorAll("filter-group")).map((g) => ({
      name: g.getAttribute("name") || "",
      label: g.getAttribute("label") || "",
      open: g.hasAttribute("open"),
      options: Array.from(g.querySelectorAll("filter-option")).map((o) => ({
        value: o.getAttribute("value") || o.textContent.trim(),
        label: o.textContent.trim(),
        count: o.getAttribute("count") || "",
        checked: o.hasAttribute("checked"),
      })),
    }));
  }

  /* ── Vertical render ─────────────────────────────────────────────────── */

  _renderVertical() {
    const groupsHTML = (this._groups || []).map((g, gi) => this._buildGroupHTML(g, gi)).join("");

    this.innerHTML = `
      <div class="rp-filterpane">
        <div class="rp-filterpane-head">
          <strong style="font-size:14px">Filters</strong>
          <button class="rp-btn rp-btn-muted rp-btn-sm" data-rp-reset>Reset</button>
        </div>
        <div class="rp-filterpane-body">
          <div class="rp-input-affix mb-3">
            <i class="bi bi-search rp-prefix"></i>
            <input class="rp-input" placeholder="Filter filters" data-rp-meta autocomplete="off" />
          </div>
          ${groupsHTML}
        </div>
      </div>`;
  }

  _buildGroupHTML(g, gi) {
    const openCls = g.open ? " is-open" : "";
    const checkedCount = g.options.filter((o) => o.checked).length;
    const badgeHTML =
      checkedCount > 0
        ? `<span class="rp-badge rp-badge-soft rp-badge-neutral ms-auto">${checkedCount}</span>`
        : "";

    const optionsHTML = g.options
      .map((o) => {
        const checkedAttr = o.checked ? " checked" : "";
        const countHTML = o.count
          ? `<span class="ms-auto rp-subtle rp-mono" style="font-size:11px">${esc(o.count)}</span>`
          : "";
        return `<label class="rp-field-row mb-2">
            <input type="checkbox" class="rp-check"${checkedAttr} value="${esc(o.value)}" data-rp-gi="${gi}" />
            <span>${esc(o.label)}</span>
            ${countHTML}
          </label>`;
      })
      .join("");

    return `
      <div class="rp-filter-group" data-rp-group="${esc(g.name)}">
        <button class="rp-accordion-trigger${openCls}" style="font-size:13px" data-rp-toggle="${gi}">
          <i class="bi bi-chevron-right"></i>${esc(g.label)}${badgeHTML}
        </button>
        <div class="rp-accordion-body">${optionsHTML}</div>
      </div>`;
  }

  /* ── Vertical events ─────────────────────────────────────────────────── */

  _bindVerticalEvents() {
    this.addEventListener("click", (e) => {
      if (e.target.closest("[data-rp-reset]")) {
        this.reset();
        return;
      }
      const trigger = e.target.closest("[data-rp-toggle]");
      if (trigger) trigger.classList.toggle("is-open");
    });

    this.addEventListener("change", (e) => {
      if (!e.target.classList.contains("rp-check")) return;
      const gi = parseInt(e.target.getAttribute("data-rp-gi"), 10);
      const group = (this._groups || [])[gi];
      if (group) {
        const opt = group.options.find((o) => o.value === e.target.value);
        if (opt) opt.checked = e.target.checked;
        this._syncBadge(gi);
      }
      this._emitChange();
    });

    this.addEventListener("input", (e) => {
      if (!e.target.hasAttribute("data-rp-meta")) return;
      const q = e.target.value.toLowerCase();
      this.querySelectorAll(".rp-filter-group").forEach((g) => {
        const label = g.querySelector(".rp-accordion-trigger")?.textContent.toLowerCase() ?? "";
        g.hidden = !!q && !label.includes(q);
      });
    });
  }

  _syncBadge(gi) {
    const groups = Array.from(this.querySelectorAll("[data-rp-group]"));
    const el = groups[gi];
    if (!el) return;
    const trigger = el.querySelector("[data-rp-toggle]");
    if (!trigger) return;

    const checked = el.querySelectorAll(".rp-check:checked").length;
    let badge = trigger.querySelector(".rp-badge");

    if (checked > 0) {
      if (badge) {
        badge.textContent = checked;
      } else {
        trigger.insertAdjacentHTML(
          "beforeend",
          `<span class="rp-badge rp-badge-soft rp-badge-neutral ms-auto">${checked}</span>`,
        );
      }
    } else {
      badge?.remove();
    }
  }

  /* ── Horizontal events ───────────────────────────────────────────────── */

  _bindHorizontalEvents() {
    let _debounce;

    // Enter key in search field triggers immediate update
    this.addEventListener("rp:search", () => {
      clearTimeout(_debounce);
      this._emitChange();
    });

    // Typing in search field triggers debounced update
    this.addEventListener("input", (e) => {
      if (e.target.type === "search") {
        clearTimeout(_debounce);
        _debounce = setTimeout(() => this._emitChange(), 400);
      }
    });

    this.addEventListener("change", (e) => {
      if (e.target.tagName === "SELECT") this._emitChange();
    });
  }

  /* ── Public API ──────────────────────────────────────────────────────── */

  /*
   * Returns human-readable label metadata for currently active filters.
   * Each entry: { name, label, values: [{ value, label }] }
   */
  getFilterLabels() {
    if (this._layout === "vertical") {
      return (this._groups || [])
        .filter((g) => g.options.some((o) => o.checked))
        .map((g) => ({
          name: g.name,
          label: g.label,
          values: g.options
            .filter((o) => o.checked)
            .map((o) => ({ value: o.value, label: o.label })),
        }));
    }

    const result = [];
    Array.from(this.children).forEach((child) => {
      const name = child.getAttribute?.("param") || child.getAttribute?.("name");
      if (!name) return;
      const value = String(child.value ?? "");
      if (!value) return;
      const label =
        child.getAttribute?.("label") ||
        child.getAttribute?.("filter-label") ||
        this._humanize(name);
      const select = child.querySelector?.("select");
      let displayValue = value;
      if (select) {
        const opt = Array.from(select.options).find((o) => o.value === value);
        if (opt?.text) displayValue = opt.text;
      }
      result.push({ name, label, values: [{ value, label: displayValue }] });
    });
    return result;
  }

  /*
   * Clear a specific filter by its param/name.
   * Horizontal: resets the matching field child.
   * Vertical: unchecks all options in the matching group.
   */
  clearFilter(name) {
    if (this._layout === "vertical") {
      const groups = Array.from(this.querySelectorAll("[data-rp-group]"));
      const groupEl = groups.find((g) => g.getAttribute("data-rp-group") === name);
      if (!groupEl) return;
      groupEl.querySelectorAll(".rp-check").forEach((cb) => (cb.checked = false));
      const gi = groups.indexOf(groupEl);
      if (this._groups?.[gi]) {
        this._groups[gi].options.forEach((o) => (o.checked = false));
        this._syncBadge(gi);
      }
    } else {
      const child = Array.from(this.children).find(
        (c) => c.getAttribute?.("param") === name || c.getAttribute?.("name") === name,
      );
      if (!child) return;
      const input = child.querySelector?.(".rp-input");
      if (input) input.value = "";
      const select = child.querySelector?.("select");
      if (select) select.selectedIndex = 0;
    }
    this._emitChange();
  }

  _humanize(name) {
    return String(name)
      .replace(/_/g, " ")
      .replace(/\b\w/g, (c) => c.toUpperCase());
  }

  getParams() {
    const params = new URLSearchParams();

    if (this._layout === "vertical") {
      this.querySelectorAll("[data-rp-group]").forEach((groupEl) => {
        const name = groupEl.getAttribute("data-rp-group");
        groupEl.querySelectorAll(".rp-check:checked").forEach((cb) => {
          params.append(name, cb.value);
        });
      });
    } else {
      Array.from(this.children).forEach((child) => {
        const name = child.getAttribute?.("param") || child.getAttribute?.("name");
        if (!name) return;
        const value = String(child.value ?? "");
        if (value !== "") params.set(name, value);
      });
    }

    return params;
  }

  reset() {
    if (this._layout === "vertical") {
      this.querySelectorAll(".rp-check").forEach((cb) => {
        cb.checked = false;
      });
      (this._groups || []).forEach((g) => g.options.forEach((o) => (o.checked = false)));
      Array.from(this.querySelectorAll("[data-rp-group]")).forEach((_, i) => this._syncBadge(i));
    } else {
      Array.from(this.children).forEach((child) => {
        const input = child.querySelector?.(".rp-input");
        if (input) input.value = "";
        const select = child.querySelector?.("select");
        if (select) select.selectedIndex = 0;
      });
    }
    this._emitChange();
  }

  /* ── Helpers ─────────────────────────────────────────────────────────── */

  _emitChange() {
    this.dispatchEvent(
      new CustomEvent("rp:filter:change", {
        bubbles: true,
        detail: { params: this.getParams() },
      }),
    );
  }
}

customElements.define("filter-panel", FilterPanel);
