import { PrimaryButton } from "./primary-button.js";

/* DeactivateButton  <deactivate-button>
 * Extends PrimaryButton with variant "rp-btn-deactivate". Same attributes.
 * See primary-button.js for full attribute / API documentation. */
class DeactivateButton extends PrimaryButton {
  get _variant() {
    return "rp-btn-deactivate";
  }
}

customElements.define("deactivate-button", DeactivateButton);
