/* HeatmapChart  <heatmap-chart>
 *
 * Pure CSS Grid heatmap (no charting library) — member/sprint utilisation
 * grid with discrete threshold-bucket coloring and an inline legend. Used
 * for the Utilisation Graph's Members tab "heatmap" view.
 *
 * Attributes:
 *   title  – card heading text
 *
 * Public API:
 *   chart.data = { sprints, rows }
 *     sprints – array of { sprint_code, sprint_number } (or plain strings)
 *     rows    – array of { label, sublabel, cells }
 *       cells – array of { display, bucket, is_over }
 *         display – text shown in the cell (e.g. "70%", "10d", "—")
 *         bucket  – one of "none" | "ramp" | "healthy" | "excellent" | "over",
 *                   or null for the absolute-day fallback (no capacity but
 *                   some allocation) — rendered with the neutral/fallback style
 *         is_over – true adds the red "over" underline treatment
 *
 * Bucket legend and thresholds:
 *   none      – 0% / no allocation
 *   ramp      – < 50% (ramp-down)
 *   healthy   – 50–89%
 *   excellent – 90–100%
 *   over      – > 100%
 */
import { esc } from "../utils.js";

const LEGEND = [
  { bucket: "none", label: "0% No alloc" },
  { bucket: "ramp", label: "35% Ramp-down (<50%)" },
  { bucket: "healthy", label: "65% Healthy" },
  { bucket: "excellent", label: "90% Excellent" },
  { bucket: "over", label: "110% Over" },
];

class HeatmapChart extends HTMLElement {
  static get observedAttributes() {
    return ["title"];
  }

  connectedCallback() {
    this._render();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (oldVal !== newVal && this.isConnected) this._render();
  }

  get _title() {
    return this.getAttribute("title") || "";
  }

  set data(payload) {
    this._data = payload;
    if (this.isConnected) this._render();
  }

  get data() {
    return this._data;
  }

  _legendHTML() {
    return LEGEND.map(
      (l) =>
        `<span class="rp-hm-legend-item"><span class="rp-hm-cell rp-hm-${l.bucket} rp-hm-swatch"></span> ${esc(l.label)}</span>`,
    ).join("");
  }

  _render() {
    this.className = "rp-chart-card";
    const { sprints = [], rows = [] } = this._data || {};

    const headHTML = this._title
      ? `<div class="rp-chart-head"><h4>${esc(this._title)}</h4></div>`
      : "";
    const legendHTML = `<div class="rp-hm-legend">${this._legendHTML()}</div>`;

    if (!rows.length) {
      this.innerHTML = `${headHTML}<div class="rp-chart-body">${legendHTML}<p class="small mb-0" style="color:var(--rp-text-muted)">No data available.</p></div>`;
      return;
    }

    const sprintLabel = (s) =>
      typeof s === "string" ? s : s.sprint_number ? `Sprint ${s.sprint_number}` : s.sprint_code;

    const headerCells = sprints
      .map((s) => `<div class="rp-hm-head">${esc(sprintLabel(s))}</div>`)
      .join("");

    const bodyRows = rows
      .map((row) => {
        const cells = row.cells
          .map((cell) => {
            const bucketClass = cell.bucket ? `rp-hm-${esc(cell.bucket)}` : "rp-hm-fallback";
            const overClass = cell.is_over ? " rp-hm-over-marker" : "";
            return `<div class="rp-hm-cell ${bucketClass}${overClass}">${esc(cell.display)}</div>`;
          })
          .join("");
        const sublabelHTML = row.sublabel
          ? `<div class="rp-hm-sublabel">${esc(row.sublabel)}</div>`
          : "";
        return `
          <div class="rp-hm-label"><div>${esc(row.label)}</div>${sublabelHTML}</div>
          ${cells}
        `;
      })
      .join("");

    this.innerHTML = `
      ${headHTML}
      <div class="rp-chart-body">
        ${legendHTML}
        <div class="rp-heatmap-wrap">
          <div class="rp-heatmap" style="grid-template-columns: 140px repeat(${sprints.length}, minmax(44px, 1fr));">
            <div class="rp-hm-head"></div>${headerCells}
            ${bodyRows}
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define("heatmap-chart", HeatmapChart);
