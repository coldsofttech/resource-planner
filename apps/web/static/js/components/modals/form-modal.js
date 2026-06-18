import { Modal } from "./modal.js";

/* FormModal  <form-modal>
 *
 * A general-purpose modal that hosts arbitrary slotted child content in its body. Child
 * nodes declared in HTML are captured before the first render and re-inserted each time
 * the modal re-renders (same pattern as DrawerModal). This preserves custom-element state
 * across open/close cycles.
 *
 * The inner `.rp-modal` panel uses `overflow: visible` so that dropdown fields (e.g.
 * `<member-field>`) whose lists are absolutely positioned are not clipped.
 *
 * Attributes:
 *   title          – heading text in the modal header
 *   primary-label  – label for the primary action button (default: "Confirm")
 *   primary-icon   – Bootstrap icon class for the primary button (e.g. "bi-check2")
 *   open, closeable – inherited from Modal
 *
 * Public API:
 *   modal.show()            – open the modal
 *   modal.hide()            – close the modal
 *   modal.setTitle(text)    – update the header title without a full re-render
 *
 * Events fired (all bubble):
 *   rp:primary  – primary action button clicked
 *   rp:cancel   – cancel / close button clicked
 *
 * Inheritance: Modal → FormModal
 */
class FormModal extends Modal {
  connectedCallback() {
    this._capturedNodes = Array.from(this.childNodes);
    super.connectedCallback();
  }

  get _title() {
    return this.getAttribute("title") || "";
  }
  get _primaryLabel() {
    return this.getAttribute("primary-label") || "Confirm";
  }
  get _primaryIcon() {
    return this.getAttribute("primary-icon") || "";
  }

  _render() {
    this.className = "rp-modal-back";
    this.style.display = this._isOpen ? "grid" : "none";

    this.innerHTML = `
      <div class="rp-modal" style="overflow:visible;max-width:520px;">
        <div class="rp-modal-head">
          <strong data-form-modal-title>${this._esc(this._title)}</strong>
          <button class="rp-iconbtn" data-close-modal aria-label="Close"><i class="bi bi-x-lg"></i></button>
        </div>
        <div class="rp-modal-body" style="overflow:visible;">
          <div data-form-modal-content></div>
        </div>
        <div class="rp-modal-foot">
          <muted-button data-cancel-modal label="Cancel"></muted-button>
          <primary-button data-primary-modal prefix-icon="${this._esc(this._primaryIcon)}" label="${this._esc(this._primaryLabel)}"></primary-button>
        </div>
      </div>`;

    const content = this.querySelector("[data-form-modal-content]");
    if (content && this._capturedNodes) {
      this._capturedNodes.forEach((node) => content.appendChild(node));
    }

    this.querySelector("[data-close-modal]")?.addEventListener("click", () => this.hide());
    this.querySelector("[data-cancel-modal]")?.addEventListener("click", () => {
      this.hide();
      this.dispatchEvent(new CustomEvent("rp:cancel", { bubbles: true }));
    });
    this.querySelector("[data-primary-modal]")?.addEventListener("click", () => {
      this.dispatchEvent(new CustomEvent("rp:primary", { bubbles: true }));
    });
  }

  _bindContent() {}

  setTitle(text) {
    const el = this.querySelector("[data-form-modal-title]");
    if (el) el.textContent = text;
  }
}

customElements.define("form-modal", FormModal);
