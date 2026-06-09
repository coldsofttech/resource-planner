/* ViewField  <view-field>
 *
 * Read-only display field rendered as a <dt>/<dd> pair inside a definition list.
 * Use inside a <dl> element. Value is set programmatically via the `value` property;
 * the initial display is an em dash (—) until a value is assigned.
 *
 * Attributes:
 *   label – field label rendered in the <dt> element
 *   meta  – boolean; adds "is-meta" class for compact/secondary styling
 *   code  – boolean; wraps the value in <code class="rp-mono"> for monospace display
 *   badge – CSS class(es) for a badge wrapper span around the value
 *           e.g. badge="rp-badge rp-badge-success" or badge="rp-status-badge"
 *   desc  – boolean; switches to single-column stacked layout so long value text
 *           wraps on its own full-width line beneath the label
 *   tags  – CSS class(es) for each tag span when value is an array
 *           e.g. tags="rp-badge rp-badge-soft"; enables flex-wrap layout on the <dd>
 *
 * Public API:
 *   field.value = html  – setter: sets innerHTML when value is a string
 *   field.value = arr   – setter: renders each string in the array as a tag span; [] shows "—"
 *   field.value         – getter: returns current innerHTML of the value element
 */
import { esc } from "../utils.js";

class ViewField extends HTMLElement {
  static get observedAttributes() {
    return ["label", "meta", "code", "badge", "desc", "tags"];
  }

  connectedCallback() {
    this._connected = true;
    this._render();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this._connected && oldVal !== newVal) this._render();
  }

  get value() {
    return this.querySelector("[data-rp-fv]")?.innerHTML ?? "";
  }

  set value(v) {
    const el = this.querySelector("[data-rp-fv]");
    if (!el) return;
    if (Array.isArray(v)) {
      if (!v.length) {
        el.innerHTML = "—";
        return;
      }
      const cls = this.getAttribute("tags") || "rp-badge rp-badge-soft";
      el.innerHTML = v
        .map((item) => `<span class="${esc(cls)}">${esc(String(item))}</span>`)
        .join("");
    } else {
      el.innerHTML = v;
    }
  }

  _render() {
    const label = this.getAttribute("label") || "";
    const badgeClass = this.getAttribute("badge");
    const isCode = this.hasAttribute("code");

    this.classList.toggle("is-meta", this.hasAttribute("meta"));

    let valueDd;
    if (isCode) {
      valueDd = `<dd><code class="rp-mono" data-rp-fv>—</code></dd>`;
    } else if (badgeClass) {
      valueDd = `<dd><span class="${esc(badgeClass)}" data-rp-fv>—</span></dd>`;
    } else {
      valueDd = `<dd data-rp-fv>—</dd>`;
    }

    this.innerHTML = `<dt>${esc(label)}</dt>${valueDd}`;
  }
}

customElements.define("view-field", ViewField);
