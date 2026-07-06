import { ConfirmModal } from "./confirm-modal.js";

/* ResyncModal  <resync-modal>
 * Extends ConfirmModal with resync-specific styling and defaults.
 * Default action label: "Resync". Action button variant: primary-button (bi-arrow-repeat icon).
 * See confirm-modal.js for full attribute and event documentation. */
class ResyncModal extends ConfirmModal {
  get _modifierClass() {
    return "rp-modal-resync";
  }
  _defaultActionLabel() {
    return "Resync";
  }
  _actionBtnTag() {
    return "primary-button";
  }
  _actionBtnIcon() {
    return "bi-arrow-repeat";
  }
}

customElements.define("resync-modal", ResyncModal);
