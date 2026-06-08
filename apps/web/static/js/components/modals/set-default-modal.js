import { ConfirmModal } from "./confirm-modal.js";

/* SetDefaultModal  <set-default-modal>
 * Extends ConfirmModal with set-default-specific styling and defaults.
 * Default action label: "Set as Default". Action button variant: primary-button (bi-star-fill icon).
 * See confirm-modal.js for full attribute and event documentation. */
class SetDefaultModal extends ConfirmModal {
  get _modifierClass() {
    return "rp-modal-set-default";
  }
  _defaultActionLabel() {
    return "Set as Default";
  }
  _actionBtnTag() {
    return "primary-button";
  }
  _actionBtnIcon() {
    return "bi-star-fill";
  }
}

customElements.define("set-default-modal", SetDefaultModal);
