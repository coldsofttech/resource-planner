/* heatmapChart(container, config) — imperative counterpart to the
 * declarative <heatmap-chart> custom element
 * (apps/web/static/js/components/charts/heatmap-chart.js). Creates a
 * <heatmap-chart>, mounts it into `container`, and sets its data — for
 * pages that build chart placement dynamically rather than declaring
 * <heatmap-chart> markup directly in a template.
 *
 * config: { title, data: { sprints, rows } }
 *
 * Returns the mounted <heatmap-chart> element so callers can later
 * reassign `.data` (re-render in place) or `.remove()` it. */
export function heatmapChart(container, { title = "", data } = {}) {
  const el = document.createElement("heatmap-chart");
  if (title) el.setAttribute("title", title);
  container.appendChild(el);
  if (data) el.data = data;
  return el;
}
