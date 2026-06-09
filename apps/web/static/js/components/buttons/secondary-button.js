import { PrimaryButton } from "./primary-button.js";

/* SecondaryButton  <secondary-button>
 * Extends PrimaryButton with variant "rp-btn-secondary". Same attributes.
 * See primary-button.js for full attribute / API documentation. */
class SecondaryButton extends PrimaryButton {
  get _variant() {
    return "rp-btn-secondary";
  }
}

customElements.define("secondary-button", SecondaryButton);
