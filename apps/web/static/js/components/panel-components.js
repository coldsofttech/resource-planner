/* PanelField: <rp-panel> */
class PanelField extends HTMLElement {
  static get observedAttributes() {
    return ["col", "title", "icon", "id", "name"];
  }

  connectedCallback() {
    if (this._bodyNodes === undefined) {
      // <panel-title> innerHTML takes precedence over the title="" attribute.
      // Captured once here (=== undefined guard) before _render() replaces innerHTML.
      const titleEl = this.querySelector("panel-title");
      this._titleContent = titleEl ? titleEl.innerHTML.trim() : null;

      const body = this.querySelector("panel-body");
      this._bodyNodes = body ? Array.from(body.children) : [];
    }
    // When the wizard moves this element the .rp-card shell is still intact —
    // skip the full re-render to avoid detaching/reattaching body nodes.
    if (!this.querySelector(".rp-card")) this._render();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this._bodyNodes !== undefined && oldVal !== newVal) this._render();
  }

  get _col() {
    return this.getAttribute("col") || "col-12";
  }
  get _title() {
    return this.getAttribute("title") || "";
  }
  get _icon() {
    return this.getAttribute("icon") || "";
  }
  get _fieldId() {
    return this.id || "";
  }
  get _name() {
    return this.getAttribute("name") || this._fieldId;
  }

  _render() {
    this.className = this._col;
    const headContent = this._titleContent ?? (this._title ? this._esc(this._title) : "");
    const iconHTML = this._icon
      ? `<i class="bi ${this._esc(this._icon)} rp-card-head-icon"></i>`
      : "";
    const headHTML =
      headContent || iconHTML
        ? `<div class="rp-card-head">${iconHTML}<strong>${headContent}</strong></div>`
        : "";
    this.innerHTML = `<div class="rp-card rp-card-sunken">${headHTML}<div class="rp-card-body" data-panel-body></div></div>`;
    const slot = this.querySelector("[data-panel-body]");
    if (slot && this._bodyNodes) this._bodyNodes.forEach((node) => slot.appendChild(node));
  }

  _esc(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
}

customElements.define("rp-panel", PanelField);

/* PanelTitle: <panel-title> */
class PanelTitle extends HTMLElement {}

customElements.define("panel-title", PanelTitle);

/* PanelBody: <panel-body> */
class PanelBody extends HTMLElement {}

customElements.define("panel-body", PanelBody);
