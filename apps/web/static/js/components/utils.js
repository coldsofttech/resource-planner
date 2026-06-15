/**
 * Escapes a value for safe insertion into HTML attribute values and text content.
 * Handles null and undefined by treating them as empty strings.
 */
export function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/**
 * Escapes a value for safe insertion into SVG text content and XML elements.
 * Use esc() for HTML attribute values; use escSvg() for SVG/XML text nodes.
 */
export function escSvg(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

/**
 * Sets the breadcrumb trail on the shared <page-breadcrumbs> element.
 * Home is always prepended automatically by the component.
 * Pass crumbs without Home: [{ label }, { label, href }]
 * Crumbs with href render as links; without href render as plain text.
 */
export function setBreadcrumbs(crumbs) {
  const el = document.getElementById("app-breadcrumbs");
  if (!el?.setCrumbs || !crumbs.length) return;
  const trail = crumbs.map((c, i) => (i === crumbs.length - 1 ? { ...c, current: true } : c));
  el.setCrumbs([{ label: "Home", href: "/dashboard" }, ...trail]);
}
