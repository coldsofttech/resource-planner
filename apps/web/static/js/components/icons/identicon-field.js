/* IdenticonField  <identicon-field>
 *
 * Deterministic avatar component.
 *
 * Attributes:
 *   name     – Display name used to derive initials and colour palette seed. Required.
 *   variant  – "monogram" (default) | "initials" | "geometric"
 *   size     – "sm" | "md" (default) | "lg" | "xl"
 *   shape    – "rounded" (default for monogram) | "circle" (default for initials)
 *   bordered – Boolean. Adds a subtle ring shadow around the identicon.
 *   label    – Accessible label for the SVG. Defaults to the `name` value.
 *
 * Examples:
 *   <identicon-field name="Platform"></identicon-field>
 *   <identicon-field name="Mira Aslan" variant="initials"></identicon-field>
 *   <identicon-field name="Platform" size="lg" shape="circle"></identicon-field>
 *   <identicon-field name="Alpha Team" variant="monogram" size="sm" bordered></identicon-field>
 */

import { escSvg } from "../utils.js";

// Curated palettes (pleasing hue combinations)
const PALETTES = [
  ["#7c8aff", "#5867d8"],
  ["#f59e6c", "#d97c4f"],
  ["#7ce0c4", "#3aa57a"],
  ["#9c7cff", "#5e3ee0"],
  ["#ffd17a", "#d9a23a"],
  ["#f08fa0", "#d04a6a"],
  ["#9bd6f5", "#3e7fb4"],
  ["#f59ec3", "#c84d8a"],
  ["#aab2ff", "#4859d8"],
  ["#88e3a5", "#3aa15f"],
  ["#ffb39e", "#d96c5a"],
  ["#b69bff", "#7349c4"],
  ["#80d6e0", "#3097a8"],
  ["#ffc78a", "#d98b3a"],
  ["#9be3a3", "#449a52"],
  ["#f5b8e0", "#b855a0"],
  ["#a5c4ff", "#3a64c0"],
  ["#ffd9a0", "#c79330"],
];

function hash(str) {
  let h = 2166136261 >>> 0;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function rng(seed) {
  let s = seed >>> 0;
  return function () {
    s = Math.imul(s ^ (s >>> 15), 2246822507) >>> 0;
    s = Math.imul(s ^ (s >>> 13), 3266489909) >>> 0;
    s = (s ^ (s >>> 16)) >>> 0;
    return s / 4294967296;
  };
}

function initials(name) {
  const parts = String(name || "")
    .trim()
    .split(/[\s_\-.]+/)
    .filter(Boolean);
  if (parts.length === 0) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function renderMonogram(name) {
  const seed = hash(String(name || "x"));
  const r = rng(seed);
  const pal = PALETTES[Math.floor(r() * PALETTES.length)];
  const text = initials(name);
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" aria-hidden="true">
    <rect width="64" height="64" fill="${pal[1]}" opacity="0.16"/>
    <rect x="6" y="6" width="52" height="52" rx="12" fill="${pal[0]}" opacity="0.92"/>
    <text x="32" y="42" text-anchor="middle" font-family="Plus Jakarta Sans, system-ui, sans-serif" font-size="22" font-weight="800" fill="#fff" letter-spacing="-0.5">${escSvg(text)}</text>
  </svg>`;
}

function renderInitials(name) {
  const seed = hash(String(name || "x"));
  const r = rng(seed);
  const pal = PALETTES[Math.floor(r() * PALETTES.length)];
  const id = "rpi-" + (seed >>> 0).toString(36);
  const text = initials(name);
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" aria-hidden="true">
    <defs><linearGradient id="${id}" gradientTransform="rotate(135)"><stop offset="0" stop-color="${pal[0]}"/><stop offset="1" stop-color="${pal[1]}"/></linearGradient></defs>
    <rect width="64" height="64" fill="url(#${id})"/>
    <text x="32" y="42" text-anchor="middle" font-family="Plus Jakarta Sans, system-ui, sans-serif" font-size="26" font-weight="700" fill="#fff" letter-spacing="-0.5">${escSvg(text)}</text>
  </svg>`;
}

function renderGeometric(name) {
  const seed = hash(String(name || "x"));
  const r = rng(seed);
  const pal = PALETTES[Math.floor(r() * PALETTES.length)];
  const cells = 5;
  const cellSize = 64 / cells;
  let cellsSvg = "";
  for (let y = 0; y < cells; y++) {
    for (let x = 0; x < Math.ceil(cells / 2); x++) {
      if (r() > 0.5) {
        const mx = cells - 1 - x;
        const color = r() > 0.7 ? pal[0] : pal[1];
        cellsSvg += `<rect x="${x * cellSize}" y="${y * cellSize}" width="${cellSize}" height="${cellSize}" fill="${color}"/>`;
        if (x !== mx)
          cellsSvg += `<rect x="${mx * cellSize}" y="${y * cellSize}" width="${cellSize}" height="${cellSize}" fill="${color}"/>`;
      }
    }
  }
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" fill="${pal[1]}" opacity="0.18"/>${cellsSvg}</svg>`;
}

const VARIANTS = {
  monogram: renderMonogram,
  initials: renderInitials,
  geometric: renderGeometric,
};

const SIZE_CLASSES = new Set(["sm", "lg", "xl"]);

export class IdenticonField extends HTMLElement {
  static get observedAttributes() {
    return ["name", "variant", "size", "shape", "bordered", "no-border", "label"];
  }

  connectedCallback() {
    this._rendered = false;
    this._render();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this._rendered && oldVal !== newVal) this._render();
  }

  _render() {
    const name = this.getAttribute("name") || "";
    const variant = this.getAttribute("variant") || "monogram";
    const size = this.getAttribute("size") || "md";
    const defaultShape = variant === "initials" ? "circle" : "rounded";
    const shape = this.getAttribute("shape") || defaultShape;
    const bordered = this.hasAttribute("bordered");
    const noBorder = this.hasAttribute("no-border");
    const label = this.getAttribute("label") || name;

    // Apply CSS classes to self so identicons.css picks them up
    const classes = ["rp-identicon"];
    if (SIZE_CLASSES.has(size)) classes.push(size);
    if (shape === "circle") classes.push("circle");
    if (noBorder) classes.push("no-border");
    if (bordered) classes.push("bordered");
    this.className = classes.join(" ");

    // Accessibility
    this.setAttribute("role", "img");
    this.setAttribute("aria-label", label || "identicon");

    const fn = VARIANTS[variant] ?? VARIANTS.monogram;
    const doc = new DOMParser().parseFromString(fn(name), "image/svg+xml");
    this.replaceChildren(doc.documentElement);
    this._rendered = true;
  }
}

customElements.define("identicon-field", IdenticonField);
