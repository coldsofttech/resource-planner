"use strict";

import { esc } from "../../utils.js";

/* UserAvatar  <user-avatar>
 *
 * Circular avatar display for user/member rows, drawers, and any other
 * context that needs to render a user photo with an initials fallback.
 *
 * Applies rp-avatar (and the appropriate size modifier) directly to itself so
 * it can be dropped in anywhere an rp-avatar div would have been used.
 *
 * Attributes:
 *   avatar-url  — photo URL; absent or empty triggers the initials fallback
 *   name        — display name used for alt text and initials derivation
 *   size        — "sm" | "md" (default, 32 px) | "lg" | "xl"
 *
 * Usage:
 *   <user-avatar name="Mira Aslan" size="sm"></user-avatar>
 *   <user-avatar avatar-url="/media/avatars/1.jpg" name="Mira Aslan" size="lg"></user-avatar>
 *
 *   <!-- setting attributes from JS after data loads -->
 *   el.setAttribute("avatar-url", row.avatar_url || "");
 *   el.setAttribute("name", name);
 */

const _SIZE_CLASS = { sm: "rp-avatar--sm", lg: "rp-avatar--lg", xl: "rp-avatar--xl" };

function _initials(name) {
  const parts = String(name || "")
    .trim()
    .split(/\s+/)
    .filter(Boolean);
  if (!parts.length) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

function _initialsFromSeed(seed) {
  const parts = String(seed || "")
    .trim()
    .split(/[\s@._-]+/)
    .filter(Boolean);
  if (!parts.length) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

class UserAvatar extends HTMLElement {
  static get observedAttributes() {
    return ["avatar-url", "name", "size", "seed"];
  }

  connectedCallback() {
    this._rendered = false;
    this._render();
  }

  attributeChangedCallback(attr, oldVal, newVal) {
    if (this._rendered && oldVal !== newVal) this._render();
  }

  _render() {
    const avatarUrl = this.getAttribute("avatar-url") || "";
    const name = this.getAttribute("name") || "";
    const seed = this.getAttribute("seed") || "";
    const size = this.getAttribute("size") || "md";

    const sizeClass = _SIZE_CLASS[size] || null;
    this.className = sizeClass ? `rp-avatar ${sizeClass}` : "rp-avatar";

    const fallbackInitials = seed ? _initialsFromSeed(seed) : _initials(name);

    if (avatarUrl) {
      this.innerHTML = `<img src="${esc(avatarUrl)}" alt="${esc(name)}" style="width:100%;height:100%;object-fit:cover;display:block;" data-ua-img />`;
      this.querySelector("[data-ua-img]")?.addEventListener("error", () => {
        this.textContent = fallbackInitials;
      });
    } else {
      this.textContent = fallbackInitials;
    }

    this._rendered = true;
  }
}

customElements.define("user-avatar", UserAvatar);
