/* Breadcrumbs: <page-breadcrumbs>
 *
 * Renders breadcrumb navigation. Auto-generates from window.location.pathname
 * by default; override with the crumbs attribute (JSON array) or setCrumbs().
 *
 * Attribute:
 *   crumbs – JSON string: [{label, href?}, ..., {label, current: true}]
 *            omit or pass [] to auto-generate from the URL path
 *
 * Public API:
 *   el.setCrumbs([{label, href?}, ..., {label}])
 *     Update from page JS when the page knows the entity name:
 *     document.getElementById('app-breadcrumbs')
 *       .setCrumbs([{label:'Projects',href:'/projects'},{label:'Alpha',current:true}]);
 *
 * Auto-generation rules:
 *   /dashboard or /    → [{label:"Home", current:true}]
 *   /projects          → [{label:"Home", href:"/dashboard"}, {label:"Projects", current:true}]
 *   /projects/123      → [{label:"Home",...}, {label:"Projects",...}, {label:"…", current:true}]
 *   Numeric segments render as "…" — call setCrumbs() from the page module to set the real name.
 *   Kebab-case segments are title-cased: "resource-plans" → "Resource Plans".
 */
import { esc } from "../utils.js";

class Breadcrumbs extends HTMLElement {
  static get observedAttributes() {
    return ["crumbs"];
  }

  connectedCallback() {
    this._connected = true;
    this.classList.add("rp-breadcrumbs");
    this._render();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this._connected && oldVal !== newVal) this._render();
  }

  setCrumbs(crumbs) {
    this.setAttribute("crumbs", JSON.stringify(crumbs));
  }

  get _crumbs() {
    const attr = this.getAttribute("crumbs");
    if (attr) {
      try {
        const parsed = JSON.parse(attr);
        if (parsed.length) return parsed;
      } catch {}
    }
    return this._fromUrl();
  }

  _fromUrl() {
    const path = window.location.pathname.replace(/\/$/, "") || "/";
    if (path === "/" || path === "/dashboard") {
      return [{ label: "Home", current: true }];
    }

    const segments = path.split("/").filter(Boolean);
    const crumbs = [{ label: "Home", href: "/dashboard" }];

    const labelOverrides = {
      "emp-types": "Employment Types",
      profile: "Profile",
      fy: "Financial Years",
    };

    segments.forEach((seg, i) => {
      const isLast = i === segments.length - 1;
      const isNumeric = /^\d+$/.test(seg);
      const label = isNumeric
        ? "…"
        : labelOverrides[seg] || seg.replace(/-/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
      crumbs.push({
        label,
        href: isLast ? undefined : "/" + segments.slice(0, i + 1).join("/"),
        current: isLast,
      });
    });

    return crumbs;
  }

  _trunc(label, max = 40) {
    return label.length > max ? label.slice(0, 22) + "…" : label;
  }

  _render() {
    const crumbs = this._crumbs;
    const parts = [];
    crumbs.forEach((c, i) => {
      if (i > 0) parts.push(`<span class="sep">/</span>`);
      const display = this._trunc(c.label);
      const needsTitle = display !== c.label;
      const titleAttr = needsTitle ? ` title="${esc(c.label)}"` : "";
      if (c.current) {
        parts.push(`<span class="crumb-current"${titleAttr}>${esc(display)}</span>`);
      } else if (c.href) {
        parts.push(`<a class="crumb" href="${esc(c.href)}"${titleAttr}>${esc(display)}</a>`);
      } else {
        parts.push(`<span class="crumb"${titleAttr}>${esc(display)}</span>`);
      }
    });
    this.innerHTML = parts.join("");
  }
}

customElements.define("page-breadcrumbs", Breadcrumbs);
