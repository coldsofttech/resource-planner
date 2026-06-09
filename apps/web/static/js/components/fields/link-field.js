/* LinkField  <link-field>
 *
 * Anchor link component that wraps all <a> tag scenarios with consistent
 * styling, accessibility, external-link safety, and optional icon support.
 * Not a form field — does not extend BaseField.
 *
 * Text content vs label attribute:
 *   Both produce the same result. Text content is captured once on first connect
 *   before innerHTML is replaced; the `label` attribute takes precedence when both
 *   are provided. Re-connections (e.g. wizard moving the element) reuse the
 *   originally captured value.
 *
 *   <link-field href="/login/">Sign in</link-field>          ← text content
 *   <link-field href="/login/" label="Sign in"></link-field> ← attribute (equivalent)
 *
 * Attributes:
 *   href           – link destination; defaults to "#" when absent
 *   label          – link text; falls back to text content declared between tags
 *   icon           – Bootstrap Icons class, with or without the "bi-" prefix (optional)
 *   icon-position  – "start" (default) | "end" — icon placement relative to label text
 *   target         – forwarded to the <a> element; "_blank" auto-adds rel="noopener noreferrer"
 *   rel            – explicit rel value; merged with auto-added safety rel for _blank links
 *   disabled       – boolean; renders non-interactive: aria-disabled="true", tabindex="-1",
 *                    adds "is-disabled" class, and intercepts clicks via event listener
 *   active         – boolean; adds "is-active" class
 *   auto-active    – boolean; compares href to location.pathname; adds "is-active" when
 *                    the pathname exactly matches href or starts with href + "/"
 *   variant        – "link" (default, rp-link) | "muted" (rp-muted) |
 *                    "icon-btn" (rp-iconbtn, renders icon only) | "plain" (no class)
 *   icon-size      – named size: "xs" | "sm" | "md" (default) | "lg" | "xl" | "2x"
 *                    OR any valid CSS font-size value (e.g. "1.25rem")
 *   icon-color     – named token: "info" | "success" | "warning" | "danger" | "muted" | "primary"
 *                    OR any valid CSS color value (e.g. "var(--rp-info)")
 *   title          – tooltip text forwarded to the anchor element
 *
 * Variants:
 *   link      → class="rp-link"     standard styled text link (default)
 *   muted     → class="rp-muted"    secondary / footer link
 *   icon-btn  → class="rp-iconbtn"  icon-only action link; always renders icon without text
 *   plain     → no extra class      inherits parent styling (nav, custom contexts)
 *
 * External link safety:
 *   When target="_blank", rel="noopener noreferrer" is always included to prevent
 *   reverse tabnapping, merged with any explicit rel value set via the attribute.
 *
 * Icon rendering:
 *   When text is visible alongside an icon the icon is always aria-hidden="true" (decorative).
 *   For icon-only links (icon-btn variant or no label text) the anchor carries aria-label
 *   from the `label` attribute, falling back to `title`. Always set label or title on
 *   icon-only links so they are accessible.
 *
 * Auto-active detection:
 *   Adds "is-active" if location.pathname exactly matches href, or starts with href
 *   followed by "/". The "#" href is never considered active. For finer control use
 *   the boolean `active` attribute instead.
 *
 * Icon size tokens:
 *   xs → 0.75rem  |  sm → 0.875rem  |  md → 1rem  |  lg → 1.25rem  |  xl → 1.5rem  |  2x → 2rem
 *
 * Icon colour tokens:
 *   info → var(--rp-info)           |  success → var(--rp-success-soft-text)
 *   warning → var(--rp-warning-soft-text)  |  danger → var(--rp-danger-soft-text)
 *   muted → var(--rp-text-muted)    |  primary → var(--rp-primary)
 *
 * Examples:
 *   <!-- Text link (declarative content) -->
 *   <link-field href="/login/">Sign in</link-field>
 *
 *   <!-- Text link with icon prefix -->
 *   <link-field href="/login/" icon="bi-arrow-left">Sign in</link-field>
 *
 *   <!-- Text link with icon suffix -->
 *   <link-field href="/onboarding/" icon="arrow-right-circle-fill" icon-position="end" label="Get started"></link-field>
 *
 *   <!-- External link (auto-adds rel="noopener noreferrer") -->
 *   <link-field href="https://example.com" target="_blank" label="Docs"></link-field>
 *
 *   <!-- Muted secondary link -->
 *   <link-field href="/forgot-password/" variant="muted" label="Forgot password?"></link-field>
 *
 *   <!-- Icon-only action link (label provides accessible text) -->
 *   <link-field href="/projects/1/" icon="bi-eye" label="View project" variant="icon-btn" title="View project"></link-field>
 *
 *   <!-- Disabled link (click intercepted, aria-disabled set) -->
 *   <link-field href="/restricted/" disabled label="Restricted"></link-field>
 *
 *   <!-- Auto-active navigation link -->
 *   <link-field href="/projects/" auto-active label="Projects"></link-field>
 */
import { esc } from "../utils.js";

const NAMED_SIZES = {
  xs: "0.75rem",
  sm: "0.875rem",
  md: "1rem",
  lg: "1.25rem",
  xl: "1.5rem",
  "2x": "2rem",
};

const NAMED_COLORS = {
  info: "var(--rp-info)",
  success: "var(--rp-success-soft-text)",
  warning: "var(--rp-warning-soft-text)",
  danger: "var(--rp-danger-soft-text)",
  muted: "var(--rp-text-muted)",
  primary: "var(--rp-primary)",
};

const VARIANT_CLASSES = {
  link: "rp-link",
  muted: "rp-muted",
  "icon-btn": "rp-iconbtn",
  plain: "",
};

class LinkField extends HTMLElement {
  static get observedAttributes() {
    return [
      "href",
      "label",
      "icon",
      "icon-position",
      "target",
      "rel",
      "disabled",
      "active",
      "auto-active",
      "variant",
      "icon-size",
      "icon-color",
      "title",
    ];
  }

  connectedCallback() {
    // Capture declarative text content once, before _render() replaces innerHTML.
    // Guard with === undefined so reconnects (e.g. wizard moving the element) do not
    // overwrite the value captured on first connect.
    if (this._textContent === undefined) {
      this._textContent = this.textContent.trim();
    }
    this._connected = true;
    this._render();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this._connected && oldVal !== newVal) this._render();
  }

  // --- Attribute getters ---

  get _href() {
    return this.getAttribute("href") || "#";
  }

  get _label() {
    return this.getAttribute("label") || this._textContent || "";
  }

  get _icon() {
    const raw = this.getAttribute("icon") || "";
    if (!raw) return "";
    return raw.startsWith("bi-") ? raw : `bi-${raw}`;
  }

  get _iconPosition() {
    return this.getAttribute("icon-position") === "end" ? "end" : "start";
  }

  get _target() {
    return this.getAttribute("target") || "";
  }

  get _rel() {
    const explicit = (this.getAttribute("rel") || "").trim();
    if (this._target === "_blank") {
      // Always include noopener noreferrer for _blank links (reverse tabnapping prevention).
      const safety = ["noopener", "noreferrer"];
      const merged = new Set([...explicit.split(/\s+/), ...safety].filter(Boolean));
      return [...merged].join(" ");
    }
    return explicit;
  }

  get _disabled() {
    return this.hasAttribute("disabled");
  }

  get _active() {
    if (this.hasAttribute("active")) return true;
    if (this.hasAttribute("auto-active")) {
      const href = this._href;
      if (!href || href === "#") return false;
      // Normalise to trailing slash so "/projects" matches "/projects/1/".
      const normalized = href.replace(/\/?$/, "/");
      return location.pathname === href || location.pathname.startsWith(normalized);
    }
    return false;
  }

  get _variant() {
    const v = this.getAttribute("variant") || "link";
    return v in VARIANT_CLASSES ? v : "link";
  }

  get _iconSize() {
    const val = this.getAttribute("icon-size") || "";
    return NAMED_SIZES[val] ?? val;
  }

  get _iconColor() {
    const val = this.getAttribute("icon-color") || "";
    return NAMED_COLORS[val] ?? val;
  }

  get _title() {
    return this.getAttribute("title") || "";
  }

  // --- Icon HTML (always decorative; anchor or surrounding text carries the label) ---

  _iconHTML() {
    const icon = this._icon;
    if (!icon) return "";
    const size = this._iconSize;
    const color = this._iconColor;
    const styles = [size ? `font-size:${size}` : "", color ? `color:${color}` : ""]
      .filter(Boolean)
      .join(";");
    const styleAttr = styles ? ` style="${esc(styles)}"` : "";
    return `<i class="bi ${esc(icon)}" aria-hidden="true"${styleAttr}></i>`;
  }

  // --- Render ---

  _render() {
    const label = this._label;
    const variant = this._variant;
    const isIconBtn = variant === "icon-btn";
    // hasText: visible label content rendered alongside (or without) the icon
    const hasText = !!label && !isIconBtn;

    // Anchor CSS classes
    const variantClass = VARIANT_CLASSES[variant];
    const classes = [
      variantClass,
      this._active ? "is-active" : "",
      this._disabled ? "is-disabled" : "",
    ].filter(Boolean);
    const classAttr = classes.length ? ` class="${esc(classes.join(" "))}"` : "";

    // Anchor attributes
    const targetAttr = this._target ? ` target="${esc(this._target)}"` : "";
    const relAttr = this._rel ? ` rel="${esc(this._rel)}"` : "";
    const titleAttr = this._title ? ` title="${esc(this._title)}"` : "";
    // Disabled: remove from tab order; clicks are intercepted in the event listener below.
    const disabledAttrs = this._disabled ? ` aria-disabled="true" tabindex="-1"` : "";
    // Icon-only links carry their accessible label on the anchor element.
    const accessibleLabel = label || this._title;
    const ariaLabelAttr =
      !hasText && accessibleLabel ? ` aria-label="${esc(accessibleLabel)}"` : "";

    const iconStr = this._iconHTML();

    let content;
    if (isIconBtn || !hasText) {
      content = iconStr;
    } else {
      const parts = this._iconPosition === "end" ? [esc(label), iconStr] : [iconStr, esc(label)];
      content = parts.filter(Boolean).join(" ");
    }

    this.innerHTML = `<a href="${esc(this._href)}"${classAttr}${targetAttr}${relAttr}${titleAttr}${disabledAttrs}${ariaLabelAttr}>${content}</a>`;

    if (this._disabled) {
      this.querySelector("a").addEventListener("click", (e) => e.preventDefault());
    }
  }
}

customElements.define("link-field", LinkField);
