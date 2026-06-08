import { PrimaryButton } from "./primary-button.js";

/* ActivateButton  <activate-button>
 * Extends PrimaryButton with variant "rp-btn-activate". Same attributes.
 * See primary-button.js for full attribute / API documentation. */
class ActivateButton extends PrimaryButton {
  get _variant() {
    return "rp-btn-activate";
  }
}

customElements.define("activate-button", ActivateButton);
