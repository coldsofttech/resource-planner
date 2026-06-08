import { PanelModal } from "./panel-modal.js";

/* DeleteModal  <delete-modal>
 *
 * Extends PanelModal with a destructive delete action. Optionally gates the action behind a
 * text-confirmation input: when `confirm-value` is set, the Delete button stays disabled until
 * the user types the exact confirmation string.
 *
 * Inherited attributes:
 *   open, closeable  – from Modal
 *   title            – from PanelModal (modal heading)
 *
 * Additional attributes:
 *   body                 – explanatory text shown in the modal body
 *   confirm-value        – string the user must type to enable the Delete button; omit to skip gate
 *   confirm-placeholder  – placeholder text for the confirmation input; defaults to
 *                          `Type "confirm-value" to confirm` when confirm-value is set
 *   action-label         – label for the Delete button (default "Delete")
 *
 * Events fired (all bubble):
 *   rp:delete   – Delete button clicked (guard passed if confirm-value was set)
 *   rp:cancel   – Cancel button clicked (modal also hides)
 */
class DeleteModal extends PanelModal {
  static get observedAttributes() {
    return [
      ...super.observedAttributes,
      "title",
      "body",
      "confirm-value",
      "confirm-placeholder",
      "action-label",
    ];
  }

  get _body() {
    return this.getAttribute("body") || "";
  }
  get _confirmValue() {
    return this.getAttribute("confirm-value") || "";
  }
  get _confirmPlaceholder() {
    const override = this.getAttribute("confirm-placeholder");
    if (override) return override;
    return this._confirmValue ? `Type "${this._confirmValue}" to confirm` : "";
  }
  get _actionLabel() {
    return this.getAttribute("action-label") || "Delete";
  }

  get _modifierClass() {
    return "rp-delete-modal";
  }

  _renderBody() {
    const bodyHTML = this._body ? `<p class="mb-2">${this._esc(this._body)}</p>` : "";

    const textHTML = this._confirmValue
      ? `<text-field
           id="rp-modal-delete-confirm-text"
           data-confirm-text
           col="col-12"
           placeholder="${this._esc(this._confirmPlaceholder)}"
           autocomplete="off"
         ></text-field>`
      : "";

    const fieldsHTML = textHTML ? `<div class="row g-2">${textHTML}</div>` : "";

    return bodyHTML + fieldsHTML;
  }

  _renderActionBtn() {
    return `<delete-button
               data-delete-modal
               label="${this._esc(this._actionLabel)}"
               prefix-icon="bi-trash3"
               ${this._confirmValue ? "disabled" : ""}
             ></delete-button>`;
  }

  _bindContent() {
    this.querySelector("[data-cancel-modal]")?.addEventListener("click", () => {
      this.dispatchEvent(new CustomEvent("rp:cancel", { bubbles: true }));
      this.hide();
    });

    const textField = this.querySelector("[data-confirm-text]");
    const deleteBtn = this.querySelector("[data-delete-modal]");

    if (textField && deleteBtn) {
      textField.addEventListener("input", () => {
        const value = textField.querySelector(".rp-input")?.value ?? "";
        if (value === this._confirmValue) {
          deleteBtn.removeAttribute("disabled");
        } else {
          deleteBtn.setAttribute("disabled", "");
        }
      });
    }

    deleteBtn?.addEventListener("click", () => {
      this.dispatchEvent(new CustomEvent("rp:delete", { bubbles: true }));
    });
  }
}

customElements.define("delete-modal", DeleteModal);
