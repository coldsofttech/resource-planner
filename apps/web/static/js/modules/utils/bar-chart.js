/* barChart(container, config) — imperative counterpart to the declarative
 * <bar-chart> custom element (apps/web/static/js/components/charts/bar-chart.js).
 * Creates a <bar-chart>, mounts it into `container`, and sets its data —
 * for pages that build chart placement dynamically rather than declaring
 * <bar-chart> markup directly in a template.
 *
 * config: { title, subtitle, data: { labels, bars, line } }
 *
 * Returns the mounted <bar-chart> element so callers can later reassign
 * `.data` (re-render in place) or `.remove()` it. */
export function barChart(container, { title = "", subtitle = "", data } = {}) {
  const el = document.createElement("bar-chart");
  if (title) el.setAttribute("title", title);
  if (subtitle) el.setAttribute("subtitle", subtitle);
  container.appendChild(el);
  if (data) el.data = data;
  return el;
}
