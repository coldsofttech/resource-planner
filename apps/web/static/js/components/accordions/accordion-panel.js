import { esc } from "../utils.js";

/* AccordionPanel  <accordion-panel>
 *
 * Collapsible panel with a clickable header and a body slot. Supports optional
 * grouping via the `group` attribute — when set, all accordion-panel elements
 * sharing the same group value act as an exclusive set (opening one closes others).
 *
 * Declarative children (captured once on connect, before _render replaces innerHTML):
 *   <accordion-header>  – raw child nodes used as header content; takes precedence over `label`
 *   <accordion-body>    – raw child nodes moved into the collapsible body slot
 *
 * Attributes:
 *   label  – plain-text header label (used when <accordion-header> is absent)
 *   icon   – Bootstrap Icon class shown before the label (e.g. "bi-tag")
 *   open   – boolean presence attribute; panel starts expanded when present
 *   group  – string; panels sharing the same value form an exclusive accordion group
 *
 * Public API:
 *   panel.show()   – expand the panel
 *   panel.hide()   – collapse the panel
 *   panel.toggle() – toggle open/close
 *   panel.isOpen   – boolean getter
 *
 * Events (all bubble):
 *   rp:open   – fired after the panel expands
 *   rp:close  – fired after the panel collapses
 */
class AccordionPanel extends HTMLElement {
  static get observedAttributes() {
    return ["label", "icon", "open", "group"];
  }

  connectedCallback() {
    if (this._captured === undefined) {
      // Capture declarative slot children once before _render() replaces innerHTML.
      // The === undefined guard keeps them safe across wizard reconnects.
      const headerEl = this.querySelector(":scope > accordion-header");
      const bodyEl = this.querySelector(":scope > accordion-body");
      this._headerNodes = headerEl ? Array.from(headerEl.childNodes) : null;
      this._bodyNodes = bodyEl ? Array.from(bodyEl.childNodes) : [];
      this._captured = true;
    }
    // Skip re-render if the shell already exists (wizard-safe).
    if (!this.querySelector(".rp-acc-panel-hd")) this._render();
    this._rebindGroupListener();
  }

  disconnectedCallback() {
    this._removeGroupListener();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (oldVal === newVal || this._captured === undefined) return;
    if (name === "open") {
      this._syncOpen(this.hasAttribute("open"));
    } else if (name === "group") {
      this._rebindGroupListener();
    }
  }

  // ── Public API ──────────────────────────────────────────────────────────────

  show() {
    if (this.isOpen) return;
    this._setOpen(true);
  }

  hide() {
    if (!this.isOpen) return;
    this._setOpen(false);
  }

  toggle() {
    this._setOpen(!this.isOpen);
  }

  get isOpen() {
    return this.dataset.open === "true";
  }

  // ── Internals ───────────────────────────────────────────────────────────────

  _render() {
    const open = this.hasAttribute("open");
    this.dataset.open = String(open);

    const label = this.getAttribute("label") || "";
    const icon = this.getAttribute("icon") || "";
    const iconHTML = icon ? `<span class="rp-acc-panel-icon bi ${esc(icon)}"></span>` : "";
    const defaultHeader = `${iconHTML}<span class="rp-acc-panel-label">${esc(label)}</span>`;

    this.innerHTML = `
      <div class="rp-acc-panel-hd" role="button" tabindex="0" aria-expanded="${open}">
        <span class="rp-acc-chevron bi bi-chevron-right"></span>
        ${this._headerNodes ? "" : defaultHeader}
      </div>
      <div class="rp-acc-panel-bd"${open ? "" : " hidden"}></div>
    `.trim();

    // Re-insert custom header nodes after the chevron.
    if (this._headerNodes) {
      const hd = this.querySelector(".rp-acc-panel-hd");
      this._headerNodes.forEach((node) => hd.appendChild(node));
    }

    // Move body nodes into the body slot.
    const bd = this.querySelector(".rp-acc-panel-bd");
    if (bd && this._bodyNodes) this._bodyNodes.forEach((node) => bd.appendChild(node));

    // Bind the trigger after innerHTML is set (old element discarded).
    const hd = this.querySelector(".rp-acc-panel-hd");
    hd?.addEventListener("click", () => this.toggle());
    hd?.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        this.toggle();
      }
    });
  }

  _setOpen(open) {
    this._syncOpen(open);
    // Notify group peers so they close themselves.
    const group = this.getAttribute("group");
    if (open && group) {
      document.dispatchEvent(
        new CustomEvent("rp:accordion-group", { detail: { group, source: this } }),
      );
    }
    this.dispatchEvent(new CustomEvent(open ? "rp:open" : "rp:close", { bubbles: true }));
  }

  _syncOpen(open) {
    this.dataset.open = String(open);
    const hd = this.querySelector(".rp-acc-panel-hd");
    const bd = this.querySelector(".rp-acc-panel-bd");
    if (hd) hd.setAttribute("aria-expanded", String(open));
    if (bd) bd.hidden = !open;
  }

  _rebindGroupListener() {
    this._removeGroupListener();
    const group = this.getAttribute("group");
    if (!group) return;
    this._groupHandler = (e) => {
      if (e.detail.group === this.getAttribute("group") && e.detail.source !== this) {
        this.hide();
      }
    };
    document.addEventListener("rp:accordion-group", this._groupHandler);
  }

  _removeGroupListener() {
    if (this._groupHandler) {
      document.removeEventListener("rp:accordion-group", this._groupHandler);
      this._groupHandler = null;
    }
  }
}

customElements.define("accordion-panel", AccordionPanel);
