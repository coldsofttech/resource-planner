import { ConfirmModal } from "./confirm-modal.js";

/* RejectModal  <reject-modal>
 * Extends ConfirmModal with reject-specific styling and defaults.
 * Default action label: "Reject". Action button variant: delete-button (bi-x-circle icon).
 * See confirm-modal.js for full attribute and event documentation. */
class RejectModal extends ConfirmModal {
  get _modifierClass() {
    return "rp-delete-modal";
  }
  _defaultActionLabel() {
    return "Reject";
  }
  _actionBtnTag() {
    return "delete-button";
  }
  _actionBtnIcon() {
    return "bi-x-circle";
  }
}

customElements.define("reject-modal", RejectModal);
