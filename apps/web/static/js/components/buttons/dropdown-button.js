import { esc } from "../utils.js";

/* DropdownButton  <dropdown-button>
 *
 * Split button with an attached dropdown panel. The left side is a standard
 * clickable button; the right chevron opens a dropdown of options.
 *
 * Attributes (host element):
 *   label        – text shown on the main button
 *   prefix-icon  – Bootstrap Icons class for the main button (e.g. "bi-plus-lg")
 *   variant      – visual style: "primary" (default) | "secondary" | "muted" |
 *                  "engine" | "delete" | "activate" | "deactivate" | "neutral"
 *   size         – "sm" | "lg" | omit for default
 *   disabled     – disables both the main button and the chevron
 *
 * Declarative children (captured once on first connect):
 *   <values-list>
 *     <value [value="…"] [icon="bi-…"] [href="…"] [disabled]>Label</value>
 *   </values-list>
 *
 *   • `href`  → renders as <a href="…">  (page navigation)
 *   • no href → renders as <button class="rp-dd-link">  (JS action); fires
 *               an "rp:select" CustomEvent on the host:
 *               detail: { value: string, label: string }
 *   • `disabled` on a <value> greys out that specific item
 *
 * Events:
 *   rp:select  – bubbles; detail { value, label } — fired for non-href items
 *
 * Example:
 *   <dropdown-button label="New project" prefix-icon="bi-plus-lg">
 *     <values-list>
 *       <value icon="bi-kanban" href="/projects/new/">From scratch</value>
 *       <value icon="bi-clipboard-data" value="estimate">From estimate</value>
 *     </values-list>
 *   </dropdown-button>
 */

const VARIANT_MAP = {
  primary: "rp-btn-primary",
  secondary: "rp-btn-secondary",
  muted: "rp-btn-muted",
  engine: "rp-btn-engine",
  delete: "rp-btn-delete",
  activate: "rp-btn-activate",
  deactivate: "rp-btn-deactivate",
  neutral: "rp-btn-neutral",
};

export class DropdownButton extends HTMLElement {
  static get observedAttributes() {
    return ["label", "prefix-icon", "variant", "size", "disabled"];
  }

  get _label() {
    return this.getAttribute("label") || "";
  }
  get _prefixIcon() {
    return this.getAttribute("prefix-icon") || "";
  }
  get _variantClass() {
    return VARIANT_MAP[this.getAttribute("variant")] || VARIANT_MAP.primary;
  }
  get _sizeClass() {
    const s = this.getAttribute("size");
    if (s === "sm") return "rp-btn-sm";
    if (s === "lg") return "rp-btn-lg";
    return "";
  }
  get _disabled() {
    return this.hasAttribute("disabled");
  }

  connectedCallback() {
    // Capture declarative children once before innerHTML is replaced.
    // Guard prevents overwrite on re-connections (e.g. inside a wizard).
    if (this._initialOptions === undefined) {
      this._initialOptions = Array.from(this.querySelectorAll("values-list value")).map((el) => ({
        value: el.getAttribute("value") || "",
        icon: el.getAttribute("icon") || "",
        href: el.getAttribute("href") || "",
        label: el.textContent.trim(),
        disabled: el.hasAttribute("disabled"),
      }));
    }
    this._doRender();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this._rendered && oldVal !== newVal) this._doRender();
  }

  disconnectedCallback() {
    this._removeDocListeners();
  }

  _doRender() {
    this._removeDocListeners();
    this._render();
    this._bindEvents();
    this._rendered = true;
  }

  _buildItems() {
    return (this._initialOptions || [])
      .map((o) => {
        const icon = o.icon ? `<i class="bi ${esc(o.icon)}"></i>` : "";
        const label = esc(o.label);
        if (o.href) {
          const disabled = o.disabled ? ' aria-disabled="true" tabindex="-1"' : "";
          return `<a href="${esc(o.href)}"${disabled}>${icon}${label}</a>`;
        }
        const disabled = o.disabled ? " disabled" : "";
        return `<button class="rp-dd-link" type="button" data-value="${esc(o.value)}"${disabled}>${icon}${label}</button>`;
      })
      .join("");
  }

  _render() {
    const v = this._variantClass;
    const sz = this._sizeClass;
    const disabled = this._disabled ? " disabled" : "";
    const btnCls = [v, sz].filter(Boolean).join(" ");
    const prefix = this._prefixIcon ? `<i class="bi ${esc(this._prefixIcon)}"></i>` : "";
    const label = esc(this._label);

    this.innerHTML = `
      <div class="rp-splitbtn-wrap">
        <div class="rp-splitbtn">
          <button type="button" class="rp-btn ${btnCls}"${disabled}>${prefix}${label}</button>
          <button
            type="button"
            class="rp-btn rp-btn-split ${btnCls}"
            aria-expanded="false"
            aria-haspopup="true"
            ${disabled}
          ><i class="bi bi-chevron-down"></i></button>
        </div>
        <div class="rp-dd-panel" role="menu">${this._buildItems()}</div>
      </div>`;
  }

  _bindEvents() {
    const splitBtn = this.querySelector(".rp-btn-split");
    const panel = this.querySelector(".rp-dd-panel");
    if (!splitBtn || !panel) return;

    splitBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = panel.classList.contains("rp-dd-open");
      this._close();
      if (!isOpen) this._open();
    });

    panel.addEventListener("click", (e) => {
      // Link items — just close the panel; navigation happens natively
      if (e.target.closest("a")) {
        this._close();
        return;
      }
      // Button items — close + dispatch rp:select
      const btn = e.target.closest("button.rp-dd-link");
      if (!btn || btn.disabled) return;
      this._close();
      this.dispatchEvent(
        new CustomEvent("rp:select", {
          bubbles: true,
          detail: { value: btn.dataset.value, label: btn.textContent.trim() },
        }),
      );
    });

    // Close when clicking anywhere outside this component
    this._onOutside = (e) => {
      if (!this.contains(e.target)) this._close();
    };
    // Close on Escape
    this._onKeyDown = (e) => {
      if (e.key === "Escape") this._close();
    };

    document.addEventListener("click", this._onOutside);
    document.addEventListener("keydown", this._onKeyDown);
  }

  _removeDocListeners() {
    if (this._onOutside) document.removeEventListener("click", this._onOutside);
    if (this._onKeyDown) document.removeEventListener("keydown", this._onKeyDown);
  }

  _open() {
    const panel = this.querySelector(".rp-dd-panel");
    const splitBtn = this.querySelector(".rp-btn-split");
    panel?.classList.add("rp-dd-open");
    splitBtn?.setAttribute("aria-expanded", "true");
  }

  _close() {
    const panel = this.querySelector(".rp-dd-panel");
    const splitBtn = this.querySelector(".rp-btn-split");
    panel?.classList.remove("rp-dd-open");
    splitBtn?.setAttribute("aria-expanded", "false");
  }
}

customElements.define("dropdown-button", DropdownButton);
