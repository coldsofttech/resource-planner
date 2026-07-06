import { ConfirmModal } from "./confirm-modal.js";

/* RestoreModal  <restore-modal>
 * Extends ConfirmModal with restore-specific styling and defaults.
 * Default action label: "Restore". Action button variant: primary-button (bi-arrow-counterclockwise icon).
 * See confirm-modal.js for full attribute and event documentation. */
class RestoreModal extends ConfirmModal {
  get _modifierClass() {
    return "rp-modal-restore";
  }
  _defaultActionLabel() {
    return "Restore";
  }
  _actionBtnTag() {
    return "primary-button";
  }
  _actionBtnIcon() {
    return "bi-arrow-counterclockwise";
  }
}

customElements.define("restore-modal", RestoreModal);
