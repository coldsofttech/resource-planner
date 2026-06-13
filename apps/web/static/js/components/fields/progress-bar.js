/* ProgressBar  <progress-bar>
 *
 * Renders a labelled progress bar using the shared .rp-progress CSS.
 *
 * Attributes:
 *   percent  – 0–100 fill percentage (default 0)
 *   variant  – CSS variant appended to .rp-progress: "success" | "warning" | "danger" | "striped"
 *   label    – left-side label text (default "")
 *   hide-meta – when present, hides the label row (percent and label text)
 */
import { esc } from "../utils.js";

class ProgressBar extends HTMLElement {
  static get observedAttributes() {
    return ["percent", "variant", "label", "hide-meta"];
  }

  connectedCallback() {
    this._render();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (oldVal !== newVal && this.isConnected) this._render();
  }

  get _percent() {
    const v = parseFloat(this.getAttribute("percent") ?? "0");
    return Math.min(100, Math.max(0, isNaN(v) ? 0 : v));
  }

  get _variant() {
    return this.getAttribute("variant") || "";
  }

  get _label() {
    return this.getAttribute("label") || "";
  }

  _render() {
    const pct = this._percent;
    const variantClass = this._variant ? ` ${esc(this._variant)}` : "";
    const metaHidden = this.hasAttribute("hide-meta");
    const metaHTML = metaHidden
      ? ""
      : `<div class="d-flex justify-content-between mb-1" style="font-size:12px">
           <span>${esc(this._label)}</span>
           <span class="rp-mono">${pct}%</span>
         </div>`;

    this.innerHTML = `${metaHTML}<div class="rp-progress${variantClass}"><span style="width:${pct}%"></span></div>`;
  }
}

customElements.define("progress-bar", ProgressBar);
