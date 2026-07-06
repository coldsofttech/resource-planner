import { ConfirmModal } from "./confirm-modal.js";

/* AcceptModal  <accept-modal>
 * Extends ConfirmModal with accept-specific styling and defaults.
 * Default action label: "Accept". Action button variant: success-button (bi-check-circle-fill icon).
 * See confirm-modal.js for full attribute and event documentation. */
class AcceptModal extends ConfirmModal {
  get _modifierClass() {
    return "rp-modal-activate";
  }
  _defaultActionLabel() {
    return "Accept";
  }
  _actionBtnTag() {
    return "success-button";
  }
  _actionBtnIcon() {
    return "bi-check-circle-fill";
  }
}

customElements.define("accept-modal", AcceptModal);
