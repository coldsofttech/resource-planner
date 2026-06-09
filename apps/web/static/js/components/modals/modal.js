/* Modal  (exported base class — not registered as a custom element)
 *
 * Base class for all modal components. Provides open/close lifecycle, backdrop-click-to-close,
 * and an optional close button. Subclasses implement `_renderContent()` and `_bindContent()`.
 *
 * Attributes:
 *   open       – boolean; when present the modal is visible (managed via show()/hide())
 *   closeable  – string; set to "false" to remove the close button and disable backdrop-click-close
 *                (default: closeable unless explicitly set to "false")
 *
 * Public API:
 *   modal.show()   – sets the `open` attribute, making the modal visible
 *   modal.hide()   – removes the `open` attribute, hiding the modal
 *
 * Interactions:
 *   - Backdrop click closes the modal (unless closeable="false")
 *   - Close button (×) closes the modal (unless closeable="false")
 *
 * Inheritance:
 *   Modal → PanelModal → ConfirmModal → ActivateModal / DeactivateModal
 *   Modal → PanelModal → DeleteModal
 *   Modal → StatusModal
 */
import { esc } from "../utils.js";

export class Modal extends HTMLElement {
  static get observedAttributes() {
    return ["open", "closeable"];
  }

  connectedCallback() {
    this._render();
    this._bindGlobal();
  }

  attributeChangedCallback(name, oldVal, newVal) {
    if (this.isConnected && oldVal !== newVal) this._render();
  }

  get _isOpen() {
    return this.hasAttribute("open");
  }
  get _closeable() {
    return !this.hasAttribute("closeable") || this.getAttribute("closeable") !== "false";
  }

  show() {
    this.setAttribute("open", "");
  }
  hide() {
    this.removeAttribute("open");
  }

  _render() {
    this.className = ["rp-modal-back", this._modifierClass].filter(Boolean).join(" ");
    this.style.display = this._isOpen ? "grid" : "none";

    const closeBtn = this._closeable
      ? `<button class="rp-iconbtn" data-close-modal style="position:absolute;top:10px;right:10px;z-index:1"><i class="bi bi-x-lg"></i></button>`
      : "";

    this.innerHTML = `
      <div class="rp-modal" style="position:relative">
        ${closeBtn}
        ${this._renderContent()}
      </div>`;

    this.querySelector("[data-close-modal]")?.addEventListener("click", () => this.hide());
    this._bindContent();
  }

  get _modifierClass() {
    return "";
  }
  _renderContent() {
    return "";
  }
  _bindContent() {}

  _bindGlobal() {
    this.addEventListener("click", (e) => {
      if (e.target === this && this._closeable) this.hide();
    });
  }

  _esc(s) {
    return esc(s);
  }
}
