import { esc } from "../utils.js";

/* MenuBar: <menu-bar>
 *
 * Renders the application navigation bar from a declarative child structure.
 * Children are parsed once on connect, then replaced with rendered nav HTML.
 *
 * Dropdown panels are rendered as direct siblings of the scrollable nav container
 * so they escape the overflow-x scroll context and display correctly.
 *
 * <menu-item> attributes:  id, name, href, icon
 * <menu-group> attributes: id, name, icon, cols (number of mega-menu columns, default 1)
 * <menu-section> attributes: label
 *
 * Active state: items whose href exactly matches or is a prefix of the current
 * pathname automatically receive the is-active class.
 *
 * Mobile: a hamburger toggle button is rendered and shown only on narrow viewports.
 * Clicking it toggles the rp-mobile-open class on the host element.
 */
class MenuBar extends HTMLElement {
  connectedCallback() {
    this.classList.add("rp-menubar");
    this.setAttribute("role", "navigation");

    if (this._items === undefined) {
      this._items = this._parseItems();
    }

    this._render();
    this._bindEvents();
  }

  disconnectedCallback() {
    document.removeEventListener("click", this._onOutsideClick);
    document.removeEventListener("keydown", this._onDocKeyDown);
  }

  _parseItems() {
    const container = this.querySelector("menu-items");
    if (!container) return [];

    return Array.from(container.children)
      .map((el) => {
        const tag = el.tagName.toLowerCase();

        if (tag === "menu-item") {
          return {
            type: "item",
            id: el.id || "",
            name: el.getAttribute("name") || "",
            href: el.getAttribute("href") || "#",
            icon: el.getAttribute("icon") || "",
          };
        }

        if (tag === "menu-group") {
          return {
            type: "group",
            id: el.id || "",
            name: el.getAttribute("name") || "",
            icon: el.getAttribute("icon") || "",
            cols: parseInt(el.getAttribute("cols") || "1", 10) || 1,
            sections: Array.from(el.querySelectorAll("menu-section")).map((sec) => ({
              label: sec.getAttribute("label") || "",
              items: Array.from(sec.querySelectorAll("menu-item")).map((item) => ({
                id: item.id || "",
                name: item.getAttribute("name") || "",
                href: item.getAttribute("href") || "#",
                icon: item.getAttribute("icon") || "",
              })),
            })),
          };
        }

        return null;
      })
      .filter(Boolean);
  }

  _isActive(href) {
    if (!href || href === "#") return false;
    const path = window.location.pathname;
    if (href === path) return true;
    if (href === "/") return false;
    // Normalise so prefix check works whether or not href has a trailing slash
    const prefix = href.endsWith("/") ? href : href + "/";
    return path.startsWith(prefix);
  }

  _panelId(group) {
    const base = group.id || group.name.toLowerCase().replace(/\W+/g, "-");
    return `rp-mnupanel-${base}`;
  }

  _renderItem(item) {
    const idAttr = item.id ? ` id="${esc(item.id)}"` : "";
    const active = this._isActive(item.href) ? " is-active" : "";
    const iconHtml = item.icon ? `<i class="bi ${esc(item.icon)}"></i>` : "";
    return `<a class="rp-menubar-item${active}" href="${esc(item.href)}"${idAttr}>${iconHtml}${esc(item.name)}</a>`;
  }

  _renderGroupTrigger(group) {
    const idAttr = group.id ? ` id="${esc(group.id)}"` : "";
    const iconHtml = group.icon ? `<i class="bi ${esc(group.icon)}"></i>` : "";
    const panelId = this._panelId(group);
    // Mark group trigger active when any child item is active
    const hasActive = group.sections.some((s) => s.items.some((i) => this._isActive(i.href)));
    const active = hasActive ? " is-active" : "";
    return `<div class="rp-menubar-item${active}" data-dropdown data-panel="${panelId}" tabindex="0"
      aria-haspopup="true" aria-expanded="false"${idAttr}
    >${iconHtml}${esc(group.name)}<i class="bi bi-chevron-down"></i></div>`;
  }

  _renderPanel(group) {
    const isMega = group.cols > 1 || group.sections.length > 1;
    const panelClass = isMega ? "rp-dd-panel mega" : "rp-dd-panel";
    const numCols = Math.max(group.cols, group.sections.length);
    const colsStyle = isMega ? ` style="--cols:${numCols}"` : "";
    const panelId = this._panelId(group);

    const sectionsHtml = group.sections
      .map((sec) => {
        const labelHtml = sec.label ? `<div class="rp-dd-label">${esc(sec.label)}</div>` : "";
        const itemsHtml = sec.items
          .map((si) => {
            const siId = si.id ? ` id="${esc(si.id)}"` : "";
            const siIcon = si.icon ? `<i class="bi ${esc(si.icon)}"></i>` : "";
            const siActive = this._isActive(si.href) ? ' class="is-active"' : "";
            return `<a href="${esc(si.href)}"${siId}${siActive}>${siIcon}${esc(si.name)}</a>`;
          })
          .join("");
        return `<div class="rp-mega-col">${labelHtml}${itemsHtml}</div>`;
      })
      .join("");

    return `<div class="${panelClass}" id="${panelId}"${colsStyle}>${sectionsHtml}</div>`;
  }

  _render() {
    const toggleBtn = `<button class="rp-menubar-toggle" aria-label="Navigation menu" aria-expanded="false">
      <span class="rp-menubar-toggle-label"><i class="bi bi-list"></i>Menu</span>
      <i class="bi bi-chevron-down rp-menubar-toggle-chevron"></i>
    </button>`;

    const navHtml = this._items
      .map((item) =>
        item.type === "item" ? this._renderItem(item) : this._renderGroupTrigger(item),
      )
      .join("");

    // Panels rendered as siblings of the nav container — outside the overflow scroll context
    const panelsHtml = this._items
      .filter((item) => item.type === "group")
      .map((item) => this._renderPanel(item))
      .join("");

    this.innerHTML = `${toggleBtn}<div class="rp-menubar-nav">${navHtml}</div>${panelsHtml}`;
  }

  _bindEvents() {
    this.addEventListener("click", (e) => {
      // Mobile hamburger toggle
      if (e.target.closest(".rp-menubar-toggle")) {
        const isOpen = this.classList.toggle("rp-mobile-open");
        const btn = this.querySelector(".rp-menubar-toggle");
        if (btn) btn.setAttribute("aria-expanded", String(isOpen));
        if (!isOpen) this._closeAll();
        return;
      }

      // Dropdown trigger
      const trigger = e.target.closest("[data-dropdown]");
      if (!trigger || !this.contains(trigger)) return;

      const panelId = trigger.getAttribute("data-panel");
      const panel = panelId ? this.querySelector(`#${panelId}`) : null;
      if (!panel) return;

      const isOpen = panel.classList.contains("rp-dd-open");
      this._closeAll();
      if (!isOpen) {
        if (window.innerWidth > 640) {
          // Desktop: float panel absolutely, aligned with trigger's left edge
          const triggerRect = trigger.getBoundingClientRect();
          const barRect = this.getBoundingClientRect();
          panel.style.left = `${triggerRect.left - barRect.left}px`;
        } else {
          // Mobile: move panel inline immediately after its trigger so it appears below it
          trigger.insertAdjacentElement("afterend", panel);
        }
        panel.classList.add("rp-dd-open");
        trigger.setAttribute("aria-expanded", "true");
      }
    });

    // Keyboard: Enter / Space opens focused dropdown triggers
    this.addEventListener("keydown", (e) => {
      if (e.key !== "Enter" && e.key !== " ") return;
      const trigger = e.target.closest("[data-dropdown]:not(a)");
      if (trigger && this.contains(trigger)) {
        e.preventDefault();
        trigger.click();
      }
    });

    // Close mobile menu + dropdowns when a nav link is followed
    this.addEventListener("click", (e) => {
      if (e.target.closest("a[href]") && e.target.closest(".rp-menubar-nav")) {
        this._closeMobileMenu();
      }
    });

    this._onOutsideClick = (e) => {
      if (!this.contains(e.target)) {
        this._closeAll();
        this._closeMobileMenu();
      }
    };
    this._onDocKeyDown = (e) => {
      if (e.key === "Escape") {
        this._closeAll();
        this._closeMobileMenu();
      }
    };
    document.addEventListener("click", this._onOutsideClick);
    document.addEventListener("keydown", this._onDocKeyDown);
  }

  _closeAll() {
    this.querySelectorAll(".rp-dd-panel.rp-dd-open").forEach((p) => {
      p.classList.remove("rp-dd-open");
      if (p.id) {
        this.querySelector(`[data-panel="${p.id}"]`)?.setAttribute("aria-expanded", "false");
      }
    });
    // Return any panels that were moved inline (mobile) back to the bar root
    this.querySelectorAll(".rp-menubar-nav .rp-dd-panel").forEach((p) => {
      this.appendChild(p);
    });
  }

  _closeMobileMenu() {
    if (!this.classList.contains("rp-mobile-open")) return;
    this.classList.remove("rp-mobile-open");
    const btn = this.querySelector(".rp-menubar-toggle");
    if (btn) btn.setAttribute("aria-expanded", "false");
  }
}

customElements.define("menu-bar", MenuBar);
