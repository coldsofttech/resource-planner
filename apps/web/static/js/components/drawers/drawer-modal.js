import { esc } from "../utils.js";

/* DrawerModal  <drawer-modal>
 *
 * A slide-in right-side panel (drawer) with a resizable handle, tab support,
 * and a structured header/body/footer. Configured entirely through declarative
 * child elements that are parsed once on connect, then replaced with rendered HTML.
 *
 * Declarative children (captured before first render):
 *   <drawer-header eyebrow="…" title="…" badge="…" badge-variant="…" [no-sizes]>
 *     Optional child: <identicon-field> or <user-avatar> — placed in the header avatar slot
 *   <drawer-tabs>
 *     <drawer-tab panel="panelName" [count="3"] [active]>Label</drawer-tab>
 *   </drawer-tabs>
 *   <drawer-panel name="panelName">  ← body content per tab
 *   <drawer-footer
 *     [meta="Updated …"]
 *     [close="Cancel"]
 *     [secondary="…"] [secondary-icon="bi-…"]
 *     [primary="Save"] [primary-icon="bi-…"]
 *   >
 *
 * Attributes:
 *   width  – initial drawer width in pixels (default 640); or "full"
 *
 * Public API:
 *   drawer.show()               – open the drawer
 *   drawer.hide()               – close the drawer
 *   drawer.setTab(panelName)    – switch to named panel tab
 *   drawer.setWidth(width)      – set width: number (px) or "full"
 *   drawer.setTitle(text)       – update the header title text (preserves badge if present)
 *
 * Events fired (all bubble):
 *   rp:open           – drawer opened
 *   rp:close          – drawer closed (backdrop, close button, footer close)
 *   rp:tab-change     – tab switched; detail: { panel: "panelName" }
 *   rp:resize         – width changed; detail: { width: number | "full" }
 *   rp:footer-close   – footer cancel/close button clicked
 *   rp:footer-secondary – footer secondary button clicked
 *   rp:footer-primary – footer primary/save button clicked
 *
 * Interactions:
 *   - Resize handle (left edge): drag to resize; double-click to reset to default width
 *   - Mobile: swipe down on the grab bar (top strip) to close
 *   - Backdrop click closes the drawer
 *   - Width snap buttons: 440 / 640 / 900 / full (hidden when no-sizes on drawer-header)
 */
class DrawerModal extends HTMLElement {
  connectedCallback() {
    this._defaultWidth = this._parseWidth(this.getAttribute("width") || "640");
    this._currentWidth = this._defaultWidth;
    this.classList.add("rp-rdrawer-back");
    this._capture();
    this._render();
    this._bindEvents();
  }

  // ── Public API ──────────────────────────────────────────────────────────

  show() {
    this.classList.add("is-open");
    this.dispatchEvent(new CustomEvent("rp:open", { bubbles: true }));
  }

  hide() {
    this.classList.remove("is-open");
    this.dispatchEvent(new CustomEvent("rp:close", { bubbles: true }));
  }

  setTab(panelName) {
    this.querySelectorAll(".rp-rdrawer-tab").forEach((btn) => {
      btn.classList.toggle("is-active", btn.dataset.panel === panelName);
    });
    this.querySelectorAll("[data-panel]").forEach((p) => {
      p.hidden = p.dataset.panel !== panelName;
    });
    this.dispatchEvent(
      new CustomEvent("rp:tab-change", { bubbles: true, detail: { panel: panelName } }),
    );
  }

  setWidth(width) {
    const drawer = this.querySelector(".rp-rdrawer");
    if (!drawer) return;
    this._currentWidth = width;
    drawer.style.width = width === "full" ? "calc(100vw - 24px)" : `${width}px`;
    this._syncSizeButtons();
    this.dispatchEvent(new CustomEvent("rp:resize", { bubbles: true, detail: { width } }));
  }

  setTitle(text) {
    const h3 = this.querySelector(".rp-rdrawer-titles h3");
    if (!h3) return;
    const badge = h3.querySelector(".rp-badge");
    h3.textContent = text;
    if (badge) h3.appendChild(badge);
  }

  // ── Internals ────────────────────────────────────────────────────────────

  _parseWidth(val) {
    if (val === "full") return "full";
    const n = parseInt(val, 10);
    return isNaN(n) ? 640 : n;
  }

  _capture() {
    const headerEl = this.querySelector("drawer-header");
    this._header = headerEl
      ? {
          eyebrow: headerEl.getAttribute("eyebrow") || "",
          title: headerEl.getAttribute("title") || "",
          badge: headerEl.getAttribute("badge") || "",
          badgeVariant: headerEl.getAttribute("badge-variant") || "neutral",
          noSizes: headerEl.hasAttribute("no-sizes"),
          avatarNode: headerEl.querySelector("identicon-field, user-avatar") || null,
          spanNode: headerEl.querySelector(":scope > span") || null,
        }
      : null;

    const tabsEl = this.querySelector("drawer-tabs");
    this._tabs = tabsEl
      ? Array.from(tabsEl.querySelectorAll("drawer-tab")).map((t) => ({
          panel: t.getAttribute("panel") || "",
          label: t.textContent.trim(),
          count: t.getAttribute("count") || "",
          active: t.hasAttribute("active"),
        }))
      : [];

    this._panels = Array.from(this.querySelectorAll("drawer-panel")).map((p) => ({
      name: p.getAttribute("name") || "",
      nodes: Array.from(p.childNodes),
    }));

    const footerEl = this.querySelector("drawer-footer");
    this._footer = footerEl
      ? {
          meta: footerEl.getAttribute("meta") || "",
          close: footerEl.getAttribute("close") || "",
          secondary: footerEl.getAttribute("secondary") || "",
          secondaryIcon: footerEl.getAttribute("secondary-icon") || "",
          primary: footerEl.getAttribute("primary") || "",
          primaryIcon: footerEl.getAttribute("primary-icon") || "",
        }
      : null;
  }

  _render() {
    const h = this._header;
    const f = this._footer;
    const hasTabs = this._tabs.length > 0;
    const activePanel = hasTabs
      ? (this._tabs.find((t) => t.active) || this._tabs[0]).panel
      : (this._panels[0]?.name ?? "");

    // Header
    const eyebrowHTML = h?.eyebrow ? `<div class="rp-rdrawer-eyebrow">${esc(h.eyebrow)}</div>` : "";
    const badgeHTML = h?.badge
      ? ` <span class="rp-badge rp-badge-soft rp-badge-${esc(h.badgeVariant)}">${esc(h.badge)}</span>`
      : "";
    const titleHTML = h?.title ? `<h3>${esc(h.title)}${badgeHTML}</h3>` : "";
    const sizesHTML = h?.noSizes
      ? ""
      : `<div class="rp-rdrawer-sizes" title="Drawer width">
           <button data-size="440" title="Narrow"><i class="bi bi-layout-sidebar-inset-reverse"></i></button>
           <button data-size="640" title="Medium"><i class="bi bi-layout-sidebar-reverse"></i></button>
           <button data-size="900" title="Large"><i class="bi bi-columns"></i></button>
           <button data-size="full" title="Wide"><i class="bi bi-fullscreen"></i></button>
         </div>`;

    const headHTML = `
      <div class="rp-rdrawer-head">
        <div class="rp-rdrawer-titles">${eyebrowHTML}${titleHTML}</div>
        <div class="rp-rdrawer-head-actions">
          ${sizesHTML}
          <button class="rp-iconbtn" data-close-drawer title="Close">
            <i class="bi bi-x-lg"></i>
          </button>
        </div>
      </div>`;

    // Tabs
    const tabsHTML = hasTabs
      ? `<div class="rp-rdrawer-tabs">
           ${this._tabs
             .map((t) => {
               const countHTML = t.count ? `<span class="rp-tab-count">${esc(t.count)}</span>` : "";
               const active = t.panel === activePanel ? " is-active" : "";
               return `<button class="rp-rdrawer-tab${active}" data-panel="${esc(t.panel)}">${esc(t.label)}${countHTML}</button>`;
             })
             .join("")}
         </div>`
      : "";

    // Body panels — empty placeholders; content re-inserted after render
    const panelsHTML = this._panels
      .map((p) => {
        const hidden = hasTabs && p.name !== activePanel ? " hidden" : "";
        return `<div data-panel="${esc(p.name)}"${hidden}></div>`;
      })
      .join("");
    const bodyHTML = `<div class="rp-rdrawer-body">${panelsHTML || '<div data-panel=""></div>'}</div>`;

    // Footer
    let footHTML = "";
    if (f) {
      const closeHTML = f.close
        ? `<muted-button label="${esc(f.close)}" data-footer-close></muted-button>`
        : "";
      const secHTML = f.secondary
        ? `<secondary-button label="${esc(f.secondary)}"${f.secondaryIcon ? ` prefix-icon="${esc(f.secondaryIcon)}"` : ""} data-footer-secondary></secondary-button>`
        : "";
      const priHTML = f.primary
        ? `<primary-button label="${esc(f.primary)}"${f.primaryIcon ? ` prefix-icon="${esc(f.primaryIcon)}"` : ""} data-footer-primary></primary-button>`
        : "";
      footHTML = `
        <div class="rp-rdrawer-foot">
          <span class="rp-rdrawer-foot-meta">${esc(f.meta)}</span>
          <div class="rp-rdrawer-foot-actions">${closeHTML}${secHTML}${priHTML}</div>
        </div>`;
    }

    const widthStyle =
      this._currentWidth === "full" ? "calc(100vw - 24px)" : `${this._currentWidth}px`;

    this.innerHTML = `
      <div class="rp-rdrawer sheet" role="dialog" aria-modal="true" style="width:${widthStyle}">
        <div class="rp-rdrawer-resize" title="Drag to resize · double-click to reset">
          <span class="grip"><i class="bi bi-grip-vertical"></i></span>
        </div>
        <div class="rp-rdrawer-grabber"></div>
        ${headHTML}
        ${tabsHTML}
        ${bodyHTML}
        ${footHTML}
      </div>`;

    this._syncSizeButtons();

    // Re-insert captured panel content
    this._panels.forEach((p) => {
      const slot = Array.from(this.querySelectorAll("[data-panel]")).find(
        (el) => el.dataset.panel === p.name,
      );
      if (slot) p.nodes.forEach((node) => slot.appendChild(node));
    });

    // Re-insert identicon or avatar node into the header avatar slot
    const avatarNode = this._header?.avatarNode;
    if (avatarNode) {
      const head = this.querySelector(".rp-rdrawer-head");
      const titles = head?.querySelector(".rp-rdrawer-titles");
      if (head && titles) {
        avatarNode.classList.add("rp-rdrawer-avatar");
        head.insertBefore(avatarNode, titles);
      }
    }

    // Re-insert <span> child from <drawer-header> into the title <h3>
    const spanNode = this._header?.spanNode;
    if (spanNode) {
      const h3 = this.querySelector(".rp-rdrawer-titles h3");
      if (h3) h3.appendChild(spanNode);
    }
  }

  _syncSizeButtons() {
    this.querySelectorAll("[data-size]").forEach((btn) => {
      const val = btn.dataset.size === "full" ? "full" : Number(btn.dataset.size);
      btn.classList.toggle("is-active", val === this._currentWidth);
    });
  }

  _bindEvents() {
    this.addEventListener("click", (e) => {
      // Backdrop
      if (e.target === this) {
        this.hide();
        return;
      }
      // Header close / any data-close-drawer
      if (e.target.closest("[data-close-drawer]")) {
        this.hide();
        return;
      }
      // Size snap buttons
      const sizeBtn = e.target.closest("[data-size]");
      if (sizeBtn) {
        this.setWidth(sizeBtn.dataset.size === "full" ? "full" : Number(sizeBtn.dataset.size));
        return;
      }
      // Tab buttons
      const tab = e.target.closest(".rp-rdrawer-tab");
      if (tab) {
        this.setTab(tab.dataset.panel);
        return;
      }
      // Footer close
      if (e.target.closest("[data-footer-close]")) {
        this.dispatchEvent(new CustomEvent("rp:footer-close", { bubbles: true }));
        this.hide();
        return;
      }
      // Footer secondary
      if (e.target.closest("[data-footer-secondary]")) {
        this.dispatchEvent(new CustomEvent("rp:footer-secondary", { bubbles: true }));
        return;
      }
      // Footer primary
      if (e.target.closest("[data-footer-primary]")) {
        this.dispatchEvent(new CustomEvent("rp:footer-primary", { bubbles: true }));
      }
    });

    // Resize drag
    const handle = this.querySelector(".rp-rdrawer-resize");
    if (handle) {
      handle.addEventListener("mousedown", (e) => this._startResize(e));
      handle.addEventListener("dblclick", () => this.setWidth(this._defaultWidth));
    }

    // Mobile grab-bar drag-to-close
    const grabber = this.querySelector(".rp-rdrawer-grabber");
    const drawerEl = this.querySelector(".rp-rdrawer");
    if (grabber && drawerEl) {
      let startY = 0;
      let dragY = 0;

      const resetDrag = () => {
        drawerEl.style.transition = "";
        drawerEl.style.transform = "";
      };

      grabber.addEventListener(
        "touchstart",
        (e) => {
          startY = e.touches[0].clientY;
          dragY = startY;
          drawerEl.style.transition = "none";
        },
        { passive: true },
      );

      grabber.addEventListener(
        "touchmove",
        (e) => {
          dragY = e.touches[0].clientY;
          const delta = Math.max(0, dragY - startY);
          drawerEl.style.transform = `translateY(${delta}px)`;
        },
        { passive: true },
      );

      grabber.addEventListener("touchend", () => {
        const delta = dragY - startY;
        if (delta > 80) {
          // Animate off-screen, then hide once settled
          drawerEl.style.transition = "transform 0.22s ease";
          drawerEl.style.transform = "translateY(100%)";
          drawerEl.addEventListener(
            "transitionend",
            () => {
              this.hide();
              resetDrag();
            },
            { once: true },
          );
        } else {
          resetDrag();
        }
      });

      grabber.addEventListener("touchcancel", resetDrag);
    }
  }

  _startResize(e) {
    e.preventDefault();
    const drawer = this.querySelector(".rp-rdrawer");
    const startX = e.clientX;
    const startW = drawer.getBoundingClientRect().width;
    const handle = this.querySelector(".rp-rdrawer-resize");

    handle.classList.add("is-dragging");
    document.body.classList.add("rp-resizing");

    const onMove = (ev) => {
      const newW = Math.min(
        Math.max(startW + (startX - ev.clientX), 360),
        window.innerWidth * 0.96,
      );
      drawer.style.width = `${newW}px`;
      this._currentWidth = Math.round(newW);
      this._syncSizeButtons();
    };

    const onUp = () => {
      handle.classList.remove("is-dragging");
      document.body.classList.remove("rp-resizing");
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
      this.dispatchEvent(
        new CustomEvent("rp:resize", {
          bubbles: true,
          detail: { width: this._currentWidth },
        }),
      );
    };

    document.addEventListener("mousemove", onMove);
    document.addEventListener("mouseup", onUp);
  }
}

customElements.define("drawer-modal", DrawerModal);
