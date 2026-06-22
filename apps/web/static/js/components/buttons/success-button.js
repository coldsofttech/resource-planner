import { PrimaryButton } from "./primary-button.js";

/* SuccessButton  <success-button>
 * Extends PrimaryButton with variant "rp-btn-success". Same attributes.
 * Typical use: confirm, approve, or complete actions.
 * See primary-button.js for full attribute / API documentation. */
class SuccessButton extends PrimaryButton {
  get _variant() {
    return "rp-btn-success";
  }
}

customElements.define("success-button", SuccessButton);
