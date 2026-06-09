import { PanelModal } from "./panel-modal.js";

/* ConfirmModal  (exported base class — not registered as a custom element)
 *
 * Extends PanelModal with a confirm/cancel action pair. Renders optional body text and a
 * configurable action button. Subclasses override `_defaultActionLabel()`, `_actionBtnTag()`,
 * and `_actionBtnIcon()` to customise the action button appearance and variant.
 *
 * Inherited attributes:
 *   open, closeable  – from Modal
 *   title            – from PanelModal (modal heading)
 *
 * Additional attributes:
 *   body          – paragraph text shown in the modal body
 *   action-label  – label for the action button (falls back to `_defaultActionLabel()`)
 *
 * Events fired (all bubble):
 *   rp:confirm  – action button clicked
 *   rp:cancel   – cancel button clicked (modal also hides)
 *
 * Inheritance:
 *   ConfirmModal → ActivateModal
 *   ConfirmModal → DeactivateModal
 */
export class ConfirmModal extends PanelModal {
  static get observedAttributes() {
    return [...super.observedAttributes, "title", "body", "action-label"];
  }

  get _body() {
    return this.getAttribute("body") || "";
  }
  get _actionLabel() {
    return this.getAttribute("action-label") || this._defaultActionLabel();
  }

  _defaultActionLabel() {
    return "Confirm";
  }
  _actionBtnTag() {
    return "primary-button";
  }
  _actionBtnIcon() {
    return "";
  }

  _renderBody() {
    return this._body ? `<p>${this._esc(this._body)}</p>` : "";
  }

  _renderActionBtn() {
    const tag = this._actionBtnTag();
    const iconAttr = this._actionBtnIcon()
      ? ` prefix-icon="${this._esc(this._actionBtnIcon())}"`
      : "";
    return `<${tag} data-action-modal label="${this._esc(this._actionLabel)}"${iconAttr}></${tag}>`;
  }

  _bindContent() {
    this.querySelector("[data-cancel-modal]")?.addEventListener("click", () => {
      this.dispatchEvent(new CustomEvent("rp:cancel", { bubbles: true }));
      this.hide();
    });

    this.querySelector("[data-action-modal]")?.addEventListener("click", () => {
      this.dispatchEvent(new CustomEvent("rp:confirm", { bubbles: true }));
    });
  }
}
