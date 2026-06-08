"use strict";

import { apiFetch } from "../../../modules/utils/utils.js";
import { toast } from "../../../modules/utils/toast.js";
import { API_URLS } from "../../../modules/main/urls.js";

/* UserAvatarProfile  <user-avatar-profile>
 *
 * Avatar card for the profile page. Renders a large circular avatar with a
 * camera-icon overlay to upload a new image. Falls back to an identicon when
 * no avatar has been set. For SSO-provisioned accounts the camera button is
 * rendered disabled with a tooltip.
 *
 * Attributes:
 *   avatar-url  — URL of the current avatar image, or absent/empty for identicon
 *   seed        — identicon seed (typically email)
 *   is-sso      — if present (any value), the upload button is disabled
 *   sso-name    — SSO provider name shown in the disabled tooltip
 *
 * Events dispatched on the element:
 *   rp:avatar:changed  — fired after a successful upload; detail = { avatarUrl }
 *
 * Usage:
 *   <user-avatar-profile id="profile-avatar" seed="user@example.com"></user-avatar-profile>
 *   <user-avatar-profile avatar-url="/api/v1/users/me/avatar/" seed="user@example.com" is-sso sso-name="Google"></user-avatar-profile>
 */

const _ALLOWED_TYPES = ["image/jpeg", "image/png", "image/gif", "image/webp"];
const _MAX_MB = 5;

class UserAvatarProfile extends HTMLElement {
  static get observedAttributes() {
    return ["avatar-url", "seed", "is-sso", "sso-name"];
  }

  connectedCallback() {
    this._render();
  }

  attributeChangedCallback() {
    if (this.isConnected) this._render();
  }

  // ── Public API ────────────────────────────────────────────────────────────

  setAvatar(url) {
    this.setAttribute("avatar-url", url);
  }

  // ── Private ───────────────────────────────────────────────────────────────

  _render() {
    const avatarUrl = this.getAttribute("avatar-url") || "";
    const seed = this.getAttribute("seed") || "user";
    const isSso = this.hasAttribute("is-sso");
    const ssoName = this.getAttribute("sso-name") || "your SSO provider";

    const cameraDisabledAttr = isSso ? "disabled" : "";
    const cameraTitle = isSso ? `Avatar is managed by ${ssoName}` : "Change avatar";

    this.innerHTML = `
      <div class="rp-user-avatar-wrap">
        <div class="rp-user-avatar-img" data-avatar-display>
          ${avatarUrl ? this._imgTag(avatarUrl, seed) : this._identiconSvg(seed)}
        </div>
        <button
          type="button"
          class="rp-user-avatar-camera${isSso ? " rp-user-avatar-camera--disabled" : ""}"
          title="${cameraTitle}"
          aria-label="${cameraTitle}"
          ${cameraDisabledAttr}
          data-camera-btn
        >
          <i class="bi bi-camera-fill"></i>
        </button>
        <input type="file" accept="image/jpeg,image/png,image/gif,image/webp" hidden data-file-input />
      </div>
    `;

    if (!isSso) {
      this.querySelector("[data-camera-btn]").addEventListener("click", () => {
        this.querySelector("[data-file-input]").click();
      });
      this.querySelector("[data-file-input]").addEventListener("change", (e) => {
        const file = e.target.files?.[0];
        if (file) this._handleUpload(file);
        e.target.value = "";
      });
    }

    // Bind image error handler via JS to avoid broken HTML from SVG special chars in onerror attr.
    const img = this.querySelector(".rp-user-avatar-photo");
    if (img) {
      const seed = this.getAttribute("seed") || "user";
      img.addEventListener("error", () => {
        const display = this.querySelector("[data-avatar-display]");
        if (display) display.innerHTML = this._identiconSvg(seed);
      });
    }
  }

  _imgTag(url) {
    return `<img src="${url}" alt="Avatar" class="rp-user-avatar-photo" />`;
  }

  _identiconSvg(seed) {
    if (typeof window.rpIdenticon !== "function") {
      const initials = this._initials(seed);
      return `<div class="rp-avatar rp-avatar--xl">${initials}</div>`;
    }
    const svg = window.rpIdenticon(seed, { style: "initials", name: seed });
    return `<div class="rp-user-avatar-identicon">${svg}</div>`;
  }

  _initials(seed) {
    const parts = String(seed || "")
      .trim()
      .split(/[\s@._-]+/)
      .filter(Boolean);
    if (!parts.length) return "?";
    if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
    return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  }

  async _handleUpload(file) {
    if (!_ALLOWED_TYPES.includes(file.type)) {
      toast({
        type: "error",
        title: "Invalid file",
        message: "Please upload a JPEG, PNG, GIF, or WEBP image.",
      });
      return;
    }
    if (file.size > _MAX_MB * 1024 * 1024) {
      toast({
        type: "error",
        title: "File too large",
        message: `Maximum avatar size is ${_MAX_MB} MB.`,
      });
      return;
    }

    const btn = this.querySelector("[data-camera-btn]");
    if (btn) btn.disabled = true;

    try {
      const formData = new FormData();
      formData.append("avatar", file);

      const { href, method } = API_URLS.users.uploadAvatar();
      // Pass Content-Type: undefined so apiFetch's header filter strips it,
      // letting the browser set multipart/form-data with the correct boundary.
      const resp = await apiFetch(href, {
        method,
        headers: { "Content-Type": undefined },
        body: formData,
      });

      const newUrl = resp?.data?.avatar_url || "/api/v1/users/me/avatar/";
      const bustedUrl = `${newUrl}?t=${Date.now()}`;
      this.setAttribute("avatar-url", bustedUrl);

      this.dispatchEvent(
        new CustomEvent("rp:avatar:changed", {
          bubbles: true,
          detail: { avatarUrl: bustedUrl },
        }),
      );

      toast({
        type: "success",
        title: "Avatar updated",
        message: "Your new avatar has been saved.",
      });
    } catch (err) {
      toast({
        type: "error",
        title: "Upload failed",
        message: err?.data?.error?.message || "Could not upload avatar.",
      });
    } finally {
      if (btn) btn.disabled = false;
    }
  }
}

customElements.define("user-avatar-profile", UserAvatarProfile);
