import { ConfirmModal } from "./confirm-modal.js";

/* ActivateModal  <activate-modal>
 * Extends ConfirmModal with activate-specific styling and defaults.
 * Default action label: "Activate". Action button variant: activate-button (bi-toggle-on icon).
 * See confirm-modal.js for full attribute and event documentation. */
class ActivateModal extends ConfirmModal {
  get _modifierClass() {
    return "rp-modal-activate";
  }
  _defaultActionLabel() {
    return "Activate";
  }
  _actionBtnTag() {
    return "activate-button";
  }
  _actionBtnIcon() {
    return "bi-toggle-on";
  }
}

customElements.define("activate-modal", ActivateModal);
