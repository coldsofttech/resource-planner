import { ConfirmModal } from "./confirm-modal.js";

/* DeactivateModal  <deactivate-modal>
 * Extends ConfirmModal with deactivate-specific styling and defaults.
 * Default action label: "Deactivate". Action button variant: deactivate-button (bi-toggle-off icon).
 * See confirm-modal.js for full attribute and event documentation. */
class DeactivateModal extends ConfirmModal {
  get _modifierClass() {
    return "rp-modal-deactivate";
  }
  _defaultActionLabel() {
    return "Deactivate";
  }
  _actionBtnTag() {
    return "deactivate-button";
  }
  _actionBtnIcon() {
    return "bi-toggle-off";
  }
}

customElements.define("deactivate-modal", DeactivateModal);
