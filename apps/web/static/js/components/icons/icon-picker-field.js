import { BaseField } from "../fields/base-field.js";

/* IconPickerField: <icon-picker-field>
 *
 * Attributes (same conventions as other BaseField subclasses):
 *   id, name, label, value, required, hint, hint-type, col, disabled, placeholder
 *
 * Public API:
 *   el.value           → current icon name (without "bi-" prefix), e.g. "rocket-takeoff"
 *   el.value = "name"  → set programmatically
 *   el.open()          → open the picker panel
 *   el.close()         → close the picker panel
 *
 * Emits:
 *   change (bubbles)   → when the user selects a new icon
 *
 * Icon data is loaded lazily from /static/js/data/bootstrap-icons.json on the
 * first open. Generate that file with: scripts/build/generate_icons_json.py
 */
class IconPickerField extends BaseField {
  static get observedAttributes() {
    return [...super.observedAttributes, "disabled", "placeholder"];
  }

  // ── Singleton panel state ────────────────────────────────────────────────
  static _panel = null;
  static _backdrop = null;
  static _icons = null; // { all: [...], categories: [{id, label}], icons: {catId: [...]} }
  static _loadPromise = null;
  static _activeInstance = null;
  static _pendingValue = "";
  static _currentCat = "all";

  // ── Instance lifecycle ───────────────────────────────────────────────────
  connectedCallback() {
    this._pickerValue = this.getAttribute("value") || "";
    super.connectedCallback();
  }

  get _disabled() {
    return this.hasAttribute("disabled");
  }

  get _placeholder() {
    return this.getAttribute("placeholder") || "Select an icon";
  }

  get _value() {
    return this._pickerValue ?? (this.getAttribute("value") || "");
  }

  get value() {
    return this._value;
  }

  set value(v) {
    this._pickerValue = v || "";
    this._updateTrigger();
    if (this._touched) this._updateError();
  }

  _savedValue() {
    return this._pickerValue;
  }

  _restoreValue(val) {
    if (val === null) return;
    this._pickerValue = val;
    this._updateTrigger();
  }

  _validate() {
    if (this._required && !this._value) return "Please select an icon.";
    return this._runCustomValidators();
  }

  // ── Render ───────────────────────────────────────────────────────────────
  _buildHTML() {
    const v = this._value;
    const labelText = v ? `bi-${v}` : this._placeholder;
    const iconHTML = v
      ? `<i class="bi bi-${this._esc(v)}"></i>`
      : `<i class="bi bi-grid-3x3-gap" style="color:var(--rp-text-muted)"></i>`;
    const disabledAttr = this._disabled ? " disabled" : "";

    return `
      <div class="rp-field">
        ${this._labelHTML()}
        <button
          type="button"
          class="rp-iconpick"
          data-iconpick
          data-value="${this._esc(v)}"
          id="${this._esc(this._fieldId)}-input"
          aria-haspopup="dialog"
          aria-expanded="false"
          aria-label="Icon picker: ${this._esc(labelText)}"${disabledAttr}
        >
          <span class="rp-iconpick-preview">${iconHTML}</span>
          <span class="rp-iconpick-label">${this._esc(labelText)}</span>
          <i class="rp-iconpick-chev bi bi-chevron-down"></i>
        </button>
        <input
          type="hidden"
          name="${this._esc(this._name)}"
          value="${this._esc(v)}"
          data-iconpick-hidden
        />
        ${this._errorHTML()}
        ${this._hintHTML()}
      </div>
    `;
  }

  _updateTrigger() {
    const v = this._value;
    const btn = this.querySelector("[data-iconpick]");
    const hidden = this.querySelector("[data-iconpick-hidden]");
    const preview = this.querySelector(".rp-iconpick-preview");
    const labelEl = this.querySelector(".rp-iconpick-label");

    if (btn) btn.dataset.value = v;
    if (hidden) hidden.value = v;
    if (preview)
      preview.innerHTML = v
        ? `<i class="bi bi-${this._esc(v)}"></i>`
        : `<i class="bi bi-grid-3x3-gap" style="color:var(--rp-text-muted)"></i>`;
    if (labelEl) labelEl.textContent = v ? `bi-${v}` : this._placeholder;
    if (btn)
      btn.setAttribute(
        "aria-label",
        `Icon picker: ${v ? `bi-${this._esc(v)}` : this._placeholder}`,
      );
  }

  _bindEvents() {
    const btn = this.querySelector("[data-iconpick]");
    if (!btn) return;

    btn.addEventListener("click", () => {
      if (this._disabled) return;
      this.open();
    });

    btn.addEventListener("blur", () => {
      if (!IconPickerField._panel?.classList.contains("is-open")) {
        this._touched = true;
        this._updateError();
      }
    });
  }

  // ── Public API ───────────────────────────────────────────────────────────
  open() {
    IconPickerField._openFor(this);
  }

  close() {
    IconPickerField._closePanel();
  }

  // ── Singleton panel ──────────────────────────────────────────────────────
  static _getOrCreatePanel() {
    if (IconPickerField._panel) return IconPickerField._panel;

    const backdrop = document.createElement("div");
    backdrop.className = "rp-iconpick-backdrop";
    document.body.appendChild(backdrop);

    const panel = document.createElement("div");
    panel.className = "rp-iconpick-panel";
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-modal", "true");
    panel.setAttribute("aria-label", "Select icon");
    panel.innerHTML = `
      <div class="rp-iconpick-head">
        <div class="rp-iconpick-head-row">
          <strong>Select Icon</strong>
          <button type="button" class="rp-iconbtn" data-iconpick-close aria-label="Close panel">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
        <div class="rp-iconpick-search-wrap">
          <i class="bi bi-search"></i>
          <input
            type="text"
            class="rp-iconpick-search"
            placeholder="Search icons…"
            data-iconpick-search
            autocomplete="off"
            spellcheck="false"
            aria-label="Search icons"
          />
        </div>
        <div class="rp-iconpick-cats" data-iconpick-cats role="tablist" aria-label="Icon categories">
          <button class="rp-iconpick-cat is-active" data-cat="all" type="button" role="tab" aria-selected="true">All</button>
        </div>
      </div>
      <div class="rp-iconpick-grid" data-iconpick-grid role="listbox" aria-label="Icons" tabindex="0"></div>
      <div class="rp-iconpick-foot">
        <div class="rp-iconpick-current" data-iconpick-current>
          <span style="color:var(--rp-text-muted);font-size:12px">No icon selected</span>
        </div>
        <button type="button" class="rp-btn rp-btn-muted" data-iconpick-clear style="font-size:12px;height:28px;padding:0 10px">Clear</button>
      </div>
    `;
    document.body.appendChild(panel);

    IconPickerField._panel = panel;
    IconPickerField._backdrop = backdrop;

    // Close triggers
    backdrop.addEventListener("click", () => IconPickerField._closePanel());
    panel
      .querySelector("[data-iconpick-close]")
      .addEventListener("click", () => IconPickerField._closePanel());

    // Clear button
    panel.querySelector("[data-iconpick-clear]").addEventListener("click", () => {
      IconPickerField._pendingValue = "";
      IconPickerField._confirmSelection();
    });

    // Search
    panel.querySelector("[data-iconpick-search]").addEventListener("input", () => {
      IconPickerField._filterIcons();
    });

    // Category tabs (delegated)
    panel.querySelector("[data-iconpick-cats]").addEventListener("click", (e) => {
      const btn = e.target.closest("[data-cat]");
      if (!btn) return;
      IconPickerField._currentCat = btn.dataset.cat;
      panel.querySelectorAll("[data-cat]").forEach((b) => {
        const active = b === btn;
        b.classList.toggle("is-active", active);
        b.setAttribute("aria-selected", active);
      });
      panel.querySelector("[data-iconpick-search]").value = "";
      IconPickerField._filterIcons();
    });

    // Icon grid — single click confirms immediately
    panel.querySelector("[data-iconpick-grid]").addEventListener("click", (e) => {
      const item = e.target.closest("[data-icon]");
      if (!item) return;
      IconPickerField._pendingValue = item.dataset.icon;
      IconPickerField._confirmSelection();
    });

    // Keyboard navigation
    document.addEventListener("keydown", IconPickerField._onKeyDown, true);

    return panel;
  }

  static async _openFor(instance) {
    IconPickerField._activeInstance = instance;
    IconPickerField._pendingValue = instance._value;

    const panel = IconPickerField._getOrCreatePanel();
    const backdrop = IconPickerField._backdrop;

    // Mark trigger aria-expanded
    instance.querySelector("[data-iconpick]")?.setAttribute("aria-expanded", "true");

    // Load icon data once
    if (!IconPickerField._icons) {
      await IconPickerField._loadIcons(panel);
    }

    // Reset UI state
    const search = panel.querySelector("[data-iconpick-search]");
    if (search) search.value = "";
    IconPickerField._currentCat = "all";
    panel.querySelectorAll("[data-cat]").forEach((b) => {
      const active = b.dataset.cat === "all";
      b.classList.toggle("is-active", active);
      b.setAttribute("aria-selected", active);
    });

    IconPickerField._filterIcons();
    IconPickerField._updatePanelFooter();

    // Show
    panel.classList.add("is-open");
    backdrop.classList.add("is-open");
    IconPickerField._positionPanel(panel, instance.querySelector("[data-iconpick]"));

    // Don't auto-focus on mobile/tablet — triggering the keyboard immediately
    // causes iOS Safari to shrink the visual viewport while position:fixed;bottom:0
    // stays anchored to the layout viewport, hiding the panel behind the keyboard.
    if (window.innerWidth >= 768) requestAnimationFrame(() => search?.focus());

    // Reposition on scroll/resize (once per open cycle)
    IconPickerField._cleanupReposition?.();
    const onReposition = () =>
      IconPickerField._positionPanel(panel, instance.querySelector("[data-iconpick]"));
    window.addEventListener("scroll", onReposition, { passive: true, capture: true });
    window.addEventListener("resize", onReposition, { passive: true });
    IconPickerField._cleanupReposition = () => {
      window.removeEventListener("scroll", onReposition, { capture: true });
      window.removeEventListener("resize", onReposition);
    };
  }

  static _closePanel() {
    const panel = IconPickerField._panel;
    const backdrop = IconPickerField._backdrop;
    const inst = IconPickerField._activeInstance;

    if (panel) panel.classList.remove("is-open");
    if (backdrop) backdrop.classList.remove("is-open");
    if (inst) {
      inst.querySelector("[data-iconpick]")?.setAttribute("aria-expanded", "false");
      inst._touched = true;
      inst._updateError();
    }

    IconPickerField._cleanupReposition?.();
    IconPickerField._cleanupReposition = null;
    IconPickerField._activeInstance = null;
  }

  static _confirmSelection() {
    const inst = IconPickerField._activeInstance;
    if (inst) {
      const prev = inst._value;
      inst._pickerValue = IconPickerField._pendingValue;
      inst._updateTrigger();
      inst._touched = true;
      inst._updateError();
      if (inst._pickerValue !== prev) {
        inst.dispatchEvent(new Event("change", { bubbles: true }));
      }
    }
    IconPickerField._closePanel();
  }

  static _positionPanel(panel, trigger) {
    if (!trigger || window.innerWidth < 768) {
      // On mobile/tablet CSS @media (max-width: 767px) handles layout as a
      // bottom-sheet.  Clear any desktop CSS custom properties so they don't
      // bleed in if the viewport is resized from a wider size.
      panel.style.removeProperty("--rp-pick-left");
      panel.style.removeProperty("--rp-pick-top");
      return;
    }
    const rect = trigger.getBoundingClientRect();
    const panelW = 460;
    const panelH = Math.min(520, window.innerHeight * 0.8);
    const margin = 6;

    let left = rect.left;
    let top = rect.bottom + margin;

    if (left + panelW > window.innerWidth - 12) left = window.innerWidth - panelW - 12;
    if (left < 8) left = 8;
    if (top + panelH > window.innerHeight - 8) top = rect.top - panelH - margin;
    if (top < 8) top = 8;

    // Write position as CSS custom properties — NOT as inline left/top — so
    // the mobile @media rule can cleanly override without !important.
    panel.style.setProperty("--rp-pick-left", `${left}px`);
    panel.style.setProperty("--rp-pick-top", `${top}px`);
  }

  // ── Icon data ────────────────────────────────────────────────────────────
  static async _loadIcons(panel) {
    if (IconPickerField._loadPromise) return IconPickerField._loadPromise;

    const grid = panel.querySelector("[data-iconpick-grid]");
    grid.innerHTML = `<div class="rp-iconpick-empty"><i class="bi bi-hourglass-split"></i>Loading icons…</div>`;

    IconPickerField._loadPromise = fetch("/static/js/data/bootstrap-icons.json")
      .then((r) => {
        if (!r.ok) throw new Error(r.status);
        return r.json();
      })
      .then((data) => {
        IconPickerField._icons = data;

        // Populate category tabs (skip "all" — already in HTML)
        const catsEl = panel.querySelector("[data-iconpick-cats]");
        (data.categories || []).forEach((cat) => {
          if (cat.id === "all") return;
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "rp-iconpick-cat";
          btn.dataset.cat = cat.id;
          btn.textContent = cat.label;
          btn.setAttribute("role", "tab");
          btn.setAttribute("aria-selected", "false");
          catsEl.appendChild(btn);
        });
      })
      .catch(() => {
        IconPickerField._loadPromise = null;
        grid.innerHTML = `<div class="rp-iconpick-empty"><i class="bi bi-exclamation-triangle"></i>Could not load icon list.</div>`;
      });

    return IconPickerField._loadPromise;
  }

  // ── Filtering & rendering ────────────────────────────────────────────────
  static _filterIcons() {
    const panel = IconPickerField._panel;
    if (!panel || !IconPickerField._icons) return;

    const grid = panel.querySelector("[data-iconpick-grid]");
    const query = (panel.querySelector("[data-iconpick-search]")?.value || "").toLowerCase().trim();
    const cat = IconPickerField._currentCat;

    let icons =
      cat === "all" ? IconPickerField._icons.all : IconPickerField._icons.icons?.[cat] || [];

    if (query) icons = icons.filter((n) => n.includes(query));

    if (!icons.length) {
      const empty = document.createElement("div");
      empty.className = "rp-iconpick-empty";
      const searchIcon = document.createElement("i");
      searchIcon.className = "bi bi-search";
      empty.appendChild(searchIcon);
      if (query) {
        empty.appendChild(document.createTextNode('No icons match "'));
        const strong = document.createElement("strong");
        strong.textContent = query;
        empty.appendChild(strong);
        empty.appendChild(document.createTextNode('"'));
      } else {
        empty.appendChild(document.createTextNode("No icons in this category."));
      }
      grid.replaceChildren(empty);
      return;
    }

    const selected = IconPickerField._pendingValue;

    // Render first batch immediately, load more lazily as user scrolls
    const BATCH = 300;
    grid.innerHTML = IconPickerField._renderItems(icons.slice(0, BATCH), selected);
    grid.scrollTop = 0;

    if (icons.length > BATCH) {
      let offset = BATCH;
      const sentinel = document.createElement("div");
      sentinel.dataset.sentinel = "";
      sentinel.style.cssText = "height:1px;grid-column:1/-1";
      grid.appendChild(sentinel);

      const io = new IntersectionObserver(
        (entries) => {
          if (!entries[0].isIntersecting || offset >= icons.length) {
            io.disconnect();
            return;
          }
          const frag = document.createDocumentFragment();
          const tmp = document.createElement("div");
          tmp.innerHTML = IconPickerField._renderItems(
            icons.slice(offset, offset + BATCH),
            selected,
          );
          while (tmp.firstChild) frag.appendChild(tmp.firstChild);
          sentinel.before(frag);
          offset += BATCH;
          if (offset >= icons.length) io.disconnect();
        },
        { root: grid, threshold: 0 },
      );
      io.observe(sentinel);
    }

    // Scroll selected item into view
    requestAnimationFrame(() => {
      const sel = grid.querySelector(".is-selected");
      if (sel) sel.scrollIntoView({ block: "nearest" });
    });
  }

  static _renderItems(names, selected) {
    return names
      .map((name) => {
        const isSel = name === selected;
        return `<button
          type="button"
          class="rp-iconpick-item${isSel ? " is-selected" : ""}"
          data-icon="${name}"
          title="bi-${name}"
          role="option"
          aria-label="bi-${name}"
          aria-selected="${isSel}"
        ><i class="bi bi-${name}"></i></button>`;
      })
      .join("");
  }

  static _updatePanelFooter() {
    const panel = IconPickerField._panel;
    if (!panel) return;
    const v = IconPickerField._pendingValue;
    const foot = panel.querySelector("[data-iconpick-current]");
    if (!foot) return;
    if (v) {
      foot.innerHTML = `<i class="bi bi-${v}"></i><span class="name">bi-${v}</span>`;
    } else {
      foot.innerHTML = `<span style="color:var(--rp-text-muted);font-size:12px">No icon selected</span>`;
    }
  }

  // ── Keyboard ─────────────────────────────────────────────────────────────
  static _onKeyDown = (e) => {
    const panel = IconPickerField._panel;
    if (!panel?.classList.contains("is-open")) return;

    if (e.key === "Escape") {
      e.preventDefault();
      e.stopPropagation();
      IconPickerField._closePanel();
      return;
    }

    const grid = panel.querySelector("[data-iconpick-grid]");
    const focused = document.activeElement;
    const items = Array.from(grid.querySelectorAll("[data-icon]"));

    if (!items.length) return;

    if (["ArrowRight", "ArrowLeft", "ArrowDown", "ArrowUp"].includes(e.key)) {
      e.preventDefault();
      const idx = items.indexOf(focused);
      const cols = Math.round(grid.clientWidth / 48) || 1;
      const delta =
        e.key === "ArrowRight"
          ? 1
          : e.key === "ArrowLeft"
            ? -1
            : e.key === "ArrowDown"
              ? cols
              : -cols;
      const next = items[Math.max(0, Math.min(items.length - 1, idx + delta))];
      next?.focus();
    }

    if (e.key === "Enter" && focused?.dataset?.icon) {
      e.preventDefault();
      IconPickerField._pendingValue = focused.dataset.icon;
      IconPickerField._confirmSelection();
    }

    if (e.key === "Tab" && !e.shiftKey) {
      // Trap focus inside panel
      const focusable = panel.querySelectorAll(
        "button:not([disabled]), input:not([disabled]), [tabindex='0']",
      );
      const last = focusable[focusable.length - 1];
      if (document.activeElement === last) {
        e.preventDefault();
        focusable[0]?.focus();
      }
    }
  };
}

customElements.define("icon-picker-field", IconPickerField);
