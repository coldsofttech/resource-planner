/* CardPanel  <card-panel>
 *
 * Flexible slot-driven card container. Maps three declarative children to the
 * three CSS regions of `.rp-card` and handles both visual variants.
 * Re-connection is wizard-safe: the render is skipped if the card shell already exists.
 *
 * Declarative children (captured before first render):
 *   <panel-header>  – child nodes inserted into .rp-card-head (border-bottom separator)
 *   <panel-body>    – child nodes inserted into .rp-card-body (shared with <section-panel>)
 *   <panel-footer>  – child nodes inserted into .rp-card-foot (border-top separator)
 *
 * Omit any slot to suppress that CSS region entirely. If no children are declared,
 * an empty .rp-card-body is rendered as a fallback.
 *
 * Attributes:
 *   col      – Bootstrap column class applied to the host element (default "col-12")
 *   variant  – "default" (surface bg, border, shadow) | "sunken" (sunken bg, no shadow)
 *              default: "default"
 *
 * Examples:
 *   <!-- Content-only sunken card -->
 *   <card-panel variant="sunken">
 *     <panel-body>
 *       <strong>File specification</strong>
 *       <ul class="mt-2">...</ul>
 *     </panel-body>
 *   </card-panel>
 *
 *   <!-- Header + body + footer -->
 *   <card-panel>
 *     <panel-header>
 *       <span class="rp-card-title">Team members</span>
 *       <primary-button label="Add member"></primary-button>
 *     </panel-header>
 *     <panel-body>...</panel-body>
 *     <panel-footer>
 *       <span class="rp-text-muted">5 members</span>
 *     </panel-footer>
 *   </card-panel>
 */

class CardPanel extends HTMLElement {
  static get observedAttributes() {
    return ["col", "variant"];
  }

  connectedCallback() {
    if (this._slots === undefined) {
      // Capture slot children once, before _render() replaces innerHTML.
      // The === undefined guard ensures wizard reconnects do not overwrite.
      const header = this.querySelector(":scope > panel-header");
      const body = this.querySelector(":scope > panel-body");
      const footer = this.querySelector(":scope > panel-footer");
      this._slots = {
        header: header ? Array.from(header.childNodes) : null,
        body: body ? Array.from(body.childNodes) : null,
        footer: footer ? Array.from(footer.childNodes) : null,
      };
    }
    // Wizard-safe: skip re-render if the card shell is already in the DOM.
    if (!this.querySelector(".rp-card")) this._render();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this._slots !== undefined && oldVal !== newVal) this._render();
  }

  get _col() {
    return this.getAttribute("col") || "col-12";
  }

  get _variant() {
    return this.getAttribute("variant") || "default";
  }

  _render() {
    this.className = this._col;

    const variantClass = this._variant === "sunken" ? " rp-card-sunken" : "";

    let sections = "";
    if (this._slots.header !== null)
      sections += `<div class="rp-card-head" data-card-header></div>`;
    if (this._slots.body !== null) sections += `<div class="rp-card-body" data-card-body></div>`;
    if (this._slots.footer !== null)
      sections += `<div class="rp-card-foot" data-card-footer></div>`;
    // Fallback: empty body when no children were declared.
    if (!sections) sections = `<div class="rp-card-body" data-card-body></div>`;

    this.innerHTML = `<div class="rp-card${variantClass}">${sections}</div>`;

    const move = (selector, nodes) => {
      if (!nodes) return;
      const slot = this.querySelector(selector);
      if (slot) nodes.forEach((node) => slot.appendChild(node));
    };

    move("[data-card-header]", this._slots.header);
    move("[data-card-body]", this._slots.body);
    move("[data-card-footer]", this._slots.footer);
  }
}

customElements.define("card-panel", CardPanel);
