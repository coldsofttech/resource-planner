/* PieChart  <pie-chart>
 *
 * Single-series pie/doughnut chart backed by Chart.js.
 *
 * Attributes:
 *   title     – card heading text
 *   subtitle  – small muted text next to the title
 *   variant   – "pie" (default) or "doughnut"
 *
 * Public API:
 *   chart.data = { labels, values, colors, meta }
 *     labels  – array of segment labels
 *     values  – array of segment values (same length/order as labels)
 *     colors  – array of segment colors (same length/order as labels)
 *     meta    – optional right-aligned header text
 *
 * Re-assigning `.data` destroys and recreates the underlying Chart instance,
 * matching the pattern used by <bar-chart>.
 */
import Chart from "chart.js/auto";
import { esc } from "../utils.js";

class PieChart extends HTMLElement {
  static get observedAttributes() {
    return ["title", "subtitle", "variant"];
  }

  connectedCallback() {
    this._renderShell();
    if (this._data) this._renderChart();
  }

  disconnectedCallback() {
    this._chart?.destroy();
    this._chart = null;
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (oldVal !== newVal && this.isConnected) {
      if (name === "variant") this._renderChart();
      else this._renderShell(true);
    }
  }

  get _title() {
    return this.getAttribute("title") || "";
  }

  get _subtitle() {
    return this.getAttribute("subtitle") || "";
  }

  get _variant() {
    return this.getAttribute("variant") === "doughnut" ? "doughnut" : "pie";
  }

  set data(payload) {
    this._data = payload;
    if (this.isConnected) this._renderChart();
  }

  get data() {
    return this._data;
  }

  _renderShell(preserveCanvas = false) {
    const meta = this._data?.meta || "";
    const headHTML =
      this._title || this._subtitle || meta
        ? `<div class="rp-chart-head">
           <span>
             ${this._title ? `<h4 class="d-inline">${esc(this._title)}</h4>` : ""}
             ${this._subtitle ? ` <span class="rp-subtle">${esc(this._subtitle)}</span>` : ""}
           </span>
           ${meta ? `<span class="rp-subtle">${esc(meta)}</span>` : ""}
         </div>`
        : "";

    if (preserveCanvas && this.querySelector("canvas")) {
      const head = this.querySelector(".rp-chart-head");
      if (head) head.outerHTML = headHTML;
      else if (headHTML) this.insertAdjacentHTML("afterbegin", headHTML);
      return;
    }

    this._chart?.destroy();
    this._chart = null;
    this.className = "rp-chart-card";
    this.innerHTML = `${headHTML}<div class="rp-chart-body"><canvas></canvas></div>`;
  }

  _renderChart() {
    const { labels = [], values = [], colors = [] } = this._data || {};
    const canvas = this.querySelector("canvas");
    if (!canvas) return;

    // The header's `meta` text is read directly from `this._data` at shell-
    // render time, but if data is reassigned without a full shell rebuild
    // (preserveCanvas path), refresh it here too.
    this._renderShell(true);

    this._chart?.destroy();

    this._chart = new Chart(canvas, {
      type: this._variant,
      data: {
        labels,
        datasets: [
          {
            data: values,
            backgroundColor: colors,
            borderWidth: 1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "bottom" } },
      },
    });
  }
}

customElements.define("pie-chart", PieChart);
