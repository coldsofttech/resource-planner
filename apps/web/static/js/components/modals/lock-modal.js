import { ConfirmModal } from "./confirm-modal.js";

/* LockModal  <lock-modal>
 * Extends ConfirmModal with lock-specific styling and defaults.
 * Default action label: "Lock". Action button variant: primary-button (bi-lock-fill icon).
 * See confirm-modal.js for full attribute and event documentation. */
class LockModal extends ConfirmModal {
  get _modifierClass() {
    return "rp-modal-lock";
  }
  _defaultActionLabel() {
    return "Lock";
  }
  _actionBtnTag() {
    return "primary-button";
  }
  _actionBtnIcon() {
    return "bi-lock-fill";
  }
}

customElements.define("lock-modal", LockModal);
