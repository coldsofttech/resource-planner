/* BarChart  <bar-chart>
 *
 * Grouped-bar + multi-line combo chart backed by Chart.js. Supports a single
 * left axis (e.g. the Programmes tab's all-£ Forecast/Budget/Cumulative
 * view) or a dual axis (e.g. the Teams/Members tabs' Days-vs-Util% view).
 *
 * Attributes:
 *   title     – card heading text
 *   subtitle  – small muted text next to the title
 *
 * Public API:
 *   chart.data = { labels, bars, lines, axisLeftLabel, axisRightLabel, meta }
 *     labels         – array of x-axis labels (e.g. sprint names)
 *     bars           – array of { label, data, color } — grouped bars on the
 *                      left axis
 *     lines          – array of { label, data, color, axis, dashed, max }
 *                      `axis` — "y" (left, default) or "y1" (right); only
 *                      declare a line on "y1" when a genuinely different
 *                      unit needs its own scale (e.g. a % line alongside
 *                      absolute-value bars). `dashed` renders a dashed
 *                      stroke (e.g. a constant baseline line). `max` sets
 *                      that line's axis ceiling.
 *     axisLeftLabel  – left axis title (default "Value")
 *     axisRightLabel – right axis title, only rendered if a line uses "y1"
 *     meta           – optional right-aligned header text (e.g. a
 *                      "Budget: £X  Forecast: £Y" summary)
 *
 * Re-assigning `.data` destroys and recreates the underlying Chart instance
 * (Chart.js does not support swapping datasets across unrelated axis
 * configurations safely, and this component may be re-rendered many times
 * as filters change).
 */
import Chart from "chart.js/auto";
import { esc } from "../utils.js";

class BarChart extends HTMLElement {
  static get observedAttributes() {
    return ["title", "subtitle"];
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
    if (oldVal !== newVal && this.isConnected) this._renderShell(true);
  }

  get _title() {
    return this.getAttribute("title") || "";
  }

  get _subtitle() {
    return this.getAttribute("subtitle") || "";
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
    const {
      labels = [],
      bars = [],
      lines = [],
      axisLeftLabel = "Value",
      axisRightLabel = "",
    } = this._data || {};
    const canvas = this.querySelector("canvas");
    if (!canvas) return;

    // The header's `meta` text is read directly from `this._data` at shell-
    // render time, but if data is reassigned without a full shell rebuild
    // (preserveCanvas path), refresh it here too.
    this._renderShell(true);

    this._chart?.destroy();

    const datasets = bars.map((b) => ({
      type: "bar",
      label: b.label,
      data: b.data,
      backgroundColor: b.color,
      borderRadius: 4,
      maxBarThickness: 24,
      yAxisID: "y",
    }));

    const rightAxisLines = lines.filter((l) => l.axis === "y1");
    lines.forEach((l) => {
      datasets.push({
        type: "line",
        label: l.label,
        data: l.data,
        borderColor: l.color,
        backgroundColor: `${l.color}33`,
        yAxisID: l.axis === "y1" ? "y1" : "y",
        borderDash: l.dashed ? [6, 4] : undefined,
        tension: l.dashed ? 0 : 0.3,
        pointRadius: l.dashed ? 0 : 3,
        pointHoverRadius: l.dashed ? 0 : 5,
        fill: false,
      });
    });

    const scales = {
      x: { grid: { display: false } },
      y: {
        position: "left",
        beginAtZero: true,
        title: { display: true, text: axisLeftLabel },
      },
    };
    if (rightAxisLines.length) {
      const maxLine = rightAxisLines.find((l) => l.max !== undefined);
      scales.y1 = {
        position: "right",
        beginAtZero: true,
        max: maxLine?.max,
        grid: { display: false },
        ticks: { callback: (v) => `${v}%` },
        title: { display: true, text: axisRightLabel },
      };
    }

    this._chart = new Chart(canvas, {
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: "bottom" } },
        scales,
      },
    });
  }
}

customElements.define("bar-chart", BarChart);
