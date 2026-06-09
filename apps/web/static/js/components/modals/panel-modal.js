import { Modal } from "./modal.js";

/* PanelModal  (exported base class — not registered as a custom element)
 *
 * Extends Modal with a structured head / body / foot panel layout. Renders a title bar with a
 * close button and a Cancel button in the footer. Subclasses implement `_renderBody()` and
 * `_renderActionBtn()` to populate the body and the primary action button.
 *
 * Inherited attributes:
 *   open, closeable  – from Modal
 *
 * Additional attributes:
 *   title  – heading text displayed in the modal header bar
 *
 * Inheritance:
 *   PanelModal → ConfirmModal → ActivateModal / DeactivateModal
 *   PanelModal → DeleteModal
 */
export class PanelModal extends Modal {
  get _title() {
    return this.getAttribute("title") || "";
  }

  _render() {
    this.className = ["rp-modal-back", this._modifierClass].filter(Boolean).join(" ");
    this.style.display = this._isOpen ? "grid" : "none";

    this.innerHTML = `
      <div class="rp-modal">
        <div class="rp-modal-head">
          <strong>${this._esc(this._title)}</strong>
          <button class="rp-iconbtn" data-close-modal><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="rp-modal-body">
          ${this._renderBody()}
        </div>
        <div class="rp-modal-foot">
          <muted-button data-cancel-modal label="Cancel"></muted-button>
          ${this._renderActionBtn()}
        </div>
      </div>`;

    this.querySelector("[data-close-modal]")?.addEventListener("click", () => this.hide());
    this._bindContent();
  }

  _renderBody() {
    return "";
  }
  _renderActionBtn() {
    return "";
  }
}
