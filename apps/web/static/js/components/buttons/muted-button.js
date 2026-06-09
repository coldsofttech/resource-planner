import { PrimaryButton } from "./primary-button.js";

/* MutedButton  <muted-button>
 * Extends PrimaryButton with variant "rp-btn-muted". Same attributes.
 * Typical use: cancel / back / secondary-action buttons.
 * See primary-button.js for full attribute / API documentation. */
class MutedButton extends PrimaryButton {
  get _variant() {
    return "rp-btn-muted";
  }
}

customElements.define("muted-button", MutedButton);
