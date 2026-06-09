import { PrimaryButton } from "./primary-button.js";

/* DeleteButton  <delete-button>
 * Extends PrimaryButton with variant "rp-btn-delete" (red / destructive). Same attributes.
 * See primary-button.js for full attribute / API documentation. */
class DeleteButton extends PrimaryButton {
  get _variant() {
    return "rp-btn-delete";
  }
}

customElements.define("delete-button", DeleteButton);
